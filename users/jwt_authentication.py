"""
JWT Authentication backend for DealsBasket
Provides comprehensive JWT token management with refresh capabilities
"""
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from rest_framework.response import Response
from rest_framework import status
import threading
from collections import defaultdict

User = get_user_model()

# JWT Configuration
JWT_SECRET_KEY = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
JWT_ALGORITHM = getattr(settings, 'JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_LIFETIME = getattr(settings, 'JWT_ACCESS_TOKEN_LIFETIME', timedelta(minutes=60))
JWT_REFRESH_TOKEN_LIFETIME = getattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME', timedelta(days=7))
JWT_ALLOW_REFRESH = getattr(settings, 'JWT_ALLOW_REFRESH', True)

# In-memory token blacklist with expiry
class TokenBlacklist:
    def __init__(self):
        self._blacklist = defaultdict(lambda: 0)
        self._lock = threading.Lock()

    def add(self, token, exp_timestamp):
        with self._lock:
            self._blacklist[token] = exp_timestamp
            self._cleanup()

    def check(self, token):
        with self._lock:
            self._cleanup()
            return token in self._blacklist

    def _cleanup(self):
        now = datetime.utcnow().timestamp()
        expired = [token for token, exp in self._blacklist.items() if exp < now]
        for token in expired:
            del self._blacklist[token]

TOKEN_BLACKLIST = TokenBlacklist()


class JWTTokenManager:
    """
    JWT Token management utility class
    """
    
    @staticmethod
    def generate_tokens(user):
        """
        Generate access and refresh tokens for a user
        """
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'exp': now + JWT_ACCESS_TOKEN_LIFETIME,
            'iat': now,
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'exp': now + JWT_REFRESH_TOKEN_LIFETIME,
            'iat': now,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_token_expires': access_payload['exp'],
            'refresh_token_expires': refresh_payload['exp']
        }
    
    @staticmethod
    def verify_token(token, token_type='access'):
        """
        Verify and decode JWT token
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check token type
            if payload.get('type') != token_type:
                raise jwt.InvalidTokenError(f'Invalid token type. Expected {token_type}')
            
            # Check if token is blacklisted
            if JWTTokenManager.is_token_blacklisted(token):
                raise jwt.InvalidTokenError('Token has been revoked')
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """
        Generate new access token from refresh token
        """
        if not JWT_ALLOW_REFRESH:
            raise exceptions.AuthenticationFailed('Token refresh is disabled')
        
        try:
            payload = JWTTokenManager.verify_token(refresh_token, 'refresh')
            user = User.objects.get(id=payload['user_id'])
            
            # Generate new access token
            tokens = JWTTokenManager.generate_tokens(user)
            return tokens['access_token'], tokens['access_token_expires']
            
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')
    
    @staticmethod
    def blacklist_token(token):
        """
        Add token to blacklist
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
            exp = payload.get('exp')
            if exp:
                TOKEN_BLACKLIST.add(token, exp)
                return True
        except:
            pass
        return False
    
    @staticmethod
    def is_token_blacklisted(token):
        """
        Check if token is blacklisted
        """
        return TOKEN_BLACKLIST.check(token)


class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT authentication backend for Django REST Framework
    """
    
    def authenticate(self, request):
        """
        Authenticate user using JWT token
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        try:
            # Extract token from Authorization header
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return None
        
        try:
            # Verify JWT token
            payload = JWTTokenManager.verify_token(token, 'access')
            user_id = payload['user_id']
            
            # Get user
            user = User.objects.get(id=user_id)
            
            # Check if user is active
            if not user.is_active:
                raise exceptions.AuthenticationFailed({
                    'detail': 'User account is disabled',
                    'code': 'user_disabled'
                })
            
            return (user, token)
            
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed({
                'detail': 'User not found',
                'code': 'user_not_found'
            })
        except exceptions.AuthenticationFailed as e:
            raise
        except Exception as e:
            raise exceptions.AuthenticationFailed({
                'detail': str(e),
                'code': 'authentication_failed'
            })
    
    def authenticate_header(self, request):
        """
        Return authentication header for 401 responses
        """
        return 'Bearer'



