from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings


def health_check(request):
    """Health check endpoint for monitoring."""
    health_status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = 'error'
        health_status['status'] = 'unhealthy'
    
    # Check Redis
    try:
        cache.set('health_check', 'ok', 1)
        if cache.get('health_check') == 'ok':
            health_status['checks']['redis'] = 'ok'
        else:
            health_status['checks']['redis'] = 'error'
            health_status['status'] = 'unhealthy'
    except Exception:
        health_status['checks']['redis'] = 'error'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)