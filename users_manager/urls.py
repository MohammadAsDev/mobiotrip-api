from django.urls import path
from .views import *

urlpatterns = [

    path(route="riders/" , view=RidersView.as_view() , name="riders") ,
    path(route="riders/register/" , view=CreateRiderView.as_view(), name="register_rider"),
    path(route="riders/<int:pk>/" , view=RetrieveRiderView.as_view() , name="get_rider") ,

    path(route="drivers/" , view=DriversView.as_view() , name="drivers"),
    path(route="drivers/<int:pk>/" , view=RetrieveDriverView.as_view(), name="get_driver"),

    path(route="login/" , view=UserLoginView.as_view(), name="login"),
    path(route="logout/" , view=UserLogoutView.as_view(), name="logout"),
    path(route='refresh/', view=UserRefreshTokenView.as_view(), name='token_refresh'),    
]
