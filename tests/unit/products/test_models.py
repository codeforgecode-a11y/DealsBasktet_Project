"""
Tests for Product models
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from products.models import Category, Product
from shop.models import Shop

User = get_user_model()


@pytest.mark.django_db
class TestCategoryModel:
    """Test Category model functionality"""

    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='Electronics',
            description='Electronic items and gadgets'
        )
        
        assert category.name == 'Electronics'
        assert category.description == 'Electronic items and gadgets'
        assert category.is_active is True  # Default value

    def test_category_str_representation(self):
        """Test category string representation"""
        category = Category.objects.create(name='Books')
        assert str(category) == 'Books'

    def test_category_name_unique(self):
        """Test category name uniqueness"""
        Category.objects.create(name='Electronics')
        
        with pytest.raises(IntegrityError):
            Category.objects.create(name='Electronics')

    def test_category_ordering(self):
        """Test category default ordering"""
        Category.objects.create(name='Zebra')
        Category.objects.create(name='Apple')
        Category.objects.create(name='Books')
        
        categories = list(Category.objects.all())
        names = [cat.name for cat in categories]
        assert names == ['Apple', 'Books', 'Zebra']  # Alphabetical order

    def test_category_optional_fields(self):
        """Test category optional fields"""
        category = Category.objects.create(name='Minimal Category')
        
        assert category.description is None
        assert category.image is None

    def test_category_timestamps(self):
        """Test category timestamp fields"""
        category = Category.objects.create(name='Test Category')
        
        assert category.created_at is not None
        assert category.updated_at is not None
        assert category.created_at <= category.updated_at


@pytest.mark.django_db
class TestProductModel:
    """Test Product model functionality"""

    def setup_method(self):
        """Set up test data"""
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
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic items'
        )

    def test_create_product(self):
        """Test creating a product"""
        product = Product.objects.create(
            shop=self.shop,
            name='Smartphone',
            description='Latest smartphone',
            category=self.category,
            price=Decimal('599.99'),
            stock_quantity=10,
            weight=Decimal('0.2'),
            dimensions='15x7x0.8 cm',
            sku='PHONE001',
            discount_percentage=Decimal('10.00')
        )
        
        assert product.name == 'Smartphone'
        assert product.shop == self.shop
        assert product.category == self.category
        assert product.price == Decimal('599.99')
        assert product.stock_quantity == 10
        assert product.is_available is True  # Default value

    def test_product_str_representation(self):
        """Test product string representation"""
        product = Product.objects.create(
            shop=self.shop,
            name='Test Product',
            price=Decimal('99.99')
        )
        
        expected = 'Test Product - Test Shop'
        assert str(product) == expected

    def test_product_discounted_price_property(self):
        """Test product discounted price calculation"""
        # Product with discount
        product_with_discount = Product.objects.create(
            shop=self.shop,
            name='Discounted Product',
            price=Decimal('100.00'),
            discount_percentage=Decimal('20.00')
        )
        
        assert product_with_discount.discounted_price == Decimal('80.00')
        
        # Product without discount
        product_no_discount = Product.objects.create(
            shop=self.shop,
            name='Regular Product',
            price=Decimal('100.00'),
            discount_percentage=Decimal('0.00')
        )
        
        assert product_no_discount.discounted_price == Decimal('100.00')

    def test_product_is_in_stock_property(self):
        """Test product stock availability property"""
        # Product in stock
        product_in_stock = Product.objects.create(
            shop=self.shop,
            name='In Stock Product',
            price=Decimal('50.00'),
            stock_quantity=5
        )
        
        assert product_in_stock.is_in_stock is True
        
        # Product out of stock
        product_out_of_stock = Product.objects.create(
            shop=self.shop,
            name='Out of Stock Product',
            price=Decimal('50.00'),
            stock_quantity=0
        )
        
        assert product_out_of_stock.is_in_stock is False

    def test_product_can_be_ordered_property(self):
        """Test product orderability property"""
        # Product that can be ordered
        orderable_product = Product.objects.create(
            shop=self.shop,
            name='Orderable Product',
            price=Decimal('50.00'),
            stock_quantity=5,
            is_available=True
        )
        
        assert orderable_product.can_be_ordered is True
        
        # Product that cannot be ordered (not available)
        unavailable_product = Product.objects.create(
            shop=self.shop,
            name='Unavailable Product',
            price=Decimal('50.00'),
            stock_quantity=5,
            is_available=False
        )
        
        assert unavailable_product.can_be_ordered is False
        
        # Product that cannot be ordered (out of stock)
        out_of_stock_product = Product.objects.create(
            shop=self.shop,
            name='Out of Stock Product',
            price=Decimal('50.00'),
            stock_quantity=0,
            is_available=True
        )
        
        assert out_of_stock_product.can_be_ordered is False

    def test_product_can_be_ordered_shop_status(self):
        """Test product orderability based on shop status"""
        # Create shop with different status
        pending_shop = Shop.objects.create(
            owner=User.objects.create_user(
                username='pending_shopkeeper',
                email='pending@example.com',
                role='shopkeeper'
            ),
            name='Pending Shop',
            address='456 Pending Street',
            phone='+9876543210',
            status='pending'
        )
        
        product = Product.objects.create(
            shop=pending_shop,
            name='Product from Pending Shop',
            price=Decimal('50.00'),
            stock_quantity=5,
            is_available=True
        )
        
        assert product.can_be_ordered is False  # Shop not approved

    def test_product_sku_unique_per_shop(self):
        """Test SKU uniqueness constraint per shop"""
        # Create product with SKU
        Product.objects.create(
            shop=self.shop,
            name='Product 1',
            price=Decimal('50.00'),
            sku='UNIQUE001'
        )
        
        # Try to create another product with same SKU in same shop
        with pytest.raises(IntegrityError):
            Product.objects.create(
                shop=self.shop,
                name='Product 2',
                price=Decimal('60.00'),
                sku='UNIQUE001'
            )

    def test_product_sku_can_be_same_across_shops(self):
        """Test that SKU can be same across different shops"""
        # Create another shop
        another_shopkeeper = User.objects.create_user(
            username='another_shopkeeper',
            email='another@example.com',
            role='shopkeeper'
        )
        another_shop = Shop.objects.create(
            owner=another_shopkeeper,
            name='Another Shop',
            address='789 Another Street',
            phone='+1111111111',
            status='approved'
        )
        
        # Create products with same SKU in different shops
        Product.objects.create(
            shop=self.shop,
            name='Product 1',
            price=Decimal('50.00'),
            sku='SAME001'
        )
        
        Product.objects.create(
            shop=another_shop,
            name='Product 2',
            price=Decimal('60.00'),
            sku='SAME001'
        )
        
        # Should not raise any error

    def test_product_price_validation(self):
        """Test product price validation"""
        # Valid price
        product = Product.objects.create(
            shop=self.shop,
            name='Valid Price Product',
            price=Decimal('0.01')  # Minimum valid price
        )
        assert product.price == Decimal('0.01')

    def test_product_discount_percentage_validation(self):
        """Test discount percentage validation"""
        # Valid discount percentages
        valid_discounts = [Decimal('0'), Decimal('50.5'), Decimal('100')]
        
        for discount in valid_discounts:
            product = Product.objects.create(
                shop=self.shop,
                name=f'Product {discount}',
                price=Decimal('100.00'),
                discount_percentage=discount
            )
            assert product.discount_percentage == discount

    def test_product_optional_fields(self):
        """Test product optional fields"""
        product = Product.objects.create(
            shop=self.shop,
            name='Minimal Product',
            price=Decimal('50.00')
        )
        
        assert product.description is None
        assert product.category is None
        assert product.image is None
        assert product.weight is None
        assert product.dimensions is None
        assert product.sku is None

    def test_product_ordering(self):
        """Test product default ordering"""
        # Create products with different creation times
        product1 = Product.objects.create(
            shop=self.shop,
            name='First Product',
            price=Decimal('50.00')
        )
        
        product2 = Product.objects.create(
            shop=self.shop,
            name='Second Product',
            price=Decimal('60.00')
        )
        
        # Should be ordered by -created_at (newest first)
        products = list(Product.objects.all())
        assert products[0] == product2  # Newest first
        assert products[1] == product1

    def test_product_timestamps(self):
        """Test product timestamp fields"""
        product = Product.objects.create(
            shop=self.shop,
            name='Test Product',
            price=Decimal('50.00')
        )
        
        assert product.created_at is not None
        assert product.updated_at is not None
        assert product.created_at <= product.updated_at
