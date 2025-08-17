from rest_framework import serializers
from .models import SystemSettings, AdminAction, Notification
from users.serializers import UserProfileSerializer
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from decimal import Decimal

User = get_user_model()


class SystemSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for SystemSettings model
    """
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminActionSerializer(serializers.ModelSerializer):
    """
    Serializer for AdminAction model
    """
    admin_user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = AdminAction
        fields = [
            'id', 'admin_user', 'action_type', 'target_model',
            'target_id', 'description', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'admin_user', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model
    """
    recipient = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'notification_type', 'title', 'message',
            'is_read', 'metadata', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'recipient', 'created_at', 'read_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications
    """
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='List of recipient user IDs'
    )
    send_to_all = serializers.BooleanField(
        write_only=True,
        default=False,
        help_text='Send to all users'
    )
    send_to_role = serializers.ChoiceField(
        choices=[('user', 'Users'), ('shopkeeper', 'Shopkeepers'), ('delivery', 'Delivery Persons')],
        write_only=True,
        required=False,
        help_text='Send to all users with specific role'
    )
    
    class Meta:
        model = Notification
        fields = [
            'notification_type', 'title', 'message', 'metadata',
            'recipient_ids', 'send_to_all', 'send_to_role'
        ]
    
    def create(self, validated_data):
        recipient_ids = validated_data.pop('recipient_ids', [])
        send_to_all = validated_data.pop('send_to_all', False)
        send_to_role = validated_data.pop('send_to_role', None)
        
        notifications = []
        
        if send_to_all:
            recipients = User.objects.filter(is_active=True)
        elif send_to_role:
            recipients = User.objects.filter(role=send_to_role, is_active=True)
        elif recipient_ids:
            recipients = User.objects.filter(id__in=recipient_ids, is_active=True)
        else:
            raise serializers.ValidationError("Must specify recipients")
        
        for recipient in recipients:
            notification = Notification.objects.create(
                recipient=recipient,
                **validated_data
            )
            notifications.append(notification)
        
        return notifications[0] if notifications else None


class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer for dashboard statistics
    """
    total_users = serializers.IntegerField()
    total_shopkeepers = serializers.IntegerField()
    total_delivery_persons = serializers.IntegerField()
    total_shops = serializers.IntegerField()
    pending_shops = serializers.IntegerField()
    approved_shops = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders_today = serializers.IntegerField()
    revenue_today = serializers.DecimalField(max_digits=12, decimal_places=2)


class UserStatsSerializer(serializers.Serializer):
    """
    Serializer for user statistics
    """
    role = serializers.CharField()
    count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    inactive_count = serializers.IntegerField()


class OrderStatsSerializer(serializers.Serializer):
    """
    Serializer for order statistics
    """
    status = serializers.CharField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class RevenueStatsSerializer(serializers.Serializer):
    """
    Serializer for revenue statistics
    """
    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class BulkActionSerializer(serializers.Serializer):
    """
    Serializer for bulk actions
    """
    action = serializers.ChoiceField(
        choices=[
            ('activate', 'Activate'),
            ('deactivate', 'Deactivate'),
            ('delete', 'Delete'),
            ('approve', 'Approve'),
            ('reject', 'Reject'),
            ('suspend', 'Suspend'),
        ]
    )
    target_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Reason for the action'
    )
    
    def validate_target_ids(self, value):
        if len(value) > 100:  # Limit bulk operations
            raise serializers.ValidationError("Cannot perform bulk action on more than 100 items")
        return value
