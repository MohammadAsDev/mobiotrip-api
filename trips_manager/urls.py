from django.urls import path

from .views import *

urlpatterns = [
    path("" , TripsView.as_view() , name="list_trips"),
    path("<int:pk>/" , TripDetailsView.as_view() , name="list_trips"),
    path("create/" , CreateTripView.as_view(), name="create_trip"),
    path("search/" , SearchOnVehicleView.as_view() , name="trip_search"),
    path("tracking/activate/" , ActivateView.as_view(), name="tracking_activate"),
    path("tracking/deactivate/" , DeactivateView.as_view(), name="tracking_deactivate"),
    path("my_trips/" , MyTripsView.as_view(), name="my_trips"),
    path('new/' , AskForTripView.as_view(), name="new_trip"),
    path('acknowledge/' , AcknowledgeTripView.as_view(), name="acknowledge_trip"),
    path('start/' , StartTripView.as_view(), name="start_trip"),
    path('cancel/' , CancelTripView.as_view(), name="cancel_trip"),
    path('report/', ReportTripView.as_view(), name="report_trip"),
    path('statistics/trips/', YearlyTripCountStats.as_view(), name="trips_count"),
    path('statistics/trips/time/', YearlyTotalTripsTime.as_view(), name="trips_count"),
]
