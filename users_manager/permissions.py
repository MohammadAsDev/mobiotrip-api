from rest_framework import permissions
from .models import UserTypes

class IsOwnerOrStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            return obj.id == request.user.id or request.user.user_type == UserTypes.STAFF
        return False
    
class IsRider(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.user_type == UserTypes.RIDER
        return False
    
class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.user_type == UserTypes.DRIVER
        return False
