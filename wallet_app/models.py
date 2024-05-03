from django.db import models
from users_manager.models import User
import uuid

# Create your models here.
"""
    For the current version of the systme
    wallet will have only one type (default type)
"""
class Wallet(models.Model):
    owner = models.OneToOneField(to=User, name="owner", on_delete=models.CASCADE , blank=False)
    balance = models.FloatField(name="balance" , default=0.0)
    pin_code = models.CharField(name="pin_code" , blank=False , max_length=4)
    wallet_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now=True)

class PaymentGatewayChoices(models.IntegerChoices):
    SYRIATEL_CASH = 0

class PaymentAccount(models.Model):
    class Meta:
        abstract = True

"""
    SyriatelCashAccount will contain the account's details
    this information going to be fetched from a third-party API 
    (which is the syriatel-cash API in this case)
    all operations on this model will depend on the gateway's API
"""
class SyriatelCashAccount(models.Model):
    class Meta:
        db_table = "wallet_app_syriatel_cash"

    account_number = models.CharField(max_length=10 , name="account_number" , unique=True, blank=False)
    account_code = models.CharField(max_length=4 , name="account_code" , blank=False)

"""
    We can provide different payment methods for the same wallet
    so we have this relation, where method_id defines the payment method
    and account_id defines the payment account (i.e SyriatelCashAccount)
"""
class WalletPaymentGateways(models.Model):
    class Meta:
        db_table = "wallet_app_payment_gateways"

    method_id = models.IntegerField(name="method_id" , db_index=True,blank= False, choices=PaymentGatewayChoices.choices)
    account_id = models.IntegerField(blank=False, name="account_id")

    wallet = models.ForeignKey(to=Wallet, name="wallet" , blank=False, on_delete=models.CASCADE)
    provided_at = models.DateTimeField(auto_now=True)

    primary_key = ["method_id" , "account_id"]

class WalletSyriatelGateways(WalletPaymentGateways):
    class Meta:
        proxy = True
    objects = WalletPaymentGateways.objects.filter(method_id = PaymentGatewayChoices.SYRIATEL_CASH)

"""
    Transaction model
    to store all payment transactions inside the system
"""
class Transaction(models.Model):
    sender_wallet = models.ForeignKey(to=Wallet, name="sender_wallet", related_name="sender_wallet" , on_delete=models.CASCADE)
    receiver_wallet = models.ForeignKey(to=Wallet, name="receiver_wallet", related_name="receiver_wallet", on_delete=models.CASCADE)
    amount = models.FloatField(name="amount")
    created_at = models.DateTimeField(auto_now=True)


"""
    UserWalletView Model
    Represents a view that contain wallets and their owners
"""
class UserWalletView(models.Model):
    class Meta:
        managed = False
        db_table = "user_wallet_view"
    phone_number = models.CharField(max_length=100 , blank=False, unique=True , name="phone_number")
    first_name = models.CharField(max_length=100, blank=False, name="first_name")
    last_name = models.CharField(max_length=100, blank=False, name="last_name")
    birth_date = models.DateField(name="birth_date" , blank=False, null=False)
    gender = models.CharField(name="gender" , blank=False, max_length=10)

    wallet_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    balance = models.FloatField(name="balance")
    pin_code = models.CharField(name="pin_code" , blank=False , max_length=4)
    created_at = models.DateTimeField(name="created_ats")

