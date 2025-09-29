from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """Comprehensive health check including auth server status"""
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'services': {}
    }
    
    overall_healthy = True
    
    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = {
            'status': 'healthy',
            'type': 'postgresql'
        }
    except Exception as e:
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'error': str(e),
            'type': 'postgresql'
        }
        overall_healthy = False
    
    # Redis health check
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['services']['cache'] = {
            'status': 'healthy',
            'type': 'redis'
        }
    except Exception as e:
        health_status['services']['cache'] = {
            'status': 'unhealthy',
            'error': str(e),
            'type': 'redis'
        }
        overall_healthy = False
    
    # Auth Server health check (if enabled)
    if getattr(settings, 'USE_ROZITECH_AUTH', False):
        try:
            from core.auth.rozitech_auth import is_auth_server_available
            auth_healthy = is_auth_server_available()
            health_status['services']['auth_server'] = {
                'status': 'healthy' if auth_healthy else 'unhealthy',
                'url': getattr(settings, 'ROZITECH_AUTH_SERVER_URL', 'not configured'),
                'required': True
            }
            if not auth_healthy:
                overall_healthy = False
        except Exception as e:
            health_status['services']['auth_server'] = {
                'status': 'unhealthy',
                'error': str(e),
                'required': True
            }
            overall_healthy = False
    else:
        health_status['services']['auth_server'] = {
            'status': 'disabled',
            'required': False
        }
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
    
    # Return appropriate HTTP status
    status_code = 200 if overall_healthy else 503
    
    return JsonResponse(health_status, status=status_code)


def auth_server_status(request):
    """Detailed auth server status check"""
    if not getattr(settings, 'USE_ROZITECH_AUTH', False):
        return JsonResponse({
            'status': 'disabled',
            'message': 'Auth server integration is disabled'
        })
    
    try:
        from core.auth.rozitech_auth import RozitechAuthServerClient
        
        client = RozitechAuthServerClient()
        
        status_info = {
            'url': client.base_url,
            'configured': bool(client.api_key),
            'timeout': client.timeout,
            'timestamp': time.time()
        }
        
        # Test connectivity
        healthy = client.health_check()
        status_info['status'] = 'healthy' if healthy else 'unhealthy'
        status_info['reachable'] = healthy
        
        status_code = 200 if healthy else 503
        
    except Exception as e:
        status_info = {
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }
        status_code = 503
    
    return JsonResponse(status_info, status=status_code)