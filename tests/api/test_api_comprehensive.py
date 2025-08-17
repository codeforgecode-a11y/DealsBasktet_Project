#!/usr/bin/env python
"""
Comprehensive API Testing Script for DealsBasket Project
Tests all major API endpoints, authentication, authorization, and business logic
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
import uuid
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from shop.models import Shop
from products.models import Product, Category
from orders.models import Order, OrderItem
from delivery.models import DeliveryPerson, DeliveryZone, DeliveryAssignment
from adminpanel.models import SystemSettings, AdminAction, Notification

User = get_user_model()


class APITestingFramework:
    """Framework for comprehensive API testing"""
    
    def __init__(self):
        self.client = APIClient()
        self.test_results = []
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup test users and basic data"""
        # Create test users for each role
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123',
            role='user',
            firebase_uid='test_user_uid'
        )
        
        self.shopkeeper = User.objects.create_user(
            username='testshopkeeper',
            email='shopkeeper@test.com',
            password='testpass123',
            role='shopkeeper',
            firebase_uid='test_shopkeeper_uid'
        )
        
        self.delivery_person = User.objects.create_user(
            username='testdelivery',
            email='delivery@test.com',
            password='testpass123',
            role='delivery',
            firebase_uid='test_delivery_uid'
        )
        
        self.admin = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True,
            firebase_uid='test_admin_uid'
        )
        
        # Create test shop
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            description='A test shop',
            address='123 Test Street',
            phone='+1234567890',
            status='approved',
            is_active=True
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic items'
        )
        
        # Create test product
        self.product = Product.objects.create(
            shop=self.shop,
            name='Test Product',
            description='A test product',
            category=self.category,
            price=Decimal('99.99'),
            stock_quantity=10,
            is_available=True
        )
    
    def log_test_result(self, test_name, endpoint, method, status_code, expected_status, passed, error_msg=None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'expected_status': expected_status,
            'passed': passed,
            'error_msg': error_msg
        }
        self.test_results.append(result)
        
        status_icon = "✅" if passed else "❌"
        print(f"{status_icon} {test_name}: {method} {endpoint} -> {status_code} (expected {expected_status})")
        if error_msg:
            print(f"   Error: {error_msg}")
    
    def authenticate_user(self, user):
        """Authenticate user for API calls"""
        self.client.force_authenticate(user=user)
    
    def test_endpoint(self, test_name, method, endpoint, data=None, expected_status=200, user=None):
        """Generic endpoint testing method"""
        if user:
            self.authenticate_user(user)
        else:
            self.client.force_authenticate(user=None)
        
        try:
            if method.upper() == 'GET':
                response = self.client.get(endpoint)
            elif method.upper() == 'POST':
                response = self.client.post(endpoint, data, format='json')
            elif method.upper() == 'PUT':
                response = self.client.put(endpoint, data, format='json')
            elif method.upper() == 'PATCH':
                response = self.client.patch(endpoint, data, format='json')
            elif method.upper() == 'DELETE':
                response = self.client.delete(endpoint)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            passed = response.status_code == expected_status
            error_msg = None if passed else f"Response: {response.data if hasattr(response, 'data') else response.content}"
            
            self.log_test_result(test_name, endpoint, method, response.status_code, expected_status, passed, error_msg)
            return response
            
        except Exception as e:
            self.log_test_result(test_name, endpoint, method, 'ERROR', expected_status, False, str(e))
            return None


def run_comprehensive_api_tests():
    """Run comprehensive API tests"""
    print("🚀 Starting Comprehensive API Testing for DealsBasket")
    print("=" * 60)

    framework = APITestingFramework()

    # Test 1: API Endpoint Testing
    print("\n📋 1. API ENDPOINT TESTING")
    print("-" * 30)

    # Users endpoints
    framework.test_endpoint("User Profile (Authenticated)", "GET", "/api/v1/users/profile/", user=framework.user)
    framework.test_endpoint("User Profile (Unauthenticated)", "GET", "/api/v1/users/profile/", expected_status=401)

    # Shop endpoints
    framework.test_endpoint("Shop List (Public)", "GET", "/api/v1/shops/")
    framework.test_endpoint("Shop Registration", "POST", "/api/v1/shops/register/",
                          data={'name': 'New Shop', 'address': '456 New Street', 'phone': '+9876543210'},
                          user=framework.shopkeeper, expected_status=400)  # Already has shop

    # Product endpoints
    framework.test_endpoint("Product List (Public)", "GET", "/api/v1/products/")
    framework.test_endpoint("Product Detail", "GET", f"/api/v1/products/{framework.product.id}/")
    framework.test_endpoint("Product Search", "GET", "/api/v1/products/search/?q=test")

    # Categories
    framework.test_endpoint("Category List", "GET", "/api/v1/products/categories/")

    # Test 2: Authentication & Authorization Testing
    print("\n🔐 2. AUTHENTICATION & AUTHORIZATION TESTING")
    print("-" * 45)

    # Test role-based access
    framework.test_endpoint("Admin Dashboard (Admin)", "GET", "/api/v1/admin/dashboard/", user=framework.admin)
    framework.test_endpoint("Admin Dashboard (User)", "GET", "/api/v1/admin/dashboard/", user=framework.user, expected_status=403)
    framework.test_endpoint("My Shop (Shopkeeper)", "GET", "/api/v1/shops/my-shop/", user=framework.shopkeeper)
    framework.test_endpoint("My Shop (User)", "GET", "/api/v1/shops/my-shop/", user=framework.user, expected_status=403)

    # Test 3: Business Logic Testing
    print("\n💼 3. BUSINESS LOGIC TESTING")
    print("-" * 30)

    # Test order creation (fix: use shop_id instead of shop)
    order_data = {
        'shop_id': framework.shop.id,
        'delivery_address': '789 Customer Street',
        'delivery_phone': '+1111111111',
        'items': [
            {
                'product_id': framework.product.id,
                'quantity': 2
            }
        ]
    }
    framework.test_endpoint("Create Order", "POST", "/api/v1/orders/create/",
                          data=order_data, user=framework.user, expected_status=201)

    # Test 4: Error Handling & Edge Cases
    print("\n⚠️ 4. ERROR HANDLING & EDGE CASES")
    print("-" * 35)

    # Test invalid data
    framework.test_endpoint("Invalid Product ID", "GET", "/api/v1/products/99999/", expected_status=404)
    # Note: Shop detail requires authentication, so test with authenticated user
    framework.test_endpoint("Invalid Shop ID", "GET", "/api/v1/shops/99999/", user=framework.admin, expected_status=404)

    # Test malformed data
    invalid_order_data = {
        'shop': 'invalid',
        'items': []
    }
    framework.test_endpoint("Invalid Order Data", "POST", "/api/v1/orders/create/",
                          data=invalid_order_data, user=framework.user, expected_status=400)

    print(f"\n📊 Overall Testing Results:")
    passed_tests = sum(1 for result in framework.test_results if result['passed'])
    total_tests = len(framework.test_results)
    print(f"Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")

    return framework.test_results


if __name__ == '__main__':
    results = run_comprehensive_api_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE API TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['passed'])
    failed = len(results) - passed
    
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {passed/len(results)*100:.1f}%")
    
    if failed > 0:
        print(f"\n❌ Failed Tests:")
        for result in results:
            if not result['passed']:
                print(f"  - {result['test_name']}: {result['method']} {result['endpoint']}")
                if result['error_msg']:
                    print(f"    Error: {result['error_msg'][:100]}...")
    
    sys.exit(0 if failed == 0 else 1)
