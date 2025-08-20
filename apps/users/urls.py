from django.urls import path, include
from . import views
from .views.auth_views import RegisterView, change_password

app_name = 'users'

urlpatterns = [
    # JWT authentication endpoints
    path('jwt/', include('apps.users.jwt_urls')),

    # User registration and authentication
    path('register/', RegisterView.as_view(), name='user-register'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('me/', views.current_user, name='current-user'),
    path('change-password/', change_password, name='change-password'),
    
    # User management (admin)
    path('', views.UserListView.as_view(), name='user-list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
]
