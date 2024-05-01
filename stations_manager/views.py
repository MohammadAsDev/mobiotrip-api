from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from rest_framework.exceptions import ValidationError , NotFound

from django.core.exceptions import ObjectDoesNotExist
from django_filters.rest_framework import DjangoFilterBackend

from vehicles_manager.serializers import VehicleModelSerializer
from vehicles_manager.models import Vehicle
from .models import Station, Edge
from .serializers import AddVehicleSerializer, EdgeModelSerializer, StationModelSerializer

# Create your views here.
class StationDetails(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StationModelSerializer
    queryset = Station.objects.all()
    permission_classes = [IsAdminUser, ]

class CreateStation(generics.CreateAPIView):
    serializer_class = StationModelSerializer
    queryset = Station.objects.all()
    permission_classes = [IsAdminUser, ]

class StationsList(generics.ListAPIView):
    serializer_class = StationModelSerializer
    queryset= Station.objects.all()
    permission_classes = [IsAdminUser, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["station_name", "stations_vehicles"]

####################

class AddVehicle(generics.CreateAPIView):
    serializer_class = AddVehicleSerializer
    queryset = Station.objects.all()
    permission_classes = [IsAdminUser, ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer()
        data = serializer.validate(request.data)
        serializer.create(data)
        headers = self.get_success_headers(serializer.data)
        return Response(data=data ,status=status.HTTP_201_CREATED , headers = headers)

class RelatedVehicles(generics.ListAPIView):
    serializer_class = VehicleModelSerializer
    queryset = Vehicle.objects.all()
    permission_classes = [IsAdminUser, ]

    def list(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_field
        assert lookup_url_kwarg in kwargs , (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )
        try:
            station = Station.objects.get(pk= kwargs[self.lookup_field])
        
        except ObjectDoesNotExist:
            raise NotFound("station does not exist")

        serializer = StationModelSerializer(station)
        
        related_vehicles = serializer.data.get("stations_vehicles")
        vehicles = [Vehicle.objects.get(owner_id = vehicle_id) for vehicle_id in related_vehicles]

        queryset = self.filter_queryset(vehicles)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

####################

class AddPath(generics.CreateAPIView):
    serializer_class = EdgeModelSerializer
    queryset = Edge.objects.all()
    permission_classes = [IsAdminUser, ]


class ListPathes(generics.ListAPIView):
    serializer_class =  EdgeModelSerializer
    queryset = Edge.objects.all()
    permission_classes = [IsAdminUser, ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["src_station" , "dst_station"]

class RelatedStations(generics.ListAPIView):
    serializer_class = StationModelSerializer
    queryset = Edge.objects.all()
    permission_classes = [IsAdminUser, ]
    lookup_field = 'src_station'
    
    def get_related_staitons(self, stations_querydict):
        related_stations = []
        for station in stations_querydict:
            related_stations.append(station.dst_station)
        return related_stations


    def list(self, request, *args, **kwargs):

        lookup_url_kwarg = self.lookup_field

        # Checking lookup field in url_kwarg
        assert lookup_url_kwarg in kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field : kwargs[lookup_url_kwarg]}
        queryset = self.filter_queryset(self.get_queryset().filter(**filter_kwargs))

        related_stations = self.get_related_staitons(queryset)
        page = self.paginate_queryset(related_stations)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(related_stations, many=True)
        return Response(serializer.data)