"""
Serializers for service management API
"""
from rest_framework import serializers
from apps.services.models import (
    Service, ServiceCategory, TenantService, 
    ServiceDependency, ServiceMetric, ServiceAlert
)


class ServiceCategorySerializer(serializers.ModelSerializer):
    """Serializer for service categories"""
    
    class Meta:
        model = ServiceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'sort_order', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ServiceDependencySerializer(serializers.ModelSerializer):
    """Serializer for service dependencies"""
    depends_on_name = serializers.CharField(source='depends_on.name', read_only=True)
    
    class Meta:
        model = ServiceDependency
        fields = [
            'id', 'depends_on', 'depends_on_name', 'dependency_type',
            'min_version', 'max_version', 'description'
        ]
        read_only_fields = ['id']


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for services"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    dependencies = ServiceDependencySerializer(many=True, read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'category_name', 'type', 'status', 'version',
            'api_version', 'repository_url', 'documentation_url',
            'api_base_url', 'health_check_url', 'min_cpu_cores',
            'min_memory_gb', 'min_storage_gb', 'supports_auto_scaling',
            'max_instances', 'min_instances', 'requires_database',
            'requires_redis', 'requires_file_storage', 'supports_multitenancy',
            'docker_image', 'environment_variables', 'startup_command',
            'has_custom_pricing', 'base_monthly_cost', 'per_user_cost',
            'tags', 'features', 'integrations', 'logo_url', 'screenshot_urls',
            'sort_order', 'is_featured', 'is_public', 'is_available',
            'dependencies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_available', 'created_at', 'updated_at']


class ServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for service listings"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'slug', 'short_description', 'category',
            'category_name', 'type', 'status', 'version', 'logo_url',
            'is_featured', 'is_available', 'base_monthly_cost'
        ]
        read_only_fields = ['id', 'is_available']


