from django.contrib import admin
from .models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """
    Admin configuration for Shop model
    """
    list_display = ['name', 'owner', 'status', 'is_active', 'phone', 'created_at']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['name', 'owner__username', 'address', 'phone']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'description', 'address')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude')
        }),
        ('Operating Hours', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')
