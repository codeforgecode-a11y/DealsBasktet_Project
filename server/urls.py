"""
URL configuration for DealsBasket server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .health import health_check


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """
    DealsBasket API Root
    Welcome to the DealsBasket API - A local e-commerce platform with role-based access control.
    """
    return Response({
        'message': 'Welcome to DealsBasket API',
        'version': '1.0.0',
        'documentation': {
            'swagger': request.build_absolute_uri('/api/docs/'),
            'redoc': request.build_absolute_uri('/api/redoc/'),
            'schema': request.build_absolute_uri('/api/schema/')
        },
        'endpoints': {
            'auth': request.build_absolute_uri('/api/auth/'),
            'users': request.build_absolute_uri('/api/v1/users/'),
            'shops': request.build_absolute_uri('/api/v1/shops/'),
            'products': request.build_absolute_uri('/api/v1/products/'),
            'orders': request.build_absolute_uri('/api/v1/orders/'),
            'delivery': request.build_absolute_uri('/api/v1/delivery/'),
            'admin': request.build_absolute_uri('/api/v1/admin/')
        }
    })


urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Health check
    path('health/', health_check, name='health-check'),

    # API root
    path('api/', api_root, name='api-root'),

    # Authentication endpoints
    # Authentication endpoints
    path('api/auth/', include('users.auth_urls')),
    path('api/auth/jwt/', include('users.jwt_urls')),

    # API v1 endpoints
    path('api/v1/users/', include('users.urls')),
    path('api/v1/shops/', include('shop.urls')),
    path('api/v1/products/', include('products.urls')),
    path('api/v1/orders/', include('orders.urls')),
    path('api/v1/delivery/', include('delivery.urls')),
    path('api/v1/admin/', include('adminpanel.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Add debug toolbar URLs in development
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
