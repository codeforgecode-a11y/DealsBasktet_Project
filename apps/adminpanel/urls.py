from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # System settings
    path('settings/', views.SystemSettingsView.as_view(), name='settings-list'),
    path('settings/<int:pk>/', views.SystemSettingsDetailView.as_view(), name='settings-detail'),
    
    # Admin actions audit
    path('actions/', views.AdminActionListView.as_view(), name='action-list'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    
    # Statistics
    path('stats/users/', views.user_statistics, name='user-stats'),
    path('stats/orders/', views.order_statistics, name='order-stats'),
    path('stats/revenue/', views.revenue_statistics, name='revenue-stats'),
    
    # Bulk actions
    path('bulk/users/', views.bulk_user_action, name='bulk-user-action'),
    path('bulk/shops/', views.bulk_shop_action, name='bulk-shop-action'),
]
