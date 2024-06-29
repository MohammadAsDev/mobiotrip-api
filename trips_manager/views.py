from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from django.core.exceptions import BadRequest
from django.conf import settings
from django.db.transaction import atomic

import uuid
from hashlib import md5
from datetime import datetime
import random 
import math

from users_manager.models import Rider, Driver
from .models import Trip, TripStageChoices
from .serializers import *

from users_manager.permissions import IsDriver, IsRider
from users_manager.models import Driver
from users_manager.serializers import DriverSerializer, RiderSerializer
from users_manager.models import UserTypes
from wallet_app.models import Wallet

# Create your views here.
# Note: no one should have the permission to update trip information
# Kakfa Client (Don't forget to send events)

cache = settings.SYSTEM_CACHE

class TripsView(generics.ListAPIView):
    queryset = Trip.objects.all()
    permission_classes = [IsAdminUser]
    serializer_class = DefaultTripSerializer

class CreateTripView(generics.CreateAPIView):
    queryset= Trip.objects.all()
    serializer_class = DefaultTripSerializer
    permission_classes = [IsAdminUser]

class TripDetailsView(generics.RetrieveDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = RetrieveTripSerializer
    permission_classes = [IsAdminUser]


class MyTripsView(generics.ListAPIView):
    serializer_class = RetrieveTripSerializer

    def list(self, request, *args, **kwargs):
        if request.user.user_type == UserTypes.RIDER:
            queryset = Trip.objects.filter(rider = request.user.id)
        elif request.user.user_type == UserTypes.DRIVER:
            queryset = Trip.objects.filter(driver = request.user.id)
        else:
            return Response({"details" : "no valid trips for your account"} , status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SearchOnVehicleView(APIView):

    permission_classes = [IsRider, ]

    def filter_results(self , results: list):
        filtered_results = [
                driver 
                for driver in results 
                if not cache.exists(settings.RUNNING_TRIPS_KEY_FORMAT.format(driver[0]))
                and 
                cache.exists(settings.ACTIVE_DRIVER_KEY_FORMAT.format(driver[0]))
                and
                not cache.exists(settings.BUSY_DRIVERS_KEY_FORMAT.format(driver[0]))
        ]

        return filtered_results

        
    def _reformat_response(self, redis_results : list) -> dict:
        results= list()

        for result in redis_results:
            result_dict= {}
            result_dict = {
                'driver_id' : result[0],
                'distance' : result[1],
                'coords' : tuple(result[2])
            }
            results.append(result_dict)

        return results
    
    def post(self, request, format=None):
        serializer = SearchOnVehicleSerailizer(data=request.data)
        default_radius = 500
        default_unit = 'm'

        if serializer.is_valid():
            x_coord = serializer.validated_data['x_coord']
            y_coord = serializer.validated_data['y_coord']
            radius = serializer.validated_data.get('radius' , default_radius)
            unit  = serializer.validated_data.get('unit' , default_unit)

            nearby_drivers = cache.georadius(
                settings.TRACKING_KEY , 
                longitude=y_coord , 
                latitude=x_coord , 
                radius=radius,  
                unit=unit , 
                withdist=True, 
                withcoord=True
            )

            search_result = self.filter_results(nearby_drivers)
            
            repsonse = self._reformat_response(search_result)
            return Response(repsonse[:5])   # choosing the first five drivers
        
        return Response(serializer.errors)


class ActivateView(APIView):
    permission_classes = [IsDriver, ]

    def get(self, request, format=None):

        driver_mem_id = settings.ACTIVE_DRIVER_KEY_FORMAT.format(request.user.id)

        if cache.exists(driver_mem_id):
            raise ValidationError("you already activated")

        driver = Driver.objects.filter(pk=request.user.id)[0]
        serializer = DriverSerializer(driver)

        driver_token = str(uuid.uuid4()) 

        driver_map= {key : val for key, val in serializer.data.items()}
        driver_map["token"] = driver_token

        cache.hset(driver_mem_id , mapping= driver_map)

        tracker = {
            "addr" : "127.0.0.1:8090" ,
            "protocl" : "ws" ,
            "token" : driver_token
        }
        return Response({"tracker" : tracker , "status":"successful"}, status=status.HTTP_202_ACCEPTED)
    

class DeactivateView(APIView):

    permission_classes = [IsDriver, ]

    # TODO: should send an event to tracker to close web-socket
    def get(self, request, format=None):
        if not cache.exists(settings.BUSY_DRIVERS_KEY_FORMAT.format(request.user.id)):
            driver_mem_id = settings.ACTIVE_DRIVER_KEY_FORMAT.format(request.user.id)
            cache.delete(driver_mem_id)

            return Response(status=status.HTTP_204_NO_CONTENT)

        raise BadRequest("driver is in trip")


#   TODO: calculate trip price, and check rider's e-wallet
#   TODO: sends notifications to selected driver
class AskForTripView(APIView):

    permission_classes = [IsRider,]

    def is_busy(self, user_id):
        if cache.exists(settings.BUSY_RIDERS_KEY_FORMAT.format(user_id)):
            return True
        return False
    
    def calculate_distance(self, start_coords, end_coords):
        dlat = end_coords[0] - start_coords[0]
        dlon = end_coords[1] - start_coords[1]
        a = math.sin(dlat / 2)**2 + math.cos(start_coords[0]) * math.cos(end_coords[0]) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return c
    
    def calculate_price(self, trip_distance):
        trip_price = 500
        return trip_distance * trip_price

    def enough_balance(self, user_id, price):
        wallet = Wallet.objects.filter(owner=user_id)[0]
        if wallet.balance > price:
            return True
        return False
    
    def has_wallet(self, user_id):
        user_wallet = Wallet.objects.filter(owner=user_id)
        if len(user_wallet):
            return True
        return False

    def post(self, request, format=None):

        if self.is_busy(request.user.id):
            raise ValidationError("you are already in a trip")
        
        if not self.has_wallet(user_id=request.user.id):
            return Response({"details" : "you don't have an e-wallet"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer_class = AskForTripSerializer(data=request.data)
        if serializer_class.is_valid():
            
            trip_id = "{}_{}".format(request.user.id , serializer_class.validated_data["driver_id"])
            trip_code = md5(trip_id.encode()).hexdigest()

            rider_id = request.user.id
            driver_id = serializer_class.validated_data["driver_id"]

            start_coords = (serializer_class.validated_data["start_xcoord"] , serializer_class.validated_data["start_ycoord"])
            end_coords = (serializer_class.validated_data["end_xcoord"] , serializer_class.validated_data["end_ycoord"])

            distance = self.calculate_distance(start_coords , end_coords)
            price = self.calculate_price(distance)


            if not self.enough_balance(user_id=rider_id, price=price):
                return Response({"details" : "you don't have enough balance"}, status=status.HTTP_400_BAD_REQUEST)


            if not self.enough_balance(rider_id, price):
                return Response({"details" : "user does not have the trip's price"} , status=status.HTTP_400_BAD_REQUEST)

            trip_data = {
                "trip_id" : trip_code,
                "driver_id" : driver_id,
                "rider_id" : rider_id,
                "start_xcoord" : serializer_class.validated_data["start_xcoord"],
                "start_ycoord" : serializer_class.validated_data["start_ycoord"],
                "end_xcoord" : serializer_class.validated_data["end_xcoord"],
                "end_ycoord" : serializer_class.validated_data["end_ycoord"] ,
                "start_time" : str(datetime.now()),
                "status" : TripStageChoices.NEED_ACK,
                "price" : price
            }

            rider = Rider.objects.filter(pk=rider_id)[0]
            driver = Driver.objects.filter(pk=driver_id)[0]

            driver_serializer = DriverSerializer(driver)
            rider_serializer = RiderSerializer(rider)

            driver_data = driver_serializer.data
            rider_data = rider_serializer.data

            cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_code), mapping=trip_data)
            cache.hset(settings.BUSY_RIDERS_KEY_FORMAT.format(rider_id), mapping=rider_data)
            cache.hset(settings.BUSY_DRIVERS_KEY_FORMAT.format(driver_id), mapping=driver_data)

            return Response(trip_data , status=status.HTTP_201_CREATED)
        
        return Response(serializer_class.errors)

# NEED TEST
class CancelTripView(APIView):

    # TODO: sends notification to driver
    # TODO: sends "cancelation" commands to timer and tracker
    def post(self, request, format=None):
        class_serializer = CancelTripSerializer(data=request.data)
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]
            
            trip_status = cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status")
            if not trip_status == TripStageChoices.NEED_ACK:
                return Response({"details" : "your trip is not able to be canceled"} , status=status.HTTP_400_BAD_REQUEST)

            cache.delete(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id))
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(class_serializer.errors)


