from django.urls import path

from .views import *

urlpatterns = [
    path(route="" , view=WalletsList.as_view() , name="list_wallets"),
    path(route="create/"  , view=CreateWallet.as_view() , name="create_wallet"),
    path(route="<int:pk>/", view=WalletDetails.as_view(), name="wallet_details"),
    path(route="<int:pk>/owner/", view=RetrieveUserWalletInfo.as_view(), name="user_wallet_details"),
    path(route="transfer/", view=TransferMoney.as_view() , name="transfer_money"),
    path(route="transactions/", view=TransactionsList.as_view() , name="transfer_money"),
    path(route="charge/" , view=ChargeWallet.as_view(), name="charge_wallet"),
    path(route="my_wallet/" , view=MyWalletView.as_view(), name="my_wallet"),
    path(route="statistics/transactions/" , view=TransactionsReport.as_view(), name="transaction_report"),
    path(route="statistics/wallets/" , view=EwalletsReport.as_view() , name="wallets_report"),
    path(route="statistics/income/" , view=IncomeReport.as_view() , name="income_report"),
    path(route="statistics/trips/income/" , view=TripsIncomeReport.as_view(), name="public_trips_income_report"),
]
