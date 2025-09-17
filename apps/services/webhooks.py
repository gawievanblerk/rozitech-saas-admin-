"""
Webhook dispatcher for service provisioning events
"""
import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
import hashlib
import hmac
import json

from apps.tenants.models import Organization as Tenant

logger = logging.getLogger(__name__)


class WebhookDispatcher:
    """Dispatch webhook notifications for service events"""
    
    def __init__(self):
        self.webhook_url = getattr(settings, 'WEBHOOK_URL', None)
        self.webhook_secret = getattr(settings, 'WEBHOOK_SECRET', None)
        self.timeout = getattr(settings, 'WEBHOOK_TIMEOUT', 10)
        self.max_retries = getattr(settings, 'WEBHOOK_MAX_RETRIES', 3)
    
    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for webhook payload"""
        if not self.webhook_secret:
            return ''
        
        signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f'sha256={signature}'
    
    def _send_webhook(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Send webhook notification"""
        if not self.webhook_url:
            logger.debug("No webhook URL configured, skipping webhook")
            return True
        
        payload = {
            'event': event_type,
            'timestamp': timezone.now().isoformat(),
            'data': data
        }
        
        payload_json = json.dumps(payload)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': event_type,
            'X-Webhook-Timestamp': payload['timestamp']
        }
        
        if self.webhook_secret:
            headers['X-Webhook-Signature'] = self._generate_signature(payload_json)
        
        for retry in range(self.max_retries):
            try:
                response = requests.post(
                    self.webhook_url,
                    data=payload_json,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook sent successfully: {event_type}")
                    return True
                else:
                    logger.warning(
                        f"Webhook failed with status {response.status_code}: {response.text}"
                    )
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Webhook timeout (attempt {retry + 1}/{self.max_retries})")
            except requests.exceptions.RequestException as e:
                logger.error(f"Webhook error: {str(e)}")
            
            if retry < self.max_retries - 1:
                import time
                time.sleep(2 ** retry)  # Exponential backoff
        
        logger.error(f"Webhook failed after {self.max_retries} attempts")
        return False
    
    def dispatch_provisioning_started(
        self, 
        tenant_id: str, 
        service_id: str, 
        instance_name: str
    ):
        """Dispatch webhook for provisioning started event"""
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            data = {
                'tenant_id': tenant_id,
                'tenant_name': tenant.name,
                'service_id': service_id,
                'instance_name': instance_name,
                'status': 'provisioning'
            }
            
            self._send_webhook('service.provisioning.started', data)
            
        except Tenant.DoesNotExist:
            logger.error(f"Tenant not found: {tenant_id}")
    
    def dispatch_provisioning_complete(
        self,
        tenant_id: str,
        service_id: str,
        tenant_service_id: str,
        metadata: Dict[str, Any]
    ):
        """Dispatch webhook for provisioning complete event"""
        try:
            from apps.services.models import TenantService
            
            tenant_service = TenantService.objects.get(id=tenant_service_id)
            tenant = tenant_service.tenant
            service = tenant_service.service
            
            data = {
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'service_id': str(service.id),
                'service_name': service.name,
                'tenant_service_id': tenant_service_id,
                'instance_name': tenant_service.instance_name,
                'status': 'active',
                'public_url': tenant_service.public_url,
                'admin_url': tenant_service.admin_url,
                'api_key': tenant_service.api_key,
                'metadata': metadata
            }
            
            self._send_webhook('service.provisioning.completed', data)
            
        except Exception as e:
            logger.error(f"Error dispatching provisioning complete webhook: {str(e)}")
    
    def dispatch_provisioning_failed(
        self,
        tenant_id: str,
        service_id: str,
        error_message: str
    ):
        """Dispatch webhook for provisioning failed event"""
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            
            data = {
                'tenant_id': tenant_id,
                'tenant_name': tenant.name,
                'service_id': service_id,
                'status': 'failed',
                'error': error_message
            }
            
            self._send_webhook('service.provisioning.failed', data)
            
        except Tenant.DoesNotExist:
            logger.error(f"Tenant not found: {tenant_id}")
    
    def dispatch_service_suspended(
        self,
        tenant_service_id: str,
        reason: str
    ):
        """Dispatch webhook for service suspended event"""
        try:
            from apps.services.models import TenantService
            
            tenant_service = TenantService.objects.get(id=tenant_service_id)
            
            data = {
                'tenant_id': str(tenant_service.tenant.id),
                'tenant_name': tenant_service.tenant.name,
                'service_id': str(tenant_service.service.id),
                'service_name': tenant_service.service.name,
                'tenant_service_id': tenant_service_id,
                'instance_name': tenant_service.instance_name,
                'status': 'suspended',
                'reason': reason
            }
            
            self._send_webhook('service.suspended', data)
            
        except Exception as e:
            logger.error(f"Error dispatching service suspended webhook: {str(e)}")
    
    def dispatch_service_resumed(self, tenant_service_id: str):
        """Dispatch webhook for service resumed event"""
        try:
            from apps.services.models import TenantService
            
            tenant_service = TenantService.objects.get(id=tenant_service_id)
            
            data = {
                'tenant_id': str(tenant_service.tenant.id),
                'tenant_name': tenant_service.tenant.name,
                'service_id': str(tenant_service.service.id),
                'service_name': tenant_service.service.name,
                'tenant_service_id': tenant_service_id,
                'instance_name': tenant_service.instance_name,
                'status': 'active'
            }
            
            self._send_webhook('service.resumed', data)
            
        except Exception as e:
            logger.error(f"Error dispatching service resumed webhook: {str(e)}")
    
    def dispatch_service_deprovisioned(self, tenant_service_id: str):
        """Dispatch webhook for service deprovisioned event"""
        try:
            from apps.services.models import TenantService
            
            tenant_service = TenantService.objects.get(id=tenant_service_id)
            
            data = {
                'tenant_id': str(tenant_service.tenant.id),
                'tenant_name': tenant_service.tenant.name,
                'service_id': str(tenant_service.service.id),
                'service_name': tenant_service.service.name,
                'tenant_service_id': tenant_service_id,
                'instance_name': tenant_service.instance_name,
                'status': 'deprovisioned'
            }
            
            self._send_webhook('service.deprovisioned', data)
            
        except Exception as e:
            logger.error(f"Error dispatching service deprovisioned webhook: {str(e)}")
    
    def dispatch_health_status_changed(
        self,
        tenant_service_id: str,
        old_status: str,
        new_status: str
    ):
        """Dispatch webhook for health status change event"""
        try:
            from apps.services.models import TenantService
            
            tenant_service = TenantService.objects.get(id=tenant_service_id)
            
            data = {
                'tenant_id': str(tenant_service.tenant.id),
                'tenant_name': tenant_service.tenant.name,
                'service_id': str(tenant_service.service.id),
                'service_name': tenant_service.service.name,
                'tenant_service_id': tenant_service_id,
                'instance_name': tenant_service.instance_name,
                'old_health_status': old_status,
                'new_health_status': new_status
            }
            
            self._send_webhook('service.health.changed', data)
            
        except Exception as e:
            logger.error(f"Error dispatching health status changed webhook: {str(e)}")
    
    def dispatch_alert_triggered(
        self,
        alert_id: str,
        tenant_service_id: str,
        alert_type: str,
        severity: str,
        message: str
    ):
        """Dispatch webhook for alert triggered event"""
        try:
            from apps.services.models import TenantService, ServiceAlert
            
            alert = ServiceAlert.objects.get(id=alert_id)
            tenant_service = alert.tenant_service
            
            data = {
                'alert_id': alert_id,
                'tenant_id': str(tenant_service.tenant.id),
                'tenant_name': tenant_service.tenant.name,
                'service_id': str(tenant_service.service.id),
                'service_name': tenant_service.service.name,
                'tenant_service_id': tenant_service_id,
                'instance_name': tenant_service.instance_name,
                'alert_type': alert_type,
                'severity': severity,
                'message': message
            }
            
            self._send_webhook('service.alert.triggered', data)
            
        except Exception as e:
            logger.error(f"Error dispatching alert triggered webhook: {str(e)}")
    
    def dispatch_scaling_event(
        self,
        tenant_service_id: str,
        old_instances: int,
        new_instances: int,
        reason: str
    ):
        """Dispatch webhook for scaling event"""
        try:
            from apps.services.models import TenantService
            
            tenant_service = TenantService.objects.get(id=tenant_service_id)
            
            data = {
                'tenant_id': str(tenant_service.tenant.id),
                'tenant_name': tenant_service.tenant.name,
                'service_id': str(tenant_service.service.id),
                'service_name': tenant_service.service.name,
                'tenant_service_id': tenant_service_id,
                'instance_name': tenant_service.instance_name,
                'old_instances': old_instances,
                'new_instances': new_instances,
                'reason': reason
            }
            
            self._send_webhook('service.scaling', data)
            
        except Exception as e:
            logger.error(f"Error dispatching scaling event webhook: {str(e)}")