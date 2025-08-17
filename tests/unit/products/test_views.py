"""
Tests for Product views and API endpoints
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from products.models import Category, Product
from shop.models import Shop

User = get_user_model()


@pytest.mark.django_db
class TestProductListView:
    """Test public product list endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('products:product-list')
        
        # Create shopkeeper and shop
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.approved_shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Approved Shop',
            address='123 Shop Street',
            phone='+1234567890',
            status='approved',
            is_active=True
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic items'
        )
        
        # Create products
        self.available_product = Product.objects.create(
            shop=self.approved_shop,
            name='Available Product',
            description='An available product',
            category=self.category,
            price=Decimal('99.99'),
            stock_quantity=10,
            is_available=True
        )
        
        self.unavailable_product = Product.objects.create(
            shop=self.approved_shop,
            name='Unavailable Product',
            price=Decimal('49.99'),
            stock_quantity=5,
            is_available=False
        )

    def test_get_product_list_public(self):
        """Test getting public product list"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should only return available products from approved shops
        product_names = [product['name'] for product in response.data['results']]
        assert 'Available Product' in product_names
        assert 'Unavailable Product' not in product_names

    def test_product_list_filtering(self):
        """Test product list filtering"""
        # Test category filtering
        response = self.client.get(self.url, {'category': self.category.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

        # Test shop filtering
        response = self.client.get(self.url, {'shop': self.approved_shop.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

        # Test availability filtering
        response = self.client.get(self.url, {'is_available': 'true'})
        assert response.status_code == status.HTTP_200_OK

    def test_product_list_search(self):
        """Test product list search functionality"""
        # Search by product name
        response = self.client.get(self.url, {'search': 'Available'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

        # Search by shop name
        response = self.client.get(self.url, {'search': 'Approved Shop'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1

    def test_product_list_ordering(self):
        """Test product list ordering"""
        # Test ordering by price
        response = self.client.get(self.url, {'ordering': 'price'})
        assert response.status_code == status.HTTP_200_OK

        # Test ordering by name
        response = self.client.get(self.url, {'ordering': 'name'})
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProductDetailView:
    """Test product detail endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create shopkeeper and shop
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            address='123 Shop Street',
            phone='+1234567890',
            status='approved'
        )
        
        # Create product
        self.product = Product.objects.create(
            shop=self.shop,
            name='Test Product',
            description='A test product',
            price=Decimal('99.99'),
            stock_quantity=10,
            is_available=True
        )
        
        self.url = reverse('products:product-detail', kwargs={'pk': self.product.pk})

    def test_get_product_detail(self):
        """Test getting product detail"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Product'
        assert response.data['description'] == 'A test product'
        assert response.data['price'] == '99.99'
        assert response.data['stock_quantity'] == 10

    def test_get_product_detail_not_found(self):
        """Test getting non-existent product detail"""
        url = reverse('products:product-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestShopProductListView:
    """Test shop product management endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('products:my-products')
        
        # Create shopkeeper and shop
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            address='123 Shop Street',
            phone='+1234567890',
            status='approved'
        )
        
        # Create category
        self.category = Category.objects.create(name='Electronics')
        
        # Create product
        self.product = Product.objects.create(
            shop=self.shop,
            name='My Product',
            price=Decimal('99.99'),
            stock_quantity=10
        )

    def test_get_my_products_as_shopkeeper(self):
        """Test getting my products as shopkeeper"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert response.data['results'][0]['name'] == 'My Product'

    def test_get_my_products_as_non_shopkeeper(self):
        """Test getting my products as non-shopkeeper"""
        user = User.objects.create_user(
            username='user',
            email='user@example.com',
            role='user'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_product_as_shopkeeper(self):
        """Test creating product as shopkeeper"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        data = {
            'name': 'New Product',
            'description': 'A new product',
            'category': self.category.id,
            'price': '149.99',
            'stock_quantity': 20,
            'weight': '0.5',
            'dimensions': '10x10x5 cm',
            'sku': 'NEW001',
            'discount_percentage': '10.00'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Product'
        assert response.data['price'] == '149.99'

        # Verify product was created in database
        product = Product.objects.get(name='New Product')
        assert product.shop == self.shop
        assert product.category == self.category

    def test_create_product_invalid_data(self):
        """Test creating product with invalid data"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        data = {
            'name': '',  # Empty name
            'price': 'invalid',  # Invalid price
            'stock_quantity': -1  # Negative stock
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_product_no_shop(self):
        """Test creating product when shopkeeper has no shop"""
        shopkeeper_no_shop = User.objects.create_user(
            username='no_shop',
            email='no_shop@example.com',
            role='shopkeeper'
        )
        self.client.force_authenticate(user=shopkeeper_no_shop)
        
        data = {
            'name': 'Product',
            'price': '99.99'
        }

        response = self.client.post(self.url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestShopProductDetailView:
    """Test shop product detail management endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create shopkeeper and shop
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            address='123 Shop Street',
            phone='+1234567890',
            status='approved'
        )
        
        # Create product
        self.product = Product.objects.create(
            shop=self.shop,
            name='My Product',
            price=Decimal('99.99'),
            stock_quantity=10
        )
        
        self.url = reverse('products:my-product-detail', kwargs={'pk': self.product.pk})

    def test_get_my_product_detail(self):
        """Test getting my product detail"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'My Product'

    def test_update_my_product(self):
        """Test updating my product"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        data = {
            'name': 'Updated Product',
            'price': '149.99',
            'stock_quantity': 15
        }

        response = self.client.patch(self.url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Product'
        assert response.data['price'] == '149.99'
        assert response.data['stock_quantity'] == 15

        # Verify changes in database
        self.product.refresh_from_db()
        assert self.product.name == 'Updated Product'

    def test_delete_my_product(self):
        """Test deleting my product"""
        self.client.force_authenticate(user=self.shopkeeper)
        
        response = self.client.delete(self.url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify product was deleted
        assert not Product.objects.filter(pk=self.product.pk).exists()

    def test_access_other_shopkeeper_product(self):
        """Test accessing another shopkeeper's product"""
        other_shopkeeper = User.objects.create_user(
            username='other_shopkeeper',
            email='other@example.com',
            role='shopkeeper'
        )
        self.client.force_authenticate(user=other_shopkeeper)
        
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestProductSearchView:
    """Test product search endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('products:product-search')
        
        # Create test data
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@example.com',
            role='shopkeeper'
        )
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Electronics Store',
            address='123 Shop Street',
            phone='+1234567890',
            status='approved'
        )
        
        self.category = Category.objects.create(name='Electronics')
        
        # Create products for search
        Product.objects.create(
            shop=self.shop,
            name='iPhone 13',
            description='Latest Apple smartphone',
            category=self.category,
            price=Decimal('999.99'),
            stock_quantity=5,
            is_available=True
        )
        
        Product.objects.create(
            shop=self.shop,
            name='Samsung Galaxy',
            description='Android smartphone',
            category=self.category,
            price=Decimal('799.99'),
            stock_quantity=3,
            is_available=True
        )

    def test_product_search_by_name(self):
        """Test product search by name"""
        response = self.client.get(self.url, {'q': 'iPhone'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert 'iPhone 13' in [p['name'] for p in response.data['results']]

    def test_product_search_by_description(self):
        """Test product search by description"""
        response = self.client.get(self.url, {'q': 'smartphone'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2  # Both products match

    def test_product_search_with_filters(self):
        """Test product search with additional filters"""
        response = self.client.get(self.url, {
            'q': 'phone',
            'category': self.category.id,
            'min_price': '800',
            'max_price': '1000'
        })
        
        assert response.status_code == status.HTTP_200_OK
        # Should return iPhone 13 but not Samsung Galaxy (price filter)

    def test_product_search_empty_query(self):
        """Test product search with empty query"""
        response = self.client.get(self.url, {'q': ''})
        
        assert response.status_code == status.HTTP_200_OK
        # Should return all available products

    def test_product_search_no_results(self):
        """Test product search with no matching results"""
        response = self.client.get(self.url, {'q': 'nonexistent'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestCategoryListView:
    """Test category list endpoint"""

    def setup_method(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = reverse('products:category-list')
        
        # Create categories
        Category.objects.create(name='Electronics', is_active=True)
        Category.objects.create(name='Books', is_active=True)
        Category.objects.create(name='Inactive Category', is_active=False)

    def test_get_category_list(self):
        """Test getting category list"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should only return active categories
        category_names = [cat['name'] for cat in response.data['results']]
        assert 'Electronics' in category_names
        assert 'Books' in category_names
        assert 'Inactive Category' not in category_names

    def test_category_list_ordering(self):
        """Test category list ordering (alphabetical)"""
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Should be ordered alphabetically
        category_names = [cat['name'] for cat in response.data['results']]
        assert category_names == sorted(category_names)
