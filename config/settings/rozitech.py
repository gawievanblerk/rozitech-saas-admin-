"""
Rozitech-specific production settings
"""
from .production import *
import os

# Rozitech branding
COMPANY_NAME = "Rozitech"
SITE_NAME = "Rozitech SaaS Platform"

# Domain configuration
PRIMARY_DOMAIN = os.getenv('PRIMARY_DOMAIN', 'rozitech.com')
SECONDARY_DOMAIN = os.getenv('SECONDARY_DOMAIN', 'rozitech.co.za')
APP_DOMAIN = os.getenv('APP_DOMAIN', 'app.rozitech.com')

# Multi-domain support
ALLOWED_HOSTS = [
    PRIMARY_DOMAIN,
    f'www.{PRIMARY_DOMAIN}',
    SECONDARY_DOMAIN,
    f'www.{SECONDARY_DOMAIN}',
    APP_DOMAIN,
    f'admin.{PRIMARY_DOMAIN}',
    f'*.{PRIMARY_DOMAIN}',  # Tenant subdomains
    f'*.{SECONDARY_DOMAIN}',  # SA tenant subdomains
    'localhost',
    '127.0.0.1',
]

# Email configuration with Rozitech mail servers
EMAIL_HOST = os.getenv('EMAIL_HOST', f'mail.{PRIMARY_DOMAIN}')
DEFAULT_FROM_EMAIL = f'Rozitech SaaS <noreply@{PRIMARY_DOMAIN}>'
SERVER_EMAIL = f'Rozitech Server <server@{PRIMARY_DOMAIN}>'

# Business email addresses
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', f'contact@{PRIMARY_DOMAIN}')
SALES_EMAIL = os.getenv('SALES_EMAIL', f'sales@{PRIMARY_DOMAIN}')
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', f'support@{PRIMARY_DOMAIN}')
MARKETING_EMAIL = os.getenv('MARKETING_EMAIL', f'marketing@{PRIMARY_DOMAIN}')

# South African specific emails
CONTACT_ZA_EMAIL = os.getenv('CONTACT_ZA_EMAIL', f'contact@{SECONDARY_DOMAIN}')
SALES_ZA_EMAIL = os.getenv('SALES_ZA_EMAIL', f'sales@{SECONDARY_DOMAIN}')
SUPPORT_ZA_EMAIL = os.getenv('SUPPORT_ZA_EMAIL', f'support@{SECONDARY_DOMAIN}')

# Regional settings
USE_TZ = True
TIME_ZONE = os.getenv('DEFAULT_TIMEZONE', 'Africa/Johannesburg')

# Localization
LANGUAGE_CODE = 'en-za'  # South African English
LANGUAGES = [
    ('en', 'English'),
    ('en-za', 'English (South Africa)'),
    ('af', 'Afrikaans'),
]

