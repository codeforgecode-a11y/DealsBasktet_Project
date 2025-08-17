from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from shop.models import Shop
from products.models import Product
import uuid

User = get_user_model()


class Order(models.Model):
    """
    Order model for customer purchases
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('packed', 'Packed'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text='Unique order identifier'
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        limit_choices_to={'role': 'user'},
        help_text='Customer who placed the order'
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='orders',
        help_text='Shop fulfilling the order'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Order status'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        help_text='Payment status'
    )
    delivery_person = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_orders',
        limit_choices_to={'role': 'delivery'},
        help_text='Assigned delivery person'
    )
    delivery_address = models.TextField(
        help_text='Delivery address'
    )
    delivery_phone = models.CharField(
        max_length=17,
        help_text='Delivery contact phone'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Order notes or special instructions'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Total order amount'
    )
    delivery_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Delivery fee'
    )
    estimated_delivery_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Estimated delivery time'
    )
    actual_delivery_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Actual delivery time'
    )
    otp = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        help_text='OTP for delivery verification'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.username}"

    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'accepted']

    @property
    def is_delivered(self):
        """Check if order is delivered"""
        return self.status == 'delivered'

    @property
    def total_items(self):
        """Get total number of items in order"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0


class OrderItem(models.Model):
    """
    Order item model for individual products in an order
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Order this item belongs to'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='order_items',
        help_text='Product being ordered'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Quantity of the product'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Unit price at the time of order'
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Total price for this item (quantity * unit_price)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        unique_together = ['order', 'product']

    def __str__(self):
        return f"{self.product.name} x {self.quantity} - Order {self.order.order_id}"

    def save(self, *args, **kwargs):
        """Calculate total price before saving"""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
