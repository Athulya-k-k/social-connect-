# accounts/permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj is User instance
        return request.user and (request.user.is_staff or obj == request.user)
