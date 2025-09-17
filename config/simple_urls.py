"""
Simple URL configuration for quick start
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def home_view(request):
    return JsonResponse({
        'message': 'Welcome to Rozitech SaaS Admin Platform!',
        'status': 'running',
        'features': [
            'Multi-tenant architecture ready',
            'Subscription management',
            'Payment processing framework',
            'Service orchestration',
            'RESTful API'
        ],
        'api_docs': '/api/docs/',
        'admin': '/admin/'
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
