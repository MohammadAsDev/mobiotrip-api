from django.urls import path

from .views import *

urlpatterns = [
    path(route="" , view=WalletsList.as_view() , name="list_wallets"),
    path(route="create/"  , view=CreateWallet.as_view() , name="create_wallet"),
    path(route="<int:pk>/", view=WalletDetails.as_view(), name="wallet_details"),
    path(route="transfer/", view=TransferMoney.as_view() , name="transfer_money"),
    path(route="charge/" , view=ChargeWallet.as_view(), name="charge_wallet"),
]
