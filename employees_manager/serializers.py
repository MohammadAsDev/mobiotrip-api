from rest_framework.serializers import ModelSerializer

from users_manager.serializers import EmployeeUserSerializer
from users_manager.models import UserTypes

class PublisherSerializer(EmployeeUserSerializer):
    user_type = None
 
    def create(self, validated_data: dict) -> any:
        validated_data["user_type"] = UserTypes.PUBLISHER
        return super().create(validated_data)
