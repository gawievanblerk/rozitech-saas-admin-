#!/bin/bash

# Rozitech SaaS Platform - GitHub Secrets Setup Script
# This script helps you generate and configure the necessary secrets for CI/CD

set -e

echo "🔐 Setting up GitHub Secrets for Rozitech SaaS Platform"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create deployment directory
mkdir -p deployment/secrets
cd deployment

print_info "Step 1: Generate SSH Key for Deployment"
echo "========================================"

# Generate SSH key if it doesn't exist
if [ ! -f "secrets/github-deploy-key" ]; then
    print_info "Generating new SSH key for GitHub Actions deployment..."
    ssh-keygen -t ed25519 -f secrets/github-deploy-key -N "" -C "github-actions@rozitech.com"
    print_status "SSH key generated: secrets/github-deploy-key"
else
    print_warning "SSH key already exists: secrets/github-deploy-key"
fi

print_info "Step 2: Display Public Key for Server Setup"
echo "============================================"

echo ""
echo "📋 Copy this PUBLIC KEY and add it to your Hetzner server:"
echo "-----------------------------------------------------------"
cat secrets/github-deploy-key.pub
echo ""
echo "Run this command on your Hetzner server:"
echo "echo '$(cat secrets/github-deploy-key.pub)' >> ~/.ssh/authorized_keys"
echo ""

print_info "Step 3: Generate Environment Files"
echo "==================================="

# Create production environment template
cat > secrets/.env.production.template << 'EOF'
# Rozitech SaaS Platform - Production Environment
# Copy this to .env.production and fill in your actual values

# Domain Configuration
PRIMARY_DOMAIN=rozitech.com
SECONDARY_DOMAIN=rozitech.co.za
APP_DOMAIN=app.rozitech.com

# Database (generate strong passwords)
DB_NAME=rozitech_saas
DB_USER=rozitech
DB_PASSWORD=REPLACE_WITH_STRONG_PASSWORD

# Django (generate strong secret key)
SECRET_KEY=REPLACE_WITH_DJANGO_SECRET_KEY
DJANGO_SETTINGS_MODULE=config.settings.rozitech
DEBUG=False
ALLOWED_HOSTS=rozitech.com,www.rozitech.com,rozitech.co.za,www.rozitech.co.za,app.rozitech.com,*.rozitech.com,*.rozitech.co.za

# Email Configuration
EMAIL_HOST=mail.rozitech.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@rozitech.com
EMAIL_HOST_PASSWORD=REPLACE_WITH_EMAIL_PASSWORD
DEFAULT_FROM_EMAIL=Rozitech SaaS <noreply@rozitech.com>

# Business Emails
CONTACT_EMAIL=contact@rozitech.com
SALES_EMAIL=sales@rozitech.com
SUPPORT_EMAIL=support@rozitech.com
MARKETING_EMAIL=marketing@rozitech.com
CONTACT_ZA_EMAIL=contact@rozitech.co.za
SALES_ZA_EMAIL=sales@rozitech.co.za

# Storage (Hetzner Object Storage)
STORAGE_BACKEND=hetzner
HETZNER_STORAGE_ENDPOINT=fsn1.rozitech.storage.hetzner.cloud
HETZNER_STORAGE_ACCESS_KEY=REPLACE_WITH_HETZNER_ACCESS_KEY
HETZNER_STORAGE_SECRET_KEY=REPLACE_WITH_HETZNER_SECRET_KEY
HETZNER_STORAGE_BUCKET=rozitech-saas-media

# CDN
USE_CDN=True
CDN_DOMAIN=cdn.rozitech.com

# Payment Gateways
STRIPE_PUBLISHABLE_KEY=pk_live_REPLACE_WITH_STRIPE_PUBLIC_KEY
STRIPE_SECRET_KEY=sk_live_REPLACE_WITH_STRIPE_SECRET_KEY
PAYFAST_MERCHANT_ID=REPLACE_WITH_PAYFAST_MERCHANT_ID
PAYFAST_MERCHANT_KEY=REPLACE_WITH_PAYFAST_MERCHANT_KEY
PAYFAST_PASSPHRASE=REPLACE_WITH_PAYFAST_PASSPHRASE
YOCO_SECRET_KEY=sk_live_REPLACE_WITH_YOCO_SECRET_KEY

# Webhooks
WEBHOOK_URL=https://rozitech.com/webhooks/provisioning/
WEBHOOK_SECRET=REPLACE_WITH_WEBHOOK_SECRET

# Monitoring
SENTRY_DSN=REPLACE_WITH_SENTRY_DSN
GOOGLE_ANALYTICS_ID=G-REPLACE_WITH_GA_ID

# Regional Settings
DEFAULT_TIMEZONE=Africa/Johannesburg
DEFAULT_CURRENCY=ZAR
VAT_RATE=0.15

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF

# Create staging environment template
cat > secrets/.env.staging.template << 'EOF'
# Rozitech SaaS Platform - Staging Environment

# Domain Configuration
PRIMARY_DOMAIN=staging.rozitech.com
SECONDARY_DOMAIN=staging.rozitech.co.za
APP_DOMAIN=app.staging.rozitech.com

# Database
DB_NAME=rozitech_saas_staging
DB_USER=rozitech_staging
DB_PASSWORD=REPLACE_WITH_STAGING_DB_PASSWORD

