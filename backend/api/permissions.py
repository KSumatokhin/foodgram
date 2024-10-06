from rest_framework import permissions

from foodgram_backend.constants import ME


class AllowAnyExceptMePoint(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (view.action != ME or user.is_authenticated)


class IsSuperUserOrOwnerOrReadOnly(
        permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or request.user == obj.author
        )
