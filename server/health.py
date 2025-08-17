from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import time


def health_check(request):
    """
    Health check endpoint for monitoring
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Settings check
    try:
        health_status['checks']['settings'] = {
            'debug': settings.DEBUG,
            'database_engine': settings.DATABASES['default']['ENGINE'],
        }
    except Exception as e:
        health_status['checks']['settings'] = f'error: {str(e)}'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
