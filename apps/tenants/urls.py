"""
URL configuration for tenant management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from apps.authentication.views import OrganizationDetailView

app_name = 'tenants'

# API Router
router = DefaultRouter()
router.register(r'tenants', views.TenantViewSet)
# router.register(r'invitations', views.TenantInvitationViewSet)

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),

    # Custom endpoints
    path('tenant-setup/', views.TenantSetupView.as_view(), name='tenant-setup'),
    path('current-tenant/', views.CurrentTenantView.as_view(), name='current-tenant'),
    path('switch-tenant/<uuid:tenant_id>/', views.SwitchTenantView.as_view(), name='switch-tenant'),
    # path('invitation/accept/<uuid:token>/', views.AcceptInvitationView.as_view(), name='accept-invitation'),

    # TeamSpace SSO integration endpoint (served at /api/organizations/<uuid>/)
    path('<uuid:organization_id>/', OrganizationDetailView.as_view(), name='organization-detail'),
]