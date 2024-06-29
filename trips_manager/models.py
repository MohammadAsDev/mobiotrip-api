from django.db import models

from users_manager.models import Rider, Driver
from datetime import datetime

# Create your models here.

class TripStageChoices(models.IntegerChoices):
    NEED_ACK    = 0
    ACKED       = 1
    STARTED     = 2
    DELAYED     = 3
    DONE        = 4
    REPORTED    = 5

class TripStatusChoice(models.IntegerChoices):
    DONE        = 0
    DELAYED     = 1
    REPORTED    = 2

class TripRateChoice(models.IntegerChoices):
    BAD     = 0
    NORM    = 1
    GOOD    = 2

class Trip(models.Model):
    start_xcoord = models.FloatField(name="start_xcoord" , null=False, blank=False)
    start_ycoord = models.FloatField(name="start_ycoord" , null=False, blank=False)

    end_xcoord = models.FloatField(name="end_xcoord" , null=False, blank=False)
    end_ycoord = models.FloatField(name="end_ycoord" , null=False, blank=False)

    start_time = models.DateTimeField(name="start_time" , null=False, blank=False)
    end_time = models.DateTimeField(name="end_time" , null=False, blank=False)

    rider = models.ForeignKey(related_name="rider", to=Rider , on_delete=models.CASCADE , null=False, blank=False)
    driver = models.ForeignKey(related_name="driver", to=Driver, on_delete=models.CASCADE , null=False, blank=False)

    status = models.IntegerField(choices=TripStatusChoice.choices)
    rate = models.IntegerField(choices=TripRateChoice.choices)

    created_at =models.DateTimeField(auto_now=True)