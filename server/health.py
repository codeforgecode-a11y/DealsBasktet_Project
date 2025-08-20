from django.http import JsonResponse, HttpResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
import time
import json


@csrf_exempt
@never_cache
def simple_health_check(request):
    """
    Simple health check that bypasses most Django middleware
    """
    try:
        # Debug information
        debug_info = []
        debug_info.append(f"Host: {request.get_host()}")
        debug_info.append(f"Method: {request.method}")
        debug_info.append(f"Path: {request.path}")

        # Check ALLOWED_HOSTS
        from django.conf import settings
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        debug_info.append(f"ALLOWED_HOSTS: {allowed_hosts}")

        host = request.get_host()
        host_allowed = host in allowed_hosts or '*' in allowed_hosts
        debug_info.append(f"Host allowed: {host_allowed}")

        # Check environment configuration
        try:
            import os
            debug_info.append(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
            debug_info.append(f"Database URL configured: {'DATABASE_URL' in os.environ}")
        except Exception as env_e:
            debug_info.append(f"Environment check: FAILED - {str(env_e)}")

        response_text = "OK\n" + "\n".join(debug_info)
        return HttpResponse(response_text, content_type="text/plain", status=200)
    except Exception as e:
        return HttpResponse(f"ERROR: {str(e)}", content_type="text/plain", status=500)


@csrf_exempt
@never_cache
def health_check(request):
    """
    Detailed health check endpoint for monitoring
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'checks': {}
    }

    # Basic application check
    try:
        health_status['checks']['application'] = 'healthy'
        health_status['checks']['django'] = 'running'

        # Check ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        health_status['checks']['allowed_hosts'] = allowed_hosts

        # Check if request host is allowed
        host = request.get_host()
        health_status['checks']['request_host'] = host
        health_status['checks']['host_allowed'] = host in allowed_hosts or '*' in allowed_hosts

    except Exception as e:
        health_status['checks']['application'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Database check (optional - don't fail if DB is not available)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unavailable: {str(e)}'
        # Don't mark as unhealthy for database issues in initial deployment

    # Settings check
    try:
        health_status['checks']['settings'] = {
            'debug': getattr(settings, 'DEBUG', 'unknown'),
            'secret_key_configured': bool(getattr(settings, 'SECRET_KEY', None)),
        }
        # Only include database engine if it's configured
        if hasattr(settings, 'DATABASES') and 'default' in settings.DATABASES:
            health_status['checks']['settings']['database_engine'] = settings.DATABASES['default'].get('ENGINE', 'unknown')
    except Exception as e:
        health_status['checks']['settings'] = f'error: {str(e)}'

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
