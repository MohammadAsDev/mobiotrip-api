from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status

from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

import random

from .serializers import *
from .models import Wallet, WalletSyriatelGateways , SyriatelCashAccount, Transaction, PaymentGatewayChoices
from .permissions import IsOwnerOrStaff

# Create your views here.
"""
    Wallet API CRUD
"""
class WalletsList(generics.ListAPIView):
    serializer_class = WalletSerializer
    queryset = Wallet.objects.all()
    permission_classes = [IsAdminUser, ]

class CreateWallet(generics.CreateAPIView):
    serializer_class = WalletPaymentGatewaySerailizer
    permission_classes = [IsAuthenticated,]


class WalletDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WalletSerializer
    queryset = Wallet.objects.all()
    permission_classes = [IsOwnerOrStaff, ]

"""
    Charge your wallet using provided gateways
"""
class ChargeWallet(APIView):
    permission_classes = [IsAuthenticated, ]

    def get_user_wallet(self, user : User):
        try:
            user_wallet = Wallet.objects.get(owner = user)
        except ObjectDoesNotExist:
            return None
        return user_wallet

    """
        Note: this function should connect to syriatel cash service 
        but for now, we want to fake this operation.
    """
    def check_account_balance(self):
        return random.randint(1 , 1_000_000) % 2 == 0

    def do_charge(self , payment_account : SyriatelCashAccount, wallet : Wallet,  amount):
        print("Sending a request to syriatel cash, to update account with id. ({})".format(payment_account.account_number))
        wallet.balance += amount
        wallet.save()

    def post(self, request, format=None):
        serializer = ChargeWalletSerializer(data= request.data)
        user_wallet = self.get_user_wallet(request.user)
        
        if not user_wallet:
            return Response({"details" : "You don't have a wallet, please create one."} , status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            payment_method = serializer.data.get("payment_method")
            charging_amount = serializer.data.get("charging_amount")
            
            if payment_method == PaymentGatewayChoices.SYRIATEL_CASH:
                try:
                    syriatel_payment_method = WalletSyriatelGateways.objects.get(wallet = user_wallet)
                
                except ObjectDoesNotExist:
                    return Response({"details" : "Your wallet does not provide syriatel cash as payment method"} , status=status.HTTP_400_BAD_REQUEST)
                
                syriate_accout = SyriatelCashAccount.objects.get(pk = syriatel_payment_method.account_id)
                
                if not self.check_account_balance():
                    return Response({"details" : "your account does not have enough balance"}, status=status.HTTP_400_BAD_REQUEST)
                
                with atomic():
                    self.do_charge(syriate_accout , user_wallet , charging_amount)
                
                return Response(data= {"status" : "completed" , "gateway" : "syriatel cash"}, status=status.HTTP_200_OK)
    
        return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)

"""
    Transfer money from your wallet to another wallets.
"""
class TransferMoney(APIView):   
    permission_classes = [IsAuthenticated, ]

    def get_user_wallet(self, user : User):
        try:
            user_wallet = Wallet.objects.get(owner = user)
        except ObjectDoesNotExist:
            return None
        return user_wallet

    def do_transaction(self ,sender_wallet : Wallet, receiver_wallet : Wallet , amount):
        transaction = Transaction()
        transaction.amount = amount
        transaction.sender_wallet = sender_wallet
        transaction.receiver_wallet = receiver_wallet
        transaction.save()

        sender_wallet.balance -= amount
        sender_wallet.save()

        receiver_wallet.balance += amount
        receiver_wallet.save()

        return transaction

    def post(self,request, format=None):
        transfer_money_serializer = TransferMoneySerializer(data= request.data)
        user = request.user
        
        user_wallet = self.get_user_wallet(user)
        if not user_wallet:
            return Response({"details" : "You don't have a wallet, please create one."} , status=status.HTTP_400_BAD_REQUEST)    
        
        if transfer_money_serializer.is_valid():
            transaction_data = transfer_money_serializer.data 
            receiver_uuid = transaction_data.get("receiver_wallet_uuid")

            try:
                receiver_wallet = Wallet.objects.get(wallet_uuid = receiver_uuid)
            except:
                return Response({"details" : "recieved wallet does not found in the system"} , status=status.HTTP_400_BAD_REQUEST)
        
            amount = transaction_data.get("amount")
            if user_wallet.balance - amount < 0:
                return Response({"details" : "your wallet balance is not enough"})
            
            with atomic():
                transaction = self.do_transaction(user_wallet , receiver_wallet , amount)
            
            transaction_response = TransactionSerializer(transaction).data
            return Response(data=transaction_response , status=status.HTTP_201_CREATED)
        
        return Response(transfer_money_serializer.errors , status=status.HTTP_400_BAD_REQUEST)

