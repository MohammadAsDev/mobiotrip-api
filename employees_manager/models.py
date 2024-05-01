from django.db import models

from users_manager.models import User, UserTypes

# Create your models here.

"""
    Staff: proxy class to deal with staff-typed users
"""
class Staff(User):
    
    activation_number = None

    class Meta:
        db_table = "staffs" # the name of the staffs' view
        proxy = True
    
    def save(self , *args, **kwargs):
        kwargs["user_type"] = UserTypes.STAFF
        return super().save(*args , **kwargs)

    objects = User.objects.filter(user_type=UserTypes.STAFF)

"""
    Publishers: proxy class to deal with publisher-typed users
"""
class Publisher(User):
    
    activation_number = None

    class Meta:
        db_table = "publishers"
        proxy = True

    def save(self, *args, **kwargs):
        kwargs["user_type"] = UserTypes.PUBLISHER
        return super().save(*args , **kwargs)

    objects = User.objects.filter(user_type=UserTypes.PUBLISHER)
