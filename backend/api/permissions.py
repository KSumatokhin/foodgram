from rest_framework import permissions


class AllowAnyExceptMePoint(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if view.action == 'me' and user.is_authenticated is False:
            return False
        return True


class IsSuperUserOrOwnerOrReadOnly(
        permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or request.user == obj.author
        )
