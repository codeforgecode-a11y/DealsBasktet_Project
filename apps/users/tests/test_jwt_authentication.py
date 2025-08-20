"""
Tests for JWT authentication system
"""
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.jwt_authentication import JWTTokenManager, JWTAuthentication

User = get_user_model()

# Base URL for all JWT endpoints
JWT_BASE_URL = '/api/auth/jwt'


@pytest.mark.django_db
class TestJWTTokenManager:
    """Test JWT token management functionality"""

    def setup_method(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )

    def test_generate_tokens(self):
        """Test JWT token generation"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert 'access_token_expires' in tokens
        assert 'refresh_token_expires' in tokens
        
        # Verify token structure
        access_payload = jwt.decode(
            tokens['access_token'], 
            options={"verify_signature": False}
        )
        refresh_payload = jwt.decode(
            tokens['refresh_token'], 
            options={"verify_signature": False}
        )
        
        assert access_payload['user_id'] == self.user.id
        assert access_payload['username'] == self.user.username
        assert access_payload['email'] == self.user.email
        assert access_payload['role'] == self.user.role
        assert access_payload['type'] == 'access'
        
        assert refresh_payload['user_id'] == self.user.id
        assert refresh_payload['type'] == 'refresh'

    def test_verify_valid_access_token(self):
        """Test verification of valid access token"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        payload = JWTTokenManager.verify_token(tokens['access_token'], 'access')
        
        assert payload['user_id'] == self.user.id
        assert payload['type'] == 'access'

    def test_verify_valid_refresh_token(self):
        """Test verification of valid refresh token"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        payload = JWTTokenManager.verify_token(tokens['refresh_token'], 'refresh')
        
        assert payload['user_id'] == self.user.id
        assert payload['type'] == 'refresh'

    def test_verify_invalid_token_type(self):
        """Test verification with wrong token type"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        
        with pytest.raises(Exception):
            JWTTokenManager.verify_token(tokens['access_token'], 'refresh')

    @patch('users.jwt_authentication.jwt.decode')
    def test_verify_expired_token(self, mock_decode):
        """Test verification of expired token"""
        mock_decode.side_effect = jwt.ExpiredSignatureError('Token expired')
        
        with pytest.raises(Exception):
            JWTTokenManager.verify_token('expired_token', 'access')

    def test_refresh_access_token(self):
        """Test access token refresh"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        new_access_token, expires = JWTTokenManager.refresh_access_token(tokens['refresh_token'])
        
        assert new_access_token != tokens['access_token']
        assert isinstance(expires, datetime)
        
        # Verify new token
        payload = JWTTokenManager.verify_token(new_access_token, 'access')
        assert payload['user_id'] == self.user.id

    @override_settings(JWT_ALLOW_REFRESH=False)
    def test_refresh_disabled(self):
        """Test token refresh when disabled"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        
        with pytest.raises(Exception):
            JWTTokenManager.refresh_access_token(tokens['refresh_token'])


@pytest.mark.django_db
class TestJWTAuthentication:
    """Test JWT authentication backend"""

    def setup_method(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )
        self.auth_backend = JWTAuthentication()
        self.client = APIClient()

    def test_no_authorization_header(self):
        """Test authentication with no authorization header"""
        request = self.client.get('/').wsgi_request
        result = self.auth_backend.authenticate(request)
        assert result is None

    def test_invalid_authorization_header_format(self):
        """Test authentication with invalid header format"""
        request = self.client.get('/', HTTP_AUTHORIZATION='InvalidFormat').wsgi_request
        result = self.auth_backend.authenticate(request)
        assert result is None

    def test_valid_jwt_token(self):
        """Test authentication with valid JWT token"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        request = self.client.get(
            '/', 
            HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}'
        ).wsgi_request
        
        result = self.auth_backend.authenticate(request)
        assert result is not None
        auth_user, auth_token = result
        assert auth_user == self.user
        assert auth_token == tokens["access_token"]

    def test_inactive_user(self):
        """Test authentication with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        tokens = JWTTokenManager.generate_tokens(self.user)
        request = self.client.get(
            '/', 
            HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}'
        ).wsgi_request
        
        with pytest.raises(Exception):
            self.auth_backend.authenticate(request)

    def test_nonexistent_user(self):
        """Test authentication with token for nonexistent user"""
        tokens = JWTTokenManager.generate_tokens(self.user)
        self.user.delete()
        
        request = self.client.get(
            '/', 
            HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}'
        ).wsgi_request
        
        with pytest.raises(Exception):
            self.auth_backend.authenticate(request)


class TestJWTViews(APITestCase):
    """Test JWT authentication views"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user'
        )

    def test_jwt_login_success(self):
        """Test successful JWT login"""
        response = self.client.post(f'{JWT_BASE_URL}/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data

    def test_jwt_login_with_email(self):
        """Test JWT login with email"""
        response = self.client.post(f'{JWT_BASE_URL}/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['success'] is True

    def test_jwt_login_invalid_credentials(self):
        """Test JWT login with invalid credentials"""
        response = self.client.post(f'{JWT_BASE_URL}/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert 'error' in data

    def test_jwt_login_missing_fields(self):
        """Test JWT login with missing fields"""
        response = self.client.post(f'{JWT_BASE_URL}/login/', {
            'username': 'testuser'
        })
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_jwt_refresh_success(self):
        """Test successful JWT token refresh"""
        # First login to get tokens
        login_response = self.client.post(f'{JWT_BASE_URL}/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        tokens = login_response.json()
        
        # Refresh token
        response = self.client.post(f'{JWT_BASE_URL}/refresh/', {
            'refresh_token': tokens['refresh_token']
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['success'] is True
        assert 'access_token' in data

    def test_jwt_refresh_invalid_token(self):
        """Test JWT refresh with invalid token"""
        response = self.client.post(f'{JWT_BASE_URL}/refresh/', {
            'refresh_token': 'invalid_token'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_jwt_verify_valid_token(self):
        """Test JWT token verification with valid token"""
        # Get token
        login_response = self.client.post(f'{JWT_BASE_URL}/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        tokens = login_response.json()
        
        # Verify token
        response = self.client.post(f'{JWT_BASE_URL}/verify/', {
            'token': tokens['access_token']
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['valid'] is True

    def test_jwt_verify_invalid_token(self):
        """Test JWT token verification with invalid token"""
        response = self.client.post(f'{JWT_BASE_URL}/verify/', {
            'token': 'invalid_token'
        })
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data['valid'] is False

    def test_jwt_logout(self):
        """Test JWT logout"""
        # Login first
        login_response = self.client.post(f'{JWT_BASE_URL}/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        tokens = login_response.json()
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access_token"]}')
        
        # Logout
        response = self.client.post(f'{JWT_BASE_URL}/logout/', {
            'refresh_token': tokens['refresh_token']
        })
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['success'] is True