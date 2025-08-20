from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator

User = get_user_model()


class Shop(models.Model):
    """
    Shop model for shopkeeper businesses
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
        ('rejected', 'Rejected'),
    ]

    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shop',
        limit_choices_to={'role': 'shopkeeper'},
        help_text='Shop owner (must be a shopkeeper)'
    )
    name = models.CharField(
        max_length=200,
        help_text='Shop name'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Shop description'
    )
    address = models.TextField(
        help_text='Shop address'
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text='Shop contact phone number'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text='Shop contact email'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Shop approval status'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the shop is currently active'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Shop latitude for location services'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        help_text='Shop longitude for location services'
    )
    opening_time = models.TimeField(
        blank=True,
        null=True,
        help_text='Shop opening time'
    )
    closing_time = models.TimeField(
        blank=True,
        null=True,
        help_text='Shop closing time'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shops'
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.owner.username}"

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def can_accept_orders(self):
        return self.is_active and self.is_approved
