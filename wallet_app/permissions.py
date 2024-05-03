from rest_framework.permissions import BasePermission

from users_manager.models import UserTypes

class IsOwnerOrStaff(BasePermission):
    def has_object_permission(self, request, view, wallet):
        if not request.user:
            return False
        
        if request.user.user_type == UserTypes.STAFF:
            return True
        
        if request.user == wallet.owner:
            return True
        
        return False
