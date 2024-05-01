from users_manager.models import  UserTypes
from rest_framework.permissions import BasePermission

class IsVehicleOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view , vehicle):
        if vehicle.owner_id == request.user.id or request.user.user_type == UserTypes.STAFF:
            return True
        return False