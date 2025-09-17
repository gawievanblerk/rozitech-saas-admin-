"""
Payment processing models for billing and transactions
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone


class PaymentProvider(models.Model):
    """
    Payment gateway providers (Stripe, PayPal, etc.)
    """
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('payfast', 'PayFast (South Africa)'),
        ('paygate', 'PayGate (South Africa)'),
        ('ozow', 'Ozow (South Africa)'),
        ('snapscan', 'SnapScan (South Africa)'),
        ('manual', 'Manual Payment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    
    # Configuration
    is_active = models.BooleanField(default=True)
    is_test_mode = models.BooleanField(default=True)
    
    # API Configuration (encrypted in production)
    api_key = models.TextField(blank=True, help_text="Primary API key")
    api_secret = models.TextField(blank=True, help_text="API secret key")
    webhook_secret = models.TextField(blank=True, help_text="Webhook secret for verification")
    
    # Supported features
    supports_subscriptions = models.BooleanField(default=True)
    supports_refunds = models.BooleanField(default=True)
    supports_webhooks = models.BooleanField(default=True)
    
    # Regional settings
    supported_currencies = models.JSONField(default=list, help_text="List of supported currency codes")
    supported_countries = models.JSONField(default=list, help_text="List of supported country codes")
    
    # Fee structure
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0, help_text="Fee as percentage")
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Fixed fee amount")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments_provider'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"
    
    def calculate_fees(self, amount):
        """Calculate processing fees for given amount"""
        percentage_fee = amount * (self.fee_percentage / 100)
        return percentage_fee + self.fee_fixed


class PaymentMethod(models.Model):
    """
    Stored payment methods for customers
    """
    TYPE_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank_account', 'Bank Account'),
        ('paypal', 'PayPal'),
        ('eft', 'EFT'),
        ('debit_order', 'Debit Order'),
        ('wallet', 'Digital Wallet'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    tenant = models.ForeignKey('tenants.Organization', on_delete=models.CASCADE, related_name='payment_methods')
    provider = models.ForeignKey(PaymentProvider, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Payment method details
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    external_id = models.CharField(max_length=255, help_text="Provider's payment method ID")
    
    # Card details (for display only - no sensitive data stored)
    last_four_digits = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    expiry_month = models.PositiveIntegerField(blank=True, null=True)
    expiry_year = models.PositiveIntegerField(blank=True, null=True)
    
    # Bank account details (for display only)
    bank_name = models.CharField(max_length=100, blank=True)
    account_holder_name = models.CharField(max_length=255, blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'payments_payment_method'
        unique_together = ['tenant', 'external_id']
        indexes = [
            models.Index(fields=['tenant', 'is_active', 'is_default']),
            models.Index(fields=['provider', 'external_id']),
        ]
    
    def __str__(self):
        if self.type == 'card' and self.last_four_digits:
            return f"{self.card_brand} ****{self.last_four_digits}"
        elif self.type == 'bank_account' and self.bank_name:
            return f"{self.bank_name} - {self.account_holder_name}"
        return f"{self.get_type_display()} - {self.external_id[:8]}..."
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per tenant
        if self.is_default:
            PaymentMethod.objects.filter(
                tenant=self.tenant,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """
    Payment transactions and their status
    """
    TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('chargeback', 'Chargeback'),
        ('transfer', 'Transfer'),
        ('fee', 'Processing Fee'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('requires_action', 'Requires Action'),
        ('disputed', 'Disputed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=100, unique=True, help_text="Unique transaction reference")
    
    # Relationships
    tenant = models.ForeignKey('tenants.Organization', on_delete=models.CASCADE, related_name='transactions')
    invoice = models.ForeignKey('subscriptions.Invoice', on_delete=models.CASCADE, blank=True, null=True, related_name='transactions')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, blank=True, null=True)
    provider = models.ForeignKey(PaymentProvider, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='payment')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount minus fees")
    currency = models.CharField(max_length=3, default='ZAR')
    
    # Provider information
    external_id = models.CharField(max_length=255, blank=True, help_text="Provider's transaction ID")
    external_reference = models.CharField(max_length=255, blank=True)
    
    # Status tracking
    processed_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    failure_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    provider_response = models.JSONField(default=dict, blank=True, help_text="Raw provider response")
    
    class Meta:
        db_table = 'payments_transaction'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['reference']),
            models.Index(fields=['external_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.amount} {self.currency} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Calculate net amount
        self.net_amount = self.amount - self.fee_amount
        
        # Set processed_at when status changes to succeeded
        if self.status == 'succeeded' and not self.processed_at:
            self.processed_at = timezone.now()
        
        # Set failed_at when status changes to failed
        if self.status == 'failed' and not self.failed_at:
            self.failed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_successful(self):
        """Check if transaction was successful"""
        return self.status == 'succeeded'
    
    @property
    def is_pending(self):
        """Check if transaction is pending"""
        return self.status in ['pending', 'processing', 'requires_action']


class PaymentAttempt(models.Model):
    """
    Track payment attempts for invoices
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    invoice = models.ForeignKey('subscriptions.Invoice', on_delete=models.CASCADE, related_name='payment_attempts')
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='payment_attempt')
    
    # Attempt details
    attempt_number = models.PositiveIntegerField(help_text="Sequential attempt number for this invoice")
    is_automatic = models.BooleanField(default=True, help_text="Whether this was an automatic retry")
    
    # Timestamps
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'payments_payment_attempt'
        unique_together = ['invoice', 'attempt_number']
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['invoice', 'attempt_number']),
            models.Index(fields=['attempted_at']),
        ]
    
    def __str__(self):
        return f"Attempt #{self.attempt_number} for {self.invoice.invoice_number}"


class Refund(models.Model):
    """
    Refund records for transactions
    """
    REASON_CHOICES = [
        ('duplicate', 'Duplicate Payment'),
        ('fraudulent', 'Fraudulent'),
        ('requested_by_customer', 'Requested by Customer'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('service_issue', 'Service Issue'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    original_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='refunds')
    refund_transaction = models.OneToOneField(
        Transaction, 
        on_delete=models.CASCADE, 
        related_name='refund_record',
        blank=True, 
        null=True
    )
    
    # Refund details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='ZAR')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Provider information
    external_id = models.CharField(max_length=255, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments_refund'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['original_transaction']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Refund {self.amount} {self.currency} for {self.original_transaction.reference}"


class PaymentWebhook(models.Model):
    """
    Webhook events from payment providers
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    provider = models.ForeignKey(PaymentProvider, on_delete=models.CASCADE, related_name='webhooks')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, blank=True, null=True, related_name='webhooks')
    
    # Webhook details
    event_id = models.CharField(max_length=255, help_text="Provider's event ID")
    event_type = models.CharField(max_length=100)
    
    # Processing status
    is_processed = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    
    # Data
    payload = models.JSONField(help_text="Raw webhook payload")
    headers = models.JSONField(default=dict, help_text="HTTP headers")
    
    # Timestamps
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'payments_webhook'
        unique_together = ['provider', 'event_id']
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['is_processed', 'received_at']),
        ]
    
    def __str__(self):
        return f"{self.provider.name} - {self.event_type} ({self.event_id})"