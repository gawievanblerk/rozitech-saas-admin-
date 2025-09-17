"""
API views for service management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django_filters import rest_framework as filters

from apps.services.models import (
    Service, ServiceCategory, TenantService,
    ServiceMetric, ServiceAlert
)
from apps.services.serializers import (
    ServiceSerializer, ServiceListSerializer,
    ServiceCategorySerializer, TenantServiceSerializer,
    TenantServiceListSerializer, ProvisionServiceSerializer,
    ServiceActionSerializer, ScaleServiceSerializer,
    ServiceMetricSerializer, ServiceAlertSerializer,
    AcknowledgeAlertSerializer
)
from apps.services.tasks import (
    provision_service, deprovision_service,
    check_service_health, scale_service,
    perform_service_backup
)
from apps.services.webhooks import WebhookDispatcher


class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for service categories"""
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Filter active categories"""
        return self.queryset.annotate(
            service_count=Count('services', filter=Q(services__is_public=True))
        ).filter(service_count__gt=0)


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for available services"""
    queryset = Service.objects.filter(is_public=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['category', 'type', 'status', 'is_featured']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ServiceListSerializer
        return ServiceSerializer
    
    def get_queryset(self):
        """Filter available services"""
        queryset = self.queryset.filter(
            status__in=['beta', 'active']
        ).select_related('category').prefetch_related('dependencies')
        
        # Filter by search query
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def check_availability(self, request, slug=None):
        """Check if service is available for provisioning"""
        service = self.get_object()
        
        # Check tenant quota
        tenant = request.tenant
        tenant_services = TenantService.objects.filter(
            tenant=tenant,
            status__in=['provisioning', 'active', 'suspended']
        ).count()
        
        # Check if tenant has reached service limit
        max_services = getattr(tenant, 'max_services', 10)
        can_provision = tenant_services < max_services
        
        # Check dependencies
        missing_dependencies = []
        for dependency in service.dependencies.filter(dependency_type='required'):
            if not TenantService.objects.filter(
                tenant=tenant,
                service=dependency.depends_on,
                status='active'
            ).exists():
                missing_dependencies.append({
                    'service': dependency.depends_on.name,
                    'type': dependency.dependency_type
                })
        
        return Response({
            'available': service.is_available and can_provision and not missing_dependencies,
            'service_available': service.is_available,
            'quota_available': can_provision,
            'current_services': tenant_services,
            'max_services': max_services,
            'missing_dependencies': missing_dependencies
        })


class TenantServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for tenant services"""
    serializer_class = TenantServiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['service', 'status', 'health_status']
    
    def get_queryset(self):
        """Filter services for current tenant"""
        return TenantService.objects.filter(
            tenant=self.request.tenant
        ).select_related('service', 'tenant').order_by('-provisioned_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TenantServiceListSerializer
        elif self.action == 'provision':
            return ProvisionServiceSerializer
        elif self.action == 'scale':
            return ScaleServiceSerializer
        elif self.action == 'service_action':
            return ServiceActionSerializer
        return TenantServiceSerializer
    
    @action(detail=False, methods=['post'])
    def provision(self, request):
        """Provision a new service instance"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        tenant = request.tenant
        
        # Dispatch provisioning webhook
        webhook_dispatcher = WebhookDispatcher()
        webhook_dispatcher.dispatch_provisioning_started(
            str(tenant.id),
            str(data['service_id']),
            data['instance_name']
        )
        
        # Create configuration
        configuration = {
            'environment': 'production',
            'resource_allocation': {
                'cpu_cores': float(data.get('allocated_cpu_cores', 0.5)),
                'memory_gb': float(data.get('allocated_memory_gb', 1.0)),
                'storage_gb': float(data.get('allocated_storage_gb', 5.0))
            },
            'custom_config': data.get('configuration', {}),
            'auto_scaling_enabled': data.get('auto_scaling_enabled', True),
            'monitoring_enabled': True,
            'backup_enabled': True
        }
        
        # Start async provisioning task
        task = provision_service.apply_async(
            kwargs={
                'tenant_id': str(tenant.id),
                'service_id': str(data['service_id']),
                'instance_name': data['instance_name'],
                'configuration': configuration
            }
        )
        
        return Response({
            'message': 'Service provisioning started',
            'task_id': task.id,
            'instance_name': data['instance_name']
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def deprovision(self, request, pk=None):
        """Deprovision a service instance"""
        tenant_service = self.get_object()
        
        if tenant_service.status == 'deprovisioned':
            return Response({
                'error': 'Service is already deprovisioned'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Start async deprovisioning task
        task = deprovision_service.apply_async(
            kwargs={'tenant_service_id': str(tenant_service.id)}
        )
        
        # Dispatch webhook
        webhook_dispatcher = WebhookDispatcher()
        webhook_dispatcher.dispatch_service_deprovisioned(str(tenant_service.id))
        
        return Response({
            'message': 'Service deprovisioning started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def service_action(self, request, pk=None):
        """Perform an action on a service instance"""
        tenant_service = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        reason = serializer.validated_data.get('reason', '')
        
        webhook_dispatcher = WebhookDispatcher()
        
        if action_type == 'suspend':
            tenant_service.status = 'suspended'
            tenant_service.suspended_at = timezone.now()
            tenant_service.save()
            webhook_dispatcher.dispatch_service_suspended(
                str(tenant_service.id), reason
            )
            message = 'Service suspended'
            
        elif action_type == 'resume':
            tenant_service.status = 'active'
            tenant_service.suspended_at = None
            tenant_service.save()
            webhook_dispatcher.dispatch_service_resumed(str(tenant_service.id))
            message = 'Service resumed'
            
        elif action_type == 'restart':
            # TODO: Implement restart logic
            message = 'Service restart initiated'
            
        elif action_type == 'backup':
            task = perform_service_backup.apply_async(
                kwargs={'tenant_service_id': str(tenant_service.id)}
            )
            return Response({
                'message': 'Backup started',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)
            
        elif action_type == 'restore':
            # TODO: Implement restore logic
            message = 'Service restore initiated'
        
        return Response({'message': message})
    
    @action(detail=True, methods=['post'])
    def scale(self, request, pk=None):
        """Scale a service instance"""
        tenant_service = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.instance = tenant_service
        serializer.is_valid(raise_exception=True)
        
        if not tenant_service.auto_scaling_enabled:
            return Response({
                'error': 'Auto-scaling is not enabled for this service'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        target_instances = serializer.validated_data['target_instances']
        old_instances = tenant_service.current_instances
        
        # Start async scaling task
        task = scale_service.apply_async(
            kwargs={
                'tenant_service_id': str(tenant_service.id),
                'target_instances': target_instances
            }
        )
        
        # Dispatch webhook
        webhook_dispatcher = WebhookDispatcher()
        webhook_dispatcher.dispatch_scaling_event(
            str(tenant_service.id),
            old_instances,
            target_instances,
            'Manual scaling request'
        )
        
        return Response({
            'message': f'Scaling service to {target_instances} instances',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['post'])
    def check_health(self, request, pk=None):
        """Trigger health check for a service instance"""
        tenant_service = self.get_object()
        
        # Start async health check task
        task = check_service_health.apply_async(
            kwargs={'tenant_service_id': str(tenant_service.id)}
        )
        
        return Response({
            'message': 'Health check initiated',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get metrics for a service instance"""
        tenant_service = self.get_object()
        
        # Get time range from query params
        hours = int(request.query_params.get('hours', 24))
        metric_type = request.query_params.get('type')
        
        since = timezone.now() - timezone.timedelta(hours=hours)
        
        queryset = ServiceMetric.objects.filter(
            tenant_service=tenant_service,
            timestamp__gte=since
        )
        
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        # Aggregate metrics by type
        metrics = queryset.values('metric_type').annotate(
            avg_value=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value'),
            latest_value=Max('value')
        )
        
        # Get detailed metrics if requested
        if request.query_params.get('detailed') == 'true':
            detailed_metrics = ServiceMetricSerializer(
                queryset.order_by('-timestamp')[:1000],
                many=True
            ).data
        else:
            detailed_metrics = []
        
        return Response({
            'summary': list(metrics),
            'detailed': detailed_metrics
        })
    
    @action(detail=True, methods=['get'])
    def alerts(self, request, pk=None):
        """Get alerts for a service instance"""
        tenant_service = self.get_object()
        
        queryset = ServiceAlert.objects.filter(
            tenant_service=tenant_service
        ).order_by('-last_occurred')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by severity if provided
        severity_filter = request.query_params.get('severity')
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)
        
        serializer = ServiceAlertSerializer(queryset[:50], many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get provisioning logs for a service instance"""
        tenant_service = self.get_object()
        
        return Response({
            'instance_name': tenant_service.instance_name,
            'status': tenant_service.status,
            'logs': tenant_service.provisioning_logs
        })


class ServiceAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for service alerts"""
    serializer_class = ServiceAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['severity', 'status', 'alert_type']
    
    def get_queryset(self):
        """Filter alerts for current tenant"""
        return ServiceAlert.objects.filter(
            tenant_service__tenant=self.request.tenant
        ).select_related('tenant_service').order_by('-last_occurred')
    
    @action(detail=False, methods=['post'])
    def acknowledge(self, request):
        """Acknowledge multiple alerts"""
        serializer = AcknowledgeAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        alert_ids = serializer.validated_data['alert_ids']
        alerts = ServiceAlert.objects.filter(
            id__in=alert_ids,
            tenant_service__tenant=request.tenant,
            status='active'
        )
        
        updated_count = 0
        for alert in alerts:
            alert.acknowledge(request.user)
            updated_count += 1
        
        return Response({
            'message': f'{updated_count} alerts acknowledged'
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert"""
        alert = self.get_object()
        
        if alert.status == 'resolved':
            return Response({
                'error': 'Alert is already resolved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        alert.resolve()
        
        return Response({
            'message': 'Alert resolved'
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get alert summary for tenant"""
        tenant_alerts = ServiceAlert.objects.filter(
            tenant_service__tenant=request.tenant
        )
        
        summary = {
            'total': tenant_alerts.count(),
            'active': tenant_alerts.filter(status='active').count(),
            'by_severity': {},
            'by_type': {}
        }
        
        # Count by severity
        for severity in ['info', 'warning', 'error', 'critical']:
            summary['by_severity'][severity] = tenant_alerts.filter(
                severity=severity,
                status='active'
            ).count()
        
        # Count by type
        alert_types = tenant_alerts.values_list('alert_type', flat=True).distinct()
        for alert_type in alert_types:
            summary['by_type'][alert_type] = tenant_alerts.filter(
                alert_type=alert_type,
                status='active'
            ).count()
        
        return Response(summary)


from django.db.models import Max