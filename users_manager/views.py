from rest_framework.response import Response
from rest_framework import generics
from rest_framework import views
from rest_framework import status
from rest_framework.permissions import AllowAny , IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

import random

from .models import Rider, Driver
from .permissions import IsOwnerOrStaff
from .serializers import UserLoginSerializer, RiderSerializer, DriverSerializer, UserSerializer
from vehicles_manager.serializers import DriverVehicleDbViewSerializer
from vehicles_manager.models import DriverVehicleDbView

# Create your views here.

class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer


class UserLogoutView(views.APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        

class UserRefreshTokenView(TokenRefreshView):
    pass

"""
    Rider API View
"""
class RidersView(generics.ListAPIView):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend,]
    filterset_fields = ["username"]

class RetrieveRiderView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer
    permission_classes = [IsOwnerOrStaff]

class CreateRiderView(generics.CreateAPIView):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer
    permission_classes = [AllowAny]


class DriversView(generics.ListAPIView):
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["username"]        

class RetrieveDriverView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DriverVehicleDbViewSerializer
    queryset = DriverVehicleDbView.objects.all()
    permission_classes = [IsOwnerOrStaff]

    def _reformat_response(self, response_data : list) -> dict:
        formated_response = ({
            "first_name" : response_data["first_name"], 
            "last_name" : response_data["last_name"],
            "phone_number" : response_data["username"],
            "birth_date" : response_data["birth_date"],
            "gender" : response_data["gender"],
            "vehicle" : {
                "vehicle_number" : response_data["vehicle_number"],
                "vehicle_color" : response_data["vehicle_color"],
                "vehicle_governorate" : response_data["vehicle_governorate"],
                "vehicle_type" : response_data["vehicle_type"]
            }
        })        
        return formated_response
    
    def destroy(self, request, *args, **kwargs):
        view_instance = self.get_object()
        driver_instance = Driver.objects.get(pk=view_instance.id)
        self.perform_destroy(driver_instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(self._reformat_response(serializer.data))

class AccountDetails(views.APIView):
    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class UsersCountReport(views.APIView):

    permission_classes = [IsAdminUser, ]    

    def get(self, request , format=None):
        report_data = []
        person_types = ["Rider" , "Personal Driver" , "Public Driver" , "Publisher" , "Staff"]
        for type in person_types:
            type_count = random.randint(5 , 100) 
            report_data.append({
                "id" : type,
                "label" : type.replace("_" , " ").capitalize(),
                "value": type_count,
            })
        return Response({"type" : "report" , "title" : "users count report",  "data" : report_data})