"""
Django admin for simplified tenant models
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Organization, OrganizationUser, Domain


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'tier', 'status', 'max_users', 
        'created_at', 'is_active'
    ]
    list_filter = ['tier', 'status', 'is_active', 'created_at', 'country']
    search_fields = ['name', 'slug', 'email', 'company_registration']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address_line1', 'city', 'country'),
            'classes': ('collapse',)
        }),
        ('Business Information', {
            'fields': ('company_registration', 'industry'),
            'classes': ('collapse',)
        }),
        ('Subscription & Status', {
            'fields': ('tier', 'status', 'is_active', 'trial_end_date')
        }),
        ('Resource Limits', {
            'fields': ('max_users', 'max_storage_gb', 'max_api_calls_per_month')
        }),
        ('Metadata', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1
    fields = ['domain', 'is_primary', 'is_verified']


@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_active', 'created_at', 'last_login']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'organization__name']
    raw_id_fields = ['user', 'organization']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('organization', 'user', 'role', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'organization', 'is_primary', 'is_verified', 'created_at']
    list_filter = ['is_primary', 'is_verified', 'created_at']
    search_fields = ['domain', 'tenant__name']
    raw_id_fields = ['tenant']