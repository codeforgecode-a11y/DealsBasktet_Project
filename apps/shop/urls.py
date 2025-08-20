from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Shop registration and management
    path('register/', views.ShopRegistrationView.as_view(), name='shop-register'),
    path('my-shop/', views.MyShopView.as_view(), name='my-shop'),
    path('search/', views.shop_search, name='shop-search'),
    
    # Public shop listing
    path('', views.ShopListView.as_view(), name='shop-list'),
    
    # Shop detail
    path('<int:pk>/', views.ShopDetailView.as_view(), name='shop-detail'),
    
    # Admin endpoints
    path('admin/', views.AdminShopListView.as_view(), name='admin-shop-list'),
    path('<int:pk>/status/', views.update_shop_status, name='update-shop-status'),
]
