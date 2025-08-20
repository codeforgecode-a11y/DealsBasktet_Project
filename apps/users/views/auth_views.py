from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from ..serializers import (
    UserRegistrationSerializer as UserCreateSerializer, 
    UserSerializer,
    UserProfileSerializer
)
from ..jwt_authentication import JWTTokenManager
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.conf import settings
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class RegisterView(views.APIView):
    """
    Register a new user
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
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
                'user': UserSerializer(user).data,
                **tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def auth_profile(request):
    """
    Get authenticated user profile
    This endpoint matches the frontend's expectation for /api/auth/profile/
    """
    try:
        user_data = UserProfileSerializer(request.user).data
        return Response({
            'success': True,
            'data': user_data,
            'message': 'Profile fetched successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response({
            'error': 'Both old_password and new_password are required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not user.check_password(old_password):
        return Response({
            'error': 'Invalid old password'
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(new_password) < 8:
        return Response({
            'error': 'New password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)