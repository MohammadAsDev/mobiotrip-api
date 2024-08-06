from django.urls import path

from .views import *

urlpatterns = [
    path("predict/" , PredictPathView.as_view() , name="predict_path"),
]
