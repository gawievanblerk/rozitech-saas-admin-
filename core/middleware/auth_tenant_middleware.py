"""
Middleware for integrating Rozitech Auth Server with Django Tenants
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
from core.auth.rozitech_auth import get_user_organizations, RozitechAuthServerClient

logger = logging.getLogger(__name__)


class RozitechAuthTenantMiddleware(MiddlewareMixin):
    """
    Middleware that sets tenant context based on Rozitech Auth Server data
    """
    
    def process_request(self, request):
        """
        Process incoming request and set tenant context from auth server
        """
        # Skip for non-API requests or if auth server integration is disabled
        if not getattr(settings, 'USE_ROZITECH_AUTH', False):
            return None
        
        # Skip for certain paths
        skip_paths = ['/admin/', '/health/', '/api/docs/', '/static/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Get user organizations from auth server
            organizations = get_user_organizations(token)
            
            if organizations:
                # Set the primary organization as tenant context
                primary_org = organizations[0] if organizations else None
                if primary_org:
                    request.tenant_id = primary_org.get('org_id')
                    request.tenant_name = primary_org.get('org_name')
                    request.tenant_slug = primary_org.get('org_slug')
                    request.user_role = primary_org.get('role')
                    
                    logger.debug(f"Set tenant context: {request.tenant_name} for user")
            
            # Store all organizations for later use
            request.user_organizations = organizations
            
        except Exception as e:
            logger.error(f"Failed to set tenant context: {e}")
            # Don't block the request, just log the error
        
        return None


class AuthServerHealthMiddleware(MiddlewareMixin):
    """
    Middleware to check auth server health and provide fallback
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_client = RozitechAuthServerClient()
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Check auth server health for critical paths
        """
        # Only check for API endpoints when auth server is enabled
        if not getattr(settings, 'USE_ROZITECH_AUTH', False):
            return None
        
        # Skip health check for certain paths
        skip_paths = ['/health/', '/admin/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Only check for authenticated API requests
        if not request.path.startswith('/api/'):
            return None
        
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None
        
        # Check auth server health
        if not self.auth_client.health_check():
            logger.error("Auth server is unavailable")
            
            # You might want to implement fallback logic here
            # For now, we'll let the request continue and let authentication fail naturally
            request.auth_server_unavailable = True
        
        return None


class TenantSelectionMiddleware(MiddlewareMixin):
    """
    Middleware for handling multi-tenant selection when user has multiple organizations
    """
    
    def process_request(self, request):
        """
        Handle tenant selection from request headers or parameters
        """
        if not getattr(settings, 'USE_ROZITECH_AUTH', False):
            return None
        
        # Get selected tenant from header or query parameter
        selected_tenant = (
            request.META.get('HTTP_X_TENANT_ID') or 
            request.GET.get('tenant_id') or
            request.POST.get('tenant_id')
        )
        
        if selected_tenant:
            # Validate that user has access to this tenant
            user_organizations = getattr(request, 'user_organizations', [])
            
            valid_tenant = any(
                org.get('org_id') == selected_tenant 
                for org in user_organizations
            )
            
            if valid_tenant:
                # Override the default tenant with selected one
                selected_org = next(
                    (org for org in user_organizations 
                     if org.get('org_id') == selected_tenant), 
                    None
                )
                
                if selected_org:
                    request.tenant_id = selected_org.get('org_id')
                    request.tenant_name = selected_org.get('org_name')
                    request.tenant_slug = selected_org.get('org_slug')
                    request.user_role = selected_org.get('role')
                    request.selected_tenant = selected_tenant
                    
                    logger.debug(f"User selected tenant: {request.tenant_name}")
            else:
                logger.warning(f"User attempted to access unauthorized tenant: {selected_tenant}")
                return JsonResponse({
                    'error': 'Unauthorized access to tenant',
                    'tenant_id': selected_tenant
                }, status=403)
        
        return None