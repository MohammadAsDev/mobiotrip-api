from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from django.db.transaction import atomic

import uuid
from hashlib import md5
from datetime import datetime
import time
import random 
import math
import json

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

cache = settings.SYSTEM_CACHE
producer = settings.SYSTEM_PRODUCER

"""
    Traditional CRUD end-points
"""

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



"""
    Used to search on available drivers in your area,
    depends on redis cache to see all drivers in a certain
    range. 
    This end-point is specified for riders.
"""
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



"""
    This end-point is specified for drivers. Used to start 
    a connection with the tracking system, also it responsilbe on 
    registering the driver in the system.
"""
class ActivateView(APIView):

    permission_classes = [IsDriver, ]
    ACTIVATE_EVENT  = \
        int(cache.hget("config:tracking-service" , "ACTIVATE"))\
        if cache.exists("config:tracking-service")\
        else None     # defined in tracking micro-service

    def get(self, request, format=None):

        driver_mem_id = settings.ACTIVE_DRIVER_KEY_FORMAT.format(request.user.id)

        if cache.exists(driver_mem_id):
            raise ValidationError("you already activated")

        driver = Driver.objects.filter(pk=request.user.id)[0]
        serializer = DriverSerializer(driver)

        driver_token = str(uuid.uuid4()) 
        driver_map= {key : val for key, val in serializer.data.items()}

        cache.hset(driver_mem_id , mapping= driver_map)

        tracker = {
            "addr" : "127.0.0.1:8090" ,
            "protocl" : "ws" ,
            "token" : driver_token
        }

        payload = {"driver_id" : driver.id , "token" : driver_token}
        message = {"event_id" : self.ACTIVATE_EVENT , "payload" : json.dumps(payload)}
        producer.send(topic=settings.TRACKER_TOPIC , value=json.dumps(message).encode())

        return Response({"tracker" : tracker , "status":"successful"}, status=status.HTTP_202_ACCEPTED)



"""
    This end-point is specified for drivers. Used to 
    delete driver's entry from the system cache.
    Drivers can't deactivate tracking while they are in a trip
"""
class DeactivateView(APIView):

    permission_classes = [IsDriver, ]
    DEACTIVATE_EVENT  = \
        int(cache.hget("config:tracking-service" , "DEACTIVATE"))\
        if cache.exists("config:tracking-service")\
        else None     # defined in tracking micro-service

    def get(self, request, format=None):
        driver = request.user
        
        if not cache.exists(settings.ACTIVE_DRIVER_KEY_FORMAT.format(driver.id)):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"details" : "driver is not active"})
        
        if self.DEACTIVATE_EVENT == None:
            return Response({"details" : "tracking-service is not running"} , status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not cache.exists(settings.BUSY_DRIVERS_KEY_FORMAT.format(driver.id)):
            driver_mem_id = settings.ACTIVE_DRIVER_KEY_FORMAT.format(driver.id)
            cache.delete(driver_mem_id)

            payload = {"driver_id" : driver.id}
            message = {"event_id" : self.DEACTIVATE_EVENT , "payload" : json.dumps(payload)}
            producer.send(topic=settings.TRACKER_TOPIC , value=json.dumps(message).encode())
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST , data={"details" : "driver is in trip"})



