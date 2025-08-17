from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Public product endpoints
    path('', views.ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('search/', views.product_search, name='product-search'),
    
    # Shop product management
    path('my-products/', views.ShopProductListView.as_view(), name='my-products'),
    path('my-products/<int:pk>/', views.ShopProductDetailView.as_view(), name='my-product-detail'),
    path('upload-image/', views.upload_product_image, name='upload-product-image'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    
    # Admin category management
    path('admin/categories/', views.AdminCategoryView.as_view(), name='admin-category-list'),
    path('admin/categories/<int:pk>/', views.AdminCategoryDetailView.as_view(), name='admin-category-detail'),
]
