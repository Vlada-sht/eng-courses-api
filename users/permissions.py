from rest_framework import permissions

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access for unauthenticated users,
    and require authentication for modifying requests.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access for anyone,
    and require staff/admin permission for modifying requests.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to edit/delete it.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False