class AcknowledgeTripView(APIView):

    permission_classes = [IsDriver, ]

    # TODO: sends notifications to rider
    # TODO: sends "acknowledgement" command to timer
    def post(self, request, format=None):
        class_serializer = AcknowledgeTripSerializer(data=request.data)
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]
            cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status" , TripStageChoices.ACKED)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(class_serializer.errors)


# NEED TEST
class StartTripView(APIView):

    permission_classes = [IsRider, ]

    def do_payment(self, sender_wallet, receiver_wallet , price):
        if sender_wallet.balance < price:
            raise ValidationError("you don't have balance to pay trip's price")
        
        sender_wallet.balance -= price
        receiver_wallet.balance += price

        sender_wallet.save()
        receiver_wallet.save()
        

    def get_wallet_by_uuid(self, uuid):
        wallet = Wallet.objects.filter(wallet_uuid=uuid)
        if not wallet:
            raise ValidationError(f"wallet with uuid={uuid} does not exist")
        return wallet[0]
    
    def get_wallet_by_owner(self, user_id):
        wallet = Wallet.objects.filter(owner= user_id)
        if not wallet:
            raise ValidationError(f"the user with id={user_id} does not exist")
        return wallet[0]

    # TODO: do payment operation
    # TODO: sends "starting" command to timer
    def post(self, request, format=None):
        class_serializer = StartTripSerializer(data= request.data)
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]
            driver_ewallet_uuid = class_serializer.validated_data["driver_ewallet_uuid"]

            driver_wallet = self.get_wallet_by_uuid(driver_ewallet_uuid)
            rider_wallet = self.get_wallet_by_owner(request.user.id)
            
            trip_price = float(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "price"))

            with atomic():
                self.do_payment(rider_wallet , driver_wallet , trip_price)

            cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status" , TripStageChoices.STARTED)
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(class_serializer.errors)


