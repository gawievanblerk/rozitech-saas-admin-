"""
Django settings for Rozitech SaaS Admin with Auth Server Integration
"""

from .base import *

# Rozitech Auth Server Configuration
ROZITECH_AUTH_SERVER_URL = env('ROZITECH_AUTH_SERVER_URL', default='http://localhost:4000')
ROZITECH_AUTH_SERVER_API_KEY = env('ROZITECH_AUTH_SERVER_API_KEY', default='test-api-key')
ROZITECH_AUTH_SERVER_TIMEOUT = env.int('ROZITECH_AUTH_SERVER_TIMEOUT', default=30)

# Use Rozitech Auth Server instead of local JWT
USE_ROZITECH_AUTH = env.bool('USE_ROZITECH_AUTH', default=True)

if USE_ROZITECH_AUTH:
    # Override REST Framework authentication to use Rozitech Auth Server
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
        'core.auth.rozitech_auth.RozitechJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Keep for admin
    ]
    
    # Add Rozitech auth backend
    AUTHENTICATION_BACKENDS = [
        'core.auth.rozitech_auth.RozitechAuthBackend',
        'django.contrib.auth.backends.ModelBackend',  # Keep for local admin
    ]
else:
    # Use original authentication
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ]

# CORS settings for auth server integration
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # API server
    "http://localhost:4000",  # Auth server
    "http://localhost:8000",  # SaaS admin (this app)
]

# Add auth server to allowed hosts
ALLOWED_HOSTS.extend(['localhost', '127.0.0.1', 'auth-server'])

# Health check settings
HEALTH_CHECK_SETTINGS = {
    'ROZITECH_AUTH_SERVER': {
        'url': ROZITECH_AUTH_SERVER_URL + '/health',
        'timeout': 5,
        'required': USE_ROZITECH_AUTH
    }
}

# Logging configuration for auth integration
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
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'core.auth': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'rozitech_auth': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Ensure logs directory exists
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)