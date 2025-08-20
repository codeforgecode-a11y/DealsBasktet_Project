#!/usr/bin/env python
"""
Integration Testing Script for DealsBasket API
Tests Firebase authentication, Cloudinary integration, and database transactions
"""
import os
import sys
import django
from pathlib import Path

# Add project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set Django settings module for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings.test')

# Setup Django
django.setup()

# Run migrations for test database
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

import json
import time
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from apps.shop.models import Shop
from apps.products.models import Product, Category
from apps.orders.models import Order, OrderItem

User = get_user_model()


class IntegrationTestSuite:
    """Integration testing suite"""
    
    def __init__(self):
        self.client = APIClient()
        self.test_results = []
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@test.com',
            password='testpass123',
            role='user',
            firebase_uid='integration_uid'
        )
        
        self.shopkeeper = User.objects.create_user(
            username='integrationshopkeeper',
            email='shopkeeper@test.com',
            password='testpass123',
            role='shopkeeper',
            firebase_uid='shopkeeper_uid'
        )
        
        self.admin = User.objects.create_user(
            username='integrationadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True,
            firebase_uid='admin_uid'
        )
        
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Integration Test Shop',
            address='123 Integration Street',
            phone='+1234567890',
            status='approved',
            is_active=True
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Category for integration testing'
        )
        
        self.product = Product.objects.create(
            shop=self.shop,
            name='Integration Product',
            category=self.category,
            price=Decimal('49.99'),
            stock_quantity=100,
            is_available=True
        )
    
    def log_result(self, test_name, passed, details=None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'details': details
        }
        self.test_results.append(result)
        
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} {test_name}")
        if details and not passed:
            print(f"   Details: {details}")
    

    
    @patch('cloudinary.uploader.upload')
    def test_cloudinary_integration(self, mock_upload):
        """Test Cloudinary image upload integration"""
        print("\n☁️ TESTING CLOUDINARY INTEGRATION")
        print("-" * 35)
        
        # Mock Cloudinary upload response
        mock_upload.return_value = {
            'public_id': 'test_image_123',
            'secure_url': 'https://res.cloudinary.com/test/image/upload/test_image_123.jpg',
            'url': 'https://res.cloudinary.com/test/image/upload/test_image_123.jpg'
        }
        
        self.client.force_authenticate(user=self.shopkeeper)
        
        # Create a fake image file
        from django.core.files.uploadedfile import SimpleUploadedFile
        fake_image = SimpleUploadedFile(
            "test_image.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        # Test image upload endpoint
        response = self.client.post('/api/v1/products/upload-image/', 
                                  {'image': fake_image}, format='multipart')
        
        image_upload_working = response.status_code == 200
        self.log_result("Cloudinary Image Upload", image_upload_working,
                       f"Status: {response.status_code}")
        
        if image_upload_working:
            # Verify response contains image URL
            has_image_url = 'image_url' in response.data
            self.log_result("Image URL Returned", has_image_url,
                           f"Response keys: {list(response.data.keys()) if hasattr(response, 'data') else 'N/A'}")
    
    def test_database_transactions(self):
        """Test database transaction integrity"""
        print("\n💾 TESTING DATABASE TRANSACTIONS")
        print("-" * 35)
        
        self.client.force_authenticate(user=self.user)
        
        initial_product_stock = self.product.stock_quantity
        initial_order_count = Order.objects.count()
        
        # Test successful transaction
        order_data = {
            'shop_id': self.shop.id,
            'delivery_address': 'Transaction Test Address',
            'delivery_phone': '+1234567890',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 5
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', order_data, format='json')
        order_created = response.status_code == 201
        
        if order_created:
            # Verify both order creation and stock reduction happened
            self.product.refresh_from_db()
            new_order_count = Order.objects.count()
            
            order_count_increased = new_order_count == initial_order_count + 1
            stock_reduced = self.product.stock_quantity == initial_product_stock - 5
            
            self.log_result("Order Transaction Successful", order_created and order_count_increased and stock_reduced,
                           f"Order created: {order_created}, Count: {new_order_count}, Stock: {self.product.stock_quantity}")
        else:
            self.log_result("Order Transaction Failed", False,
                           f"Status: {response.status_code}")
    
    def test_api_performance(self):
        """Test API response times"""
        print("\n⚡ TESTING API PERFORMANCE")
        print("-" * 30)
        
        # Test product list performance
        start_time = time.time()
        response = self.client.get('/api/v1/products/')
        end_time = time.time()
        
        response_time = end_time - start_time
        product_list_fast = response_time < 1.0  # Should respond within 1 second
        self.log_result("Product List Performance", product_list_fast,
                       f"Response time: {response_time:.3f}s")
        
        # Test shop list performance
        start_time = time.time()
        response = self.client.get('/api/v1/shops/')
        end_time = time.time()
        
        response_time = end_time - start_time
        shop_list_fast = response_time < 1.0
        self.log_result("Shop List Performance", shop_list_fast,
                       f"Response time: {response_time:.3f}s")
        
        # Test authenticated endpoint performance
        self.client.force_authenticate(user=self.user)
        start_time = time.time()
        response = self.client.get('/api/v1/users/profile/')
        end_time = time.time()
        
        response_time = end_time - start_time
        profile_fast = response_time < 1.0
        self.log_result("User Profile Performance", profile_fast,
                       f"Response time: {response_time:.3f}s")
    
    def test_pagination_and_filtering(self):
        """Test pagination and filtering functionality"""
        print("\n📄 TESTING PAGINATION AND FILTERING")
        print("-" * 40)
        
        # Create multiple products for pagination testing
        for i in range(25):
            Product.objects.create(
                shop=self.shop,
                name=f'Pagination Product {i}',
                category=self.category,
                price=Decimal(f'{10 + i}.99'),
                stock_quantity=10,
                is_available=True
            )
        
        # Test pagination
        response = self.client.get('/api/v1/products/?page=1')
        pagination_working = response.status_code == 200 and 'results' in response.data
        self.log_result("Pagination Working", pagination_working,
                       f"Status: {response.status_code}")
        
        if pagination_working:
            # Check if pagination info is present
            has_pagination_info = all(key in response.data for key in ['count', 'next', 'previous', 'results'])
            self.log_result("Pagination Info Present", has_pagination_info,
                           f"Keys: {list(response.data.keys())}")
        
        # Test filtering
        response = self.client.get(f'/api/v1/products/?category={self.category.id}')
        filtering_working = response.status_code == 200
        self.log_result("Category Filtering Working", filtering_working,
                       f"Status: {response.status_code}")
        
        # Test search
        response = self.client.get('/api/v1/products/search/?q=Integration')
        search_working = response.status_code == 200
        self.log_result("Product Search Working", search_working,
                       f"Status: {response.status_code}")


def run_integration_tests():
    """Run integration tests"""
    print("🚀 Starting Integration Testing for DealsBasket")
    print("=" * 60)
    
    suite = IntegrationTestSuite()
    
    # Run test suites
    suite.test_cloudinary_integration()
    suite.test_database_transactions()
    suite.test_api_performance()
    suite.test_pagination_and_filtering()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in suite.test_results if r['passed'])
    failed = len(suite.test_results) - passed
    
    print(f"Total Tests: {len(suite.test_results)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed/len(suite.test_results)*100:.1f}%")
    
    if failed > 0:
        print(f"\n❌ Failed Tests:")
        for result in suite.test_results:
            if not result['passed']:
                print(f"  - {result['test_name']}")
                if result['details']:
                    print(f"    {result['details']}")
    
    return suite.test_results


if __name__ == '__main__':
    results = run_integration_tests()
    failed_count = sum(1 for r in results if not r['passed'])
    sys.exit(0 if failed_count == 0 else 1)
