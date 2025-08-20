from .views.user_views import (
    UserProfileView, UserDetailView, UserListView,
    current_user
)

# Re-export views for backward compatibility
__all__ = [
    'UserProfileView', 
    'UserDetailView', 
    'UserListView',
    'current_user'
]