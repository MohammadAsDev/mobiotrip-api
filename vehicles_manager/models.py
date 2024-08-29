from django.db import models

from users_manager.models import User
# Create your models here.

class VehicleGovernorates(models.TextChoices):
    HOMS = "Homs"
    DAMASCUS = "Damascus"
    ALEPPO = "Aleppo"
    TARTUS = "Tartus"
    LATAKIA = "Latakia"

class VehicleTypes(models.IntegerChoices):
    PUBLIC = 0
    PERSONAL = 1

class SeatsNumber(models.IntegerChoices):
    SMALL  = 2
    MEDUIM = 5
    LARGE  = 8

"""
    This is the basic vehicle model
"""
class Vehicle(models.Model):
    vehicle_number = models.TextField(
        max_length=10, 
        name="vehicle_number",
        unique=True,
        blank=False
    )

    owner = models.OneToOneField(
        db_column="owner_id",
        to=User,
        blank=False,
        name="owner",
        on_delete=models.CASCADE,
        primary_key=True
    )

    seats_number = models.SmallIntegerField(
        name="seats_number",
        blank=False,
        choices=SeatsNumber.choices
    )

    vehicle_color = models.CharField(
        name="vehicle_color",
        blank=False,
        max_length=50
    )

    vehicle_governorate = models.CharField(
        max_length=50,
        blank=False,
        name="vehicle_governorate",
        choices=VehicleGovernorates.choices
    )

    vehicle_type = models.SmallIntegerField(
        choices=VehicleTypes.choices,
        blank=False,
        name="vehicle_type",
        db_index=True
    )

"""
    Proxy model for "driver_vehicle" view
    note: please run the ".sql" script after doing migration
"""
class DriverVehicleDbView(models.Model):
    class Meta:
        managed=False   # telling django that we deal with a view
        db_table = "driver_vehicle"

    vehicle_number = models.TextField(
        max_length=10, 
        name="vehicle_number",
        unique=True,
        blank=False
    )

    seats_number = models.SmallIntegerField(
        name="seats_number",
        blank=False
    )

    vehicle_color = models.CharField(
        name="vehicle_color",
        blank=False,
        max_length=50
    )

    vehicle_governorate = models.CharField(
        max_length=50,
        blank=False,
        name="vehicle_governorate",
        choices=VehicleGovernorates.choices
    )

    vehicle_type = models.SmallIntegerField(
        choices=VehicleTypes.choices,
        blank=False,
        name="vehicle_type",
        db_index=True
    )

    first_name = models.CharField(
        name="first_name" , 
        max_length=100, 
        blank=False
    )
    
    last_name = models.CharField(
        name="last_name" , 
        max_length=100
    )
    
    username = models.CharField(
        name="username" , 
        max_length=100 , 
        db_column="email_or_phone_number",
        blank=False , 
        unique=True 
    )
    
    birth_date = models.DateField(
        name="birth_date" , 
        blank=False, 
        null=False
    )
    
    gender = models.CharField(
        name="gender", 
        max_length=10
    )

class PublicVehicle(Vehicle):
    class Meta:
        proxy = True
        db_table = "public_vehicles"

    def save(self , *args , **kwargs):
        kwargs["vehicle_type"] = VehicleTypes.PUBLIC
        return super().save(*args , **kwargs)

    objects = Vehicle.objects.filter(vehicle_type=VehicleTypes.PUBLIC)

class PersonalVehicle(Vehicle):
    class Meta:
        proxy = True
        db_table = "personal_vehicles"

    def save(self, *args, **kwargs):
        kwargs["vehicle_type"] = VehicleTypes.PERSONAL
        return super().save(*args,  **kwargs)
    
    objects = Vehicle.objects.filter(vehicle_type=VehicleTypes.PERSONAL)