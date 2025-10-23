"""
Tenant models with django-tenants support
"""
from django.db import models
from django.contrib.auth.models import User
from django_tenants.models import TenantMixin, DomainMixin
import uuid


class Organization(TenantMixin):
    """
    Organization model with multi-tenant support via TenantMixin
    """
    # TenantMixin fields (explicitly defined to match migration)
    auto_create_schema = models.BooleanField(default=True)
    auto_drop_schema = models.BooleanField(default=False)

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
    schema_name = models.CharField(max_length=63, unique=True, blank=True, null=True, help_text="PostgreSQL schema name for tenant isolation")
    
    # Contact Information
    email = models.EmailField(help_text="Primary contact email")
    phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default='ZA', help_text="ISO 3166-1 alpha-2 country code")
    
    # Business Information
    company_registration = models.CharField(max_length=50, blank=True, null=True)
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
    
    # Metadata
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
    
    def __str__(self):
        return self.name


class OrganizationUser(models.Model):
    """
    Relationship between users and organizations with role management
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'), 
        ('manager', 'Manager'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'organization_users'
        unique_together = ['organization', 'user']
        verbose_name = 'Organization User'
        verbose_name_plural = 'Organization Users'
    
    def __str__(self):
        return f"{self.user.username} @ {self.organization.name} ({self.role})"


class Domain(models.Model):
    """
    Custom domains for organizations
    Compatible with django-tenants TENANT_DOMAIN_MODEL configuration
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Use 'tenant' field name to be compatible with django-tenants DomainMixin expectations
    tenant = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'organization_domains'
        verbose_name = 'Organization Domain'
        verbose_name_plural = 'Organization Domains'

    def __str__(self):
        return f"{self.domain} ({'Primary' if self.is_primary else 'Secondary'})"

    @property
    def organization(self):
        """Alias for tenant field to maintain backward compatibility"""
        return self.tenant

    @organization.setter
    def organization(self, value):
        """Alias setter for tenant field"""
        self.tenant = value