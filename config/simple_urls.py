"""
Simple URL configuration for quick start
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def api_home_view(request):
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
    # Marketing website (takes priority for root path)
    path('', include('apps.marketing.urls')),

    # API home endpoint
    path('api/home/', api_home_view, name='api_home'),

    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),

    # TeamSpace SSO Integration API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/organizations/', include('apps.tenants.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
]
