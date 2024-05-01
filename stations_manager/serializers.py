from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.core.exceptions import ObjectDoesNotExist

from .models import Station , Edge
from vehicles_manager.models import PublicVehicle , VehicleTypes

class StationModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Station
    
    def validate_stations_vehicles(self, attrs):
        for vehicle in attrs:
            if vehicle.vehicle_type != VehicleTypes.PUBLIC:
                raise ValidationError("{} is not a public vehicle".format(vehicle))
        return super().validate(attrs)

class AddVehicleSerializer(serializers.Serializer):
    selected_station = serializers.CharField(max_length = 100 , allow_blank=False, trim_whitespace = True, label="Station Name")
    selected_vehicle = serializers.CharField(max_length = 10 , allow_blank=False, trim_whitespace=True, label="Vehicle Number")

    def validate(self, data):
        selected_station = data.get("selected_station" , "")
        selected_vehicle = data.get("selected_vehicle" , "")
        exceptions = {}

        try:
            station = Station.objects.get(station_name = selected_station)

        except ObjectDoesNotExist:
            exceptions["selected_station"] = ["selected station does not exist"]

        try:
            vehicle = PublicVehicle.objects.get(vehicle_number = selected_vehicle)
        
        except ObjectDoesNotExist:
            exceptions["selected_vehicle"] = ["selected vehicle does not exist"]

        if exceptions:
            raise ValidationError(exceptions)
        
        return data
    
    def create(self, validated_data):
        selected_station = validated_data.get("selected_station" , "")
        selected_vehicle = validated_data.get("selected_vehicle" , "")

        station = Station.objects.get(station_name = selected_station)
        vehicle = PublicVehicle.objects.get(vehicle_number = selected_vehicle)
        
        station.stations_vehicles.add(vehicle)
        station.save()

        return station



class AddEdgeSerializer(serializers.Serializer):
    src_station = serializers.CharField(max_length = 100 , allow_blank=False, trim_whitespace = True, label="Source Station Name")
    dst_station = serializers.CharField(max_length = 100 , allow_blank=False, trim_whitespace = True, label="Destinated Station Name")

    def validate(self, data):
        src_station = data.get("src_staiton" , "")
        dst_station = data.get("dst_station" , "")

        f_staiton = Station.objects.filter(station_name = src_station)
        s_staiton = Station.objects.filter(station_name = dst_station)

        if not f_staiton:
            raise ValidationError("Source station does not exist")
        
        if not s_staiton:
            raise ValidationError("Desinated station does not exist")
        
        return data

    def create(self, validated_data):
        network_path = Edge()
        network_path.src_station = validated_data.get("src_station")
        network_path.dst_station = validated_data.get("dst_station")
        network_path.save()

        return network_path
    

class EdgeModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields="__all__"
        model= Edge