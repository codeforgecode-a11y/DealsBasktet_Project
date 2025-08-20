from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin_user


class IsShopkeeper(permissions.BasePermission):
    """
    Custom permission to only allow shopkeepers.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_shopkeeper


class IsDeliveryPerson(permissions.BasePermission):
    """
    Custom permission to only allow delivery persons.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_delivery_person


class IsShopkeeperOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow shopkeepers and admin users.
    """
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                (request.user.is_shopkeeper or request.user.is_admin_user))


class IsDeliveryPersonOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow delivery persons and admin users.
    """
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                (request.user.is_delivery_person or request.user.is_admin_user))


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners and admin users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if request.user.is_admin_user:
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        else:
            return obj == request.user


class IsShopOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission for shop-related objects.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any shop
        if request.user.is_admin_user:
            return True
        
        # Shopkeepers can only access their own shop
        if request.user.is_shopkeeper:
            if hasattr(obj, 'shop'):
                return obj.shop.owner == request.user
            elif hasattr(obj, 'owner'):
                return obj.owner == request.user
            else:
                return obj == request.user
        
        return False
