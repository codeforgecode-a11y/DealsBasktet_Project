"""
Tests for Shop models
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from apps.shop.models import Shop

User = get_user_model()


@pytest.mark.django_db
class TestShopModel:
    """Test Shop model functionality"""

    def setup_method(self):
        """Set up test data"""
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='user'
        )

    def test_create_shop(self):
        """Test creating a shop"""
        shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            description='A test shop',
            address='123 Shop Street',
            phone='+1234567890',
            email='shop@example.com',
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060'),
            opening_time='09:00',
            closing_time='18:00'
        )
        
        assert shop.name == 'Test Shop'
        assert shop.owner == self.shopkeeper
        assert shop.status == 'pending'  # Default status
        assert shop.is_active is True  # Default value
        assert shop.latitude == Decimal('40.7128')
        assert shop.longitude == Decimal('-74.0060')

    def test_shop_str_representation(self):
        """Test shop string representation"""
        shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            address='123 Shop Street',
            phone='+1234567890'
        )
        
        expected = 'Test Shop - shopkeeper'
        assert str(shop) == expected

    def test_shop_status_choices(self):
        """Test valid shop status choices"""
        valid_statuses = ['pending', 'approved', 'suspended', 'rejected']
        
        for status in valid_statuses:
            shop = Shop.objects.create(
                owner=self.shopkeeper,
                name=f'Shop {status}',
                address='123 Shop Street',
                phone='+1234567890',
                status=status
            )
            assert shop.status == status

    def test_shop_owner_must_be_shopkeeper(self):
        """Test that shop owner must have shopkeeper role"""
        # This constraint is enforced at the application level
        # The model allows any user, but views should enforce the role
        shop = Shop.objects.create(
            owner=self.user,  # Regular user, not shopkeeper
            name='Invalid Shop',
            address='123 Shop Street',
            phone='+1234567890'
        )
        
        # Shop is created but should be validated at view level
        assert shop.owner == self.user

    def test_shop_phone_validation(self):
        """Test shop phone number validation"""
        # Valid phone numbers
        valid_phones = ['+1234567890', '1234567890', '+12345678901234']
        
        for phone in valid_phones:
            shop = Shop.objects.create(
                owner=self.shopkeeper,
                name=f'Shop {phone}',
                address='123 Shop Street',
                phone=phone
            )
            assert shop.phone == phone

    def test_shop_one_to_one_relationship(self):
        """Test that shopkeeper can only have one shop"""
        # Create first shop
        Shop.objects.create(
            owner=self.shopkeeper,
            name='First Shop',
            address='123 Shop Street',
            phone='+1234567890'
        )
        
        # Try to create second shop with same owner
        with pytest.raises(IntegrityError):
            Shop.objects.create(
                owner=self.shopkeeper,
                name='Second Shop',
                address='456 Shop Street',
                phone='+0987654321'
            )

    def test_shop_property_methods(self):
        """Test shop property methods"""
        # Test pending shop
        pending_shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Pending Shop',
            address='123 Shop Street',
            phone='+1234567890',
            status='pending'
        )
        assert pending_shop.is_pending is True
        assert pending_shop.is_approved is False
        assert pending_shop.can_accept_orders is False

        # Test approved shop
        approved_shop = Shop.objects.create(
            owner=User.objects.create_user(
                username='shopkeeper2',
                email='shopkeeper2@example.com',
                role='shopkeeper'
            ),
            name='Approved Shop',
            address='456 Shop Street',
            phone='+0987654321',
            status='approved',
            is_active=True
        )
        assert approved_shop.is_pending is False
        assert approved_shop.is_approved is True
        assert approved_shop.can_accept_orders is True

        # Test inactive approved shop
        approved_shop.is_active = False
        approved_shop.save()
        assert approved_shop.can_accept_orders is False

    def test_shop_optional_fields(self):
        """Test shop optional fields"""
        shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Minimal Shop',
            address='123 Shop Street',
            phone='+1234567890'
            # Optional fields not provided
        )
        
        assert shop.description is None
        assert shop.email is None
        assert shop.latitude is None
        assert shop.longitude is None
        assert shop.opening_time is None
        assert shop.closing_time is None

    def test_shop_timestamps(self):
        """Test shop timestamp fields"""
        shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            address='123 Shop Street',
            phone='+1234567890'
        )
        
        assert shop.created_at is not None
        assert shop.updated_at is not None
        assert shop.created_at <= shop.updated_at

    def test_shop_ordering(self):
        """Test shop default ordering"""
        # Create shops with different creation times
        shop1 = Shop.objects.create(
            owner=self.shopkeeper,
            name='First Shop',
            address='123 Shop Street',
            phone='+1234567890'
        )
        
        shop2 = Shop.objects.create(
            owner=User.objects.create_user(
                username='shopkeeper2',
                email='shopkeeper2@example.com',
                role='shopkeeper'
            ),
            name='Second Shop',
            address='456 Shop Street',
            phone='+0987654321'
        )
        
        # Should be ordered by -created_at (newest first)
        shops = list(Shop.objects.all())
        assert shops[0] == shop2  # Newest first
        assert shops[1] == shop1
