from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access control
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('shopkeeper', 'Shopkeeper'),
        ('delivery', 'Delivery Person'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text='User role for access control'
    )
    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text='User phone number'
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text='User address'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether the email is verified'
    )
    email_verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Token for email verification'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_user(self):
        return self.role == 'user'

    @property
    def is_shopkeeper(self):
        return self.role == 'shopkeeper'

    @property
    def is_delivery_person(self):
        return self.role == 'delivery'

    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
