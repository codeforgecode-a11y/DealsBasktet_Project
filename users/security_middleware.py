"""
Security middleware for authentication system
Provides additional security layers including rate limiting, security headers, and token validation
"""
import time
import hashlib
from collections import defaultdict
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses
    """
    
    def process_response(self, request, response):
        """
        Add security headers to all responses
        """
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://apis.google.com https://www.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
            "frame-src 'self';"
        )
        
        # X-Frame-Options
        response['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        
        # HSTS (only for HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware for authentication endpoints
    """
    
    # Rate limits: (requests, time_window_seconds)
    RATE_LIMITS = {
        '/api/auth/login/': (5, 300),  # 5 attempts per 5 minutes
        '/api/auth/refresh-token/': (20, 300),  # 20 refreshes per 5 minutes
        '/api/v1/users/register/': (3, 3600),  # 3 registrations per hour
    }
    
    def process_request(self, request):
        """
        Check rate limits for authentication endpoints
        """
        path = request.path
        
        # Check if this path has rate limiting
        if path not in self.RATE_LIMITS:
            return None
        
        max_requests, time_window = self.RATE_LIMITS[path]
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Create cache key
        cache_key = f"rate_limit:{path}:{client_ip}"
        
        # Get current request count
        current_requests = cache.get(cache_key, 0)
        
        if current_requests >= max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Please try again later.',
                'retry_after': time_window
            }, status=429)
        
        # Increment request count
        cache.set(cache_key, current_requests + 1, time_window)
        
        return None
    
    def get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuthenticationLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log authentication attempts and security events
    """
    
    AUTH_ENDPOINTS = [
        '/api/auth/login/',
        '/api/auth/register/',
        '/api/auth/refresh-token/',
        '/api/auth/verify-email/',
        '/api/auth/logout/',
        '/api/v1/users/change-password/',
    ]
    
    def process_request(self, request):
        """
        Log authentication requests
        """
        if request.path in self.AUTH_ENDPOINTS:
            client_ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            
            # Store request info for later logging
            request._auth_log_data = {
                'ip': client_ip,
                'user_agent': user_agent,
                'path': request.path,
                'method': request.method,
                'timestamp': time.time()
            }
        
        return None
    
    def process_response(self, request, response):
        """
        Log authentication responses
        """
        if hasattr(request, '_auth_log_data'):
            log_data = request._auth_log_data
            status_code = response.status_code
            
            # Determine log level based on status code
            if status_code == 200:
                log_level = 'info'
                message = 'Authentication successful'
            elif status_code in [400, 401, 403]:
                log_level = 'warning'
                message = 'Authentication failed'
            else:
                log_level = 'error'
                message = 'Authentication error'
            
            # Log the event
            getattr(logger, log_level)(
                f"{message}: {log_data['method']} {log_data['path']} "
                f"from {log_data['ip']} - Status: {status_code}"
            )
            
            # Log suspicious activity
            if status_code == 401 and log_data['path'] == '/api/auth/login/':
                self.log_failed_login_attempt(log_data)
        
        return response
    
    def log_failed_login_attempt(self, log_data):
        """
        Log and track failed login attempts
        """
        cache_key = f"failed_login:{log_data['ip']}"
        failed_attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, failed_attempts, 3600)  # Track for 1 hour
        
        if failed_attempts >= 5:
            logger.critical(
                f"Multiple failed login attempts detected from {log_data['ip']} "
                f"({failed_attempts} attempts in the last hour)"
            )
    
    def get_client_ip(self, request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TokenValidationMiddleware(MiddlewareMixin):
    """
    Middleware to validate JWT tokens and add additional security checks
    """
    
    PROTECTED_PATHS = [
        '/api/v1/users/',
        '/api/v1/shops/',
        '/api/v1/products/',
        '/api/v1/orders/',
        '/api/v1/delivery/',
        '/api/v1/admin/',
    ]
    
    def process_request(self, request):
        """
        Validate tokens for protected endpoints
        """
        # Check if this is a protected path
        if not any(request.path.startswith(path) for path in self.PROTECTED_PATHS):
            return None
        
        # Skip validation for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Please provide a valid authentication token'
            }, status=401)
        
        # Extract token
        try:
            token = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else auth_header
        except IndexError:
            return JsonResponse({
                'error': 'Invalid token format',
                'message': 'Please provide a valid Bearer token'
            }, status=401)
        
        # Additional token validation can be added here
        # For now, let the authentication backends handle validation
        
        return None


class CSRFExemptionMiddleware(MiddlewareMixin):
    """
    Middleware to exempt API endpoints from CSRF protection
    """
    
    API_PATHS = [
        '/api/',
    ]
    
    def process_request(self, request):
        """
        Exempt API endpoints from CSRF protection
        """
        if any(request.path.startswith(path) for path in self.API_PATHS):
            setattr(request, '_dont_enforce_csrf_checks', True)
        
        return None
