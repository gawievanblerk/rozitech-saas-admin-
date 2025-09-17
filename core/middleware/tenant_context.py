"""
Middleware for managing tenant context across requests
"""
import threading
from django.utils.deprecation import MiddlewareMixin
from django_tenants.utils import get_tenant_model

# Thread-local storage for tenant context
_thread_local = threading.local()


class TenantContextMiddleware(MiddlewareMixin):
    """
    Middleware to store tenant information in thread-local storage
    """
    
    def process_request(self, request):
        """Store tenant in thread-local storage"""
        tenant = getattr(request, 'tenant', None)
        set_current_tenant(tenant)
        return None
    
    def process_response(self, request, response):
        """Clear tenant from thread-local storage"""
        clear_current_tenant()
        return response
    
    def process_exception(self, request, exception):
        """Clear tenant from thread-local storage on exception"""
        clear_current_tenant()
        return None


def get_current_tenant():
    """Get the current tenant from thread-local storage"""
    return getattr(_thread_local, 'tenant', None)


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage"""
    _thread_local.tenant = tenant


def clear_current_tenant():
    """Clear the current tenant from thread-local storage"""
    if hasattr(_thread_local, 'tenant'):
        delattr(_thread_local, 'tenant')


def get_current_tenant_id():
    """Get the current tenant ID"""
    tenant = get_current_tenant()
    return tenant.id if tenant else None


def get_current_tenant_schema():
    """Get the current tenant schema name"""
    tenant = get_current_tenant()
    return tenant.schema_name if tenant else None