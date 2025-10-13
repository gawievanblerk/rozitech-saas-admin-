"""
Tenant-specific subscription models for multi-product billing
Uses product catalog from apps.products (shared models)
"""
from django.db import models
from django.core.validators import MinValueValidator
import uuid
from django.utils import timezone

# Import shared product catalog models
from apps.products.models import Product, ProductPlan, SubscriptionBundle, BundleProduct


class ProductSubscription(models.Model):
    """
    Individual product subscriptions within an organization
    TENANT-SPECIFIC MODEL - Each tenant has their own subscriptions
    """
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
        ('pending_approval', 'Pending Approval'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='product_subscriptions'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        'products.ProductPlan',
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )

    # Bundle relationship (if part of a bundle)
    parent_subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='product_subscriptions',
        help_text="Parent subscription if this is part of a bundle"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial'
    )

    # Dates
    started_at = models.DateTimeField(default=timezone.now)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Billing
    next_billing_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)

    # Usage tracking
    current_usage = models.JSONField(
        default=dict,
        help_text="Current usage metrics for this product (e.g., tasks_executed, storage_used)"
    )
    usage_limit = models.JSONField(
        default=dict,
        help_text="Usage limits for this subscription"
    )

    # Stripe integration
    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Stripe Subscription ID"
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_subscriptions'
        unique_together = ['organization', 'product']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['stripe_subscription_id']),
        ]
        verbose_name = 'Product Subscription'
        verbose_name_plural = 'Product Subscriptions'

    def __str__(self):
        return f"{self.organization.name} - {self.product.name} ({self.status})"

    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ['trial', 'active']

    @property
    def is_trial(self):
        """Check if subscription is in trial period"""
        return self.status == 'trial'

    @property
    def days_until_renewal(self):
        """Calculate days until next billing"""
        if not self.next_billing_date:
            return None
        delta = self.next_billing_date - timezone.now()
        return delta.days


class UsageRecord(models.Model):
    """
    Track usage for usage-based billing
    Records metrics like API calls, storage, tasks executed, etc.
    TENANT-SPECIFIC MODEL - Each tenant has their own usage records
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    product_subscription = models.ForeignKey(
        ProductSubscription,
        on_delete=models.CASCADE,
        related_name='usage_records'
    )

    # Usage details
    metric_name = models.CharField(
        max_length=100,
        help_text="Name of the metric being tracked (e.g., 'api_calls', 'storage_gb', 'tasks_executed')"
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(0)]
    )
    unit = models.CharField(
        max_length=50,
        default='unit',
        help_text="Unit of measurement (e.g., 'call', 'GB', 'task')"
    )

    # Pricing (if applicable)
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Price per unit for usage-based billing"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Total amount for this usage (quantity * unit_price)"
    )

    # Period
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    # Billing status
    is_billed = models.BooleanField(default=False)
    invoice = models.ForeignKey(
        'subscriptions.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usage_records'
    )

    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context about the usage"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usage_records'
        indexes = [
            models.Index(fields=['product_subscription', 'metric_name', 'timestamp']),
            models.Index(fields=['is_billed', 'period_end']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
        verbose_name = 'Usage Record'
        verbose_name_plural = 'Usage Records'

    def __str__(self):
        return f"{self.product_subscription.product.name} - {self.metric_name}: {self.quantity} {self.unit}"

    def save(self, *args, **kwargs):
        # Calculate total amount if unit_price is set
        if self.unit_price:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)