class TenantServiceSerializer(serializers.ModelSerializer):
    """Serializer for tenant services"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_version = serializers.CharField(source='service.version', read_only=True)
    service_type = serializers.CharField(source='service.type', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_healthy = serializers.BooleanField(read_only=True)
    monthly_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = TenantService
        fields = [
            'id', 'tenant', 'tenant_name', 'service', 'service_name',
            'service_version', 'service_type', 'instance_name', 'subdomain',
            'custom_domain', 'status', 'configuration', 'environment_variables',
            'allocated_cpu_cores', 'allocated_memory_gb', 'allocated_storage_gb',
            'auto_scaling_enabled', 'min_instances', 'max_instances',
            'current_instances', 'database_name', 'database_url',
            'storage_bucket', 'internal_url', 'public_url', 'admin_url',
            'api_key', 'last_health_check', 'health_status', 'uptime_percentage',
            'monthly_cost', 'usage_based_cost', 'is_active', 'is_healthy',
            'provisioned_at', 'activated_at', 'suspended_at', 'deprovisioned_at',
            'provisioning_logs', 'metadata'
        ]
        read_only_fields = [
            'id', 'database_name', 'database_url', 'storage_bucket',
            'internal_url', 'public_url', 'admin_url', 'api_key',
            'last_health_check', 'health_status', 'uptime_percentage',
            'monthly_cost', 'is_active', 'is_healthy', 'provisioned_at',
            'activated_at', 'suspended_at', 'deprovisioned_at',
            'provisioning_logs'
        ]


class TenantServiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for tenant service listings"""
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_logo = serializers.URLField(source='service.logo_url', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_healthy = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = TenantService
        fields = [
            'id', 'service', 'service_name', 'service_logo', 'instance_name',
            'status', 'health_status', 'public_url', 'is_active', 'is_healthy',
            'current_instances', 'uptime_percentage', 'provisioned_at'
        ]
        read_only_fields = fields


class ProvisionServiceSerializer(serializers.Serializer):
    """Serializer for service provisioning requests"""
    service_id = serializers.UUIDField()
    instance_name = serializers.CharField(max_length=100)
    subdomain = serializers.CharField(max_length=100, required=False, allow_blank=True)
    custom_domain = serializers.CharField(max_length=255, required=False, allow_blank=True)
    configuration = serializers.JSONField(required=False, default=dict)
    environment_variables = serializers.JSONField(required=False, default=dict)
    allocated_cpu_cores = serializers.DecimalField(
        max_digits=4, decimal_places=2, required=False, default=0.5
    )
    allocated_memory_gb = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, default=1.0
    )
    allocated_storage_gb = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, default=5.0
    )
    auto_scaling_enabled = serializers.BooleanField(default=True)
    min_instances = serializers.IntegerField(default=1, min_value=1)
    max_instances = serializers.IntegerField(default=3, min_value=1)
    
    def validate_instance_name(self, value):
        """Validate instance name is unique for tenant"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            if TenantService.objects.filter(
                tenant=request.tenant,
                instance_name=value
            ).exists():
                raise serializers.ValidationError(
                    "Instance name already exists for this tenant"
                )
        return value
    
    def validate(self, data):
        """Validate provisioning request"""
        # Validate service exists and is available
        try:
            service = Service.objects.get(id=data['service_id'])
            if not service.is_available:
                raise serializers.ValidationError(
                    "Service is not available for provisioning"
                )
        except Service.DoesNotExist:
            raise serializers.ValidationError("Service not found")
        
        # Validate resource allocation meets minimums
        if data.get('allocated_cpu_cores', 0) < service.min_cpu_cores:
            data['allocated_cpu_cores'] = service.min_cpu_cores
        
        if data.get('allocated_memory_gb', 0) < service.min_memory_gb:
            data['allocated_memory_gb'] = service.min_memory_gb
        
        if data.get('allocated_storage_gb', 0) < service.min_storage_gb:
            data['allocated_storage_gb'] = service.min_storage_gb
        
        # Validate scaling limits
        if data.get('max_instances', 1) < data.get('min_instances', 1):
            raise serializers.ValidationError(
                "Maximum instances must be greater than or equal to minimum instances"
            )
        
        return data


class ServiceActionSerializer(serializers.Serializer):
    """Serializer for service actions (suspend, resume, etc.)"""
    action = serializers.ChoiceField(choices=[
        'suspend', 'resume', 'restart', 'backup', 'restore'
    ])
    reason = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False, default=dict)


class ScaleServiceSerializer(serializers.Serializer):
    """Serializer for service scaling requests"""
    target_instances = serializers.IntegerField(min_value=1)
    
    def validate_target_instances(self, value):
        """Validate target instances within limits"""
        instance = self.instance
        if instance:
            if value < instance.min_instances:
                raise serializers.ValidationError(
                    f"Cannot scale below minimum instances ({instance.min_instances})"
                )
            if value > instance.max_instances:
                raise serializers.ValidationError(
                    f"Cannot scale above maximum instances ({instance.max_instances})"
                )
        return value


class ServiceMetricSerializer(serializers.ModelSerializer):
    """Serializer for service metrics"""
    
    class Meta:
        model = ServiceMetric
        fields = [
            'id', 'tenant_service', 'metric_type', 'value', 'unit',
            'timestamp', 'aggregation_period', 'metadata'
        ]
        read_only_fields = ['id']


class ServiceAlertSerializer(serializers.ModelSerializer):
    """Serializer for service alerts"""
    tenant_service_name = serializers.CharField(
        source='tenant_service.instance_name', read_only=True
    )
    
    class Meta:
        model = ServiceAlert
        fields = [
            'id', 'tenant_service', 'tenant_service_name', 'title',
            'message', 'severity', 'status', 'alert_type', 'source',
            'first_occurred', 'last_occurred', 'resolved_at',
            'occurrence_count', 'acknowledged_by', 'acknowledged_at',
            'metadata'
        ]
        read_only_fields = [
            'id', 'first_occurred', 'last_occurred', 'resolved_at',
            'acknowledged_by', 'acknowledged_at'
        ]


class AcknowledgeAlertSerializer(serializers.Serializer):
    """Serializer for acknowledging alerts"""
    alert_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )