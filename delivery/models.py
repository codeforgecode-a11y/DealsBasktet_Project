from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class DeliveryPerson(models.Model):
    """
    Extended profile for delivery persons
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='delivery_profile',
        limit_choices_to={'role': 'delivery'},
        help_text='User account for delivery person'
    )
    vehicle_type = models.CharField(
        max_length=50,
        choices=[
            ('bicycle', 'Bicycle'),
            ('motorcycle', 'Motorcycle'),
            ('car', 'Car'),
            ('van', 'Van'),
        ],
        help_text='Type of delivery vehicle'
    )
    vehicle_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Vehicle registration number'
    )
    license_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Driving license number'
    )
    is_available = models.BooleanField(
        default=True,
        help_text='Whether delivery person is available for assignments'
    )
    current_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Current latitude for location tracking'
    )
    current_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Current longitude for location tracking'
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Average delivery rating'
    )
    total_deliveries = models.PositiveIntegerField(
        default=0,
        help_text='Total number of completed deliveries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_persons'
        verbose_name = 'Delivery Person'
        verbose_name_plural = 'Delivery Persons'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.vehicle_type}"

    @property
    def can_accept_orders(self):
        """Check if delivery person can accept new orders"""
        return self.is_available and self.user.is_active


class DeliveryZone(models.Model):
    """
    Delivery zones for area-based delivery management
    """
    name = models.CharField(
        max_length=100,
        help_text='Zone name'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Zone description'
    )
    delivery_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Standard delivery fee for this zone'
    )
    estimated_delivery_time = models.PositiveIntegerField(
        help_text='Estimated delivery time in minutes'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the zone is active for deliveries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_zones'
        verbose_name = 'Delivery Zone'
        verbose_name_plural = 'Delivery Zones'
        ordering = ['name']

    def __str__(self):
        return self.name


class DeliveryAssignment(models.Model):
    """
    Track delivery assignments and history
    """
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    delivery_person = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='delivery_assignments',
        limit_choices_to={'role': 'delivery'},
        help_text='Assigned delivery person'
    )
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='delivery_assignment',
        help_text='Order being delivered'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned',
        help_text='Delivery assignment status'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    picked_up_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Delivery notes or issues'
    )

    class Meta:
        db_table = 'delivery_assignments'
        verbose_name = 'Delivery Assignment'
        verbose_name_plural = 'Delivery Assignments'
        ordering = ['-assigned_at']

    def __str__(self):
        return f"Assignment {self.id} - {self.delivery_person.username} - Order {self.order.order_id}"
