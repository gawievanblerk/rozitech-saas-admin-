"""
Django admin for simplified subscription models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models_simple import PricingPlan, Subscription, Invoice


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