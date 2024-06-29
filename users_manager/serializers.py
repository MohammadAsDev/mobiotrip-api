from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from .models import UserGenders, UserTypes , User
from vehicles_manager.models import Vehicle

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import APIException

from datetime import date , timedelta
import re

"""
    User Login Serializer
    Depends on TokenObtainSerializer from simple-jwt
    used to generate jwt tokens
"""
class UserLoginSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        """
            @TODO Decrypt jwt to see all the claims
        """
        token["username"] = user.username 
        token["first_name"] = user.first_name 
        token["last_name"] = user.last_name
        token["gender"] = user.gender
        token["birth_date"] = str(user.birth_date) 
        token["user_type"] = user.user_type

        return token


"""
    Default user's serailizer
    contains the shared fields between different type of users
"""
class UserSerializer(serializers.Serializer):
    
    class Meta:
        model = User

    GENDER_CHOICES = (
        (UserGenders.MALE   , "Male"),
        (UserGenders.FEMALE , "Female"),
        (UserGenders.OTHERS , "Others"),
    )

    TYPE_CHOICES = (
        (UserTypes.RIDER        , "Rider"),
        (UserTypes.DRIVER       , "Driver"),
        (UserTypes.STAFF        , "Staff"),
        (UserTypes.PUBLISHER    , "Publisher"),
    )

    id = serializers.IntegerField(allow_null=False, read_only=True)
    password = serializers.CharField(allow_null=False, allow_blank=False, min_length=8 , trim_whitespace=True, style={"input_type" : "password"})
    first_name = serializers.CharField(allow_null=False, allow_blank=False, trim_whitespace=True)
    last_name = serializers.CharField(allow_null=False, allow_blank=False, trim_whitespace=True)
    birth_date = serializers.DateField()
    gender = serializers.ChoiceField(allow_null=False, allow_blank=False, choices=GENDER_CHOICES)
    user_type = serializers.ChoiceField(allow_null=False, allow_blank=False, choices=TYPE_CHOICES, help_text="*Works only with creation")


    def validate_first_name(self, name : str) -> any:
        pattern = re.compile("[A-Za-z]+")
        if re.fullmatch(pattern, name) != None:
            return name.lower()
        raise serializers.ValidationError("First name is not valid")

    def validate_last_name(self, name : str) -> any:
        pattern = re.compile("[A-Za-z]+")
        if re.fullmatch(pattern, name) != None:
            return name.lower()
        raise serializers.ValidationError("Last name is not valid")
    

    def validate_birth_date(self, in_date : date) -> bool:
        delta_time = timedelta(days=45390)  # randomly selected range

        end_date = date.today()
        start_date = end_date - delta_time
        
        if in_date < end_date and start_date < in_date:
            return in_date        
        raise serializers.ValidationError("Birth date is not valid")

    def validate(self, data):
        first_name = self.validate_first_name(data.get("first_name"))
        last_name = self.validate_last_name(data.get("last_name"))
        birth_date = self.validate_birth_date(data.get("birth_date"))

        validated_data = {
            "first_name" : first_name,
            "last_name" : last_name,
            "birth_date" : birth_date,
        }

        for attr, val in data.items():  # add another values
            if attr not in validated_data:
                validated_data[attr] = val

        return validated_data

    def create(self, validated_data : dict) -> any: 
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data) -> User:
        instance.password = validated_data.get("password" , instance.password)
        instance.first_name = validated_data.get("first_name" , instance.first_name)
        instance.last_name = validated_data.get("last_name" , instance.last_name)
        instance.birth_date = validated_data.get("birth_date" , instance.birth_date)
        instance.gender = validated_data.get("gender", instance.gender)
        instance.save()
        return instance
    

"""
    Casual users' serializer
    used to create casual users that want to use the system
    (riders and drivers)
"""
class NormalUserSerializer(UserSerializer):
    username = serializers.CharField(allow_null=False, allow_blank=False, max_length=10 , min_length=10 , trim_whitespace=True, label="Phone number")
    
    def validate_phone_number(self , phone_number : str) -> any:
        pattern = re.compile("09[0-9]+")
        if len(phone_number) == 10 and re.fullmatch(pattern=pattern,string=phone_number) != None:
            return phone_number
        raise serializers.ValidationError("Phone number is not valid")
    
    def update(self, instance , validated_data) -> User:
        instance.phone_number_or_email = validated_data.get("username" , "")
        return super().update(instance= instance , validated_data=validated_data)

    def validate(self, data):
        phone_number = self.validate_phone_number(data.get("username"))
        data["username"] = phone_number
        return super().validate(data)
    
    def create(self, validated_data : dict) -> any: 
        username = validated_data.get("username" , "")
        user_obj = User.objects.filter(username = username)
        if not user_obj:
            return User.objects.create_user(**validated_data)
        else:
            raise APIException("username is used before")
"""
    Employees' serizlier
    used to create employees whatever their job
    (now we have staffs and publishers)
"""
class EmployeeUserSerializer(UserSerializer):
    username = serializers.EmailField(max_length=100,  allow_blank=False , allow_null=False)

    def validate_email(self , email : str) -> any:
        pattern = re.compile("[A-z0-9]+\@[a-z]+\.com")
        if re.fullmatch(pattern=pattern,string=email) != None:
            return email
        raise serializers.ValidationError("Email is not valid")
    
    def update(self, instance , validated_data) -> User:
        instance.username = validated_data.get("username" , "")
        return super().update(instance= instance , validated_data=validated_data)

    def validate(self, data):
        email = self.validate_email(data.get("username"))
        data["username"] = email
        return super().validate(data)
    
    def create(self, validated_data : dict) -> any: 
        username = validated_data.get("username" , "")
        user = User.objects.filter(username = username)
        if not user:
            return User.objects.create_user(**validated_data)
        else:
            raise APIException("username is used before")

"""
    Driver-specified serializer
    used to deal with driver-type
"""
class DriverSerializer(NormalUserSerializer):
    user_type = None
    def create(self, validated_data: dict) -> any:
        validated_data["user_type"] = UserTypes.DRIVER
        return super().create(validated_data)

"""
    Rider-specified serializer
    used to deal with rider-type
"""
class RiderSerializer(NormalUserSerializer):
    user_type = None
 
    def create(self, validated_data: dict) -> any:
        validated_data["user_type"] = UserTypes.RIDER
        return super().create(validated_data)

"""
    Staff-speicified serializer
    used to deal with staff-type
"""
class StaffSerializer(EmployeeUserSerializer):
    user_type = None

    def create(self, validate_data: dict) -> any:
        validate_data["user_type"] = UserTypes.STAFF
        return super().create(validate_data)

"""
    Publisher-speicified serializer
    used to deal with publisher-type
"""
class PublisherSerializer(EmployeeUserSerializer):
    user_type = None

    def create(self, validate_data: dict) -> any:
        validate_data["user_type"] = UserTypes.PUBLISHER
        return super().create(validate_data)
    