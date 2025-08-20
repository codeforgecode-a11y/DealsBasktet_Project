"""
JWT Authentication URL patterns for DealsBasket
"""
from django.urls import path
from . import jwt_views

app_name = 'jwt_auth'

urlpatterns = [
    # Token endpoints
    path('login/', jwt_views.JWTLoginView.as_view(), name='jwt_login'),
    path('refresh/', jwt_views.JWTRefreshView.as_view(), name='jwt_refresh'),
    path('verify/', jwt_views.JWTVerifyView.as_view(), name='jwt_verify'),
    path('logout/', jwt_views.JWTLogoutView.as_view(), name='jwt_logout'),

    # Profile endpoints
    path('profile/', jwt_views.jwt_profile, name='jwt_user_profile'),
    path('password/change/', jwt_views.jwt_change_password, name='jwt_password_change'),
]
