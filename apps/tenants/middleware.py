"""
Custom middleware for tenant routing
"""
from django_tenants.middleware.main import TenantMainMiddleware as BaseTenantMiddleware

class TenantMainMiddleware(BaseTenantMiddleware):
    """
    Custom tenant middleware that bypasses tenant resolution for specific URLs
    like webhooks that don't need tenant context.
    """
    
    # URLs that should bypass tenant resolution
    BYPASS_URLS = [
        '/api/subscriptions/webhooks/stripe/',
        '/api/subscriptions/test/stripe/',
        '/health/',
        '/api/health/',
    ]
    
    def process_request(self, request):
        # Check if the current path should bypass tenant middleware
        if any(request.path.startswith(url) for url in self.BYPASS_URLS):
            # Skip tenant resolution completely
            return None
        
        # Call parent's process_request for normal tenant URLs
        return super().process_request(request)
