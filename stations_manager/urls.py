from django.urls import path

from .views import *

"""
    @TODO end-points to create
    add a station path to a station
"""

urlpatterns = [
    path("" , StationsList.as_view(), name="stations"),
    path("create/" , CreateStation.as_view() , name="create_station"),
    path("<int:pk>/" , StationDetails.as_view() , name="station_details"),
    path("<int:pk>/vehicles/" , RelatedVehicles.as_view(), name="related_vehicles"),
    path("vehicles/create/" , AddVehicle.as_view(), name="add_vehicle"),
    path("pathes/create/", AddPath.as_view(), name="add_path"),
    path("pathes/" , ListPathes.as_view() , name="pathes"),
    path("<int:src_station>/stations/" , RelatedStations.as_view(), name="related_stations"),
]
