"""
Subscription management models for SaaS billing and plan management
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
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
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'subscriptions_pricing_plan'
        ordering = ['price']
        indexes = [
            models.Index(fields=['is_active', 'is_public']),
            models.Index(fields=['billing_interval']),
            models.Index(fields=['plan_type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_billing_interval_display()}"
    
    @property
    def monthly_price(self):
        """Convert price to monthly equivalent for comparison"""
        if self.billing_interval == 'monthly':
            return self.price
        elif self.billing_interval == 'quarterly':
            return self.price / 3
        elif self.billing_interval == 'annually':
            return self.price / 12
        return self.price
    
    def calculate_prorated_amount(self, days_used, total_days):
        """Calculate prorated amount for partial billing periods"""
        if total_days == 0:
            return Decimal('0.00')
        return (self.price * days_used) / total_days


class Subscription(models.Model):
    """
    Subscription instances for tenants
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
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(PricingPlan, on_delete=models.PROTECT, related_name='subscriptions')
    
    # Subscription details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Billing dates
    started_at = models.DateTimeField(default=timezone.now)
    trial_end_date = models.DateTimeField(blank=True, null=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    
    # Payment information
    next_billing_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
    # Usage tracking
    current_usage = models.JSONField(default=dict, help_text="Current usage metrics")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'subscriptions_subscription'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['next_billing_date']),
            models.Index(fields=['current_period_end']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name} ({self.status})"
    
    @property
    def is_trial(self):
        """Check if subscription is in trial period"""
        return self.status == 'trial' and self.trial_end_date and timezone.now() <= self.trial_end_date
    
    @property
    def is_active(self):
        """Check if subscription is active"""
        return self.status in ['trial', 'active']
    
    @property
    def days_until_renewal(self):
        """Calculate days until next billing date"""
        if not self.next_billing_date:
            return None
        delta = self.next_billing_date - timezone.now()
        return max(0, delta.days)
    
    def calculate_next_billing_date(self):
        """Calculate next billing date based on plan interval"""
        if self.plan.billing_interval == 'monthly':
            return self.current_period_end + timedelta(days=30)
        elif self.plan.billing_interval == 'quarterly':
            return self.current_period_end + timedelta(days=90)
        elif self.plan.billing_interval == 'annually':
            return self.current_period_end + timedelta(days=365)
        return self.current_period_end
    
    def cancel(self, immediate=False):
        """Cancel subscription"""
        self.cancelled_at = timezone.now()
        if immediate:
            self.status = 'cancelled'
            self.ends_at = timezone.now()
        else:
            # Cancel at end of current period
            self.ends_at = self.current_period_end
            self.auto_renew = False
        self.save()
    
    def reactivate(self):
        """Reactivate cancelled subscription"""
        if self.status == 'cancelled':
            self.status = 'active'
            self.cancelled_at = None
            self.ends_at = None
            self.auto_renew = True
            self.save()


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
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='invoices')
    
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
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'subscriptions_invoice'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.tenant.name}"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return self.status == 'pending' and timezone.now() > self.due_date
    
    def mark_as_paid(self, payment_method=None):
        """Mark invoice as paid"""
        self.status = 'paid'
        self.paid_at = timezone.now()
        if payment_method:
            self.payment_method = payment_method
        self.save()


class UsageRecord(models.Model):
    """
    Usage tracking for metered billing
    """
    METRIC_CHOICES = [
        ('api_calls', 'API Calls'),
        ('storage_gb', 'Storage (GB)'),
        ('users', 'Active Users'),
        ('transactions', 'Transactions'),
        ('emails_sent', 'Emails Sent'),
        ('custom', 'Custom Metric'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='usage_records')
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='usage_records')
    
    # Usage details
    metric = models.CharField(max_length=50, choices=METRIC_CHOICES)
    value = models.DecimalField(max_digits=15, decimal_places=4)
    unit = models.CharField(max_length=20, default='count')
    
    # Time period
    recorded_at = models.DateTimeField(default=timezone.now)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'subscriptions_usage_record'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['subscription', 'metric', 'period_start']),
            models.Index(fields=['tenant', 'recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.metric}: {self.value} {self.unit}"


class Discount(models.Model):
    """
    Discounts and promotional codes
    """
    TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
        ('free_trial', 'Free Trial Extension'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Discount configuration
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    
    # Usage limits
    max_uses = models.PositiveIntegerField(blank=True, null=True)
    uses_count = models.PositiveIntegerField(default=0)
    max_uses_per_customer = models.PositiveIntegerField(default=1)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Applicable plans
    applicable_plans = models.ManyToManyField(PricingPlan, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions_discount'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_valid(self):
        """Check if discount is currently valid"""
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.max_uses is None or self.uses_count < self.max_uses)
        )
    
    def can_be_used_by_tenant(self, tenant):
        """Check if discount can be used by specific tenant"""
        if not self.is_valid:
            return False
        
        # Check usage limit per customer
        tenant_usage = DiscountUsage.objects.filter(
            discount=self,
            subscription__tenant=tenant
        ).count()
        
        return tenant_usage < self.max_uses_per_customer
    
    def calculate_discount_amount(self, amount):
        """Calculate discount amount for given base amount"""
        if self.type == 'percentage':
            return amount * (self.value / 100)
        elif self.type == 'fixed_amount':
            return min(self.value, amount)
        return Decimal('0.00')


class DiscountUsage(models.Model):
    """
    Track discount usage by subscriptions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='usages')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='discount_usages')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, blank=True, null=True)
    
    # Usage details
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ZAR')
    
    # Timestamps
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subscriptions_discount_usage'
        indexes = [
            models.Index(fields=['discount', 'subscription']),
            models.Index(fields=['used_at']),
        ]
    
    def __str__(self):
        return f"{self.discount.code} used by {self.subscription.tenant.name}"