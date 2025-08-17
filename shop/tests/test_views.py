"""
Tests for Shop views and API endpoints
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from shop.models import Shop

User = get_user_model()


@pytest.mark.django_db
class TestShopRegistrationView:
    """Test shop registration endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('shop:shop-register')
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

    def test_shop_registration_success(self):
        """Test successful shop registration"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        data = {
            'name': 'Test Shop',
            'description': 'A test shop',
            'address': '123 Shop Street',
            'phone': '+1234567890',
            'email': 'shop@example.com',
            'latitude': '40.7128',
            'longitude': '-74.0060',
            'opening_time': '09:00',
            'closing_time': '18:00'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'message' in response.data
        assert 'shop' in response.data
        assert response.data['shop']['name'] == 'Test Shop'
        assert response.data['shop']['status'] == 'pending'

        # Verify shop was created in database
        shop = Shop.objects.get(name='Test Shop')
        assert shop.owner == self.shopkeeper
        assert shop.status == 'pending'

    def test_shop_registration_as_non_shopkeeper(self):
        """Test shop registration as non-shopkeeper user"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'name': 'Test Shop',
            'address': '123 Shop Street',
            'phone': '+1234567890'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_shop_registration_unauthenticated(self):
        """Test shop registration when not authenticated"""
        data = {
            'name': 'Test Shop',
            'address': '123 Shop Street',
            'phone': '+1234567890'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_shop_registration_duplicate_shop(self):
        """Test shop registration when shopkeeper already has a shop"""
        # Create existing shop
        Shop.objects.create(
            owner=self.shopkeeper,
            name='Existing Shop',
            address='123 Existing Street',
            phone='+1111111111'
        )

        self.client.force_authenticate(user=self.shopkeeper)
        
        data = {
            'name': 'New Shop',
            'address': '456 New Street',
            'phone': '+2222222222'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already have a registered shop' in response.data['error']

    def test_shop_registration_invalid_data(self):
        """Test shop registration with invalid data"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        data = {
            'name': '',  # Empty name
            'address': '',  # Empty address
            'phone': 'invalid'  # Invalid phone
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMyShopView:
    """Test my shop endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('shop:my-shop')
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='My Shop',
            address='123 Shop Street',
            phone='+1234567890',
            status='approved'
        )

    def test_get_my_shop(self):
        """Test getting my shop details"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'My Shop'
        assert response.data['status'] == 'approved'

    def test_get_my_shop_no_shop(self):
        """Test getting my shop when no shop exists"""
        shopkeeper_no_shop = User.objects.create_user(
            username='no_shop',
            email='no_shop@example.com',
            role='shopkeeper'
        )
        self.client.force_authenticate(user=shopkeeper_no_shop)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_my_shop(self):
        """Test updating my shop"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        data = {
            'name': 'Updated Shop Name',
            'description': 'Updated description',
            'phone': '+9876543210'
        }

        response = self.client.patch(self.url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Shop Name'
        assert response.data['description'] == 'Updated description'
        assert response.data['phone'] == '+9876543210'

        # Verify changes in database
        self.shop.refresh_from_db()
        assert self.shop.name == 'Updated Shop Name'


@pytest.mark.django_db
class TestShopListView:
    """Test public shop list endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('shop:shop-list')
        
        # Create shopkeepers
        self.shopkeeper1 = User.objects.create_user(
            username='shopkeeper1',
            email='shopkeeper1@example.com',
            role='shopkeeper'
        )
        self.shopkeeper2 = User.objects.create_user(
            username='shopkeeper2',
            email='shopkeeper2@example.com',
            role='shopkeeper'
        )
        
        # Create shops with different statuses
        self.approved_shop = Shop.objects.create(
            owner=self.shopkeeper1,
            name='Approved Shop',
            address='123 Approved Street',
            phone='+1111111111',
            status='approved',
            is_active=True
        )
        self.pending_shop = Shop.objects.create(
            owner=self.shopkeeper2,
            name='Pending Shop',
            address='456 Pending Street',
            phone='+2222222222',
            status='pending'
        )

    def test_get_shop_list_public(self):
        """Test getting public shop list (approved shops only)"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should only return approved and active shops
        shop_names = [shop['name'] for shop in response.data['results']]
        assert 'Approved Shop' in shop_names
        assert 'Pending Shop' not in shop_names

    def test_shop_list_filtering(self):
        """Test shop list filtering"""
        # Test status filtering
        response = self.client.get(self.url, {'status': 'approved'})
        assert response.status_code == status.HTTP_200_OK
        
        # Test search
        response = self.client.get(self.url, {'search': 'Approved'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1


@pytest.mark.django_db
class TestShopDetailView:
    """Test shop detail endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            address='123 Shop Street',
            phone='+1234567890'
        )
        self.url = reverse('shop:shop-detail', kwargs={'pk': self.shop.pk})

    def test_get_shop_detail_as_owner(self):
        """Test getting shop detail as owner"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Shop'

    def test_get_shop_detail_as_admin(self):
        """Test getting shop detail as admin"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Shop'

    def test_get_shop_detail_unauthorized(self):
        """Test getting shop detail as unauthorized user"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            role='user'
        )
        self.client.force_authenticate(user=other_user)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_shop_as_admin(self):
        """Test updating shop status as admin"""
        self.client.force_authenticate(user=self.admin)
        
        data = {'status': 'approved'}
        response = self.client.patch(self.url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'approved'

        # Verify change in database
        self.shop.refresh_from_db()
        assert self.shop.status == 'approved'
