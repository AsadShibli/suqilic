from rest_framework.permissions import BasePermission, IsAdminUser


class IsStaff(IsAdminUser):
    pass


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)