#   TODO: sends notifications to selected driver
"""
    This end-point is specified for riders. Used to create
    a new trip request, and register it in the system cache.
    Riders can't ask for a new trip, while they are on 
    running trip, also riders should have the trip price,
    before asking for a new trips
"""
class AskForTripView(APIView):

    permission_classes = [IsRider,]

    CREATE_EVENT = \
            int(cache.hget("config:timing-service" , "CREATE")) \
            if cache.exists("config:timing-service") \
            else None    # taken from timing micro-service 


    def is_busy(self, user_id):
        if cache.exists(settings.BUSY_RIDERS_KEY_FORMAT.format(user_id)):
            return True
        return False
    
    def calculate_distance(self, start_coords, end_coords):
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.

        start_lat, start_lon, end_lat, end_lon = map(math.radians , [start_coords[0] , start_coords[1] , end_coords[0] , end_coords[1]])

        dlat = end_lat - start_lat
        dlon = end_lon - start_lon
        a = math.sin(dlat / 2)**2 + math.cos(start_lat) * math.cos(end_lat) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        return r * c
    
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
    
    def estimate_deadline(self, distance):
        normal_speed = 20   # m/s
        deadline_ratio = 5
        return (distance * 1000 / normal_speed) * deadline_ratio

    def estimate_delation_limit(self, distance):
        normal_speed = 20   # m/s
        latency_ratio = 3
        return (distance * 1000 / normal_speed) * latency_ratio
    
    def save_trip(self, trip_id, rider_id , driver_id , price, request_data) -> dict:
        trip_data = {
                "trip_id" : trip_id,
                "driver_id" : driver_id,
                "rider_id" : rider_id,
                "start_xcoord" : request_data["start_xcoord"],
                "start_ycoord" : request_data["start_ycoord"],
                "end_xcoord" : request_data["end_xcoord"],
                "end_ycoord" : request_data["end_ycoord"] ,
                "start_time" : str(datetime.now()),
                "status" : TripStageChoices.NEED_ACK.value,
                "price" : price
        }
        
        cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id), mapping=trip_data)
        return trip_data

    def update_driver_status(self, driver_id):
        driver = Driver.objects.filter(pk=driver_id)[0]
        driver_serializer = DriverSerializer(driver)
        driver_data = driver_serializer.data
        cache.hset(settings.BUSY_DRIVERS_KEY_FORMAT.format(driver_id), mapping=driver_data)

    def update_rider_status(self, rider_id):
        rider = Rider.objects.filter(pk=rider_id)[0]
        rider_serializer = RiderSerializer(rider)
        rider_data = rider_serializer.data
        cache.hset(settings.BUSY_RIDERS_KEY_FORMAT.format(rider_id), mapping=rider_data)

    def generate_trip_code(self, rider_id : int, driver_id : int) -> str:
        trip_id = "{}_{}".format(rider_id , driver_id)
        trip_code = md5(trip_id.encode()).hexdigest()
        return trip_code


    def start_timer(self, timing_info):
        message = {"event_id" : self.CREATE_EVENT , "payload" : json.dumps(timing_info)}
        producer.send(topic=settings.TIMER_TOPIC , value=json.dumps(message).encode())


    def post(self, request, format=None):

        if self.is_busy(request.user.id):
            raise ValidationError("you are already in a trip")
        
        if not self.has_wallet(user_id=request.user.id):
            return Response({"details" : "you don't have an e-wallet"}, status=status.HTTP_400_BAD_REQUEST)
        
        if self.CREATE_EVENT == None:
            return Response({"details" : "timing-service is not running"} , status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        serializer_class = AskForTripSerializer(data=request.data)

        if serializer_class.is_valid():

            rider_id = request.user.id
            driver_id = serializer_class.validated_data["driver_id"]

            trip_code = self.generate_trip_code(rider_id , driver_id)

            start_coords = (serializer_class.validated_data["start_xcoord"] , serializer_class.validated_data["start_ycoord"])
            end_coords = (serializer_class.validated_data["end_xcoord"] , serializer_class.validated_data["end_ycoord"])

            final_distance = self.calculate_distance(start_coords , end_coords)   # distance between source and destination
            price = self.calculate_price(final_distance)

            start_time = int(time.time())    # Unix Time (Time in secs)
            
            rider_coords = start_coords
            cache_pos = cache.geopos(settings.TRACKING_KEY , "vehicle:{}".format(driver_id))[0]
            if not cache_pos:
                cache_pos = (0,0)

            driver_coords = tuple(map(
                lambda coord : float(coord) , 
                cache_pos[::-1]
            ))
            arriving_distance = self.calculate_distance(rider_coords, driver_coords)    # distance between rider and driver
            
            deadline = self.estimate_deadline(arriving_distance)
            delation_limit = self.estimate_delation_limit(arriving_distance)

            if not self.enough_balance(user_id=rider_id, price=price):
                return Response({"details" : "you don't have trip price"}, status=status.HTTP_400_BAD_REQUEST)

           
            trip_data = self.save_trip(
                trip_id=trip_code , 
                rider_id=rider_id , 
                driver_id=driver_id , 
                price=price, 
                request_data=serializer_class.validated_data
            )

            try:
                self.start_timer(timing_info={
                    "trip_id" : trip_code,
                    "driver_id" : int(driver_id),
                    "rider_id" : int(rider_id),
                    "start_time" : start_time,
                    "delation_limit" : start_time + int(delation_limit),
                    "dead_line" : start_time + int(deadline)
                })

                self.update_driver_status(driver_id)
                self.update_rider_status(rider_id)

            except:
                return Response({"details" : "can't start timing service"} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response(trip_data , status=status.HTTP_201_CREATED)
        
        return Response(serializer_class.errors)



"""
    This end-point is specified for riders, and drivers,
    driver or rider can cancel the trip request, by knowing the 
    trip id. Trip request can't be canceled if it's acknowledged
"""
class CancelTripView(APIView):

    # TODO: sends notification to driver

    CANCEL_EVENT = \
            int(cache.hget("config:timing-service" , "CANCEL")) \
            if cache.exists("config:timing-service") \
            else None    # taken from timing micro-service 

    def stop_timer(self, event_payload):
        message = {"event_id" : self.CANCEL_EVENT , "payload" : json.dumps(event_payload)}
        producer.send(topic=settings.TIMER_TOPIC , value=json.dumps(message).encode())

    def post(self, request, format=None):
        class_serializer = CancelTripSerializer(data=request.data)
        if self.CANCEL_EVENT == None:
            return Response({"details" : "timing-service is not running"} , status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]

            if not cache.exists(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id)):
                return Response({"details" : "trip id is not exist"} , status=status.HTTP_400_BAD_REQUEST)

            trip_status = int(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status"))
            driver_id = cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "driver_id")
            rider_id = cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "rider_id")
            
            if not trip_status == TripStageChoices.NEED_ACK.value:
                return Response({"details" : "your trip is not able to be canceled"} , status=status.HTTP_400_BAD_REQUEST)

            self.stop_timer({
                "driver_id" : int(driver_id)
            })
            cache.delete(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id))
            cache.delete(settings.BUSY_DRIVERS_KEY_FORMAT.format(driver_id))
            cache.delete(settings.BUSY_RIDERS_KEY_FORMAT.format(rider_id))
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(class_serializer.errors)



