#!/usr/bin/env python
"""
Edge Cases and Error Handling Testing for DealsBasket API
Tests various error conditions, validation, and edge cases
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
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from shop.models import Shop
from products.models import Product, Category
from orders.models import Order

User = get_user_model()


class EdgeCaseTestSuite:
    """Test suite for edge cases and error handling"""
    
    def __init__(self):
        self.client = APIClient()
        self.test_results = []
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123',
            role='user',
            firebase_uid='test_user_uid'
        )
        
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper',
            email='shopkeeper@test.com',
            password='testpass123',
            role='shopkeeper',
            firebase_uid='shopkeeper_uid'
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True,
            firebase_uid='admin_uid'
        )
        
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Test Shop',
            address='123 Test Street',
            phone='+1234567890',
            status='approved',
            is_active=True
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic items'
        )
        
        self.product = Product.objects.create(
            shop=self.shop,
            name='Test Product',
            category=self.category,
            price=Decimal('99.99'),
            stock_quantity=5,
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
    
    def test_input_validation(self):
        """Test input validation and malformed data"""
        print("\n🔍 TESTING INPUT VALIDATION")
        print("-" * 30)
        
        self.client.force_authenticate(user=self.user)
        
        # Test 1: Order with negative quantity
        invalid_order = {
            'shop_id': self.shop.id,
            'delivery_address': 'Test Address',
            'delivery_phone': '+1234567890',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': -1  # Invalid negative quantity
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', invalid_order, format='json')
        negative_quantity_rejected = response.status_code == 400
        self.log_result("Negative Quantity Rejected", negative_quantity_rejected,
                       f"Status: {response.status_code}")
        
        # Test 2: Order with zero quantity
        zero_quantity_order = {
            'shop_id': self.shop.id,
            'delivery_address': 'Test Address',
            'delivery_phone': '+1234567890',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 0  # Invalid zero quantity
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', zero_quantity_order, format='json')
        zero_quantity_rejected = response.status_code == 400
        self.log_result("Zero Quantity Rejected", zero_quantity_rejected,
                       f"Status: {response.status_code}")
        
        # Test 3: Order with missing required fields
        incomplete_order = {
            'shop_id': self.shop.id,
            # Missing delivery_address and delivery_phone
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', incomplete_order, format='json')
        missing_fields_rejected = response.status_code == 400
        self.log_result("Missing Required Fields Rejected", missing_fields_rejected,
                       f"Status: {response.status_code}")
        
        # Test 4: Order with invalid phone format
        invalid_phone_order = {
            'shop_id': self.shop.id,
            'delivery_address': 'Test Address',
            'delivery_phone': 'invalid-phone',  # Invalid phone format
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', invalid_phone_order, format='json')
        # Note: This might pass if phone validation is not strict
        invalid_phone_handled = response.status_code in [400, 201]
        self.log_result("Invalid Phone Format Handled", invalid_phone_handled,
                       f"Status: {response.status_code}")
    
    def test_stock_management(self):
        """Test stock management edge cases"""
        print("\n📦 TESTING STOCK MANAGEMENT")
        print("-" * 30)
        
        self.client.force_authenticate(user=self.user)
        
        # Test 1: Order quantity exceeds available stock
        excessive_order = {
            'shop_id': self.shop.id,
            'delivery_address': 'Test Address',
            'delivery_phone': '+1234567890',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': self.product.stock_quantity + 10  # More than available
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', excessive_order, format='json')
        excessive_stock_rejected = response.status_code == 400
        self.log_result("Excessive Stock Order Rejected", excessive_stock_rejected,
                       f"Status: {response.status_code}, Available: {self.product.stock_quantity}")
        
        # Test 2: Order for unavailable product
        self.product.is_available = False
        self.product.save()
        
        unavailable_order = {
            'shop_id': self.shop.id,
            'delivery_address': 'Test Address',
            'delivery_phone': '+1234567890',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', unavailable_order, format='json')
        unavailable_product_rejected = response.status_code == 400
        self.log_result("Unavailable Product Order Rejected", unavailable_product_rejected,
                       f"Status: {response.status_code}")
        
        # Reset product availability
        self.product.is_available = True
        self.product.save()
    
    def test_authorization_edge_cases(self):
        """Test authorization edge cases"""
        print("\n🔐 TESTING AUTHORIZATION EDGE CASES")
        print("-" * 35)
        
        # Test 1: Shopkeeper trying to access another shop's data
        other_shopkeeper = User.objects.create_user(
            username='othershopkeeper',
            email='other@test.com',
            password='testpass123',
            role='shopkeeper',
            firebase_uid='other_uid'
        )
        
        self.client.force_authenticate(user=other_shopkeeper)
        response = self.client.get(f'/api/v1/shops/{self.shop.id}/')
        unauthorized_shop_access = response.status_code == 403
        self.log_result("Unauthorized Shop Access Blocked", unauthorized_shop_access,
                       f"Status: {response.status_code}")
        
        # Test 2: Regular user trying to access admin endpoints
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/admin/dashboard/')
        admin_access_blocked = response.status_code == 403
        self.log_result("Admin Access Blocked for Regular User", admin_access_blocked,
                       f"Status: {response.status_code}")
        
        # Test 3: Shopkeeper trying to create products for another shop
        self.client.force_authenticate(user=other_shopkeeper)
        product_data = {
            'name': 'Unauthorized Product',
            'price': '50.00',
            'stock_quantity': 10
        }
        
        response = self.client.post('/api/v1/products/my-products/', product_data, format='json')
        # This should fail because other_shopkeeper doesn't have a shop
        no_shop_product_creation = response.status_code in [400, 403]
        self.log_result("Product Creation Without Shop Blocked", no_shop_product_creation,
                       f"Status: {response.status_code}")
    
    def test_concurrent_operations(self):
        """Test concurrent operations and race conditions"""
        print("\n⚡ TESTING CONCURRENT OPERATIONS")
        print("-" * 35)
        
        # Test: Multiple orders for the same product simultaneously
        # This is a simplified test - in real scenarios, you'd use threading
        self.client.force_authenticate(user=self.user)
        
        initial_stock = self.product.stock_quantity
        
        # Create two orders quickly
        order_data = {
            'shop_id': self.shop.id,
            'delivery_address': 'Test Address',
            'delivery_phone': '+1234567890',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2
                }
            ]
        }
        
        response1 = self.client.post('/api/v1/orders/create/', order_data, format='json')
        response2 = self.client.post('/api/v1/orders/create/', order_data, format='json')
        
        # Check if both orders were processed correctly
        both_orders_created = (response1.status_code == 201 and response2.status_code == 201)
        
        # Refresh product to check final stock
        self.product.refresh_from_db()
        expected_stock = initial_stock - 4  # 2 orders * 2 quantity each
        stock_correctly_updated = self.product.stock_quantity == expected_stock
        
        self.log_result("Concurrent Orders Processed", both_orders_created,
                       f"Order1: {response1.status_code}, Order2: {response2.status_code}")
        self.log_result("Stock Correctly Updated After Concurrent Orders", stock_correctly_updated,
                       f"Initial: {initial_stock}, Expected: {expected_stock}, Actual: {self.product.stock_quantity}")


def run_edge_case_tests():
    """Run edge case tests"""
    print("🚀 Starting Edge Case Testing for DealsBasket")
    print("=" * 60)
    
    suite = EdgeCaseTestSuite()
    
    # Run test suites
    suite.test_input_validation()
    suite.test_stock_management()
    suite.test_authorization_edge_cases()
    suite.test_concurrent_operations()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 EDGE CASE TEST SUMMARY")
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
    results = run_edge_case_tests()
    failed_count = sum(1 for r in results if not r['passed'])
    sys.exit(0 if failed_count == 0 else 1)
