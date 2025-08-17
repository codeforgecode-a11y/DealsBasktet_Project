"""
Tests for User views and API endpoints
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationView:
    """Test user registration endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('users:user-register')

    def test_user_registration_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'role': 'user',
            'phone': '+1234567890',
            'address': '123 Test Street'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'message' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'newuser'
        assert response.data['user']['email'] == 'newuser@example.com'
        assert response.data['user']['role'] == 'user'

        # Verify user was created in database
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.role == 'user'

    def test_user_registration_invalid_data(self):
        """Test user registration with invalid data"""
        data = {
            'username': '',  # Empty username
            'email': 'invalid-email',  # Invalid email
            'password': '123',  # Too short password
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_duplicate_username(self):
        """Test user registration with duplicate username"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com'
        )

        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'newpass123'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_duplicate_email(self):
        """Test user registration with duplicate email"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='existing@example.com'
        )

        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'newpass123'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserProfileView:
    """Test user profile endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('users:user-profile')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='user',
            phone='+1234567890',
            address='123 Test Street'
        )

    def test_get_user_profile_authenticated(self):
        """Test getting user profile when authenticated"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'
        assert response.data['role'] == 'user'
        assert response.data['phone'] == '+1234567890'
        assert response.data['address'] == '123 Test Street'

    def test_get_user_profile_unauthenticated(self):
        """Test getting user profile when not authenticated"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_user_profile(self):
        """Test updating user profile"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'phone': '+9876543210',
            'address': '456 New Street',
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        response = self.client.put(self.url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['phone'] == '+9876543210'
        assert response.data['address'] == '456 New Street'
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'

        # Verify changes in database
        self.user.refresh_from_db()
        assert self.user.phone == '+9876543210'
        assert self.user.address == '456 New Street'

    def test_partial_update_user_profile(self):
        """Test partial update of user profile"""
        self.client.force_authenticate(user=self.user)
        
        data = {'phone': '+9876543210'}

        response = self.client.patch(self.url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['phone'] == '+9876543210'
        # Other fields should remain unchanged
        assert response.data['address'] == '123 Test Street'


@pytest.mark.django_db
class TestCurrentUserView:
    """Test current user endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('users:current-user')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='user'
        )

    def test_get_current_user_authenticated(self):
        """Test getting current user when authenticated"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'
        assert response.data['role'] == 'user'

    def test_get_current_user_unauthenticated(self):
        """Test getting current user when not authenticated"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserListView:
    """Test user list endpoint (admin only)"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('users:user-list')
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='user'
        )

    def test_get_user_list_as_admin(self):
        """Test getting user list as admin"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2  # At least admin and user

    def test_get_user_list_as_regular_user(self):
        """Test getting user list as regular user (should be forbidden)"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_list_unauthenticated(self):
        """Test getting user list when not authenticated"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
