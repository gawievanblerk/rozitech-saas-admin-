#!/usr/bin/env python
"""
Simple setup script for Rozitech SaaS Admin Platform
Uses SQLite temporarily to get the platform running quickly
"""
import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - Compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_simple_settings():
    """Create simplified settings for quick start"""
    print("⚙️  Creating simplified settings...")
    
    settings_content = '''"""
Simple settings for quick development start
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = 'django-insecure-for-development-only-change-in-production'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.simple_urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Rozitech SaaS Admin API',
    'DESCRIPTION': 'API for the Rozitech SaaS administration platform',
    'VERSION': '1.0.0',
}

CORS_ALLOW_ALL_ORIGINS = True
'''
    
    settings_file = Path('config/settings/quickstart.py')
    settings_file.write_text(settings_content)
    print("✅ Simplified settings created")

def create_simple_urls():
    """Create simplified URL configuration"""
    print("🔗 Creating simplified URLs...")
    
    urls_content = '''"""
Simple URL configuration for quick start
"""
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

def home_view(request):
    return JsonResponse({
        'message': 'Welcome to Rozitech SaaS Admin Platform!',
        'status': 'running',
        'features': [
            'Multi-tenant architecture ready',
            'Subscription management',
            'Payment processing framework',
            'Service orchestration',
            'RESTful API'
        ],
        'api_docs': '/api/docs/',
        'admin': '/admin/'
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
'''
    
    urls_file = Path('config/simple_urls.py')
    urls_file.write_text(urls_content)
    print("✅ Simplified URLs created")

def run_migrations():
    """Run Django migrations"""
    print("🗄️  Setting up database...")
    try:
        # Run migrations
        subprocess.run([
            sys.executable, "manage.py", "migrate", 
            "--settings=config.settings.quickstart"
        ], check=True)
        print("✅ Database setup complete")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_superuser():
    """Create Django superuser"""
    print("👤 Creating admin user...")
    try:
        # Create superuser non-interactively
        env = os.environ.copy()
        env.update({
            'DJANGO_SUPERUSER_USERNAME': 'admin',
            'DJANGO_SUPERUSER_EMAIL': 'admin@rozitech.co.za',
            'DJANGO_SUPERUSER_PASSWORD': 'admin123'
        })
        
        subprocess.run([
            sys.executable, "manage.py", "createsuperuser", "--noinput",
            "--settings=config.settings.quickstart"
        ], env=env, check=True)
        print("✅ Admin user created (admin/admin123)")
        return True
    except subprocess.CalledProcessError:
        print("ℹ️  Admin user already exists or creation skipped")
        return True

def start_server():
    """Start the development server"""
    print("🚀 Starting development server...")
    print("\n" + "="*60)
    print("🎉 ROZITECH SAAS ADMIN PLATFORM")
    print("="*60)
    print(f"🌐 Server: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/api/docs/")
    print(f"⚙️  Admin: http://localhost:8000/admin/ (admin/admin123)")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        subprocess.run([
            sys.executable, "manage.py", "runserver", "0.0.0.0:8000",
            "--settings=config.settings.quickstart"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Platform ready for development!")

def main():
    """Main setup function"""
    print("🏗️  ROZITECH SAAS ADMIN - QUICK SETUP")
    print("="*50)
    print()
    
    if not check_python_version():
        return
    
    # Skip dependency installation if already done
    print("📦 Checking dependencies...")
    
    create_simple_settings()
    create_simple_urls()
    
    if not run_migrations():
        return
    
    create_superuser()
    start_server()

if __name__ == "__main__":
    main()