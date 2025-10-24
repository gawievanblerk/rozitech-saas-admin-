"""
Lead Management Admin Interface
Admin interface for managing trial signups, email logs, and email templates
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import TrialSignup, EmailLog, EmailTemplate


@admin.register(TrialSignup)
class TrialSignupAdmin(admin.ModelAdmin):
    """Admin interface for Trial Signups"""

    list_display = [
        'id',
        'full_name_link',
        'email',
        'company',
        'status_badge',
        'products_display',
        'total_price_display',
        'email_verified',
        'created_at',
    ]

    list_filter = [
        'status',
        'email_verified',
        'marketing_consent',
        'lead_source',
        'created_at',
        'trial_start_date',
    ]

    search_fields = [
        'first_name',
        'last_name',
        'email',
        'company',
        'phone',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'email_verified_at',
        'welcome_email_sent_at',
        'onboarding_call_scheduled_at',
        'verification_token_expires_at',
    ]

    fieldsets = (
        ('Contact Information', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone',
                'company',
                'job_title',
                'company_size',
            )
        }),
        ('Product Selection', {
            'fields': (
                'selected_products',
                'total_price',
                'plan_type',
                'needs',
            )
        }),
        ('Marketing', {
            'fields': (
                'marketing_consent',
                'lead_source',
                'page_source',
                'utm_source',
                'utm_medium',
                'utm_campaign',
            )
        }),
        ('Status & Assignment', {
            'fields': (
                'status',
                'trial_start_date',
                'trial_end_date',
                'assigned_to',
                'internal_notes',
            )
        }),
        ('Email Verification', {
            'fields': (
                'email_verified',
                'verification_token',
                'verification_token_expires_at',
                'email_verified_at',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'welcome_email_sent_at',
                'onboarding_call_scheduled_at',
            )
        }),
    )

    date_hierarchy = 'created_at'

    actions = ['mark_as_contacted', 'mark_as_qualified', 'mark_as_converted']

    def full_name_link(self, obj):
        """Display full name as clickable link"""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:leads_trialsignup_change', args=[obj.pk]),
            obj.full_name
        )
    full_name_link.short_description = 'Name'

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'new': '#17a2b8',
            'contacted': '#ffc107',
            'qualified': '#28a745',
            'converted': '#007bff',
            'rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def mark_as_contacted(self, request, queryset):
        """Bulk action to mark leads as contacted"""
        updated = queryset.update(status='contacted')
        self.message_user(request, f'{updated} trial signup(s) marked as contacted.')
    mark_as_contacted.short_description = 'Mark selected as Contacted'

    def mark_as_qualified(self, request, queryset):
        """Bulk action to mark leads as qualified"""
        updated = queryset.update(status='qualified')
        self.message_user(request, f'{updated} trial signup(s) marked as qualified.')
    mark_as_qualified.short_description = 'Mark selected as Qualified'

    def mark_as_converted(self, request, queryset):
        """Bulk action to mark leads as converted"""
        updated = queryset.update(status='converted')
        self.message_user(request, f'{updated} trial signup(s) marked as converted.')
    mark_as_converted.short_description = 'Mark selected as Converted'


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Admin interface for Email Logs"""

    list_display = [
        'id',
        'trial_signup_link',
        'template_name',
        'recipient_email',
        'subject',
        'status_badge',
        'sent_at',
        'delivered_at',
    ]

    list_filter = [
        'status',
        'template_name',
        'sent_at',
        'delivered_at',
    ]

    search_fields = [
        'recipient_email',
        'subject',
        'provider_message_id',
    ]

    readonly_fields = [
        'trial_signup',
        'template_name',
        'recipient_email',
        'subject',
        'status',
        'provider_message_id',
        'sent_at',
        'delivered_at',
        'opened_at',
        'clicked_at',
    ]

    fieldsets = (
        ('Email Details', {
            'fields': (
                'trial_signup',
                'template_name',
                'recipient_email',
                'subject',
            )
        }),
        ('Status & Tracking', {
            'fields': (
                'status',
                'provider_message_id',
            )
        }),
        ('Timestamps', {
            'fields': (
                'sent_at',
                'delivered_at',
                'opened_at',
                'clicked_at',
            )
        }),
    )

    date_hierarchy = 'sent_at'

    def trial_signup_link(self, obj):
        """Display trial signup as clickable link"""
        if obj.trial_signup:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:leads_trialsignup_change', args=[obj.trial_signup.pk]),
                obj.trial_signup.full_name
            )
        return '-'
    trial_signup_link.short_description = 'Trial Signup'

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': '#6c757d',
            'sent': '#17a2b8',
            'delivered': '#28a745',
            'opened': '#007bff',
            'clicked': '#20c997',
            'bounced': '#ffc107',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        """Disable adding email logs manually"""
        return False


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin interface for Email Templates"""

    list_display = [
        'id',
        'template_name',
        'subject',
        'is_active',
        'updated_at',
    ]

    list_filter = [
        'is_active',
        'created_at',
        'updated_at',
    ]

    search_fields = [
        'template_name',
        'subject',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Template Information', {
            'fields': (
                'template_name',
                'subject',
                'is_active',
            )
        }),
        ('Email Content', {
            'fields': (
                'html_content',
                'text_content',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    date_hierarchy = 'updated_at'
