from rest_framework import serializers
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.serializers import ModelSerializer

from django.db import transaction

from .models import VehicleTypes , VehicleGovernorates , Vehicle, DriverVehicleDbView
from users_manager.serializers import DriverSerializer

import re

"""
    Default Vehicle Model Serializer
"""
class VehicleModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Vehicle


"""
    Only Vehicle's Data Serializer
    Used to create vehicles regradless of their types
"""
class VehicleOnlySerializer(serializers.Serializer):

    SEATS_NUMBER_CHOICES = [
        (2  , "Small" ),
        (5 , "Medium"  ),
        (8 , "Large"  )
    ]

    VEHICLE_GOVERNORATE_CHOICES = [
        ("Homs", VehicleGovernorates.HOMS) , 
        ("Damascus" , VehicleGovernorates.DAMASCUS)  ,
        ("Aleepo" , VehicleGovernorates.ALEEPO),
        ("Tartus" , VehicleGovernorates.TARTUS), 
        ("Latakia" , VehicleGovernorates.LATAKIA)  
    ]

    VEHICLE_TYPE_CHOICES = [
        (VehicleTypes.PUBLIC , "Public"),
        (VehicleTypes.PERSONAL, "Personal")
    ]

    vehicle_number = serializers.CharField(allow_blank=False , trim_whitespace=True , max_length=10)
    seats_number = serializers.ChoiceField(allow_blank=False, choices=SEATS_NUMBER_CHOICES)
    vehicle_color = serializers.CharField(allow_blank=False, max_length=50 , trim_whitespace=True)
    vehicle_governorate = serializers.ChoiceField(allow_blank=False, choices=VEHICLE_GOVERNORATE_CHOICES)
    vehicle_type = serializers.ChoiceField(allow_blank=False, choices=VEHICLE_TYPE_CHOICES , help_text="works only with creation")

    def validate_vehicle_number(self, vehicle_number):
        pattern = re.compile("[A-Z0-9]+")
        if re.fullmatch(pattern , vehicle_number) != None and len(vehicle_number) == 7:
            return vehicle_number
        
        raise ValidationError("Vehicle Number is not valid(only upper-case letters and numbers)")
        

    def validate_vehicle_color(self, vehicle_color):
        pattern = re.compile("[A-z]+")
        if re.fullmatch(pattern,  vehicle_color) != None:
            return vehicle_color.lower()

        raise ValidationError("Color is not valid")
 

    def create(self, validated_data):
        vehicle_number = validated_data["vehicle_number"]
        vehicle_obj = Vehicle.objects.filter(vehicle_number=vehicle_number)
        if vehicle_obj:
            raise APIException("vehicle number is used before")
        return Vehicle.objects.create(**validated_data)
    
    
    def update(self, instance, validated_data):
        instance.vehicle_number = validated_data.get("vehicle_number" , instance.vehicle_number)
        instance.seats_number = validated_data.get("seats_number", instance.seats_number)
        instance.vehicle_color = validated_data.get("vehicle_color", instance.vehicle_color)
        instance.vehicle_governorate = validated_data.get("vehicle_governorate" , instance.vehicle_governorate)

        instance.save()
        return instance

    def validate(self, data):
        if not self.validate_vehicle_color(data.get("vehicle_color" , "")):
          raise ValidationError("Color is not valid")
        
        if not self.validate_vehicle_number(data.get("vehicle_number" , "")):
            raise ValidationError("Vehicle Number is not valid(only upper-case letters and numbers)")
        
        return data

"""
    Public Vehicle Serializer
    inherted from VehicleOnlySerializer, to deal only with public vehicles
"""
class PublicVehicleSerializer(VehicleOnlySerializer):
    vehicle_type = None

    def create(self, validated_data):
        validated_data["vehicle_type"] = VehicleTypes.PUBLIC
        return super().create(validated_data)

"""
    Personal Vehicle Serializer
    inherted from VehicleOnlySerializer, to deal only with personal vehicles
"""
class PersonalVehicleSerializer(VehicleOnlySerializer):
    vehicle_type = None

    def create(self, validated_data):
        validated_data["vehicle_type"] = VehicleTypes.PERSONAL
        return super().create(validated_data)

"""
    Driver-Vehicle Serializer
    used to create vehicles with their drivers
"""
class DriverVehicleSerializer(serializers.Serializer):
    owner = DriverSerializer()
    vehicle = VehicleOnlySerializer()

    def validate(self, data):
        owner_data = data.get("owner" , dict())
        vehicle_data = data.get("vehicle" , dict())

        owner_serializer = DriverSerializer()
        vehicle_serialzier = VehicleOnlySerializer()

        owner_validated_data = owner_serializer.validate(owner_data)
        vehicle_validated_data = vehicle_serialzier.validate(vehicle_data)

        validated_data = {
            "owner" : owner_validated_data , 
            "vehicle" : vehicle_validated_data
        }

        return validated_data

    def create(self, validated_data : dict):
        owner_validated_data = validated_data.get("owner" , dict())
        vehicle_validated_data = validated_data.get("vehicle" , dict())

        owner_serializer = DriverSerializer()
        vehicle_serialzier = VehicleOnlySerializer()

        with transaction.atomic():
            try:
                owner = owner_serializer.create(owner_validated_data)
            except APIException:
                raise APIException("driver's username is used before")
           
            vehicle_validated_data["owner"] = owner
           
            try:
                vehicle = vehicle_serialzier.create(vehicle_validated_data)
            except APIException:
                raise APIException("vehicle's number is used before")
           
            return dict({
                "vehicle" : vehicle , 
                "owner" : owner
            })

"""
    Public Driver-Vehicle Serializer
    inherited from Driver-Vehicle Serializer, used to create public vehicles with their drivers
"""
class PublicDriverVehicleSerializer(DriverVehicleSerializer):
    vehicle = PublicVehicleSerializer()

    def validate(self, attrs):
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data["vehicle"]["vehicle_type"] = VehicleTypes.PUBLIC
        return super().create(validated_data)

"""
    Personal Driver-Vehicle Serializer
    inherited from Driver-Vehicle Serializer, used to create personal vehicles with their drivers
"""
class PersonalDriverVehicleSerializer(DriverVehicleSerializer):
    vehicle = PersonalVehicleSerializer()
    
    def validate(self, attrs):
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data["vehicle"]["vehicle_type"] = VehicleTypes.PERSONAL
        return super().create(validated_data)

"""
    DriverVehicleSerializer is a read-only serializer
    used to serialize 'driver_vehicle' database view's rows to useful data
"""
class DriverVehicleDbViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = DriverVehicleDbView
        fields = "__all__"