# Django
SECRET_KEY=REPLACE_WITH_STAGING_SECRET_KEY
DJANGO_SETTINGS_MODULE=config.settings.rozitech
DEBUG=True
ALLOWED_HOSTS=staging.rozitech.com,*.staging.rozitech.com,*.staging.rozitech.co.za

# Email (use test configuration)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Payment Gateways (use sandbox/test keys)
STRIPE_PUBLISHABLE_KEY=pk_test_REPLACE_WITH_STRIPE_TEST_KEY
STRIPE_SECRET_KEY=sk_test_REPLACE_WITH_STRIPE_TEST_KEY
PAYFAST_MERCHANT_ID=10000100
PAYFAST_MERCHANT_KEY=46f0cd694581a
PAYFAST_PASSPHRASE=
PAYFAST_SANDBOX=True

# Storage (use local storage for staging)
STORAGE_BACKEND=local
USE_CDN=False

# Monitoring (optional for staging)
SENTRY_DSN=
GOOGLE_ANALYTICS_ID=

# Redis
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1
EOF

print_status "Environment templates created:"
print_info "  - secrets/.env.production.template"
print_info "  - secrets/.env.staging.template"

print_info "Step 4: Generate Secure Passwords and Keys"
echo "=========================================="

# Generate secure passwords
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -base64 64)
WEBHOOK_SECRET=$(openssl rand -base64 32)
STAGING_DB_PASSWORD=$(openssl rand -base64 32)
STAGING_SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || openssl rand -base64 64)

echo "Generated secure credentials:"
echo "=========================="
echo "Production DB Password: $DB_PASSWORD"
echo "Production Secret Key: $SECRET_KEY"
echo "Webhook Secret: $WEBHOOK_SECRET"
echo "Staging DB Password: $STAGING_DB_PASSWORD"
echo "Staging Secret Key: $STAGING_SECRET_KEY"
echo ""

print_info "Step 5: Create GitHub Secrets Configuration"
echo "============================================"

# Get server IP
print_info "What is your Hetzner server IP address?"
read -p "Server IP: " SERVER_IP

# Create secrets summary
cat > secrets/github-secrets.txt << EOF
GitHub Repository Secrets Configuration
=======================================

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these Repository Secrets:

## Server Access
HETZNER_SERVER_HOST = $SERVER_IP
HETZNER_SERVER_USER = root
HETZNER_SSH_KEY = (paste the PRIVATE key content from secrets/github-deploy-key)

## Environment Files (Base64 encoded)
PRODUCTION_ENV = (base64 encoded content of your .env.production file)
STAGING_ENV = (base64 encoded content of your .env.staging file)

## Docker Registry (if using private registry)
DOCKER_REGISTRY_URL = registry.rozitech.com
DOCKER_REGISTRY_USERNAME = your-registry-username
DOCKER_REGISTRY_PASSWORD = your-registry-password

## Notifications (optional)
SLACK_WEBHOOK_URL = your-slack-webhook-url
DISCORD_WEBHOOK_URL = your-discord-webhook-url

## Generated Credentials
DB_PASSWORD = $DB_PASSWORD
SECRET_KEY = $SECRET_KEY
WEBHOOK_SECRET = $WEBHOOK_SECRET
STAGING_DB_PASSWORD = $STAGING_DB_PASSWORD
STAGING_SECRET_KEY = $STAGING_SECRET_KEY
EOF

print_status "GitHub secrets configuration saved to: secrets/github-secrets.txt"

print_info "Step 6: Create Environment Files Helper Script"
echo "=============================================="

cat > create-env-files.sh << 'EOF'
#!/bin/bash

# Helper script to create environment files from templates

echo "Creating production environment file..."
cp secrets/.env.production.template secrets/.env.production

echo "Creating staging environment file..."
cp secrets/.env.staging.template secrets/.env.staging

echo ""
echo "📝 Next steps:"
echo "1. Edit secrets/.env.production with your actual production values"
echo "2. Edit secrets/.env.staging with your actual staging values"
echo "3. Encode the files for GitHub secrets:"
echo ""
echo "   # Production environment (base64)"
echo "   base64 -i secrets/.env.production"
echo ""
echo "   # Staging environment (base64)"
echo "   base64 -i secrets/.env.staging"
echo ""
echo "4. Add the base64 output to GitHub secrets as:"
echo "   - PRODUCTION_ENV"
echo "   - STAGING_ENV"
EOF

chmod +x create-env-files.sh

print_status "Environment helper script created: create-env-files.sh"

print_info "Step 7: Display Summary"
echo "======================"

echo ""
print_status "🎉 GitHub Secrets Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Add the public key to your Hetzner server authorized_keys"
echo "2. Run './create-env-files.sh' to create environment files"
echo "3. Edit the environment files with your actual values"
echo "4. Follow the instructions in 'secrets/github-secrets.txt'"
echo "5. Configure the GitHub secrets in your repository"
echo ""
echo "📁 Files created:"
echo "  - secrets/github-deploy-key (private key)"
echo "  - secrets/github-deploy-key.pub (public key)"
echo "  - secrets/.env.production.template"
echo "  - secrets/.env.staging.template"
echo "  - secrets/github-secrets.txt"
echo "  - create-env-files.sh"
echo ""
echo "🔐 Important Security Notes:"
echo "  - Never commit the secrets/ directory to git"
echo "  - Keep your private key secure"
echo "  - Use strong passwords for production"
echo "  - Rotate secrets regularly"
echo ""

print_warning "Remember to add the public key to your server before testing deployment!"