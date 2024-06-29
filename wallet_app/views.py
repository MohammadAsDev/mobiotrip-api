from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework import views

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

class MyWalletView(APIView):

    def get(self, request, format=None):
        user_id = request.user.id
        wallet= Wallet.objects.filter(owner=user_id)
        if not wallet:
            return Response({"details" : "you don't have a wallet"} , status=status.HTTP_404_NOT_FOUND)
        wallet_data = WalletSerializer(wallet[0])
        return Response(wallet_data.data)


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


class RetrieveUserWalletInfo(generics.RetrieveAPIView):
    serializer_class = UserWalletViewSerializer
    queryset = UserWalletView.objects.all()
    permission_classes = [IsOwnerOrStaff]

class TransactionsList(generics.ListAPIView):
    permission_classes = [IsAdminUser, ]
    serializer_class = ListTransactionsSerializer
    queryset = Transaction.objects.all()

    def _reformat_response(self, response_data):
        reformated_response = []
        for transaction in response_data:
            reformated_response.append({
                "id" : transaction["id"],
                "amount": transaction["amount"],
                "created_at": transaction["created_at"],
                "sender_wallet_uuid" : transaction["sender_wallet"]["wallet_uuid"],
                "receiver_wallet_uuid" : transaction["receiver_wallet"]["wallet_uuid"]
            })

        return reformated_response

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(self._reformat_response(serializer.data))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IncomeReport(views.APIView):
    permission_classes = [IsAdminUser, ]
    def get(self, request, format=None):
        total_income = random.randint(100_000 , 10_000_000)
        is_increased = False if random.randint(0 , 1) == 0 else True
        profit_amount = random.random()
        profits =  profit_amount if is_increased else -1 * profit_amount
        return Response({
            "total_income" : f"{total_income:,}",
            "profits" : f"{profits:.2f}"
        })       

class TransactionsReport(views.APIView):
    permission_classes = [IsAdminUser, ]
    def get(self, request, format = None):
        total_transactions = random.randint(5_000 , 100_000)
        is_increased = False if random.randint(0 , 1) == 0 else True
        increasing_amount = random.random()
        increasing_rate =  increasing_amount if is_increased else -1 * increasing_amount
        return Response({
            "total_transactions" : f"{total_transactions:,}" , 
            "transactions_rate" : f"{increasing_rate:.2f}"
        })

class EwalletsReport(views.APIView):
    permission_classes = [IsAdminUser, ]
    def get(self, request, format= None):
        total_ewallets = random.randint(2_000, 10_000)
        is_increased = False if random.randint(0 , 1) == 0 else True
        increasing_amount = random.random()
        increasing_rate =  increasing_amount if is_increased else -1 * increasing_amount
        return Response({
            "total_ewallets" : f"{total_ewallets:,}" , 
            "ewallets_rate" : f"{increasing_rate:.2f}"
        })

class TripsIncomeReport(views.APIView):
    permission_classes = [IsAdminUser, ]

    def get(self, request, format=None):
        report_data = []
        months = ["Jan." , "Feb." , "Mar." , "Apr." , "May" , "Jun." , "Jul." , "Aug." , "Sept." , "Oct." , "Nov." , "Dec."]
        for month in months:
            monthly_report = {
                "month" : month,
                "public_income" : random.randint(5000 , 100_000),
                "personal_income" : random.randint(10000 , 500_000)
            }
            report_data.append(monthly_report)

        return Response({"type" : "report" , "title" : "trips income" , "data" : report_data})