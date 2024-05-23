from rest_framework.permissions import BasePermission
from users_manager.models import UserTypes

class IsStaffOrPostOwner(BasePermission):
    def has_object_permission(self, request, view, post):
        if post.publisher.id == request.user.id or request.user.user_type == UserTypes.STAFF:
            return True
    
        return False
    
class IsPublisher(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == UserTypes.PUBLISHER:
            return True
        
        return False