"""
    This end-point is specified for drivers. Drivers can 
    acknowledge their trip requests if they are in 
    rider's area.
"""
class AcknowledgeTripView(APIView):

    permission_classes = [IsDriver, ]
    ACK_EVENT = \
        int(cache.hget("config:timing-service" , "ACK")) \
        if cache.exists("config:timing-service") \
        else None    # taken from timing micro-service 

    def calculate_distance(self, start_coords : tuple, end_coords : tuple):
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.

        start_lat, start_lon, end_lat, end_lon = map(math.radians , [start_coords[0] , start_coords[1] , end_coords[0] , end_coords[1]])

        dlat = end_lat - start_lat
        dlon = end_lon - start_lon
        a = math.sin(dlat / 2)**2 + math.cos(start_lat) * math.cos(end_lat) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        return r * c

    def check_place(self, driver_coords, rider_coords):
        MAX_DIST_M = 200
        dist = self.calculate_distance(driver_coords , rider_coords)
        return dist * 1000 <= MAX_DIST_M


    def acknowledge_timer(self , event_payload):
        message = {"event_id" : self.ACK_EVENT , "payload" : json.dumps(event_payload)}
        producer.send(topic=settings.TIMER_TOPIC , value=json.dumps(message).encode())

    # TODO: sends notifications to rider
    def post(self, request, format=None):
        class_serializer = AcknowledgeTripSerializer(data=request.data)

        if self.ACK_EVENT == None:
            return Response({"details" : "timing-service is not running"} , status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]

            rider_xcoord = float(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "start_xcoord"))
            rider_ycoord = float(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "start_ycoord"))
            rider_coords = (rider_xcoord , rider_ycoord)

            driver_id = int(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "driver_id"))
            driver_coords = cache.geopos(settings.TRACKING_KEY , f"vehicle:{driver_id}")[0][::-1]   # reorder the coordinates
            driver_coords = tuple([float(coord) for coord in driver_coords])

            if not self.check_place(driver_coords , rider_coords):
                return Response({"detail" : "you should be in rider's area"} , status=status.HTTP_400_BAD_REQUEST)

            cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status" , TripStageChoices.ACKED.value)
            self.acknowledge_timer({
                "driver_id" : driver_id
            })
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(class_serializer.errors)



