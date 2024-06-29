from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotFound

from django.db.transaction import atomic
from django.core.exceptions import ObjectDoesNotExist

import re

from users_manager.models import User
from .models import Wallet, SyriatelCashAccount, PaymentGatewayChoices, WalletPaymentGateways, UserWalletView, Transaction

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"

class SyriatelCashAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyriatelCashAccount
        fields = "__all__"

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

class ListTransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
    
    receiver_wallet = WalletSerializer()
    sender_wallet = WalletSerializer()


PAYMENT_GATEWAYS = [
    (PaymentGatewayChoices.SYRIATEL_CASH , "Syriatel Cash"),
]


class WalletPaymentGatewaySerailizer(serializers.Serializer):
    pin_code = serializers.CharField(max_length=4, min_length=4, allow_blank=False)
    syriatel_account = SyriatelCashAccountSerializer()

    def get_current_user_phone_number(self):
        request = self.context.get("request" , None)
        return request.user.username

    def validate_pin_code(self, pin_code):
        pattern = re.compile("[0-9]+")
        if len(pin_code) == 4 and re.fullmatch(pattern , pin_code):
            return pin_code
        raise ValidationError("pin code is not valid")
    
    def validate(self, data):
        phone_number = self.get_current_user_phone_number()
        pin_code = data.get("pin_code", "")
        syriatel_cash_account = data.get("syriatel_account")

        user = User.objects.get(username = phone_number)
        try:
            Wallet.objects.get(owner = user)
            
        except ObjectDoesNotExist:
            validated_data = {
                "pin_code" : self.validate_pin_code(pin_code), 
                "syriatel_account" : syriatel_cash_account
            }

            self._validated_data = validated_data
            return validated_data


        raise ValidationError("you already have a wallet")
        

    def create(self, validated_data):
        phone_number = self.get_current_user_phone_number()
        account_serializer = SyriatelCashAccountSerializer(data=validated_data.get("syriatel_account"))
        
        try:
            owner = User.objects.get(username= phone_number)
        
        except ObjectDoesNotExist:
            raise NotFound("no users have the entered phone number")

        if not account_serializer.is_valid():
            raise ValidationError("syriatel cash account information is not valid")    

        with atomic():
            syriatel_cash_account = account_serializer.save()
            wallet = Wallet.objects.create(
                owner= owner, 
                pin_code= validated_data.get("pin_code"),
            )
            wallet.save()
            wallet_payment_gateway = WalletPaymentGateways.objects.create(
                method_id = PaymentGatewayChoices.SYRIATEL_CASH, 
                wallet = wallet,
                account_id = syriatel_cash_account.id
            )
            wallet_payment_gateway.save()

        return {
            "pin_code" : validated_data.get("pin_code"),
            "syriatel_account" : syriatel_cash_account
        }


class UserWalletViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWalletView
        fields = "__all__"


class TransferMoneySerializer(serializers.Serializer):
    receiver_wallet_uuid = serializers.UUIDField()
    amount = serializers.FloatField()
    pin_code = serializers.CharField(max_length=4, min_length=4)


class ChargeWalletSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=PAYMENT_GATEWAYS)
    charging_amount = serializers.FloatField()

    def validate(self, attrs):
        return super().validate(attrs)

