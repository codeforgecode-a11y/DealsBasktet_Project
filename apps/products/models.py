from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField
from apps.shop.models import Shop


class Category(models.Model):
    """
    Product category model
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Category name'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Category description'
    )
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        help_text='Category image'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the category is active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Product model for shop inventory
    """
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='products',
        help_text='Shop that owns this product'
    )
    name = models.CharField(
        max_length=200,
        help_text='Product name'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Product description'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text='Product category'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Product price'
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text='Available stock quantity'
    )
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        help_text='Product image'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether the product is available for purchase'
    )
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.01)],
        help_text='Product weight in kg'
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Product dimensions (L x W x H)'
    )
    sku = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Stock Keeping Unit'
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Discount percentage (0-100)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        unique_together = ['shop', 'sku']

    def __str__(self):
        return f"{self.name} - {self.shop.name}"

    @property
    def discounted_price(self):
        """Calculate discounted price"""
        if self.discount_percentage > 0:
            discount_amount = (self.price * self.discount_percentage) / 100
            return self.price - discount_amount
        return self.price

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0

    @property
    def can_be_ordered(self):
        """Check if product can be ordered"""
        return (self.is_available and
                self.is_in_stock and
                self.shop.can_accept_orders)
