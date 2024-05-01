from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from vehicles_manager.models import Vehicle
from .serializers import *
from .permissions import IsVehicleOwnerOrStaff
from .models import *
from stations_manager.models import Station
from stations_manager.serializers import StationModelSerializer

# Create your views here.

"""
    Generic Vehicle CRUD API View
"""
class VehiclesList(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = VehicleOnlySerializer
    filter_backends = [DjangoFilterBackend]
    fieldset_filter = ["vehicle_number"]
    queryset = Vehicle.objects.all()

class VehicleDetails(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsVehicleOwnerOrStaff]
    serializer_class = VehicleOnlySerializer
    queryset= Vehicle.objects.all()


"""
    Personal vehicle CRUD API View
"""
class CreatePersonalVehicles(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PersonalDriverVehicleSerializer

class PersonalVehicleDetails(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsVehicleOwnerOrStaff]
    serializer_class = PersonalVehicleSerializer
    queryset = PersonalVehicle.objects.all()

class PersonalVehiclesList(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = PersonalVehicleSerializer
    queryset = PersonalVehicle.objects.all()


"""
    Public vehicle CRUD API View
"""
class CreatePublicVehicles(CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = PublicDriverVehicleSerializer

class PublicVehicleDetails(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsVehicleOwnerOrStaff]
    serializer_class = PublicVehicleSerializer
    queryset = PublicVehicle.objects.all()

class PublicVehiclesList(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = PublicVehicleSerializer
    queryset = PublicVehicle.objects.all()

"""
    List all stations for a specific vehicle
    (Note: this view does not have a queryset, it's manually defined as a raw query)
"""
class ListVehicleStations(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = StationModelSerializer

    def list(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_field

        # Checking lookup field in url_kwarg
        assert lookup_url_kwarg in kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        selected_station = kwargs[lookup_url_kwarg]
        queryset = self.filter_queryset(Station.objects.raw(
            """
                SELECT * FROM stations_manager_station 
                WHERE id IN (
                    SELECT station_id FROM stations_manager_station_stations_vehicles 
                    WHERE vehicle_id = {})
            """.format(selected_station)
        ))


        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)