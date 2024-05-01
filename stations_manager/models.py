from operator import index
from django.db import models

from vehicles_manager.models import Vehicle
# Create your models here.

class Station(models.Model):
    station_name = models.CharField(name="station_name" , unique=True , blank=False , max_length=100)
    station_location = models.CharField(name="station_location" , blank=False , max_length=100)
    station_longitude = models.FloatField(name="station_longitude" , blank=False)
    station_latitude = models.FloatField(name="station_latitude" , blank=False) 
    
    vehicles = models.ManyToManyField(
        name="stations_vehicles" , 
        to=Vehicle ,
        related_name="vehicles" ,
        related_query_name="vehicles",
        blank=False
    )

class Edge(models.Model):

    class Meta:
        db_table = "station_manager_station_edges"
        unique_together = (('src_station', 'dst_station'),)

    src_station = models.ForeignKey(
        name="src_station",
        to=Station , 
        on_delete=models.CASCADE ,
        related_name="src_station", 
        related_query_name="src_station",
        db_index = True,
        blank=False
    )
    
    dst_station = models.ForeignKey(
        name="dst_station", 
        to=Station,
        on_delete=models.CASCADE,
        related_name="dst_station",
        related_query_name="dst_station",
        blank=False
    )

    distance = models.FloatField(name="distance" , blank=False)