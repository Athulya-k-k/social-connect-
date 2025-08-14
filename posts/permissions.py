# posts/permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of a post to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # read-only allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # write permissions only for author
        return request.user and request.user.is_authenticated and obj.author == request.user
