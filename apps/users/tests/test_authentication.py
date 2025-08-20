"""
Tests for authentication system
"""
import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


@pytest.mark.django_db
class TestAuthentication:
    """Test JWT authentication functionality"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_verified=True
        )
        self.login_url = '/api/auth/login/'
        self.refresh_url = '/api/auth/token/refresh/'
        self.verify_url = '/api/auth/token/verify/'
        self.user_profile_url = '/api/auth/user-profile/'
        self.password_change_url = '/api/auth/password/change/'
        self.password_reset_url = '/api/auth/password/reset/'

    def test_login_success(self):
        """Test successful login"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self):
        """Test token refresh functionality"""
        refresh = RefreshToken.for_user(self.user)
        data = {'refresh': str(refresh)}
        response = self.client.post(self.refresh_url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_token_verify(self):
        """Test token verification"""
        token = AccessToken.for_user(self.user)
        data = {'token': str(token)}
        response = self.client.post(self.verify_url, data)
        assert response.status_code == status.HTTP_200_OK

    def test_protected_route_access(self):
        """Test accessing protected route with valid token"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
        response = self.client.get(self.user_profile_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == self.user.email

    def test_protected_route_no_token(self):
        """Test accessing protected route without token"""
        response = self.client.get(self.user_profile_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_route_expired_token(self):
        """Test accessing protected route with expired token"""
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(days=-1))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
        response = self.client.get(self.user_profile_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_change(self):
        """Test password change functionality"""
        token = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newtestpass123'
        }
        response = self.client.post(self.password_change_url, data)
        assert response.status_code == status.HTTP_200_OK

        # Verify new password works
        login_data = {
            'email': 'test@example.com',
            'password': 'newtestpass123'
        }
        response = self.client.post(self.login_url, login_data)
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_flow(self):
        """Test password reset flow"""
        # Request password reset
        data = {'email': 'test@example.com'}
        response = self.client.post(self.password_reset_url, data)
        assert response.status_code == status.HTTP_200_OK

        # Get the token from the user model
        self.user.refresh_from_db()
        reset_token = self.user.password_reset_token

        # Reset password
        data = {
            'token': reset_token,
            'new_password': 'resetpass123'
        }
        response = self.client.post(f'{self.password_reset_url}confirm/', data)
        assert response.status_code == status.HTTP_200_OK

        # Verify new password works
        login_data = {
            'email': 'test@example.com',
            'password': 'resetpass123'
        }
        response = self.client.post(self.login_url, login_data)
        assert response.status_code == status.HTTP_200_OK
