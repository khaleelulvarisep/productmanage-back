from rest_framework import permissions


class IsProductOwnerOrReadOnly(permissions.BasePermission):
    message = "Only the product owner can update or delete this product."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
