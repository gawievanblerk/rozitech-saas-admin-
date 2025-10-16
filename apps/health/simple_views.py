"""
Simplified health check without tenant dependencies
"""
from django.http import JsonResponse
import time

def simple_health_check(request):
    """Basic health check without database or tenant checks"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'rozitech-saas-admin',
        'timestamp': time.time(),
        'version': '1.0.0'
    })