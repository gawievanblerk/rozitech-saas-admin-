"""
Celery tasks for service provisioning and management
"""
from celery import shared_task, Task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.conf import settings
from typing import Dict, Any
import requests
import time

from apps.services.models import TenantService, Service, ServiceMetric, ServiceAlert
from apps.services.provisioning import (
    ProvisioningConfig, 
    ProvisioningFactory,
    ProvisioningResult
)
from apps.services.webhooks import WebhookDispatcher

logger = get_task_logger(__name__)


class ProvisioningTask(Task):
    """Base task class for provisioning operations"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler for task failure"""
        tenant_service_id = kwargs.get('tenant_service_id')
        if tenant_service_id:
            try:
                tenant_service = TenantService.objects.get(id=tenant_service_id)
                tenant_service.status = 'failed'
                tenant_service.save()
                
                # Create alert
                ServiceAlert.objects.create(
                    tenant_service=tenant_service,
                    title='Service Provisioning Failed',
                    message=f'Provisioning failed for {tenant_service.instance_name}: {str(exc)}',
                    severity='critical',
                    alert_type='provisioning_failure',
                    source='celery'
                )
            except TenantService.DoesNotExist:
                pass


@shared_task(base=ProvisioningTask, bind=True, max_retries=3)
def provision_service(
    self,
    tenant_id: str,
    service_id: str,
    instance_name: str,
    configuration: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Provision a new service instance for a tenant
    """
    logger.info(f"Starting service provisioning: tenant={tenant_id}, service={service_id}, instance={instance_name}")
    
    try:
        # Prepare provisioning configuration
        config = ProvisioningConfig(
            tenant_id=tenant_id,
            service_id=service_id,
            instance_name=instance_name,
            environment=configuration.get('environment', 'production') if configuration else 'production',
            resource_allocation=configuration.get('resource_allocation', {}) if configuration else {},
            custom_config=configuration.get('custom_config', {}) if configuration else {},
            auto_scaling_enabled=configuration.get('auto_scaling_enabled', True) if configuration else True,
            monitoring_enabled=configuration.get('monitoring_enabled', True) if configuration else True,
            backup_enabled=configuration.get('backup_enabled', True) if configuration else True
        )
        
        # Determine provisioning provider
        provider_type = settings.PROVISIONING_PROVIDER if hasattr(settings, 'PROVISIONING_PROVIDER') else 'docker'
        
        # Get provisioning provider
        provider = ProvisioningFactory.get_provider(provider_type, config)
        
        # Execute provisioning
        result: ProvisioningResult = provider.provision()
        
        if result.success:
            logger.info(f"Service provisioned successfully: {result.tenant_service_id}")
            
            # Send webhook notification
            webhook_dispatcher = WebhookDispatcher()
            webhook_dispatcher.dispatch_provisioning_complete(
                tenant_id,
                service_id,
                result.tenant_service_id,
                result.metadata
            )
            
            # Schedule initial health check
            check_service_health.apply_async(
                kwargs={'tenant_service_id': result.tenant_service_id},
                countdown=60  # Check after 1 minute
            )
            
            # Schedule monitoring setup
            setup_service_monitoring.apply_async(
                kwargs={'tenant_service_id': result.tenant_service_id},
                countdown=120  # Setup after 2 minutes
            )
            
            return {
                'success': True,
                'tenant_service_id': result.tenant_service_id,
                'public_url': result.public_url,
                'admin_url': result.admin_url,
                'api_key': result.api_key
            }
        else:
            logger.error(f"Service provisioning failed: {result.error_message}")
            
            # Send webhook notification
            webhook_dispatcher = WebhookDispatcher()
            webhook_dispatcher.dispatch_provisioning_failed(
                tenant_id,
                service_id,
                result.error_message
            )
            
            raise Exception(result.error_message)
            
    except Exception as e:
        logger.error(f"Provisioning task error: {str(e)}")
        
        # Retry with exponential backoff
        retry_countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=e, countdown=retry_countdown)


@shared_task
def deprovision_service(tenant_service_id: str) -> Dict[str, Any]:
    """
    Deprovision a service instance
    """
    logger.info(f"Starting service deprovisioning: {tenant_service_id}")
    
    try:
        tenant_service = TenantService.objects.get(id=tenant_service_id)
        tenant_service.status = 'deprovisioning'
        tenant_service.save()
        
        # TODO: Implement deprovisioning logic based on provider
        # This would involve:
        # 1. Backing up data if needed
        # 2. Removing containers/pods
        # 3. Cleaning up resources
        # 4. Updating DNS records
        
        # For now, just mark as deprovisioned
        tenant_service.status = 'deprovisioned'
        tenant_service.deprovisioned_at = timezone.now()
        tenant_service.save()
        
        logger.info(f"Service deprovisioned successfully: {tenant_service_id}")
        
        return {
            'success': True,
            'tenant_service_id': tenant_service_id
        }
        
    except TenantService.DoesNotExist:
        logger.error(f"TenantService not found: {tenant_service_id}")
        return {
            'success': False,
            'error': 'Service instance not found'
        }
    except Exception as e:
        logger.error(f"Deprovisioning error: {str(e)}")
        
        # Mark as failed
        try:
            tenant_service = TenantService.objects.get(id=tenant_service_id)
            tenant_service.status = 'failed'
            tenant_service.save()
        except:
            pass
        
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def check_service_health(tenant_service_id: str) -> Dict[str, Any]:
    """
    Check health status of a service instance
    """
    logger.info(f"Checking service health: {tenant_service_id}")
    
    try:
        tenant_service = TenantService.objects.get(id=tenant_service_id)
        service = tenant_service.service
        
        health_status = 'unknown'
        response_time = None
        
        # Attempt health check
        if service.health_check_url and tenant_service.internal_url:
            health_url = tenant_service.internal_url + service.health_check_url
            
            try:
                start_time = time.time()
                response = requests.get(health_url, timeout=10)
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    health_status = 'healthy'
                elif 200 < response.status_code < 500:
                    health_status = 'degraded'
                else:
                    health_status = 'unhealthy'
                    
            except requests.RequestException as e:
                health_status = 'unhealthy'
                logger.warning(f"Health check failed: {str(e)}")
        
        # Update health status
        tenant_service.health_status = health_status
        tenant_service.last_health_check = timezone.now()
        tenant_service.save()
        
        # Record metric
        if response_time:
            ServiceMetric.objects.create(
                tenant_service=tenant_service,
                metric_type='response_time',
                value=response_time,
                unit='ms'
            )
        
        # Create alert if unhealthy
        if health_status == 'unhealthy':
            # Check if there's already an active alert
            existing_alert = ServiceAlert.objects.filter(
                tenant_service=tenant_service,
                alert_type='health_check_failed',
                status='active'
            ).first()
            
            if existing_alert:
                existing_alert.last_occurred = timezone.now()
                existing_alert.occurrence_count += 1
                existing_alert.save()
            else:
                ServiceAlert.objects.create(
                    tenant_service=tenant_service,
                    title='Service Health Check Failed',
                    message=f'Health check failed for {tenant_service.instance_name}',
                    severity='error',
                    alert_type='health_check_failed',
                    source='health_monitor'
                )
        
        # Resolve alert if healthy
        elif health_status == 'healthy':
            ServiceAlert.objects.filter(
                tenant_service=tenant_service,
                alert_type='health_check_failed',
                status='active'
            ).update(
                status='resolved',
                resolved_at=timezone.now()
            )
        
        logger.info(f"Health check completed: {tenant_service_id} - {health_status}")
        
        return {
            'success': True,
            'health_status': health_status,
            'response_time': response_time
        }
        
    except TenantService.DoesNotExist:
        logger.error(f"TenantService not found: {tenant_service_id}")
        return {
            'success': False,
            'error': 'Service instance not found'
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def collect_service_metrics(tenant_service_id: str) -> Dict[str, Any]:
    """
    Collect performance metrics for a service instance
    """
    logger.info(f"Collecting metrics for service: {tenant_service_id}")
    
    try:
        tenant_service = TenantService.objects.get(id=tenant_service_id)
        
        # TODO: Implement actual metric collection based on provider
        # This would involve:
        # 1. For Docker: docker stats
        # 2. For Kubernetes: kubectl top pods
        # 3. For cloud providers: API calls to get metrics
        
        # Example placeholder metrics
        metrics = {
            'cpu_usage': 45.2,
            'memory_usage': 62.5,
            'disk_usage': 30.1,
            'network_in': 1024,
            'network_out': 2048,
            'requests_per_minute': 150
        }
        
        # Store metrics
        for metric_type, value in metrics.items():
            unit = '%' if 'usage' in metric_type else 'count'
            if 'network' in metric_type:
                unit = 'KB/s'
            
            ServiceMetric.objects.create(
                tenant_service=tenant_service,
                metric_type=metric_type,
                value=value,
                unit=unit
            )
        
        # Check for threshold violations and create alerts
        if metrics.get('cpu_usage', 0) > 80:
            ServiceAlert.objects.create(
                tenant_service=tenant_service,
                title='High CPU Usage',
                message=f"CPU usage is at {metrics['cpu_usage']}%",
                severity='warning',
                alert_type='high_cpu',
                source='metrics_collector'
            )
        
        if metrics.get('memory_usage', 0) > 90:
            ServiceAlert.objects.create(
                tenant_service=tenant_service,
                title='High Memory Usage',
                message=f"Memory usage is at {metrics['memory_usage']}%",
                severity='error',
                alert_type='high_memory',
                source='metrics_collector'
            )
        
        logger.info(f"Metrics collected successfully: {tenant_service_id}")
        
        return {
            'success': True,
            'metrics': metrics
        }
        
    except TenantService.DoesNotExist:
        logger.error(f"TenantService not found: {tenant_service_id}")
        return {
            'success': False,
            'error': 'Service instance not found'
        }
    except Exception as e:
        logger.error(f"Metric collection error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def setup_service_monitoring(tenant_service_id: str) -> Dict[str, Any]:
    """
    Setup monitoring for a newly provisioned service
    """
    logger.info(f"Setting up monitoring for service: {tenant_service_id}")
    
    try:
        tenant_service = TenantService.objects.get(id=tenant_service_id)
        
        # Schedule periodic health checks
        from django_celery_beat.models import PeriodicTask, IntervalSchedule
        
        # Create interval schedule (every 5 minutes)
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES
        )
        
        # Create periodic task for health checks
        PeriodicTask.objects.create(
            interval=schedule,
            name=f'health_check_{tenant_service_id}',
            task='apps.services.tasks.check_service_health',
            kwargs={'tenant_service_id': str(tenant_service_id)}
        )
        
        # Create periodic task for metric collection (every 1 minute)
        metric_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES
        )
        
        PeriodicTask.objects.create(
            interval=metric_schedule,
            name=f'collect_metrics_{tenant_service_id}',
            task='apps.services.tasks.collect_service_metrics',
            kwargs={'tenant_service_id': str(tenant_service_id)}
        )
        
        logger.info(f"Monitoring setup completed: {tenant_service_id}")
        
        return {
            'success': True,
            'tenant_service_id': tenant_service_id
        }
        
    except TenantService.DoesNotExist:
        logger.error(f"TenantService not found: {tenant_service_id}")
        return {
            'success': False,
            'error': 'Service instance not found'
        }
    except Exception as e:
        logger.error(f"Monitoring setup error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def scale_service(tenant_service_id: str, target_instances: int) -> Dict[str, Any]:
    """
    Scale a service instance up or down
    """
    logger.info(f"Scaling service {tenant_service_id} to {target_instances} instances")
    
    try:
        tenant_service = TenantService.objects.get(id=tenant_service_id)
        
        if not tenant_service.auto_scaling_enabled:
            raise Exception("Auto-scaling is not enabled for this service")
        
        if target_instances < tenant_service.min_instances:
            target_instances = tenant_service.min_instances
        elif target_instances > tenant_service.max_instances:
            target_instances = tenant_service.max_instances
        
        # TODO: Implement actual scaling based on provider
        # This would involve:
        # 1. For Docker: docker-compose scale or Swarm
        # 2. For Kubernetes: kubectl scale deployment
        # 3. For cloud providers: API calls to scale
        
        # Update instance count
        tenant_service.current_instances = target_instances
        tenant_service.save()
        
        logger.info(f"Service scaled successfully: {tenant_service_id}")
        
        return {
            'success': True,
            'current_instances': target_instances
        }
        
    except TenantService.DoesNotExist:
        logger.error(f"TenantService not found: {tenant_service_id}")
        return {
            'success': False,
            'error': 'Service instance not found'
        }
    except Exception as e:
        logger.error(f"Scaling error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def perform_service_backup(tenant_service_id: str) -> Dict[str, Any]:
    """
    Perform backup of service data
    """
    logger.info(f"Performing backup for service: {tenant_service_id}")
    
    try:
        tenant_service = TenantService.objects.get(id=tenant_service_id)
        
        # TODO: Implement actual backup based on service type
        # This would involve:
        # 1. Database backup if service has database
        # 2. File storage backup if service has storage
        # 3. Configuration backup
        
        logger.info(f"Backup completed successfully: {tenant_service_id}")
        
        return {
            'success': True,
            'backup_id': f'backup_{tenant_service_id}_{timezone.now().timestamp()}'
        }
        
    except TenantService.DoesNotExist:
        logger.error(f"TenantService not found: {tenant_service_id}")
        return {
            'success': False,
            'error': 'Service instance not found'
        }
    except Exception as e:
        logger.error(f"Backup error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }