from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    # Delivery person profile
    path('profile/', views.DeliveryPersonProfileView.as_view(), name='delivery-profile'),
    path('update-location/', views.update_location, name='update-location'),
    path('stats/', views.delivery_stats, name='delivery-stats'),
    
    # Delivery assignments
    path('assignments/', views.DeliveryAssignmentListView.as_view(), name='assignment-list'),
    path('assignments/<int:pk>/', views.DeliveryAssignmentDetailView.as_view(), name='assignment-detail'),
    
    # Delivery zones
    path('zones/', views.DeliveryZoneListView.as_view(), name='zone-list'),
    
    # Admin endpoints
    path('admin/zones/', views.AdminDeliveryZoneView.as_view(), name='admin-zone-list'),
    path('admin/zones/<int:pk>/', views.AdminDeliveryZoneDetailView.as_view(), name='admin-zone-detail'),
    path('admin/assign/', views.assign_delivery, name='assign-delivery'),
    path('admin/available-persons/', views.available_delivery_persons, name='available-delivery-persons'),
]
