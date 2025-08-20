from django.contrib import admin
from .models import Product, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Category model
    """
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for Product model
    """
    list_display = [
        'name', 'shop', 'category', 'price', 'stock_quantity',
        'is_available', 'created_at'
    ]
    list_filter = [
        'is_available', 'category', 'shop__status', 'created_at'
    ]
    search_fields = [
        'name', 'description', 'sku', 'shop__name', 'shop__owner__username'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'discounted_price']

    fieldsets = (
        ('Basic Information', {
            'fields': ('shop', 'name', 'description', 'category', 'sku')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_percentage', 'discounted_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_available')
        }),
        ('Product Details', {
            'fields': ('image', 'weight', 'dimensions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shop', 'category')