"""
    This end-point is specified for riders. trip
    requests should be acknowledged before starting
    Again riders can ask for new trip while they are in a trip,
    and trip can't be canceled in this phase. The only way to
    stop the trip is by making a report
"""
class StartTripView(APIView):
    permission_classes = [IsRider, ]

    START_EVENT = \
    int(cache.hget("config:tracking-service" , "START"))\
    if cache.exists("config:tracking-service")\
    else None   # defined in tracking micro-service

    COMMIT_EVENT = \
    int(cache.hget("config:timing-service" , "COMMIT")) \
    if cache.exists("config:timing-service") \
    else None    # taken from timing micro-service 

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

    def send_start_tracking_command(self, payload : dict):
        message = {"event_id" : self.START_EVENT , "payload" : json.dumps(payload)}
        producer.send(topic=settings.TRACKER_TOPIC , value=json.dumps(message).encode())

    def send_commit_trip_command(self, payload : dict):
        message = {"event_id" : self.COMMIT_EVENT , "payload" : json.dumps(payload)}
        producer.send(topic=settings.TIMER_TOPIC , value=json.dumps(message).encode())


    def post(self, request, format=None):
        class_serializer = StartTripSerializer(data= request.data)
        if self.COMMIT_EVENT == None:
            return Response({"details" : "timing-service is not running"} , status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]

            rider_id = request.user.id

            driver_id = int(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "driver_id"))
            end_lat = cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "end_xcoord")
            end_long = cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "end_ycoord")

            driver_ewallet_uuid = class_serializer.validated_data["driver_ewallet_uuid"]
            driver_wallet = self.get_wallet_by_uuid(driver_ewallet_uuid)
            rider_wallet = self.get_wallet_by_owner(request.user.id)
            
            trip_price = float(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "price"))

            with atomic():
                self.do_payment(rider_wallet , driver_wallet , trip_price)

            cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status" , TripStageChoices.STARTED.value)
            
            tracking_payload = {
                "rider_id" : int(rider_id),
                "driver_id" : int(driver_id) , 
                "trip_id" : trip_id,
                "destination" : 
                {
                    "longitude" : float(end_long),
                    "latitude" : float(end_lat)
                }
            }
            self.send_start_tracking_command(tracking_payload)
            self.send_commit_trip_command({
                "driver_id" : int(driver_id)
            })

            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(class_serializer.errors)



# NEED TEST
"""
    This end-point is specified for riders and drivers.
    if an accedent happens during the trip, users can stop
    the trip and asking for help or calling embergency 
"""
class ReportTripView(APIView):
    """
        Note: saving trips should be placed in state manager
    """
    REPORT_EVENT = \
        cache.hget("config:timing-service" , "REPORT")\
        if cache.exists("config:state_manager") \
        else None # taken from state manager micro-service # taken from timing micro-service 

    SAVE_EVENT = \
        cache.hget("config:state_manager" , "START")\
        if cache.exists("config:state_manager") \
        else None # taken from state manager micro-service

    def send_save_trip_command(self, payload : dict):
        message = {"event_id" : self.SAVE_EVENT , "payload" : json.dumps(payload)}
        producer.send(topic=settings.STATE_MANAGER_TOPIC , value=json.dumps(message).encode())

    def send_stop_timing_command(self, payload : dict) :
        message = {"event_id " : self.REPORT_EVENT , "payload" : json.dumps(payload)}
        producer.send(topic=settings.TIMER_TOPIC , value=json.dumps(message).encode())


    #   TODO : sends "reported" command to state manager
    def post(self, request, format=None):
        if self.SAVE_EVENT == None:
            return Response({"details" : "state managing-service is not running"} , status=status.HTTP_503_SERVICE_UNAVAILABLE)

        class_serializer = ReportTripSerializer(data= request.data)
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]
            driver_id = int(cache.hget(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "driver_id"))
            cache.hset(settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , "status" , TripStageChoices.REPORTED.value)
            self.send_save_trip_command({
                "trip_id" : trip_id
            })
            self.send_stop_timing_command({
                "driver_id" : driver_id
            })
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(class_serializer.errors)


class RateTripView(APIView):

    permission_classes = [IsRider, ]
    
    SAVE_EVENT = \
        cache.hget("config:state_manager" , "SAVE_AS_DONE")\
        if cache.exists("config:state_manager") \
        else None # taken from state manager micro-service

    def send_save_trip_command(self, payload : dict):
        message = {"event_id" : self.SAVE_EVENT , "payload" : json.dumps(payload)}
        producer.send(topic=settings.STATE_MANAGER_TOPIC , value=json.dumps(message).encode())

    def post(self, requset, format=None):
        if self.SAVE_EVENT == None :
            return Response({"details" : "state managing-service is not running"} , status=status.HTTP_503_SERVICE_UNAVAILABLE)

        class_serializer = RateTripSerialier(data=requset.data)
        
        if class_serializer.is_valid():
            trip_id = class_serializer.validated_data["trip_id"]
            cache.hmset(
                    settings.RUNNING_TRIPS_KEY_FORMAT.format(trip_id) , 
                    "rate" , class_serializer.validated_data["trip_rate"])
            self.send_save_trip_command({
                "trip_id" : trip_id
            })

            return Response(status=status.HTTP_204_NO_CONTENT)
        
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