"""
URL configuration for service management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.services.views import (
    ServiceCategoryViewSet,
    ServiceViewSet,
    TenantServiceViewSet,
    ServiceAlertViewSet
)

app_name = 'services'

# API Router
router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet, basename='service-category')
router.register(r'catalog', ServiceViewSet, basename='service')
router.register(r'instances', TenantServiceViewSet, basename='tenant-service')
router.register(r'alerts', ServiceAlertViewSet, basename='service-alert')

urlpatterns = [
    path('', include(router.urls)),
]