"""
Django admin for simplified subscription models
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from .models import PricingPlan, Subscription, Invoice
from .models_products import ProductSubscription, UsageRecord
from apps.products.models import Product, ProductPlan, SubscriptionBundle, BundleProduct


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'price', 'currency', 'billing_interval', 
        'plan_type', 'max_users', 'is_active', 'is_public'
    ]
    list_filter = ['billing_interval', 'plan_type', 'is_active', 'is_public', 'currency']
    search_fields = ['name', 'slug', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'currency', 'billing_interval', 'plan_type', 'trial_period_days')
        }),
        ('Feature Limits', {
            'fields': ('max_users', 'max_storage_gb', 'max_api_calls_per_month', 'max_projects')
        }),
        ('Features', {
            'fields': ('features', 'feature_limits'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'plan', 'status', 'started_at', 
        'current_period_end', 'next_billing_date', 'auto_renew'
    ]
    list_filter = ['status', 'auto_renew', 'started_at', 'plan__billing_interval']
    search_fields = ['organization__name', 'plan__name']
    raw_id_fields = ['organization', 'plan']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'plan', 'status')
        }),
        ('Billing Dates', {
            'fields': (
                'started_at', 'trial_end_date', 'current_period_start', 
                'current_period_end', 'next_billing_date', 'cancelled_at'
            )
        }),
        ('Settings', {
            'fields': ('auto_renew',)
        }),
        ('Usage', {
            'fields': ('current_usage',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'plan')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'organization', 'status', 'total_amount', 
        'currency', 'due_date', 'paid_at', 'created_at'
    ]
    list_filter = ['status', 'currency', 'created_at', 'due_date']
    search_fields = ['invoice_number', 'organization__name', 'subscription__plan__name']
    raw_id_fields = ['subscription', 'organization']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'invoice_number', 'organization', 'subscription', 'status')
        }),
        ('Amounts', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Billing Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Payment Information', {
            'fields': ('due_date', 'paid_at', 'payment_method')
        }),
        ('Line Items', {
            'fields': ('line_items',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'subscription')


# =============================================================================
# MULTI-PRODUCT BILLING ADMIN
# =============================================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'status', 'billing_type', 'is_active',
        'is_public', 'sort_order', 'subscription_count'
    ]
    list_filter = ['status', 'billing_type', 'is_active', 'is_public', 'requires_approval']
    search_fields = ['name', 'code', 'slug', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'subscription_count']
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'code', 'name', 'slug', 'tagline', 'description')
        }),
        ('Product Configuration', {
            'fields': ('billing_type', 'status', 'icon', 'color')
        }),
        ('Features & Metadata', {
            'fields': ('features', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Visibility', {
            'fields': ('is_active', 'is_public', 'requires_approval', 'sort_order')
        }),
        ('Statistics', {
            'fields': ('subscription_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'launched_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_products', 'deactivate_products', 'make_public', 'make_private']

    def subscription_count(self, obj):
        count = obj.subscriptions.filter(status__in=['trial', 'active']).count()
        return format_html('<strong>{}</strong> active', count)
    subscription_count.short_description = 'Active Subscriptions'

    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} product(s) activated.')
    activate_products.short_description = 'Activate selected products'

    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} product(s) deactivated.')
    deactivate_products.short_description = 'Deactivate selected products'

    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} product(s) made public.')
    make_public.short_description = 'Make selected products public'

    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} product(s) made private.')
    make_private.short_description = 'Make selected products private'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            active_subscription_count=Count('subscriptions', filter=admin.Q(subscriptions__status__in=['trial', 'active']))
        )


@admin.register(ProductPlan)
class ProductPlanAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'base_plan', 'display_price', 'billing_interval',
        'is_available_standalone', 'is_available_in_bundle', 'is_active',
        'subscription_count'
    ]
    list_filter = [
        'is_active', 'is_available_standalone', 'is_available_in_bundle',
        'product', 'base_plan__billing_interval'
    ]
    search_fields = ['product__name', 'base_plan__name']
    raw_id_fields = ['product', 'base_plan']
    readonly_fields = ['id', 'created_at', 'updated_at', 'display_price', 'subscription_count']

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'product', 'base_plan')
        }),
        ('Product-Specific Configuration', {
            'fields': ('product_limits', 'product_features')
        }),
        ('Availability', {
            'fields': ('is_available_standalone', 'is_available_in_bundle', 'is_active')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_product_id', 'stripe_price_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('display_price', 'subscription_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_price(self, obj):
        return format_html('<strong>{} {}</strong> / {}',
                         obj.currency, obj.price, obj.billing_interval)
    display_price.short_description = 'Price'

    def billing_interval(self, obj):
        return obj.base_plan.billing_interval
    billing_interval.short_description = 'Billing Interval'

    def subscription_count(self, obj):
        count = obj.subscriptions.filter(status__in=['trial', 'active']).count()
        return format_html('<strong>{}</strong> active', count)
    subscription_count.short_description = 'Active Subscriptions'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'base_plan')


class BundleProductInline(admin.TabularInline):
    model = BundleProduct
    extra = 1
    raw_id_fields = ['product', 'product_plan']
    fields = ['product', 'product_plan', 'is_required', 'sort_order']
    ordering = ['sort_order']


@admin.register(SubscriptionBundle)
class SubscriptionBundleAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'display_price', 'billing_interval',
        'display_discount', 'display_savings', 'product_count',
        'is_active', 'is_public', 'is_featured'
    ]
    list_filter = [
        'billing_interval', 'discount_type', 'is_active',
        'is_public', 'is_featured', 'currency'
    ]
    search_fields = ['name', 'code', 'slug', 'description']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'display_regular_price',
        'display_discount', 'display_savings', 'product_count'
    ]
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BundleProductInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'code', 'name', 'slug', 'tagline', 'description')
        }),
        ('Pricing', {
            'fields': (
                'base_price', 'currency', 'billing_interval',
                'discount_type', 'discount_value'
            )
        }),
        ('Calculated Pricing', {
            'fields': ('display_regular_price', 'display_discount', 'display_savings'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('included_users', 'features', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Visibility', {
            'fields': ('is_active', 'is_public', 'is_featured', 'sort_order')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_product_id', 'stripe_price_id'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('product_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_bundles', 'deactivate_bundles', 'make_featured']

    def display_price(self, obj):
        return format_html('<strong>{} {}</strong> / {}',
                         obj.currency, obj.base_price, obj.billing_interval)
    display_price.short_description = 'Price'

    def display_regular_price(self, obj):
        regular = obj.calculate_regular_price()
        return format_html('{} {}', obj.currency, regular)
    display_regular_price.short_description = 'Regular Price (Sum)'

    def display_discount(self, obj):
        discount = obj.calculate_discount_amount()
        if obj.discount_type == 'percentage':
            return format_html('<span style="color: green;">-{} {} ({}%)</span>',
                             obj.currency, discount, obj.discount_value)
        else:
            return format_html('<span style="color: green;">-{} {}</span>',
                             obj.currency, discount)
    display_discount.short_description = 'Discount'

    def display_savings(self, obj):
        savings_pct = obj.calculate_savings_percentage()
        return format_html('<strong style="color: green;">{}%</strong> savings',
                         round(savings_pct, 1))
    display_savings.short_description = 'Total Savings'

    def product_count(self, obj):
        count = obj.bundle_products.count()
        return format_html('<strong>{}</strong> product(s)', count)
    product_count.short_description = 'Products in Bundle'

    def activate_bundles(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} bundle(s) activated.')
    activate_bundles.short_description = 'Activate selected bundles'

    def deactivate_bundles(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} bundle(s) deactivated.')
    deactivate_bundles.short_description = 'Deactivate selected bundles'

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} bundle(s) marked as featured.')
    make_featured.short_description = 'Mark as featured'


@admin.register(ProductSubscription)
class ProductSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'organization', 'product', 'plan', 'status',
        'started_at', 'current_period_end', 'next_billing_date',
        'auto_renew', 'days_until_renewal'
    ]
    list_filter = [
        'status', 'auto_renew', 'product', 'plan__base_plan__billing_interval',
        'started_at'
    ]
    search_fields = [
        'organization__name', 'product__name', 'plan__base_plan__name',
        'stripe_subscription_id'
    ]
    raw_id_fields = ['organization', 'product', 'plan', 'parent_subscription']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'is_active', 'is_trial',
        'days_until_renewal', 'usage_summary'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'product', 'plan', 'status')
        }),
        ('Bundle Relationship', {
            'fields': ('parent_subscription',),
            'classes': ('collapse',)
        }),
        ('Billing Dates', {
            'fields': (
                'started_at', 'trial_end_date', 'current_period_start',
                'current_period_end', 'next_billing_date', 'cancelled_at'
            )
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('auto_renew',)
        }),
        ('Usage Tracking', {
            'fields': ('current_usage', 'usage_limit', 'usage_summary'),
            'classes': ('collapse',)
        }),
        ('Stripe Integration', {
            'fields': ('stripe_subscription_id',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Status Indicators', {
            'fields': ('is_active', 'is_trial', 'days_until_renewal'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['cancel_subscriptions', 'reactivate_subscriptions']

    def is_active(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'green' if obj.is_active else 'red',
            'Yes' if obj.is_active else 'No'
        )
    is_active.short_description = 'Active'

    def is_trial(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            'orange' if obj.is_trial else 'gray',
            'Yes' if obj.is_trial else 'No'
        )
    is_trial.short_description = 'Trial'

    def days_until_renewal(self, obj):
        days = obj.days_until_renewal
        if days is None:
            return '-'
        if days < 0:
            return format_html('<span style="color: red;">Overdue</span>')
        elif days == 0:
            return format_html('<span style="color: orange;">Today</span>')
        else:
            return format_html('<strong>{}</strong> days', days)
    days_until_renewal.short_description = 'Renewal In'

    def usage_summary(self, obj):
        if not obj.current_usage:
            return 'No usage data'

        html = '<table style="border: 1px solid #ddd;">'
        for metric, value in obj.current_usage.items():
            limit = obj.usage_limit.get(metric, 'Unlimited')
            html += f'<tr><td><strong>{metric}:</strong></td><td>{value} / {limit}</td></tr>'
        html += '</table>'
        return format_html(html)
    usage_summary.short_description = 'Usage Summary'

    def cancel_subscriptions(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status__in=['trial', 'active']).update(
            status='cancelled',
            cancelled_at=timezone.now()
        )
        self.message_user(request, f'{updated} subscription(s) cancelled.')
    cancel_subscriptions.short_description = 'Cancel selected subscriptions'

    def reactivate_subscriptions(self, request, queryset):
        updated = queryset.filter(status='cancelled').update(
            status='active',
            cancelled_at=None
        )
        self.message_user(request, f'{updated} subscription(s) reactivated.')
    reactivate_subscriptions.short_description = 'Reactivate cancelled subscriptions'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'product', 'plan', 'plan__base_plan'
        )


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = [
        'product_subscription', 'metric_name', 'quantity', 'unit',
        'unit_price', 'total_amount', 'timestamp', 'is_billed'
    ]
    list_filter = [
        'is_billed', 'metric_name', 'unit', 'timestamp',
        'product_subscription__product'
    ]
    search_fields = [
        'product_subscription__organization__name',
        'product_subscription__product__name',
        'metric_name'
    ]
    raw_id_fields = ['product_subscription', 'invoice']
    readonly_fields = ['id', 'created_at', 'updated_at', 'calculated_total']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'product_subscription', 'metric_name')
        }),
        ('Usage Details', {
            'fields': ('quantity', 'unit', 'unit_price', 'total_amount', 'calculated_total')
        }),
        ('Period', {
            'fields': ('period_start', 'period_end', 'timestamp')
        }),
        ('Billing Status', {
            'fields': ('is_billed', 'invoice')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_billed', 'mark_as_unbilled']

    def calculated_total(self, obj):
        if obj.unit_price:
            calc = obj.quantity * obj.unit_price
            return format_html('<strong>{}</strong> ({}  {} @ {})',
                             calc, obj.quantity, obj.unit, obj.unit_price)
        return '-'
    calculated_total.short_description = 'Calculated Total'

    def mark_as_billed(self, request, queryset):
        updated = queryset.update(is_billed=True)
        self.message_user(request, f'{updated} usage record(s) marked as billed.')
    mark_as_billed.short_description = 'Mark as billed'

    def mark_as_unbilled(self, request, queryset):
        updated = queryset.update(is_billed=False, invoice=None)
        self.message_user(request, f'{updated} usage record(s) marked as unbilled.')
    mark_as_unbilled.short_description = 'Mark as unbilled'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'product_subscription',
            'product_subscription__product',
            'product_subscription__organization',
            'invoice'
        )