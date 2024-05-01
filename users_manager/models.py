from django.db import models
from django.contrib.auth.models import AbstractUser , BaseUserManager


import re
from datetime import date , timedelta



# Create your models here.
# Don't forget to run "user_types_views.sql" script.
# To create some user-type views

"""
    @TODO Make some automation tests on the schema
"""

"""
    UserManager: objects manager class, override methods (create_user) and (create_superuser)
"""
class UserManager(BaseUserManager):

    def _is_alphabetic(self, str_data : str) -> bool:
        pattern = re.compile("[A-Za-z]+")
        return (re.fullmatch(pattern , str_data) != None)
    
    def _is_valid_date(self, in_date : date) -> bool:

        delta_time = timedelta(days=45390)  # randomly selected range

        end_date = date.today()
        start_date = end_date - delta_time
        
        if in_date < end_date and start_date < in_date:
            return True
        return False
    
    def _is_valid_phone_number(self, phone_number : str) -> bool:
        pattern = re.compile("09[0-9]+")        
        if len(phone_number) == 10 and re.fullmatch(pattern , phone_number) != None:
            return True

        return False

    def _is_valid_email(self, email_addr : str) -> bool:
        pattern = re.compile("[A-z0-9]+\@[a-z]+\.com")
        return (re.fullmatch(pattern= pattern , string=email_addr) != None)


    def _is_valid_password(self, password : str) -> bool:
        return (len(password) >= 8)

    def _validate_first_name(self, first_name : str) -> str:
        if not first_name:
            raise ValueError("first name is required to create new user")
       
        if not self._is_alphabetic(first_name) :
            raise ValueError("first name should only have alphabetic characters")
        
        return first_name.lower()
    
    def _validate_last_name(self, last_name : str) -> str:
        if not last_name:
            raise ValueError("last name is required to create new user")

        if not self._is_alphabetic(last_name):
            raise ValueError("last name should only have alphabetic characters")

        return last_name.lower()

    def _validate_phone_number(self , phone_number : str) -> str:
        if not phone_number:
            raise ValueError("phone number is required to create new user")
        if not self._is_valid_phone_number(phone_number):
            raise ValueError("phone number is not valid")
        
        return phone_number

    def _validate_birthdate(self, birth_date : date) -> date:
        if not birth_date:
            raise ValueError("birth date is required to create new user")

        if not self._is_valid_date(birth_date): 
            raise ValueError("birth date is inconsistent")

        return birth_date

    def _validate_email(self, email : str) -> str:
        if not email:
            raise ValueError("email is required to create new user")
        if not self._is_valid_email(email):
            raise ValueError("email is not valid")

        return email
    
    def _validate_password(self, password : str) -> str:
        if not password:
            raise ValueError("password is required to create new user")
        if not self._is_valid_password(password):
            raise ValueError("password is not valid")

        return password

    def _validate_gender(self, gender : str) -> str:
        if not gender:
            raise ValueError("gender is required to create new user")
        
        if gender not in dict(UserGenders.choices):
            raise ValueError("gender is not defined in the system")
        
        return gender
    
    def _validate_user_type(self, user_type : int) -> int:
        if user_type == None:
            raise ValueError("user type is required to create a new user")

        if user_type not in dict(UserTypes.choices):
            raise ValueError("user type is not defined in the system")
        
        return user_type

    def _validate_data(self, **user_data) -> dict:

        user_valid_data = dict()

        # Checking phone number or email address
        if not user_data.get("username"):    
            raise ValueError("phone number or email is required to create new user")

        if user_data.get("user_type") in CASUAL_USERS:
            if self._is_valid_phone_number(user_data.get("username")):
                user_valid_data["username"] = user_data.get("username")
            else:
                raise ValueError("invalid phone number, phone numbers should start with (09) and have 10 digits")
        
        elif user_data.get("user_type") in EMPLOYED_USERS:
            if self._is_valid_email(user_data.get("username")):
                user_valid_data["username"] = user_data.get("username")
            else:
                raise ValueError("invalid email address")
        
        else:
            raise ValueError("user type is not defined in the system")
        
        user_valid_data["first_name"] = self._validate_first_name(user_data.get("first_name"))
        user_valid_data["last_name"] = self._validate_last_name(user_data.get("last_name"))
        user_valid_data["birth_date"] = self._validate_birthdate(user_data.get("birth_date"))
        user_valid_data["gender"] = self._validate_gender(user_data.get("gender"))
        user_valid_data["user_type"] = self._validate_user_type(user_data.get("user_type"))
        user_valid_data["password"] = self._validate_password(user_data.get("password"))

        """
            Keeping data
        """
        for attr, val in user_data.items():
            if attr not in user_valid_data:
                user_valid_data[attr] = val

        return user_valid_data
    
    def create_user(self, username : str , password : str, **cred):

        cred.setdefault("is_superuser" , False)
        cred.setdefault("is_staff" , False)
        cred.setdefault("is_active" , True) # TODO Add a verification code to activate accounts

        validated_data = self._validate_data(username = username , password = password , **cred)

        if cred.get("is_superuser") == True or cred.get("is_staff") == True:
            raise ValueError("Normal users could not be super users or staffs")
          
        user = self.model(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user
        

    def create_superuser(self, username : str, password : str  , **cred):
        
        cred.setdefault("is_superuser" , True)
        cred.setdefault("is_staff" , True)
        cred.setdefault("is_active" , True)
        cred.setdefault("user_type" , UserTypes.STAFF)

        validated_data = self._validate_data(username = username , password= password, **cred)
        
        if cred.get("is_superuser") != True or cred.get("is_staff") != True:
            raise ValueError("failed to create super user, is_super and is_staff should be both True")
        
        if cred.get("user_type") != UserTypes.STAFF:
            raise ValueError("super users should have staff role on the system")
                
        user = self.model(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user
        
"""
    UserTypes: Choices class for users' types
"""
class UserTypes(models.IntegerChoices):
    RIDER       = 0
    DRIVER      = 1
    STAFF       = 2
    PUBLISHER   = 3

CASUAL_USERS = [UserTypes.RIDER, UserTypes.DRIVER]
EMPLOYED_USERS = [UserTypes.STAFF, UserTypes.PUBLISHER]

"""
    UserGender: Choices class for users' genders
"""
class UserGenders(models.TextChoices):
    MALE    = "Male"
    FEMALE  = "Female"
    OTHERS  = "Others"

"""
    The main "User" class that we'll use.
"""
class User(AbstractUser):
   
    class Meta:
        db_table = "mobiotrip_users"

    email = None

    username = models.CharField(db_column="email_or_phone_number" , max_length= 100 , blank=False, unique=True)

    first_name = models.CharField(name="first_name" , max_length=100, blank=True , null=True)
    last_name = models.CharField(name="last_name" , max_length=100)
    birth_date = models.DateField(name="birth_date" , blank=False, null=False)
    gender = models.CharField(name="gender", choices=UserGenders.choices , max_length=10)
    user_type = models.SmallIntegerField(name="user_type" , choices=UserTypes.choices , editable=False , db_index=True)
    
    REQUIRED_FIELDS = ["birth_date" , "gender" , "first_name" , "last_name" , "user_type"]

    USERNAME_FIELD = "username"

    objects = UserManager()

"""
    Rider: proxy class to deal with rider-typed users
"""
class Rider(User):
    class Meta:
        db_table = "riders"  # the name of the riders' view
        proxy = True

    def save(self , *args , **kwargs):
        kwargs["user_type"] = UserTypes.RIDER
        return super().save(*args , **kwargs)

    objects = User.objects.filter(user_type=UserTypes.RIDER)

"""
    Driver: proxy class to deal with driver-typed users
"""
class Driver(User):
    class Meta:
        db_table = "drivers" # the name of the drivers' view
        proxy = True

    def save(self , *args, **kwargs):
        kwargs["user_type"] = UserTypes.DRIVER
        return super().save(*args, **kwargs)

    objects = User.objects.filter(user_type=UserTypes.DRIVER)


class ActivationCodes(models.Model):
    user = models.OneToOneField(name="user", to=User , related_name="user", on_delete=models.CASCADE, blank=False)
    activation_number = models.CharField(name="activation_number" , max_length=10, blank=False) 