# Currency settings
DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'ZAR')
SECONDARY_CURRENCY = os.getenv('SECONDARY_CURRENCY', 'USD')
CURRENCY_CHOICES = [
    ('ZAR', 'South African Rand'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('GBP', 'British Pound'),
]

# Tax settings
VAT_RATE = float(os.getenv('VAT_RATE', '0.15'))  # 15% VAT in South Africa
TAX_REGISTRATION_NUMBER = os.getenv('TAX_REGISTRATION_NUMBER', '')

# Payment gateway settings
PAYMENT_GATEWAYS = {
    'stripe': {
        'enabled': True,
        'currencies': ['USD', 'EUR', 'GBP'],
        'regions': ['international'],
        'public_key': os.getenv('STRIPE_PUBLISHABLE_KEY'),
        'secret_key': os.getenv('STRIPE_SECRET_KEY'),
    },
    'payfast': {
        'enabled': True,
        'currencies': ['ZAR'],
        'regions': ['south-africa'],
        'merchant_id': os.getenv('PAYFAST_MERCHANT_ID'),
        'merchant_key': os.getenv('PAYFAST_MERCHANT_KEY'),
        'passphrase': os.getenv('PAYFAST_PASSPHRASE'),
        'sandbox': os.getenv('PAYFAST_SANDBOX', 'False').lower() == 'true',
    },
    'yoco': {
        'enabled': True,
        'currencies': ['ZAR'],
        'regions': ['south-africa'],
        'secret_key': os.getenv('YOCO_SECRET_KEY'),
        'public_key': os.getenv('YOCO_PUBLIC_KEY'),
    }
}

# Regional routing
REGIONAL_SETTINGS = {
    'international': {
        'domain': PRIMARY_DOMAIN,
        'currency': 'USD',
        'payment_gateways': ['stripe'],
        'tax_rate': 0.0,  # No VAT for international
        'contact_email': CONTACT_EMAIL,
        'sales_email': SALES_EMAIL,
    },
    'south-africa': {
        'domain': SECONDARY_DOMAIN,
        'currency': 'ZAR',
        'payment_gateways': ['payfast', 'yoco'],
        'tax_rate': VAT_RATE,
        'contact_email': CONTACT_ZA_EMAIL,
        'sales_email': SALES_ZA_EMAIL,
    }
}

# Compliance settings
GDPR_COMPLIANCE = True
POPI_COMPLIANCE = True  # Protection of Personal Information Act (South Africa)
DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', '2555'))  # 7 years

# Hetzner Object Storage
if os.getenv('STORAGE_BACKEND') == 'hetzner':
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    
    AWS_ACCESS_KEY_ID = os.getenv('HETZNER_STORAGE_ACCESS_KEY')
    AWS_SECRET_ACCESS_KEY = os.getenv('HETZNER_STORAGE_SECRET_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('HETZNER_STORAGE_BUCKET', 'rozitech-saas-media')
    AWS_S3_ENDPOINT_URL = f"https://{os.getenv('HETZNER_STORAGE_ENDPOINT')}"
    AWS_S3_REGION_NAME = 'eu-central'
    AWS_S3_CUSTOM_DOMAIN = os.getenv('CDN_DOMAIN', f'cdn.{PRIMARY_DOMAIN}')
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

# CDN settings
if os.getenv('USE_CDN', 'False').lower() == 'true':
    STATIC_URL = f"https://{os.getenv('CDN_DOMAIN', f'cdn.{PRIMARY_DOMAIN}')}/static/"
    MEDIA_URL = f"https://{os.getenv('CDN_DOMAIN', f'cdn.{PRIMARY_DOMAIN}')}/media/"

# Webhook configuration
WEBHOOK_ENDPOINTS = {
    'provisioning': f"https://{PRIMARY_DOMAIN}/webhooks/provisioning/",
    'payments': f"https://{PRIMARY_DOMAIN}/webhooks/payments/",
    'tenant_events': f"https://{PRIMARY_DOMAIN}/webhooks/tenant-events/",
}

# Marketing settings
MARKETING_FEATURES = {
    'newsletter_signup': True,
    'demo_requests': True,
    'contact_forms': True,
    'live_chat': True,
    'analytics': True,
}

# Analytics and tracking
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID')
FACEBOOK_PIXEL_ID = os.getenv('FACEBOOK_PIXEL_ID')

# Social media links
SOCIAL_MEDIA = {
    'linkedin': 'https://linkedin.com/company/rozitech',
    'twitter': 'https://twitter.com/rozitech',
    'facebook': 'https://facebook.com/rozitech',
    'youtube': 'https://youtube.com/rozitech',
}

# Support settings
SUPPORT_SETTINGS = {
    'helpdesk_url': f'https://support.{PRIMARY_DOMAIN}',
    'knowledge_base_url': f'https://help.{PRIMARY_DOMAIN}',
    'status_page_url': f'https://status.{PRIMARY_DOMAIN}',
    'community_url': f'https://community.{PRIMARY_DOMAIN}',
}

# Multi-tenant specific settings
TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.TenantDomain"

# Provisioning settings
PROVISIONING_PROVIDER = os.getenv('PROVISIONING_PROVIDER', 'docker')
PROVISIONING_SETTINGS = {
    'docker': {
        'network_prefix': 'rozitech',
        'volume_prefix': 'rozitech',
        'registry_url': 'registry.rozitech.com',
    },
    'kubernetes': {
        'namespace_prefix': 'rozitech',
        'cluster_domain': 'cluster.local',
        'ingress_class': 'nginx',
    }
}

# Security settings
SECURITY_SETTINGS = {
    'force_https': True,
    'ssl_redirect': True,
    'hsts_seconds': 31536000,  # 1 year
    'content_type_nosniff': True,
    'browser_xss_filter': True,
    'x_frame_options': 'DENY',
}

# Rate limiting (per minute)
RATE_LIMITS = {
    'api': 100,
    'login': 5,
    'signup': 3,
    'contact': 10,
    'password_reset': 3,
}

# Feature flags
FEATURE_FLAGS = {
    'service_provisioning': True,
    'multi_tenant': True,
    'payment_processing': True,
    'email_marketing': True,
    'analytics_dashboard': True,
    'api_access': True,
    'webhooks': True,
    'backup_automation': True,
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/rozitech.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.services': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.tenants': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Health check settings
HEALTH_CHECK_URL = f"https://{PRIMARY_DOMAIN}/health/"
HEALTH_CHECKS = [
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
]

# Celery configuration for Rozitech
CELERY_TASK_ROUTES = {
    'apps.services.tasks.provision_service': {'queue': 'provisioning'},
    'apps.services.tasks.check_service_health': {'queue': 'monitoring'},
    'apps.services.tasks.collect_service_metrics': {'queue': 'monitoring'},
    'apps.payments.tasks.process_payment': {'queue': 'payments'},
    'apps.notifications.tasks.send_email': {'queue': 'email'},
}

CELERY_TASK_ANNOTATIONS = {
    'apps.services.tasks.provision_service': {'rate_limit': '10/m'},
    'apps.services.tasks.check_service_health': {'rate_limit': '30/m'},
    'apps.notifications.tasks.send_email': {'rate_limit': '100/m'},
}

# Backup settings
BACKUP_SETTINGS = {
    'database': {
        'enabled': True,
        'schedule': '0 2 * * *',  # Daily at 2 AM
        'retention_days': 30,
        'compression': True,
    },
    'media': {
        'enabled': True,
        'schedule': '0 3 * * *',  # Daily at 3 AM
        'retention_days': 30,
        'compression': True,
    },
    'remote_storage': {
        'enabled': True,
        'provider': 'hetzner',
        'bucket': 'rozitech-backups',
    }
}