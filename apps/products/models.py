"""
Product catalog models (SHARED across all tenants)
Platform-wide product definitions, pricing plans, and bundles
"""
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Product(models.Model):
    """
    Platform products (AutoFlow AI, BuildEasy, TeamSpace)
    SHARED MODEL - Same products available to all tenants
    """
    BILLING_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('per_user', 'Per User'),
        ('usage_based', 'Usage Based'),
        ('hybrid', 'Hybrid (Base + Usage)'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('beta', 'Beta'),
        ('deprecated', 'Deprecated'),
        ('coming_soon', 'Coming Soon'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Product identification
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique product code (e.g., 'autoflow', 'buildeasy', 'teamspace')"
    )
    name = models.CharField(max_length=100, help_text="Product display name")
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    tagline = models.CharField(max_length=255, blank=True)

    # Product type
    billing_type = models.CharField(
        max_length=20,
        choices=BILLING_TYPE_CHOICES,
        default='fixed'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Product configuration
    icon = models.CharField(max_length=50, blank=True, help_text="Icon identifier or emoji")
    color = models.CharField(max_length=7, default='#000000', help_text="Brand color (hex)")

    # Features and metadata
    features = models.JSONField(
        default=list,
        help_text="List of product features"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional product metadata"
    )

    # Visibility
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(
        default=True,
        help_text="Whether this product is publicly available"
    )
    requires_approval = models.BooleanField(
        default=False,
        help_text="Whether subscription requires manual approval"
    )

    # Ordering
    sort_order = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    launched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'products'
        ordering = ['sort_order', 'name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name


class ProductPlan(models.Model):
    """
    Product-specific pricing plans
    Links products to the base PricingPlan model with product-specific configuration
    SHARED MODEL - Same pricing available to all tenants
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_plans'
    )
    base_plan = models.ForeignKey(
        'subscriptions.PricingPlan',
        on_delete=models.PROTECT,
        related_name='product_plans'
    )

    # Product-specific limits (extends base_plan limits)
    product_limits = models.JSONField(
        default=dict,
        help_text="Product-specific limits (e.g., tasks for AutoFlow, apps for BuildEasy)"
    )

    # Product-specific features (extends base_plan features)
    product_features = models.JSONField(
        default=list,
        help_text="Product-specific features enabled in this plan"
    )

    # Visibility and availability
    is_available_standalone = models.BooleanField(
        default=True,
        help_text="Can be purchased individually"
    )
    is_available_in_bundle = models.BooleanField(
        default=True,
        help_text="Can be included in bundles"
    )
    is_active = models.BooleanField(default=True)

    # Stripe integration
    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Stripe Price ID for this product plan"
    )
    stripe_product_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Stripe Product ID"
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_plans'
        unique_together = ['product', 'base_plan']
        ordering = ['product', 'base_plan__price']
        verbose_name = 'Product Plan'
        verbose_name_plural = 'Product Plans'

    def __str__(self):
        return f"{self.product.name} - {self.base_plan.name}"

    @property
    def price(self):
        """Get price from base plan"""
        return self.base_plan.price

    @property
    def currency(self):
        """Get currency from base plan"""
        return self.base_plan.currency

    @property
    def billing_interval(self):
        """Get billing interval from base plan"""
        return self.base_plan.billing_interval


class SubscriptionBundle(models.Model):
    """
    Pre-defined product bundles with discount pricing
    E.g., "Starter Bundle" (AutoFlow + TeamSpace), "Professional Bundle" (all 3)
    SHARED MODEL - Same bundles available to all tenants
    """
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
    ]

    BILLING_INTERVAL_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Bundle identification
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique bundle code (e.g., 'starter_bundle', 'pro_bundle')"
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    tagline = models.CharField(max_length=255, blank=True)

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='USD')
    billing_interval = models.CharField(
        max_length=20,
        choices=BILLING_INTERVAL_CHOICES,
        default='monthly'
    )

    # Discount
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Percentage (0-100) or fixed amount depending on discount_type"
    )

    # Included limits (for the bundle as a whole)
    included_users = models.PositiveIntegerField(
        default=0,
        help_text="Number of users included in base price (0 = unlimited)"
    )

    # Features and metadata
    features = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)

    # Visibility
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # Stripe integration
    stripe_product_id = models.CharField(max_length=255, blank=True)
    stripe_price_id = models.CharField(max_length=255, blank=True)

    # Ordering
    sort_order = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_bundles'
        ordering = ['sort_order', 'name']
        verbose_name = 'Subscription Bundle'
        verbose_name_plural = 'Subscription Bundles'

    def __str__(self):
        return self.name

    def calculate_regular_price(self):
        """Calculate the sum of individual product prices"""
        total = Decimal('0.00')
        for bundle_product in self.bundle_products.all():
            total += bundle_product.product_plan.price
        return total

    def calculate_discount_amount(self):
        """Calculate the discount amount based on type"""
        regular_price = self.calculate_regular_price()
        if self.discount_type == 'percentage':
            return regular_price * (self.discount_value / Decimal('100'))
        else:  # fixed
            return self.discount_value

    def calculate_savings_percentage(self):
        """Calculate percentage saved vs individual products"""
        regular_price = self.calculate_regular_price()
        if regular_price == 0:
            return 0
        discount = self.calculate_discount_amount()
        return (discount / regular_price) * Decimal('100')


class BundleProduct(models.Model):
    """
    Through model for products included in a bundle
    SHARED MODEL
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    bundle = models.ForeignKey(
        SubscriptionBundle,
        on_delete=models.CASCADE,
        related_name='bundle_products'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='bundle_memberships'
    )
    product_plan = models.ForeignKey(
        ProductPlan,
        on_delete=models.PROTECT,
        related_name='bundle_inclusions',
        help_text="Specific plan tier included in this bundle"
    )

    # Configuration
    is_required = models.BooleanField(
        default=True,
        help_text="Whether this product is required in the bundle"
    )
    sort_order = models.PositiveIntegerField(default=0)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bundle_products'
        unique_together = ['bundle', 'product']
        ordering = ['sort_order', 'product__name']
        verbose_name = 'Bundle Product'
        verbose_name_plural = 'Bundle Products'

    def __str__(self):
        return f"{self.bundle.name} - {self.product.name}"