# NEED TEST
class ReportTripView(APIView):

    """
        Note: saving trips should be placed in state manager
    """
    #   TODO : sends "reported" command to state manager
    def post(self, request, format=None):
        class_serializer = ReportTripSerializer(data= request.data)
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]
            cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status" , TripStageChoices.REPORTED)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(class_serializer.errors)


# NEED TEST
class RateTripView(APIView):

    permission_classes = [IsRider, ]

    def post(self, requset, format=None):
        class_serializer = RateTripSerialier(data=requset.data)
        
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]
            trip_status = cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status")
            if trip_status == TripStageChoices.DONE:
                cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status" , class_serializer.validated_data["rate"])
            else:
                return Response({"details" : "trip has not been completed yet"} , status=status.HTTP_400_BAD_REQUEST)
            
        return Response(class_serializer.errors)
    
"""
    Trips-Related Statistics
    only admins can access to see this reports
"""

class YearlyTripCountStats(APIView):

    permission_classes = [IsAdminUser,]

    def get(self , request, format=None):
        report_data = []
        months = ["Jan." , "Feb." , "Mar." , "Apr." , "May" , "Jun." , "Jul." , "Aug." , "Sept." , "Oct." , "Nov." , "Dec."]
        for month in months:
            personal_trips_n = random.randint(a=10, b=100) 
            public_trips_n = random.randint(a=10, b=100) 
            report_data.append({
                    "month" : month,
                    "personal_trips" : personal_trips_n,
                    "public_trips" : public_trips_n
                }) 
        
        return Response({"type" : "report" , "title" : "yearly trips count" , "data" : report_data})
    

class YearlyTotalTripsTime(APIView):

    permission_classes = [IsAdminUser, ]

    def get(self, request, format=None):
        report_data = []
        months = ["Jan." , "Feb." , "Mar." , "Apr." , "May" , "Jun." , "Jul." , "Aug." , "Sept." , "Oct." , "Nov." , "Dec."]
        for month in months:
            personal_trips_time = random.random() * 120 + 50
            public_trips_time = random.random() * 80 + 50
            report_data.append({
                "month" : month,
                "total_personal_hours" : float(f"{personal_trips_time:.2f}"),
                "total_public_hours" : float(f"{public_trips_time:.2f}")
            })

        return Response({"type" : "report" , "title" : "total trips time" , "data" : report_data})