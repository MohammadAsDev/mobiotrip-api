from rest_framework.response import Response
from rest_framework import generics
from rest_framework import views
from rest_framework import status
from rest_framework.permissions import AllowAny , IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Rider, Driver
from .permissions import IsOwnerOrStaff
from .serializers import UserLoginSerializer, RiderSerializer, DriverSerializer
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


"""
    Driver API View

    @TODO This view need to be refactored (naive implementation)
    also refactor the serializer of this view
"""
class DriversView(generics.ListAPIView):
    serializer_class = DriverVehicleDbViewSerializer
    queryset = DriverVehicleDbView.objects.all()
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["username"]


    def _reformat_response(self, response_data : list) -> dict:
        formated_response = list()
        for driver in response_data:
            formated_response.append({
                "first_name" : driver["first_name"], 
                "last_name" : driver["last_name"],
                "phone_number" : driver["username"],
                "birth_date" : driver["birth_date"],
                "gender" : driver["gender"],
                "vehicle" : {
                    "vehicle_number" : driver["vehicle_number"],
                    "seats_number" : driver["seats_number"],
                    "vehicle_color" : driver["vehicle_color"],
                    "vehicle_governorate" : driver["vehicle_governorate"],
                    "vehicle_type" : driver["vehicle_type"]
                }
            })        
        return formated_response

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            formated_response = self._reformat_response(serializer.data)
            return self.get_paginated_response(formated_response)

        serializer = self.get_serializer(queryset, many=True)
        
        formated_response = self._reformat_response(serializer.data)
        
        return Response(formated_response)
        
        
class RetrieveDriverView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DriverSerializer
    queryset = Driver.objects.all()
    permission_classes = [IsOwnerOrStaff]
