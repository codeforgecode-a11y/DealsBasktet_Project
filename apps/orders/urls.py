from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Customer order endpoints
    path('', views.CustomerOrderListView.as_view(), name='customer-order-list'),
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('<int:pk>/', views.CustomerOrderDetailView.as_view(), name='customer-order-detail'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel-order'),
    
    # Shop order management
    path('shop/', views.ShopOrderListView.as_view(), name='shop-order-list'),
    path('shop/<int:pk>/', views.ShopOrderDetailView.as_view(), name='shop-order-detail'),
    
    # Delivery management
    path('delivery/', views.DeliveryOrderListView.as_view(), name='delivery-order-list'),
    path('delivery/<int:pk>/', views.DeliveryOrderDetailView.as_view(), name='delivery-order-detail'),
    path('delivery/<int:pk>/generate-otp/', views.generate_delivery_otp, name='generate-delivery-otp'),
    path('delivery/<int:pk>/verify-otp/', views.verify_delivery_otp, name='verify-delivery-otp'),
    
    # Admin endpoints
    path('<int:pk>/assign-delivery/', views.assign_delivery_person, name='assign-delivery-person'),
]
