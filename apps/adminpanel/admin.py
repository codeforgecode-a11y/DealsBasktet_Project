from django.contrib import admin
from .models import SystemSettings, AdminAction, Notification


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    Admin configuration for SystemSettings model
    """
    list_display = ['key', 'value', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'value', 'description']
    ordering = ['key']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    """
    Admin configuration for AdminAction model
    """
    list_display = [
        'admin_user', 'action_type', 'target_model',
        'target_id', 'created_at'
    ]
    list_filter = ['action_type', 'target_model', 'created_at']
    search_fields = [
        'admin_user__username', 'description',
        'target_model', 'target_id'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('admin_user')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Notification model
    """
    list_display = [
        'recipient', 'notification_type', 'title',
        'is_read', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = [
        'recipient__username', 'title', 'message'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'read_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient')
