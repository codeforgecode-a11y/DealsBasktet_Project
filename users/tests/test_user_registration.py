"""
Tests for user registration and email verification
"""
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, APIClient
from rest_framework import status
from django.core import mail
from users.views.auth_views import RegisterView

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Test user registration functionality"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.factory = APIRequestFactory()
        self.register_url = '/api/auth/register/'

    def test_successful_registration(self):
        """Test successful user registration"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }

        response = self.client.post(self.register_url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data

        # Verify user was created
        user = User.objects.get(email=data['email'])
        assert user.username == data['username']
        assert user.email == data['email']
        assert user.is_verified is False
        assert user.email_verification_token is not None

        # Verify email was sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0] == data['email']

    def test_registration_with_existing_email(self):
        """Test registration with existing email"""
        # Create existing user
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='existing123'
        )

        data = {
            'username': 'newuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }

        response = self.client.post(self.register_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_registration_with_weak_password(self):
        """Test registration with weak password"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak',
            'confirm_password': 'weak'
        }

        response = self.client.post(self.register_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_registration_with_mismatched_passwords(self):
        """Test registration with mismatched passwords"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'different123'
        }

        response = self.client.post(self.register_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_registration_missing_required_fields(self):
        """Test registration with missing required fields"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }

        response = self.client.post(self.register_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_email_verification(self):
        """Test email verification process"""
        # Register a user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            email_verification_token='test_token'
        )

        # Verify email
        response = self.client.post('/api/auth/verify-email/', {
            'token': 'test_token'
        })

        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_verified is True
        assert user.email_verification_token is None

    def test_email_verification_invalid_token(self):
        """Test email verification with invalid token"""
        response = self.client.post('/api/auth/verify-email/', {
            'token': 'invalid_token'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_resend_verification_email(self):
        """Test resending verification email"""
        # Create unverified user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_verified=False
        )

        # Login
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })

        assert response.status_code == status.HTTP_200_OK
        token = response.data['access_token']

        # Request new verification email
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/api/auth/resend-verification/')

        assert response.status_code == status.HTTP_200_OK
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to[0] == user.email