"""
Full platform settings with all SaaS features enabled
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Override SHARED_APPS to include all our models but without tenants for now
SHARED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    
    # Our apps - start with core SaaS models
    'core',
    'apps.tenants',
    'apps.subscriptions',
    # 'apps.payments',      # Temporarily disabled - needs tenant reference updates
    # 'apps.services',      # Temporarily disabled - needs tenant reference updates
    'apps.analytics',
    'apps.notifications',
]

# Use standard Django apps for now (no multi-tenancy yet)
INSTALLED_APPS = SHARED_APPS + [
    'django_extensions',
    # 'debug_toolbar',  # Temporarily disabled due to URL conflict
]

# Remove tenant middleware for this setup
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',  # Temporarily disabled
]

ROOT_URLCONF = 'config.urls_simple'

# PostgreSQL Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'rozitech_saas_admin_dev',
        'USER': 'postgres',
        'PASSWORD': '',  # Empty for local development
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Remove tenant-specific settings for now
DATABASE_ROUTERS = ()

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Debug toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False

# Cache (use dummy cache for development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Static files (development)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# CORS settings (more permissive for development)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True