#!/usr/bin/env python
"""
Advanced API Testing Script for DealsBasket Project
Tests business logic workflows, edge cases, and integration scenarios
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


class AdvancedAPITestSuite:
    """Advanced API testing with business logic validation"""
    
    def __init__(self):
        self.client = APIClient()
        self.test_results = []
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup comprehensive test data"""
        # Create users
        self.user = User.objects.create_user(
            username='customer1',
            email='customer1@test.com',
            password='testpass123',
            role='user',
            firebase_uid='customer1_uid'
        )
        
        self.shopkeeper = User.objects.create_user(
            username='shopkeeper1',
            email='shopkeeper1@test.com',
            password='testpass123',
            role='shopkeeper',
            firebase_uid='shopkeeper1_uid'
        )
        
        self.delivery_person = User.objects.create_user(
            username='delivery1',
            email='delivery1@test.com',
            password='testpass123',
            role='delivery',
            firebase_uid='delivery1_uid'
        )
        
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True,
            firebase_uid='admin1_uid'
        )
        
        # Create shop
        self.shop = Shop.objects.create(
            owner=self.shopkeeper,
            name='Electronics Store',
            description='Best electronics in town',
            address='123 Tech Street',
            phone='+1234567890',
            status='approved',
            is_active=True,
            latitude=Decimal('40.7128'),
            longitude=Decimal('-74.0060')
        )
        
        # Create categories
        self.electronics_category = Category.objects.create(
            name='Electronics',
            description='Electronic devices and accessories'
        )
        
        self.books_category = Category.objects.create(
            name='Books',
            description='Books and literature'
        )
        
        # Create products
        self.smartphone = Product.objects.create(
            shop=self.shop,
            name='Smartphone X1',
            description='Latest smartphone with advanced features',
            category=self.electronics_category,
            price=Decimal('599.99'),
            stock_quantity=50,
            is_available=True,
            discount_percentage=Decimal('10.00')
        )
        
        self.laptop = Product.objects.create(
            shop=self.shop,
            name='Gaming Laptop',
            description='High-performance gaming laptop',
            category=self.electronics_category,
            price=Decimal('1299.99'),
            stock_quantity=5,
            is_available=True
        )
        
        # Create delivery zone
        self.delivery_zone = DeliveryZone.objects.create(
            name='Downtown',
            description='Downtown delivery zone',
            delivery_fee=Decimal('5.99'),
            estimated_delivery_time=30,
            is_active=True
        )
        
        # Create delivery person profile
        self.delivery_profile = DeliveryPerson.objects.create(
            user=self.delivery_person,
            vehicle_type='motorcycle',
            vehicle_number='DL01AB1234',
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
    
    def test_complete_order_workflow(self):
        """Test complete order workflow from creation to delivery"""
        print("\n🔄 TESTING COMPLETE ORDER WORKFLOW")
        print("-" * 40)
        
        # Step 1: Customer creates order
        self.client.force_authenticate(user=self.user)
        order_data = {
            'shop_id': self.shop.id,
            'delivery_address': '456 Customer Avenue',
            'delivery_phone': '+9876543210',
            'items': [
                {
                    'product_id': self.smartphone.id,
                    'quantity': 2
                },
                {
                    'product_id': self.laptop.id,
                    'quantity': 1
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', order_data, format='json')
        order_created = response.status_code == 201
        self.log_result("Order Creation", order_created, 
                       f"Status: {response.status_code}, Data: {response.data if hasattr(response, 'data') else 'N/A'}")
        
        if not order_created:
            return False

        order_id = response.data['order']['id']
        
        # Step 2: Shopkeeper accepts order
        self.client.force_authenticate(user=self.shopkeeper)
        response = self.client.put(f'/api/v1/orders/shop/{order_id}/', 
                                 {'status': 'accepted'}, format='json')
        order_accepted = response.status_code == 200
        self.log_result("Order Acceptance by Shopkeeper", order_accepted,
                       f"Status: {response.status_code}")
        
        # Step 3: Shopkeeper marks order as packed
        response = self.client.put(f'/api/v1/orders/shop/{order_id}/', 
                                 {'status': 'packed'}, format='json')
        order_packed = response.status_code == 200
        self.log_result("Order Packed by Shopkeeper", order_packed,
                       f"Status: {response.status_code}")
        
        # Step 4: Admin assigns delivery person
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/v1/orders/{order_id}/assign-delivery/', 
                                  {'delivery_person_id': self.delivery_person.id}, format='json')
        delivery_assigned = response.status_code == 200
        self.log_result("Delivery Assignment by Admin", delivery_assigned,
                       f"Status: {response.status_code}")
        
        # Step 5: Delivery person updates status
        self.client.force_authenticate(user=self.delivery_person)
        # This endpoint might not exist, so we'll test what's available
        response = self.client.get('/api/v1/delivery/assignments/')
        assignments_retrieved = response.status_code == 200
        self.log_result("Delivery Assignments Retrieved", assignments_retrieved,
                       f"Status: {response.status_code}")
        
        return order_created and order_accepted and order_packed
    
    def test_inventory_management(self):
        """Test product inventory management"""
        print("\n📦 TESTING INVENTORY MANAGEMENT")
        print("-" * 35)
        
        # Check initial stock
        initial_stock = self.smartphone.stock_quantity
        
        # Create order that should reduce stock
        self.client.force_authenticate(user=self.user)
        order_data = {
            'shop_id': self.shop.id,
            'delivery_address': '789 Test Street',
            'delivery_phone': '+1111111111',
            'items': [
                {
                    'product_id': self.smartphone.id,
                    'quantity': 3
                }
            ]
        }
        
        response = self.client.post('/api/v1/orders/create/', order_data, format='json')
        order_created = response.status_code == 201
        
        if order_created:
            # Refresh product from database
            self.smartphone.refresh_from_db()
            stock_reduced = self.smartphone.stock_quantity == (initial_stock - 3)
            self.log_result("Stock Reduction on Order", stock_reduced,
                           f"Initial: {initial_stock}, Current: {self.smartphone.stock_quantity}")
        else:
            self.log_result("Order Creation for Stock Test", False,
                           f"Status: {response.status_code}")
    
    def test_shop_approval_workflow(self):
        """Test shop registration and approval workflow"""
        print("\n🏪 TESTING SHOP APPROVAL WORKFLOW")
        print("-" * 35)
        
        # Create new shopkeeper
        new_shopkeeper = User.objects.create_user(
            username='newshopkeeper',
            email='newshop@test.com',
            password='testpass123',
            role='shopkeeper',
            firebase_uid='newshop_uid'
        )
        
        # Register new shop
        self.client.force_authenticate(user=new_shopkeeper)
        shop_data = {
            'name': 'New Book Store',
            'description': 'Selling books and magazines',
            'address': '999 Book Lane',
            'phone': '+5555555555',
            'latitude': '40.7589',
            'longitude': '-73.9851'
        }
        
        response = self.client.post('/api/v1/shops/register/', shop_data, format='json')
        shop_registered = response.status_code == 201
        self.log_result("Shop Registration", shop_registered,
                       f"Status: {response.status_code}")
        
        if shop_registered:
            shop_id = response.data['shop']['id']
            
            # Admin approves shop (fix: use PATCH method)
            self.client.force_authenticate(user=self.admin)
            response = self.client.patch(f'/api/v1/shops/{shop_id}/status/',
                                       {'status': 'approved'}, format='json')
            shop_approved = response.status_code == 200
            self.log_result("Shop Approval by Admin", shop_approved,
                           f"Status: {response.status_code}")


def run_advanced_tests():
    """Run advanced API tests"""
    print("🚀 Starting Advanced API Testing for DealsBasket")
    print("=" * 60)
    
    suite = AdvancedAPITestSuite()
    
    # Run test suites
    suite.test_complete_order_workflow()
    suite.test_inventory_management()
    suite.test_shop_approval_workflow()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 ADVANCED API TEST SUMMARY")
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
    results = run_advanced_tests()
    failed_count = sum(1 for r in results if not r['passed'])
    sys.exit(0 if failed_count == 0 else 1)
