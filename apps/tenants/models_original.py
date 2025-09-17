"""
Tenant management models for multi-tenant SaaS architecture
"""
from django.db import models
from django.contrib.auth.models import User
from django_tenants.models import TenantMixin, DomainMixin
from django.core.validators import RegexValidator
import uuid


class Tenant(TenantMixin):
    """
    Multi-tenant model representing a customer organization
    """
    TIER_CHOICES = [
        ('free', 'Free Tier'),
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('trial', 'Trial'),
        ('pending', 'Pending Setup'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Organization name")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly identifier")
    
    # Contact Information
    email = models.EmailField(help_text="Primary contact email")
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, default='ZA', help_text="ISO 3166-1 alpha-2 country code")
    
    # Business Information
    company_registration = models.CharField(max_length=50, blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True)
    
    # Subscription & Status
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=True)
    
    # Resource Limits
    max_users = models.PositiveIntegerField(default=5)
    max_storage_gb = models.PositiveIntegerField(default=1)
    max_api_calls_per_month = models.PositiveIntegerField(default=1000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    trial_end_date = models.DateTimeField(blank=True, null=True)
    last_activity = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    custom_settings = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    # Default schema_name is required by django-tenants
    auto_create_schema = True
    auto_drop_schema = True
    
    class Meta:
        db_table = 'tenants_tenant'
        ordering = ['name']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['tier']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.schema_name})"
    
    @property
    def is_trial(self):
        """Check if tenant is in trial period"""
        return self.status == 'trial'
    
    @property
    def current_users_count(self):
        """Get current number of users for this tenant"""
        from django.contrib.auth.models import User
        return User.objects.filter(tenant=self).count()
    
    @property
    def storage_usage_gb(self):
        """Calculate current storage usage in GB"""
        # This would typically query file storage or database size
        return 0.0
    
    def get_feature_limits(self):
        """Get feature limits based on tier"""
        limits = {
            'free': {
                'max_users': 5,
                'max_storage_gb': 1,
                'max_api_calls_per_month': 1000,
                'features': ['basic_support'],
            },
            'starter': {
                'max_users': 25,
                'max_storage_gb': 10,
                'max_api_calls_per_month': 10000,
                'features': ['email_support', 'basic_analytics'],
            },
            'professional': {
                'max_users': 100,
                'max_storage_gb': 50,
                'max_api_calls_per_month': 100000,
                'features': ['priority_support', 'advanced_analytics', 'api_access'],
            },
            'enterprise': {
                'max_users': 1000,
                'max_storage_gb': 500,
                'max_api_calls_per_month': 1000000,
                'features': ['dedicated_support', 'custom_integrations', 'sla'],
            },
        }
        return limits.get(self.tier, limits['free'])


class Domain(DomainMixin):
    """
    Domain model for tenant access
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='domains')
    
    class Meta:
        db_table = 'tenants_domain'


class TenantUser(models.Model):
    """
    Relationship between users and tenants with role management
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tenant_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    
    # Permissions
    permissions = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'tenants_tenant_user'
        unique_together = ['tenant', 'user']
        indexes = [
            models.Index(fields=['tenant', 'role']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} @ {self.tenant.name} ({self.role})"
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        role_permissions = {
            'owner': ['*'],  # All permissions
            'admin': [
                'manage_users', 'manage_billing', 'manage_settings',
                'view_analytics', 'manage_integrations'
            ],
            'manager': [
                'view_users', 'manage_content', 'view_analytics'
            ],
            'user': [
                'view_content', 'edit_own_content'
            ],
            'viewer': [
                'view_content'
            ],
        }
        
        default_permissions = role_permissions.get(self.role, [])
        custom_permissions = self.permissions or []
        
        # Check if user has all permissions (owner)
        if '*' in default_permissions:
            return True
        
        # Check specific permissions
        return permission in default_permissions or permission in custom_permissions


class TenantInvitation(models.Model):
    """
    Invitations for users to join a tenant
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=TenantUser.ROLE_CHOICES, default='user')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'tenants_invitation'
        unique_together = ['tenant', 'email']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Invitation for {self.email} to {self.tenant.name}"
    
    @property
    def is_expired(self):
        """Check if invitation has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def accept(self, user):
        """Accept the invitation and create tenant user relationship"""
        if self.is_expired:
            raise ValueError("Invitation has expired")
        
        if self.status != 'pending':
            raise ValueError("Invitation is not pending")
        
        # Create tenant user
        tenant_user, created = TenantUser.objects.get_or_create(
            tenant=self.tenant,
            user=user,
            defaults={'role': self.role}
        )
        
        # Update invitation status
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        return tenant_user