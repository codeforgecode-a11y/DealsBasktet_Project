from django.contrib import admin
from .models import DeliveryPerson, DeliveryZone, DeliveryAssignment


@admin.register(DeliveryPerson)
class DeliveryPersonAdmin(admin.ModelAdmin):
    """
    Admin configuration for DeliveryPerson model
    """
    list_display = [
        'user', 'vehicle_type', 'is_available', 'rating',
        'total_deliveries', 'created_at'
    ]
    list_filter = ['vehicle_type', 'is_available', 'created_at']
    search_fields = ['user__username', 'user__email', 'vehicle_number', 'license_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'can_accept_orders']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Vehicle Information', {
            'fields': ('vehicle_type', 'vehicle_number', 'license_number')
        }),
        ('Status', {
            'fields': ('is_available', 'can_accept_orders')
        }),
        ('Location', {
            'fields': ('current_latitude', 'current_longitude')
        }),
        ('Statistics', {
            'fields': ('rating', 'total_deliveries')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    """
    Admin configuration for DeliveryZone model
    """
    list_display = [
        'name', 'delivery_fee', 'estimated_delivery_time',
        'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DeliveryAssignment)
class DeliveryAssignmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for DeliveryAssignment model
    """
    list_display = [
        'id', 'delivery_person', 'order', 'status',
        'assigned_at', 'delivered_at'
    ]
    list_filter = ['status', 'assigned_at']
    search_fields = [
        'delivery_person__username', 'order__order_id',
        'order__customer__username'
    ]
    ordering = ['-assigned_at']
    readonly_fields = ['assigned_at']

    fieldsets = (
        ('Assignment Information', {
            'fields': ('delivery_person', 'order', 'status')
        }),
        ('Timestamps', {
            'fields': (
                'assigned_at', 'accepted_at', 'picked_up_at', 'delivered_at'
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'delivery_person', 'order', 'order__customer'
        )
