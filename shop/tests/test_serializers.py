"""
Tests for Shop serializers
"""
import pytest
from django.contrib.auth import get_user_model
from shop.models import Shop
from shop.serializers import (
    ShopSerializer, ShopRegistrationSerializer, ShopUpdateSerializer,
    AdminShopSerializer, ShopListSerializer
)

User = get_user_model()


@pytest.mark.django_db
class TestShopSerializers:
    """Test Shop serializers"""

    def setup_method(self):
        """Set up test data"""
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            description='A test shop',
            address='123 Shop Street',
            phone='+1234567890',
            email='shop@example.com',
            status='approved'
        )

    def test_shop_serializer(self):
        """Test basic shop serializer"""
        serializer = ShopSerializer(self.shop)
        data = serializer.data
        
        assert data['name'] == 'Test Shop'
        assert data['description'] == 'A test shop'
        assert data['address'] == '123 Shop Street'
        assert data['phone'] == '+1234567890'
        assert data['email'] == 'shop@example.com'
        assert data['status'] == 'approved'
        assert 'owner' in data

    def test_shop_list_serializer(self):
        """Test shop list serializer (minimal fields)"""
        serializer = ShopListSerializer(self.shop)
        data = serializer.data
        
        assert data['name'] == 'Test Shop'
        assert data['address'] == '123 Shop Street'
        assert data['phone'] == '+1234567890'
        assert 'description' not in data  # Should not include description

    def test_shop_registration_serializer_valid(self):
        """Test shop registration serializer with valid data"""
        data = {
            'name': 'New Shop',
            'description': 'A new shop',
            'address': '456 New Street',
            'phone': '+9876543210',
            'email': 'newshop@example.com',
            'latitude': '40.7128',
            'longitude': '-74.0060',
            'opening_time': '09:00',
            'closing_time': '18:00'
        }
        
        serializer = ShopRegistrationSerializer(data=data)
        assert serializer.is_valid()
        
        # Test save method
        shop = serializer.save(owner=self.shopkeeper)
        assert shop.name == 'New Shop'
        assert shop.owner == self.shopkeeper
        assert shop.status == 'pending'  # Default status

    def test_shop_registration_serializer_invalid(self):
        """Test shop registration serializer with invalid data"""
        data = {
            'name': '',  # Empty name
            'address': '',  # Empty address
            'phone': 'invalid'  # Invalid phone
        }
        
        serializer = ShopRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'address' in serializer.errors

    def test_shop_update_serializer(self):
        """Test shop update serializer"""
        data = {
            'name': 'Updated Shop Name',
            'description': 'Updated description',
            'phone': '+1111111111'
        }
        
        serializer = ShopUpdateSerializer(self.shop, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_shop = serializer.save()
        assert updated_shop.name == 'Updated Shop Name'
        assert updated_shop.description == 'Updated description'
        assert updated_shop.phone == '+1111111111'

    def test_admin_shop_serializer(self):
        """Test admin shop serializer (includes admin-only fields)"""
        serializer = AdminShopSerializer(self.shop)
        data = serializer.data
        
        assert data['name'] == 'Test Shop'
        assert data['status'] == 'approved'
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_admin_shop_serializer_status_update(self):
        """Test admin shop serializer status update"""
        data = {'status': 'suspended'}
        
        serializer = AdminShopSerializer(self.shop, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_shop = serializer.save()
        assert updated_shop.status == 'suspended'

    def test_shop_serializer_read_only_fields(self):
        """Test that certain fields are read-only"""
        data = {
            'name': 'Hacked Shop',
            'status': 'approved',  # Should not be updatable by regular serializer
            'created_at': '2023-01-01T00:00:00Z'  # Should not be updatable
        }
        
        serializer = ShopUpdateSerializer(self.shop, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_shop = serializer.save()
        assert updated_shop.name == 'Hacked Shop'
        assert updated_shop.status == 'approved'  # Should remain unchanged
        # created_at should remain unchanged (can't easily test exact value)

    def test_shop_serializer_validation(self):
        """Test custom validation in shop serializers"""
        # Test phone number validation
        data = {
            'name': 'Test Shop',
            'address': '123 Test Street',
            'phone': '123'  # Too short
        }
        
        serializer = ShopRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        # Phone validation is handled by the model validator

    def test_shop_serializer_nested_owner(self):
        """Test shop serializer with nested owner information"""
        serializer = ShopSerializer(self.shop)
        data = serializer.data
        
        assert 'owner' in data
        assert data['owner']['username'] == 'shopkeeper'
        assert data['owner']['email'] == 'shopkeeper@example.com'
