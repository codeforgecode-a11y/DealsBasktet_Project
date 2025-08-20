from rest_framework import generics, status, permissions, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.conf import settings
from .serializers import (
    UserSerializer, UserProfileSerializer,
    UserRegistrationSerializer, AdminUserSerializer
)
from .permissions import IsAdminUser, IsOwnerOrAdmin
from .jwt_authentication import JWTTokenManager
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate email verification token
        token = get_random_string(64)
        user.email_verification_token = token
        user.save()

        # Send verification email
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            context = {
                'user': user,
                'verification_url': verification_url
            }
            html_message = render_to_string('users/email/verify_email.html', context)
            send_mail(
                'Verify your email',
                '',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message
            )
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")

        # Generate tokens
        tokens = JWTTokenManager.generate_tokens(user)

        return Response({
            'message': 'User registered successfully',
            'user': UserProfileSerializer(user).data,
            **tokens
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    """
    Authenticate user and return tokens
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                tokens = JWTTokenManager.generate_tokens(user)
                return Response({
                    'user': UserSerializer(user).data,
                    **tokens
                })
            else:
                return Response({'error': 'Invalid credentials'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, 
                          status=status.HTTP_401_UNAUTHORIZED)


class RefreshTokenView(views.APIView):
    """
    Refresh access token using refresh token
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            access_token, expires = JWTTokenManager.refresh_access_token(refresh_token)
            return Response({
                'access_token': access_token,
                'access_token_expires': expires
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


class VerifyEmailView(views.APIView):
    """
    Verify user's email address
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email_verification_token=token)
            user.is_verified = True
            user.email_verification_token = None
            user.save()
            return Response({'message': 'Email verified successfully'})
        except User.DoesNotExist:
            return Response({'error': 'Invalid token'}, 
                          status=status.HTTP_400_BAD_REQUEST)


class LogoutView(views.APIView):
    """
    Logout user and blacklist tokens
    """
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            JWTTokenManager.blacklist_token(refresh_token)
        
        # Also blacklist the current access token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
            JWTTokenManager.blacklist_token(access_token)
        
        return Response({'message': 'Successfully logged out'})


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    User profile view and update endpoint
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    User detail view for admin or owner access
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.request.user.is_admin_user:
            return AdminUserSerializer
        return UserSerializer


class UserListView(generics.ListAPIView):
    """
    User list view for admin users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """
    Get current authenticated user details
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)





