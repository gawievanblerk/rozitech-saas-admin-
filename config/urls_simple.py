"""
Simple URL configuration for full platform without complex views
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def home_view(request):
    return JsonResponse({
        'message': 'Welcome to Rozitech SaaS Admin Platform - Full Version!',
        'status': 'running',
        'features': [
            'Organization Management',
            'Subscription Management',
            'Pricing Plans',
            'Invoice Management',
            'Payment Processing Framework',
            'Service Orchestration',
            'RESTful API'
        ],
        'admin': '/admin/',
        'api_docs': '/api/docs/',
        'models_available': [
            'Organization', 'OrganizationUser', 'Domain',
            'PricingPlan', 'Subscription', 'Invoice'
        ]
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]