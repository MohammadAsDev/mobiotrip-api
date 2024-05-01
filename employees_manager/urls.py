from django.urls import path

from .views import *

urlpatterns = [
    path("publishers/" , view=PublishersView.as_view() , name="publishers"),
    path("publishers/hire/" , view=CreatePublisher.as_view() , name="create_publisher"),
    path("publishers/<int:pk>/" , view=PublisherDetails.as_view(), name="publisher_details"),
]
