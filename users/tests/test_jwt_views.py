"""
Tests for JWT view functions
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestJWTViews:
    """Test JWT authentication view functions"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_verified=True
        )
        self.login_url = reverse('jwt_token_obtain_pair')
        self.refresh_url = reverse('jwt_token_refresh')
        self.verify_url = reverse('jwt_token_verify')
        self.blacklist_url = reverse('jwt_token_blacklist')

    def test_token_obtain_pair(self):
        """Test obtaining token pair"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

        # Try to access protected endpoint with new token
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        profile_response = self.client.get('/api/auth/user-profile/')
        assert profile_response.status_code == status.HTTP_200_OK

    def test_token_obtain_pair_unverified_user(self):
        """Test obtaining token pair with unverified user"""
        # Update user to unverified
        self.user.is_verified = False
        self.user.save()

        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_token_refresh(self):
        """Test refreshing access token"""
        # Get initial tokens
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        refresh_token = response.data['refresh']

        # Use refresh token to get new access token
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, refresh_data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

        # Verify new access token works
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        profile_response = self.client.get('/api/auth/user-profile/')
        assert profile_response.status_code == status.HTTP_200_OK

    def test_token_verify(self):
        """Test token verification"""
        # Get token
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        token = response.data['access']

        # Verify token
        verify_data = {'token': token}
        response = self.client.post(self.verify_url, verify_data)
        assert response.status_code == status.HTTP_200_OK

    def test_token_blacklist(self):
        """Test token blacklisting"""
        # Get tokens
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        refresh_token = response.data['refresh']

        # Blacklist refresh token
        blacklist_data = {'refresh': refresh_token}
        response = self.client.post(self.blacklist_url, blacklist_data)
        assert response.status_code == status.HTTP_200_OK

        # Try to use blacklisted refresh token
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, refresh_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_verify(self):
        """Test token verification with invalid token"""
        verify_data = {'token': 'invalid_token'}
        response = self.client.post(self.verify_url, verify_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_obtain_pair_invalid_credentials(self):
        """Test obtaining token pair with invalid credentials"""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_obtain_pair_inactive_user(self):
        """Test obtaining token pair with inactive user"""
        # Deactivate user
        self.user.is_active = False
        self.user.save()

        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh_expired(self):
        """Test refreshing token with expired refresh token"""
        # Get initial tokens
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        refresh_token = RefreshToken(response.data['refresh'])

        # Manually expire refresh token
        refresh_token.set_exp(lifetime=timedelta(days=-1))

        # Try to refresh with expired token
        refresh_data = {'refresh': str(refresh_token)}
        response = self.client.post(self.refresh_url, refresh_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_concurrent_refresh(self):
        """Test concurrent token refresh"""
        # Get initial tokens
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        refresh_token = response.data['refresh']

        # First refresh
        refresh_data = {'refresh': refresh_token}
        response1 = self.client.post(self.refresh_url, refresh_data)
        assert response1.status_code == status.HTTP_200_OK

        # Second refresh with same token
        response2 = self.client.post(self.refresh_url, refresh_data)
        assert response2.status_code == status.HTTP_200_OK

        # Both tokens should be valid
        token1 = response1.data['access']
        token2 = response2.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token1}')
        response = self.client.get('/api/auth/user-profile/')
        assert response.status_code == status.HTTP_200_OK

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token2}')
        response = self.client.get('/api/auth/user-profile/')
        assert response.status_code == status.HTTP_200_OK