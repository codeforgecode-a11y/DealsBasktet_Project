from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for OrderItem
    """
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin configuration for Order model
    """
    list_display = [
        'order_id', 'customer', 'shop', 'status', 'payment_status',
        'total_amount', 'delivery_person', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'shop', 'created_at'
    ]
    search_fields = [
        'order_id', 'customer__username', 'customer__email',
        'shop__name', 'delivery_person__username'
    ]
    ordering = ['-created_at']
    readonly_fields = ['order_id', 'created_at', 'updated_at', 'total_items']
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'customer', 'shop', 'status', 'payment_status')
        }),
        ('Delivery Information', {
            'fields': (
                'delivery_person', 'delivery_address', 'delivery_phone',
                'estimated_delivery_time', 'actual_delivery_time'
            )
        }),
        ('Financial Information', {
            'fields': ('total_amount', 'delivery_fee')
        }),
        ('Additional Information', {
            'fields': ('notes', 'otp', 'total_items')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'shop', 'delivery_person'
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin configuration for OrderItem model
    """
    list_display = [
        'order', 'product', 'quantity', 'unit_price', 'total_price'
    ]
    list_filter = ['order__status', 'product__category']
    search_fields = [
        'order__order_id', 'product__name', 'product__shop__name'
    ]
    readonly_fields = ['total_price', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'order', 'product', 'product__shop'
        )
