"""
Tests for User models
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model functionality"""

    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.role == 'user'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password('testpass123')

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.role == 'admin'

    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='shopkeeper'
        )
        
        expected = 'testuser (Shopkeeper)'
        assert str(user) == expected



    def test_user_role_properties(self):
        """Test user role property methods"""
        # Test regular user
        user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='user'
        )
        assert user.is_user is True
        assert user.is_shopkeeper is False
        assert user.is_delivery_person is False
        assert user.is_admin_user is False

        # Test shopkeeper
        shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        assert shopkeeper.is_user is False
        assert shopkeeper.is_shopkeeper is True
        assert shopkeeper.is_delivery_person is False
        assert shopkeeper.is_admin_user is False

        # Test delivery person
        delivery = User.objects.create_user(
            username='delivery',
            email='delivery@example.com',
            role='delivery'
        )
        assert delivery.is_user is False
        assert delivery.is_shopkeeper is False
        assert delivery.is_delivery_person is True
        assert delivery.is_admin_user is False

        # Test admin
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        assert admin.is_user is False
        assert admin.is_shopkeeper is False
        assert admin.is_delivery_person is False
        assert admin.is_admin_user is True

    def test_superuser_is_admin(self):
        """Test that superuser is considered admin"""
        superuser = User.objects.create_superuser(
            username='superuser',
            email='superuser@example.com',
            password='superpass123'
        )
        assert superuser.is_admin_user is True

    def test_user_role_choices(self):
        """Test valid role choices"""
        valid_roles = ['user', 'shopkeeper', 'delivery', 'admin']
        
        for role in valid_roles:
            user = User.objects.create_user(
                username=f'test_{role}',
                email=f'{role}@example.com',
                role=role
            )
            assert user.role == role

    def test_user_optional_fields(self):
        """Test optional user fields"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            address='123 Test Street',
            is_verified=True
        )

        assert user.phone == '+1234567890'
        assert user.address == '123 Test Street'
        assert user.is_verified is True

    def test_user_timestamps(self):
        """Test user timestamp fields"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at
