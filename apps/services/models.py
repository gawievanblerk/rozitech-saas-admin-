"""
Service catalog and provisioning models
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.utils import timezone


class ServiceCategory(models.Model):
    """
    Categories for organizing services
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class or filename")
    
    # Display order
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services_category'
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Service Categories'
    
    def __str__(self):
        return self.name


class Service(models.Model):
    """
    Available services in the platform catalog
    """
    TYPE_CHOICES = [
        ('saas', 'SaaS Application'),
        ('api', 'API Service'),
        ('integration', 'Integration Service'),
        ('addon', 'Add-on Feature'),
        ('infrastructure', 'Infrastructure Service'),
    ]
    
    STATUS_CHOICES = [
        ('development', 'Development'),
        ('beta', 'Beta'),
        ('active', 'Active'),
        ('deprecated', 'Deprecated'),
        ('discontinued', 'Discontinued'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic information
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=255)
    
    # Categorization
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='saas')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='development')
    
    # Versioning
    version = models.CharField(max_length=20, default='1.0.0')
    api_version = models.CharField(max_length=20, blank=True)
    
    # Technical details
    repository_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    api_base_url = models.URLField(blank=True)
    health_check_url = models.URLField(blank=True)
    
    # Resource requirements
    min_cpu_cores = models.DecimalField(max_digits=4, decimal_places=2, default=0.5)
    min_memory_gb = models.DecimalField(max_digits=6, decimal_places=2, default=1.0)
    min_storage_gb = models.DecimalField(max_digits=8, decimal_places=2, default=5.0)
    
    # Scaling configuration
    supports_auto_scaling = models.BooleanField(default=True)
    max_instances = models.PositiveIntegerField(default=10)
    min_instances = models.PositiveIntegerField(default=1)
    
    # Feature flags
    requires_database = models.BooleanField(default=True)
    requires_redis = models.BooleanField(default=False)
    requires_file_storage = models.BooleanField(default=True)
    supports_multitenancy = models.BooleanField(default=True)
    
    # Deployment configuration
    docker_image = models.CharField(max_length=255, blank=True)
    environment_variables = models.JSONField(default=dict, blank=True)
    startup_command = models.TextField(blank=True)
    
    # Pricing (if different from standard plans)
    has_custom_pricing = models.BooleanField(default=False)
    base_monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_user_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)
    integrations = models.JSONField(default=list, blank=True)
    
    # Display
    logo_url = models.URLField(blank=True)
    screenshot_urls = models.JSONField(default=list, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'services_service'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['status', 'is_public']),
            models.Index(fields=['category', 'type']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    @property
    def is_available(self):
        """Check if service is available for provisioning"""
        return self.status in ['beta', 'active'] and self.is_public


class TenantService(models.Model):
    """
    Services provisioned for specific tenants
    """
    STATUS_CHOICES = [
        ('provisioning', 'Provisioning'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('maintenance', 'Maintenance'),
        ('failed', 'Failed'),
        ('deprovisioning', 'Deprovisioning'),
        ('deprovisioned', 'Deprovisioned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    tenant = models.ForeignKey('tenants.Organization', on_delete=models.CASCADE, related_name='tenant_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='tenant_instances')
    
    # Instance details
    instance_name = models.CharField(max_length=100, help_text="Unique name for this instance")
    subdomain = models.CharField(max_length=100, blank=True, help_text="Custom subdomain if applicable")
    custom_domain = models.CharField(max_length=255, blank=True)
    
    # Status and configuration
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='provisioning')
    configuration = models.JSONField(default=dict, help_text="Service-specific configuration")
    environment_variables = models.JSONField(default=dict, blank=True)
    
    # Resource allocation
    allocated_cpu_cores = models.DecimalField(max_digits=4, decimal_places=2, default=0.5)
    allocated_memory_gb = models.DecimalField(max_digits=6, decimal_places=2, default=1.0)
    allocated_storage_gb = models.DecimalField(max_digits=8, decimal_places=2, default=5.0)
    
    # Scaling settings
    auto_scaling_enabled = models.BooleanField(default=True)
    min_instances = models.PositiveIntegerField(default=1)
    max_instances = models.PositiveIntegerField(default=3)
    current_instances = models.PositiveIntegerField(default=1)
    
    # Database and storage
    database_name = models.CharField(max_length=100, blank=True)
    database_url = models.URLField(blank=True)
    storage_bucket = models.CharField(max_length=255, blank=True)
    
    # Access information
    internal_url = models.URLField(blank=True, help_text="Internal service URL")
    public_url = models.URLField(blank=True, help_text="Public access URL")
    admin_url = models.URLField(blank=True, help_text="Admin interface URL")
    api_key = models.CharField(max_length=255, blank=True)
    
    # Health monitoring
    last_health_check = models.DateTimeField(blank=True, null=True)
    health_status = models.CharField(max_length=20, default='unknown')
    uptime_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Billing
    monthly_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_based_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    provisioned_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(blank=True, null=True)
    suspended_at = models.DateTimeField(blank=True, null=True)
    deprovisioned_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    provisioning_logs = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'services_tenant_service'
        unique_together = ['tenant', 'service', 'instance_name']
        ordering = ['-provisioned_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['service', 'status']),
            models.Index(fields=['status', 'health_status']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.service.name} ({self.instance_name})"
    
    @property
    def is_active(self):
        """Check if service instance is active"""
        return self.status == 'active'
    
    @property
    def is_healthy(self):
        """Check if service instance is healthy"""
        return self.health_status in ['healthy', 'ok']
    
    def calculate_monthly_cost(self):
        """Calculate total monthly cost for this service instance"""
        base_cost = self.service.base_monthly_cost if self.service.has_custom_pricing else 0
        
        # Add per-user costs if applicable
        if self.service.per_user_cost > 0:
            user_count = self.tenant.current_users_count
            user_cost = user_count * self.service.per_user_cost
        else:
            user_cost = 0
        
        # Add resource-based costs (simplified calculation)
        resource_cost = (
            self.allocated_cpu_cores * 10 +  # $10 per CPU core
            self.allocated_memory_gb * 5 +   # $5 per GB RAM
            self.allocated_storage_gb * 0.5  # $0.50 per GB storage
        )
        
        return base_cost + user_cost + resource_cost + self.usage_based_cost


class ServiceDependency(models.Model):
    """
    Dependencies between services
    """
    DEPENDENCY_TYPE_CHOICES = [
        ('required', 'Required'),
        ('optional', 'Optional'),
        ('recommended', 'Recommended'),
        ('conflicting', 'Conflicting'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='dependents')
    dependency_type = models.CharField(max_length=20, choices=DEPENDENCY_TYPE_CHOICES, default='required')
    
    # Version constraints
    min_version = models.CharField(max_length=20, blank=True)
    max_version = models.CharField(max_length=20, blank=True)
    
    # Description
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'services_dependency'
        unique_together = ['service', 'depends_on']
        verbose_name_plural = 'Service Dependencies'
    
    def __str__(self):
        return f"{self.service.name} depends on {self.depends_on.name} ({self.dependency_type})"


class ServiceMetric(models.Model):
    """
    Performance and usage metrics for service instances
    """
    METRIC_TYPE_CHOICES = [
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('disk_usage', 'Disk Usage'),
        ('network_in', 'Network In'),
        ('network_out', 'Network Out'),
        ('requests_per_minute', 'Requests per Minute'),
        ('response_time', 'Response Time'),
        ('error_rate', 'Error Rate'),
        ('active_users', 'Active Users'),
        ('storage_used', 'Storage Used'),
        ('api_calls', 'API Calls'),
        ('custom', 'Custom Metric'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    tenant_service = models.ForeignKey(TenantService, on_delete=models.CASCADE, related_name='metrics')
    
    # Metric details
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPE_CHOICES)
    value = models.DecimalField(max_digits=15, decimal_places=4)
    unit = models.CharField(max_length=20, help_text="e.g., %, MB, ms, count")
    
    # Time period
    timestamp = models.DateTimeField(default=timezone.now)
    aggregation_period = models.CharField(
        max_length=20, 
        default='1m',
        help_text="e.g., 1m, 5m, 1h, 1d"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'services_metric'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant_service', 'metric_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.tenant_service} - {self.metric_type}: {self.value} {self.unit}"


class ServiceAlert(models.Model):
    """
    Alerts and notifications for service issues
    """
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    tenant_service = models.ForeignKey(TenantService, on_delete=models.CASCADE, related_name='alerts')
    
    # Alert details
    title = models.CharField(max_length=255)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='warning')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Categorization
    alert_type = models.CharField(max_length=50)  # e.g., 'high_cpu', 'disk_full', 'service_down'
    source = models.CharField(max_length=100, help_text="Source system that generated the alert")
    
    # Timing
    first_occurred = models.DateTimeField(default=timezone.now)
    last_occurred = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(blank=True, null=True)
    occurrence_count = models.PositiveIntegerField(default=1)
    
    # Response
    acknowledged_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'services_alert'
        ordering = ['-last_occurred']
        indexes = [
            models.Index(fields=['tenant_service', 'status', 'severity']),
            models.Index(fields=['status', 'severity', 'last_occurred']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.tenant_service} ({self.severity})"
    
    def acknowledge(self, user):
        """Acknowledge the alert"""
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self):
        """Mark alert as resolved"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()