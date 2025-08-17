"""
JWT Authentication Views for DealsBasket
Provides login, logout, refresh, and token validation endpoints
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .jwt_authentication import JWTTokenManager
from .serializers import UserProfileSerializer
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class JWTLoginView(APIView):
    """
    JWT authentication login endpoint
    Accepts username/email and password, returns JWT tokens
    """
    permission_classes = [permissions.AllowAny]
    
    def get_content_type(self):
        return 'application/json'

    def post(self, request):
        """
        Authenticate user with username/email and password
        """
        username_or_email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')

        if not username_or_email or not password:
            return Response({
                'success': False,
                'code': 'missing_credentials',
                'error': 'Username/email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json')

        try:
            # Try to find user by username or email
            user = None
            if '@' in username_or_email:
                # Email provided
                try:
                    user = User.objects.get(email=username_or_email)
                except User.DoesNotExist:
                    pass
            else:
                # Username provided
                try:
                    user = User.objects.get(username=username_or_email)
                except User.DoesNotExist:
                    pass

            if not user:
                return Response({
                    'success': False,
                    'code': 'invalid_credentials',
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')

            # Check password
            if not user.check_password(password):
                return Response({
                    'success': False,
                    'code': 'invalid_credentials',
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')

            # Check if user is active
            if not user.is_active:
                return Response({
                    'success': False,
                    'code': 'account_disabled',
                    'error': 'User account is disabled'
                }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json')

            # Generate JWT tokens
            tokens = JWTTokenManager.generate_tokens(user)
            user_data = UserProfileSerializer(user).data

            logger.info(f"JWT login successful for user: {user.username}")

            return Response({
                'success': True,
                'access_token': tokens['access_token'],
                'refresh_token': tokens['refresh_token'],
                'user': user_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"JWT login error: {str(e)}")
            return Response({
                'error': 'Authentication failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class JWTRefreshView(APIView):
    """
    JWT token refresh endpoint
    Accepts refresh token and returns new access token
    """
    permission_classes = [permissions.AllowAny]
    
    def get_content_type(self):
        return 'application/json'

    def post(self, request):
        """
        Refresh access token using refresh token
        """
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({
                'detail': 'No refresh token provided'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Generate new access token
            access_token, expires = JWTTokenManager.refresh_access_token(refresh_token)

            return Response({
                'success': True,
                'access_token': access_token
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"JWT refresh error: {str(e)}")
            return Response({
                'error': 'Token refresh failed'
            }, status=status.HTTP_401_UNAUTHORIZED)


@method_decorator(csrf_exempt, name='dispatch')
class JWTLogoutView(APIView):
    """
    JWT logout endpoint
    Blacklists the provided token
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_content_type(self):
        return 'application/json'

    def post(self, request):
        """
        Logout user by blacklisting token
        """
        try:
            # Get token from request
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Blacklist the token
                JWTTokenManager.blacklist_token(token)
                
                # Also blacklist refresh token if provided
                refresh_token = request.data.get('refresh_token')
                if refresh_token:
                    JWTTokenManager.blacklist_token(refresh_token)

            logger.info(f"JWT logout successful for user: {request.user.username}")

            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"JWT logout error: {str(e)}")
            return Response({
                'error': 'Logout failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class JWTVerifyView(APIView):
    """
    JWT token verification endpoint
    Verifies if the provided token is valid
    """
    permission_classes = [permissions.AllowAny]
    
    def get_content_type(self):
        return 'application/json'

    def post(self, request):
        """
        Verify JWT token validity
        """
        token = request.data.get('token')

        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify token
            payload = JWTTokenManager.verify_token(token, 'access')
            
            # Get user data
            user = User.objects.get(id=payload['user_id'])
            user_data = UserProfileSerializer(user).data

            return Response({
                'valid': True
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({
                'success': False,
                'valid': False,
                'error': 'User not found'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'success': False,
                'valid': False,
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def jwt_profile(request):
    """
    Get authenticated user profile (JWT version)
    """
    try:
        user_data = UserProfileSerializer(request.user).data
        return Response({
            'success': True,
            'data': user_data,
            'message': 'Profile fetched successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"JWT profile error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch profile'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def jwt_change_password(request):
    """
    Change user password (JWT version)
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

    try:
        # Validate new password
        validate_password(new_password, user)
    except ValidationError as e:
        return Response({
            'error': list(e.messages)
        }, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()

    logger.info(f"Password changed successfully for user: {user.username}")

    return Response({
        'success': True,
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)
