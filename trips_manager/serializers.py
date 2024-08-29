from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.conf import settings

from .models import Trip, TripStatusChoice , TripRateChoice, TripStageChoices
from users_manager.serializers import RiderSerializer, DriverSerializer
from users_manager.models import Rider, Driver

class DefaultTripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"

    def validate_rider(self, rider):
        rider_queryset = Rider.objects.filter(pk=rider.id)
        if not rider_queryset:
            raise ValidationError("invalid rider")
        return rider

    def validate_driver(self, driver):
        driver_queryset = Driver.objects.filter(pk=driver.id)
        if not driver_queryset:
            raise ValidationError("invalid driver")
        return driver

    def validate_start_xcoord(self , start_xcoord : float):
        if start_xcoord >= -90 and start_xcoord <= 90:
            return start_xcoord
        raise ValidationError("invalid start point latitude")
    
    def validate_start_ycoord(self, start_ycoord : float):
        if start_ycoord >= -180 and start_ycoord <= 180:
            return start_ycoord
        raise ValidationError("invalid start point longitude")
    
    def validate_end_xcoord(self, end_xcoord : float):
        if end_xcoord >= -90 and end_xcoord <= 90:
            return end_xcoord
        raise ValidationError("invalid end point latitude")
    
    def validate_end_ycoord(self, end_ycoord : float):
        if end_ycoord >= -180 and end_ycoord <= 180:
            return end_ycoord
        raise ValidationError("invalid end point longitude")

class RetrieveTripSerializer(serializers.Serializer):

    TRIP_STATUS_CHOICES = (
        (TripStatusChoice.DONE      ,   "Done"      ),
        (TripStatusChoice.DELAYED   ,   "Delayed"   ),
        (TripStatusChoice.REPORTED  ,   "Reported"  ),
    )

    TRIP_RATE_CHOICES = (
        (TripRateChoice.BAD  , "Bad"    ),
        (TripRateChoice.NORM , "Normal" ),
        (TripRateChoice.GOOD , "Good"   ),
    )
    
    id = serializers.IntegerField(read_only=True)

    start_xcoord = serializers.FloatField(read_only=True)
    start_ycoord = serializers.FloatField(read_only=True)

    end_xcoord = serializers.FloatField(read_only=True)
    end_ycoord = serializers.FloatField(read_only=True)

    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(read_only=True)

    rider = RiderSerializer(read_only=True)
    driver = DriverSerializer(read_only=True)

    status = serializers.ChoiceField(choices=TRIP_STATUS_CHOICES, allow_blank=False , read_only=True)
    rate = serializers.ChoiceField(choices=TRIP_RATE_CHOICES , allow_blank=False, read_only=True)


class SearchOnVehicleSerailizer(serializers.Serializer):
    
# m, km, mi, ft.

    UNIT_CHOICES = (
        ('ft' , 'feet'),
        ('m' , 'meters'),  
        ('km' , 'kilo meters'),
        ('mi' , 'miles')
    )
    
    x_coord = serializers.FloatField()
    y_coord = serializers.FloatField()
    radius = serializers.FloatField(required=False)
    unit = serializers.ChoiceField(choices=UNIT_CHOICES , required=False)

    def validate_x_coord(self, x_coord : float):
        if x_coord <= 90 and x_coord >= -90:
            return x_coord
        raise ValidationError("invalid latitude")
    
    def validate_y_coord(self, y_coord : float):
        if y_coord <= 180 and y_coord >= -180:
            return y_coord
        raise ValidationError("invalid longitude")

class CancelTripSerializer(serializers.Serializer):
    trip_id = serializers.CharField(max_length = 32 , min_length=32)

    def validate_trip_id(self, trip_id):
        cache = settings.SYSTEM_CACHE
        if cache.exists(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id)):
            return trip_id

        return ValidationError("trip id is not exist in the system")

class AcknowledgeTripSerializer(serializers.Serializer):
    trip_id = serializers.CharField(max_length = 32 , min_length=32)

    def validate_trip_id(self, trip_id):
        cache = settings.SYSTEM_CACHE
        if cache.exists(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id)):
            return trip_id

        return ValidationError("trip id is not exist in the system")

class StartTripSerializer(serializers.Serializer):
    trip_id = serializers.CharField(max_length = 32 , min_length=32)
    driver_ewallet_uuid = serializers.UUIDField()

    def validate_trip_id(self, trip_id):
        cache = settings.SYSTEM_CACHE
        if cache.exists(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id)):
            return trip_id

        raise ValidationError("trip id is not exist in the system")
    

class ReportTripSerializer(serializers.Serializer):
    trip_id = serializers.CharField(max_length = 32 , min_length=32)
    report_message = serializers.CharField(max_length = 500 , required=False)
    
    def validate_trip_id(self, trip_id):
        cache = settings.SYSTEM_CACHE
        if cache.exists(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id)):
            trip_status = int(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status"))
            if trip_status == TripStageChoices.STARTED.value:
                return trip_id
            
            raise ValidationError("trip is not in starting stage")

        raise ValidationError("trip id is not exist in the system")

class AskForTripSerializer(serializers.Serializer):
    driver_id = serializers.IntegerField()

    start_xcoord = serializers.FloatField()
    start_ycoord = serializers.FloatField()

    end_xcoord = serializers.FloatField()
    end_ycoord = serializers.FloatField()


    def validate_driver_id(self, driver_id):
        if not settings.SYSTEM_CACHE.exists(settings.ACTIVE_DRIVER_KEY_FORMAT.format(driver_id)):
            raise ValidationError("selected driver is not active in the system")
        
        if settings.SYSTEM_CACHE.exists(settings.BUSY_DRIVERS_KEY_FORMAT.format(driver_id)):
            raise ValidationError("selected trip is busy")
        
        return driver_id
    
    def validate_start_xcoord(self, start_xcoord):
        if start_xcoord >= -90 and start_xcoord <= 90:
            return start_xcoord
        raise ValidationError("latitude for start point is not valid")

    def validate_start_ycoord(self, start_ycoord):
        if start_ycoord >= -180 and start_ycoord <= 180:
            return start_ycoord
        raise ValidationError("longitude for start point is not valid")

    def validate_end_xcoord(self, end_xcoord):
        if end_xcoord >= -90 and end_xcoord <= 90:
            return end_xcoord
        raise ValidationError("latitude for end point is not valid")

    def validate_end_ycoord(self, end_ycoord):
        if end_ycoord >= -180 and end_ycoord <= 180:
            return end_ycoord
        raise ValidationError("longitude for end point is not valid")
    
class RateTripSerialier(serializers.Serializer):
    trip_rate   = serializers.ChoiceField(choices=TripRateChoice.choices)
    trip_id     = serializers.CharField()

    def validate_trip_id(self, trip_id):
        trip_status = int(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status")[0])
        cache = settings.SYSTEM_CACHE
        if not cache.exists(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id)):
            raise ValidationError("trip id is not exist in the system")
                
        if trip_status == TripStatusChoice.DONE.value:
            raise ValidationError("trip is not done yet!") 
        
        return trip_id
