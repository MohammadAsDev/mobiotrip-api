from django.urls import path, include
from .views import *

urlpatterns = [
    path("" , VehiclesList.as_view(), name="list_vehicles"),
    path("<int:pk>/" , VehicleDetails.as_view() , name="vehicle_details"),

    path("personal/" , PersonalVehiclesList.as_view(), name="list_personal_vehicles"), 
    path("personal/create/" , CreatePersonalVehicles.as_view() , name="create_vehicle"),
    path("personal/<int:pk>/" , PersonalVehicleDetails.as_view(), name="get_personal_vehicles"),

    path("public/" , PublicVehiclesList.as_view(), name="list_public_vehicles"),
    path("public/<int:pk>/" , PublicVehicleDetails.as_view(), name="get_public_vehicle"),
    path("public/create/" , CreatePublicVehicles.as_view() , name="create_vehicle"),

    path("<int:pk>/path/" , ListVehicleStations.as_view(), name="get_vehicle_path"),
]
