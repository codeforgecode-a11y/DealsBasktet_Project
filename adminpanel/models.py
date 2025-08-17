from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SystemSettings(models.Model):
    """
    System-wide settings and configurations
    """
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text='Setting key'
    )
    value = models.TextField(
        help_text='Setting value'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Setting description'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the setting is active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_settings'
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"


class AdminAction(models.Model):
    """
    Log admin actions for audit trail
    """
    ACTION_TYPES = [
        ('user_create', 'User Created'),
        ('user_update', 'User Updated'),
        ('user_delete', 'User Deleted'),
        ('shop_approve', 'Shop Approved'),
        ('shop_reject', 'Shop Rejected'),
        ('shop_suspend', 'Shop Suspended'),
        ('order_cancel', 'Order Cancelled'),
        ('delivery_assign', 'Delivery Assigned'),
        ('system_setting', 'System Setting Changed'),
    ]

    admin_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_actions',
        limit_choices_to={'role': 'admin'},
        help_text='Admin user who performed the action'
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text='Type of action performed'
    )
    target_model = models.CharField(
        max_length=50,
        help_text='Target model name'
    )
    target_id = models.PositiveIntegerField(
        help_text='Target object ID'
    )
    description = models.TextField(
        help_text='Action description'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional action metadata'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_actions'
        verbose_name = 'Admin Action'
        verbose_name_plural = 'Admin Actions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin_user.username} - {self.get_action_type_display()}"


class Notification(models.Model):
    """
    System notifications for users
    """
    NOTIFICATION_TYPES = [
        ('order_status', 'Order Status Update'),
        ('shop_approval', 'Shop Approval'),
        ('delivery_assignment', 'Delivery Assignment'),
        ('system_announcement', 'System Announcement'),
        ('promotion', 'Promotion'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='Notification recipient'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        help_text='Type of notification'
    )
    title = models.CharField(
        max_length=200,
        help_text='Notification title'
    )
    message = models.TextField(
        help_text='Notification message'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the notification has been read'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional notification data'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='When the notification was read'
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
