from django.urls import path
from .views.auth_views import (
    RegisterView, LoginView, LogoutView,
    RefreshTokenView, VerifyEmailView
)
from .views.auth_views import (
    RegisterView, LoginView, LogoutView,
    RefreshTokenView, VerifyEmailView, 
    auth_profile, change_password
)

app_name = 'auth'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('profile/', auth_profile, name='profile'),
    path('change-password/', change_password, name='change-password'),
]
