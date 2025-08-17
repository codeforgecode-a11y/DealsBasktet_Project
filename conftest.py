"""
Global pytest configuration and fixtures for DealsBasket project
"""
import pytest
import tempfile
from django.conf import settings
from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
import os

# Set Django settings module for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings.test')

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Configure the test database
    """
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def api_client():
    """
    Return an API client for testing
    """
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """
    Return an authenticated API client
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """
    Return an authenticated admin API client
    """
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def shopkeeper_client(api_client, shopkeeper_user):
    """
    Return an authenticated shopkeeper API client
    """
    api_client.force_authenticate(user=shopkeeper_user)
    return api_client


@pytest.fixture
def delivery_client(api_client, delivery_user):
    """
    Return an authenticated delivery person API client
    """
    api_client.force_authenticate(user=delivery_user)
    return api_client


@pytest.fixture
def user():
    """
    Create a regular user for testing
    """
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role='user'
    )


@pytest.fixture
def admin_user():
    """
    Create an admin user for testing
    """
    return User.objects.create_user(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        role='admin',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def shopkeeper_user():
    """
    Create a shopkeeper user for testing
    """
    return User.objects.create_user(
        username='shopkeeper',
        email='shopkeeper@example.com',
        password='shoppass123',
        role='shopkeeper'
    )


@pytest.fixture
def delivery_user():
    """
    Create a delivery person user for testing
    """
    return User.objects.create_user(
        username='delivery',
        email='delivery@example.com',
        password='deliverypass123',
        role='delivery'
    )





@pytest.fixture
def mock_cloudinary():
    """
    Mock Cloudinary uploads for testing
    """
    with patch('cloudinary.uploader.upload') as mock_upload:
        mock_upload.return_value = {
            'public_id': 'test_image_id',
            'url': 'https://test.cloudinary.com/test_image.jpg',
            'secure_url': 'https://test.cloudinary.com/test_image.jpg'
        }
        yield mock_upload


@pytest.fixture
def temp_media_root():
    """
    Create a temporary media root for testing file uploads
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        with override_settings(MEDIA_ROOT=temp_dir):
            yield temp_dir


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests
    """
    pass





# Test data fixtures will be added in individual test files
# using factory_boy or model_bakery for more complex scenarios
