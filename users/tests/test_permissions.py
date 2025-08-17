"""
Tests for custom permission classes
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from users.permissions import (
    IsOwnerOrReadOnly, IsAdminUser, IsShopkeeper, IsDeliveryPerson,
    IsShopkeeperOrAdmin, IsDeliveryPersonOrAdmin, IsOwnerOrAdmin,
    IsShopOwnerOrAdmin
)

User = get_user_model()


@pytest.mark.django_db
class TestPermissions:
    """Test custom permission classes"""

    def setup_method(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.view = APIView()

        # Create test users
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='user'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.delivery = User.objects.create_user(
            username='delivery',
            email='delivery@example.com',
            role='delivery'
        )

    def test_is_admin_user_permission(self):
        """Test IsAdminUser permission"""
        permission = IsAdminUser()

        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin
        assert permission.has_permission(request, self.view) is True

        # Test regular user
        request.user = self.user
        assert permission.has_permission(request, self.view) is False

        # Test unauthenticated user
        request.user = None
        assert permission.has_permission(request, self.view) is False

    def test_is_shopkeeper_permission(self):
        """Test IsShopkeeper permission"""
        permission = IsShopkeeper()

        # Test shopkeeper user
        request = self.factory.get('/')
        request.user = self.shopkeeper
        assert permission.has_permission(request, self.view) is True

        # Test regular user
        request.user = self.user
        assert permission.has_permission(request, self.view) is False

        # Test admin user (should not have shopkeeper permission)
        request.user = self.admin
        assert permission.has_permission(request, self.view) is False

    def test_is_delivery_person_permission(self):
        """Test IsDeliveryPerson permission"""
        permission = IsDeliveryPerson()

        # Test delivery person
        request = self.factory.get('/')
        request.user = self.delivery
        assert permission.has_permission(request, self.view) is True

        # Test regular user
        request.user = self.user
        assert permission.has_permission(request, self.view) is False

        # Test admin user (should not have delivery permission)
        request.user = self.admin
        assert permission.has_permission(request, self.view) is False

    def test_is_shopkeeper_or_admin_permission(self):
        """Test IsShopkeeperOrAdmin permission"""
        permission = IsShopkeeperOrAdmin()

        # Test shopkeeper user
        request = self.factory.get('/')
        request.user = self.shopkeeper
        assert permission.has_permission(request, self.view) is True

        # Test admin user
        request.user = self.admin
        assert permission.has_permission(request, self.view) is True

        # Test regular user
        request.user = self.user
        assert permission.has_permission(request, self.view) is False

        # Test delivery person
        request.user = self.delivery
        assert permission.has_permission(request, self.view) is False

    def test_is_delivery_person_or_admin_permission(self):
        """Test IsDeliveryPersonOrAdmin permission"""
        permission = IsDeliveryPersonOrAdmin()

        # Test delivery person
        request = self.factory.get('/')
        request.user = self.delivery
        assert permission.has_permission(request, self.view) is True

        # Test admin user
        request.user = self.admin
        assert permission.has_permission(request, self.view) is True

        # Test regular user
        request.user = self.user
        assert permission.has_permission(request, self.view) is False

        # Test shopkeeper
        request.user = self.shopkeeper
        assert permission.has_permission(request, self.view) is False

    def test_is_owner_or_read_only_permission(self):
        """Test IsOwnerOrReadOnly permission"""
        permission = IsOwnerOrReadOnly()

        # Create mock object with user attribute
        class MockObject:
            def __init__(self, user):
                self.user = user

        obj = MockObject(self.user)

        # Test GET request (safe method)
        request = self.factory.get('/')
        request.user = self.shopkeeper  # Different user
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test POST request by owner
        request = self.factory.post('/')
        request.user = self.user  # Same user as object owner
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test POST request by different user
        request.user = self.shopkeeper  # Different user
        assert permission.has_object_permission(request, self.view, obj) is False

    def test_is_owner_or_admin_permission(self):
        """Test IsOwnerOrAdmin permission"""
        permission = IsOwnerOrAdmin()

        # Create mock object with user attribute
        class MockObject:
            def __init__(self, user):
                self.user = user

        obj = MockObject(self.user)

        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test owner user
        request.user = self.user
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test different user
        request.user = self.shopkeeper
        assert permission.has_object_permission(request, self.view, obj) is False

    def test_is_owner_or_admin_with_owner_attribute(self):
        """Test IsOwnerOrAdmin permission with owner attribute"""
        permission = IsOwnerOrAdmin()

        # Create mock object with owner attribute
        class MockObject:
            def __init__(self, owner):
                self.owner = owner

        obj = MockObject(self.user)

        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test owner user
        request.user = self.user
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test different user
        request.user = self.shopkeeper
        assert permission.has_object_permission(request, self.view, obj) is False

    def test_is_owner_or_admin_with_user_object(self):
        """Test IsOwnerOrAdmin permission with user object itself"""
        permission = IsOwnerOrAdmin()

        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin
        assert permission.has_object_permission(request, self.view, self.user) is True

        # Test same user
        request.user = self.user
        assert permission.has_object_permission(request, self.view, self.user) is True

        # Test different user
        request.user = self.shopkeeper
        assert permission.has_object_permission(request, self.view, self.user) is False

    def test_is_shop_owner_or_admin_permission(self):
        """Test IsShopOwnerOrAdmin permission"""
        permission = IsShopOwnerOrAdmin()

        # Create mock shop object
        class MockShop:
            def __init__(self, owner):
                self.owner = owner

        # Create mock object with shop attribute
        class MockObject:
            def __init__(self, shop):
                self.shop = shop

        shop = MockShop(self.shopkeeper)
        obj = MockObject(shop)

        # Test admin user
        request = self.factory.get('/')
        request.user = self.admin
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test shop owner
        request.user = self.shopkeeper
        assert permission.has_object_permission(request, self.view, obj) is True

        # Test different shopkeeper
        other_shopkeeper = User.objects.create_user(
            username='other_shopkeeper',
            email='other@example.com',
            role='shopkeeper'
        )
        request.user = other_shopkeeper
        assert permission.has_object_permission(request, self.view, obj) is False

        # Test regular user
        request.user = self.user
        assert permission.has_object_permission(request, self.view, obj) is False
