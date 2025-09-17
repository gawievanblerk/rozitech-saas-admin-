"""
Admin interface for tenant management
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Tenant, Domain, TenantUser, TenantInvitation


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'schema_name', 'tier', 'status', 'current_users_display',
        'created_at', 'last_activity', 'is_active'
    ]
    list_filter = ['tier', 'status', 'is_active', 'created_at', 'country']
    search_fields = ['name', 'schema_name', 'email', 'slug']
    readonly_fields = ['id', 'schema_name', 'created_at', 'updated_at', 'current_users_count', 'storage_usage_gb']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'schema_name', 'email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country'),
            'classes': ('collapse',)
        }),
        ('Business Information', {
            'fields': ('company_registration', 'tax_number', 'industry'),
            'classes': ('collapse',)
        }),
        ('Subscription & Status', {
            'fields': ('tier', 'status', 'is_active', 'trial_end_date', 'last_activity')
        }),
        ('Resource Limits', {
            'fields': ('max_users', 'max_storage_gb', 'max_api_calls_per_month', 
                      'current_users_count', 'storage_usage_gb')
        }),
        ('Metadata', {
            'fields': ('custom_settings', 'notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_users_display(self, obj):
        """Display current users with limit"""
        count = obj.current_users_count
        limit = obj.max_users
        color = 'red' if count >= limit else 'green'
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color, count, limit
        )
    current_users_display.short_description = 'Users'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1
    fields = ['domain', 'is_primary']


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'created_at', 'last_login']
    list_filter = ['role', 'is_active', 'created_at', 'tenant__tier']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    raw_id_fields = ['user', 'tenant']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('tenant', 'user', 'role', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'tenant')


@admin.register(TenantInvitation)
class TenantInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'tenant', 'role', 'status', 'invited_by', 'created_at', 'expires_at']
    list_filter = ['status', 'role', 'created_at', 'expires_at']
    search_fields = ['email', 'tenant__name', 'invited_by__username']
    readonly_fields = ['token', 'created_at', 'accepted_at']
    raw_id_fields = ['tenant', 'invited_by']
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('tenant', 'email', 'role', 'invited_by', 'status')
        }),
        ('Timing', {
            'fields': ('created_at', 'expires_at', 'accepted_at')
        }),
        ('Security', {
            'fields': ('token',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tenant', 'invited_by')


# Customize admin site
admin.site.site_header = 'Rozitech SaaS Admin'
admin.site.site_title = 'Rozitech SaaS Admin'
admin.site.index_title = 'Administration'