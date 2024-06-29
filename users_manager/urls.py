from django.urls import path
from .views import *

urlpatterns = [

    path(route='profile/', view=AccountDetails.as_view(), name='user_profile'),    

    path(route="riders/" , view=RidersView.as_view() , name="riders") ,
    path(route="riders/register/" , view=CreateRiderView.as_view(), name="register_rider"),
    path(route="riders/<int:pk>/" , view=RetrieveRiderView.as_view() , name="get_rider") ,

    path(route="drivers/" , view=DriversView.as_view() , name="drivers"),
    path(route="drivers/<int:pk>/" , view=RetrieveDriverView.as_view(), name="get_driver"),

    path(route="login/" , view=UserLoginView.as_view(), name="login"),
    path(route="logout/" , view=UserLogoutView.as_view(), name="logout"),
    path(route='refresh/', view=UserRefreshTokenView.as_view(), name='token_refresh'),    


    path(route="statistics/users/" , view=UsersCountReport.as_view(), name="users_count_report"),
]
