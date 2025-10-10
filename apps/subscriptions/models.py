"""
Simplified subscription models that work with standard Django
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone


class PricingPlan(models.Model):
    """
    Pricing plans available for subscription
    """
    BILLING_INTERVAL_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
        ('one_time', 'One Time'),
    ]
    
    PLAN_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('custom', 'Custom'),
        ('enterprise', 'Enterprise'),
        ('trial', 'Trial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='ZAR')
    billing_interval = models.CharField(max_length=20, choices=BILLING_INTERVAL_CHOICES, default='monthly')
    
    # Plan configuration
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default='standard')
    trial_period_days = models.PositiveIntegerField(default=0)
    
    # Feature limits
    max_users = models.PositiveIntegerField(default=5)
    max_storage_gb = models.PositiveIntegerField(default=1)
    max_api_calls_per_month = models.PositiveIntegerField(default=1000)
    max_projects = models.PositiveIntegerField(default=1)
    
    # Features (JSON field for flexible feature configuration)
    features = models.JSONField(default=list, help_text="List of features included in this plan")
    feature_limits = models.JSONField(default=dict, help_text="Specific limits for features")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True, help_text="Whether this plan is publicly available")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_plans'
        ordering = ['price']
        verbose_name = 'Pricing Plan'
        verbose_name_plural = 'Pricing Plans'
    
    def __str__(self):
        return f"{self.name} - {self.get_billing_interval_display()}"


class Subscription(models.Model):
    """
    Subscription instances for organizations
    """
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    organization = models.OneToOneField('tenants.Organization', on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT, related_name='subscriptions')
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    product_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Product code for this subscription (e.g., 'teamspace', 'insurr')"
    )

    # Billing dates
    started_at = models.DateTimeField(default=timezone.now)
    trial_end_date = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    # Payment information
    next_billing_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
    # Usage tracking
    current_usage = models.JSONField(default=dict, help_text="Current usage metrics")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
    
    def __str__(self):
        return f"{self.organization.name} - {self.plan.name} ({self.status})"


class Invoice(models.Model):
    """
    Invoices generated for subscriptions
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)
    
    # Relationships
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    organization = models.ForeignKey('tenants.Organization', on_delete=models.CASCADE, related_name='invoices')
    
    # Invoice details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    
    # Billing period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Payment information
    due_date = models.DateTimeField()
    paid_at = models.DateTimeField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    line_items = models.JSONField(default=list)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.organization.name}"