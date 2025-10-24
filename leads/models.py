"""
Lead Management Models
Manages trial signups and related email communications
"""
from django.db import models
from django.utils import timezone


class TrialSignup(models.Model):
    """Trial signup requests from the marketing website"""

    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('converted', 'Converted'),
        ('rejected', 'Rejected'),
    ]

    # Contact Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    company = models.CharField(max_length=200)
    job_title = models.CharField(max_length=150, blank=True, null=True)
    company_size = models.CharField(max_length=50, blank=True, null=True)

    # Product Selection
    selected_products = models.JSONField(help_text="Array of selected product codes")
    total_price = models.IntegerField(null=True, blank=True, help_text="Total price in cents")
    plan_type = models.CharField(max_length=50, blank=True, null=True)
    needs = models.TextField(blank=True, null=True, help_text="Customer's specific needs/requirements")

    # Marketing
    marketing_consent = models.BooleanField(default=False)
    lead_source = models.CharField(max_length=100, default='website')
    page_source = models.CharField(max_length=200, blank=True, null=True)
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=100, blank=True, null=True)

    # Status & Assignment
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    trial_start_date = models.DateField(null=True, blank=True)
    trial_end_date = models.DateField(null=True, blank=True)
    assigned_to = models.CharField(max_length=100, blank=True, null=True, help_text="Sales rep assigned to this lead")
    internal_notes = models.TextField(blank=True, null=True)

    # Email Verification
    email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True, null=True)
    verification_token_expires_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    welcome_email_sent_at = models.DateTimeField(null=True, blank=True)
    onboarding_call_scheduled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'trial_signups'
        managed = False  # Don't let Django manage this table
        ordering = ['-created_at']
        verbose_name = 'Trial Signup'
        verbose_name_plural = 'Trial Signups'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.company}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_price_display(self):
        """Display price in currency format"""
        if self.total_price:
            return f"R{self.total_price / 100:.2f}"
        return "N/A"

    @property
    def products_display(self):
        """Display selected products as comma-separated list"""
        if isinstance(self.selected_products, list):
            return ", ".join(self.selected_products)
        return str(self.selected_products)


class EmailLog(models.Model):
    """Log of all emails sent to trial signups"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('clicked', 'Clicked'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    ]

    trial_signup = models.ForeignKey(
        TrialSignup,
        on_delete=models.CASCADE,
        related_name='email_logs',
        db_column='trial_signup_id',
        null=True,
        blank=True
    )
    template_name = models.CharField(max_length=100, blank=True, null=True, help_text="Name of email template used")
    recipient_email = models.EmailField(max_length=255)
    subject = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='sent')
    provider_message_id = models.CharField(max_length=200, blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_logs'
        managed = False  # Don't let Django manage this table
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'

    def __str__(self):
        template = self.template_name or 'Email'
        return f"{template} to {self.recipient_email} - {self.status}"


class EmailTemplate(models.Model):
    """Email templates for various trial signup communications"""

    template_name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    html_content = models.TextField(help_text="HTML email body")
    text_content = models.TextField(help_text="Plain text email body")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_templates'
        managed = False  # Don't let Django manage this table
        ordering = ['template_name']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return f"{self.template_name}"
