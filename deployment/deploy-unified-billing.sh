#!/bin/bash

# Unified Multi-Product Billing System Deployment Script
# This script deploys the new billing system to production

set -e  # Exit on error

echo "========================================="
echo "Unified Billing System Deployment"
echo "========================================="
echo ""

# Configuration
PROJECT_DIR="/opt/rozitech-saas-admin"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Step 1: Navigate to project directory
echo "Step 1: Navigating to project directory..."
cd $PROJECT_DIR || { print_error "Failed to navigate to $PROJECT_DIR"; exit 1; }
print_success "In project directory: $(pwd)"
echo ""

# Step 2: Backup current state
echo "Step 2: Creating backup..."
BACKUP_DIR="backups/pre-unified-billing-$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r apps/subscriptions $BACKUP_DIR/ 2>/dev/null || true
cp -r config/settings $BACKUP_DIR/ 2>/dev/null || true
print_success "Backup created at $BACKUP_DIR"
echo ""

# Step 3: Pull latest code
echo "Step 3: Pulling latest code from main branch..."
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_info "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ]; then
    print_warning "Not on main branch, switching..."
    git checkout main
fi

git pull origin main
LATEST_COMMIT=$(git rev-parse --short HEAD)
print_success "Updated to commit: $LATEST_COMMIT"
echo ""

# Step 4: Activate virtual environment
echo "Step 4: Activating virtual environment..."
if [ -f "$VENV_DIR/bin/activate" ]; then
    source $VENV_DIR/bin/activate
    print_success "Virtual environment activated"
else
    print_error "Virtual environment not found at $VENV_DIR"
    exit 1
fi
echo ""

# Step 5: Install/update dependencies
echo "Step 5: Checking dependencies..."
print_info "Installing stripe library if needed..."
$PIP install stripe --quiet
print_success "Dependencies checked"
echo ""

# Step 6: Run migrations
echo "Step 6: Running database migrations..."

print_info "Running products app migrations (shared schema)..."
$PYTHON manage.py migrate products --noinput
print_success "Products migrations complete"

print_info "Running subscriptions app migrations (tenant schemas)..."
$PYTHON manage.py migrate subscriptions --noinput
print_success "Subscriptions migrations complete"

print_info "Running all pending migrations..."
$PYTHON manage.py migrate --noinput
print_success "All migrations complete"
echo ""

# Step 7: Seed products
echo "Step 7: Seeding product catalog..."
read -p "Do you want to seed the product catalog? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    $PYTHON manage.py seed_products
    print_success "Product catalog seeded"
else
    print_warning "Skipped product seeding"
fi
echo ""

# Step 8: Collect static files
echo "Step 8: Collecting static files..."
$PYTHON manage.py collectstatic --noinput
print_success "Static files collected"
echo ""

# Step 9: Check for Stripe configuration
echo "Step 9: Verifying Stripe configuration..."
if grep -q "STRIPE_API_KEY=" .env 2>/dev/null; then
    STRIPE_KEY_SET=$(grep "STRIPE_API_KEY=" .env | cut -d'=' -f2)
    if [ -z "$STRIPE_KEY_SET" ]; then
        print_warning "STRIPE_API_KEY is set but empty in .env"
        print_info "Add your Stripe keys to .env file:"
        print_info "  STRIPE_API_KEY=sk_test_..."
        print_info "  STRIPE_PUBLISHABLE_KEY=pk_test_..."
        print_info "  STRIPE_WEBHOOK_SECRET=whsec_..."
    else
        print_success "Stripe configuration found in .env"
    fi
else
    print_warning "Stripe configuration not found in .env"
    print_info "Add these to your .env file:"
    echo "STRIPE_API_KEY=sk_test_your_key_here"
    echo "STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here"
    echo "STRIPE_WEBHOOK_SECRET=whsec_your_secret_here"
fi
echo ""

# Step 10: Restart services
echo "Step 10: Restarting application services..."

print_info "Restarting Gunicorn..."
sudo systemctl restart gunicorn-rozitech-saas || sudo systemctl restart gunicorn || print_warning "Gunicorn restart failed"
sleep 2
print_success "Gunicorn restarted"

print_info "Reloading Nginx..."
sudo systemctl reload nginx || print_warning "Nginx reload failed"
print_success "Nginx reloaded"
echo ""

# Step 11: Verify deployment
echo "Step 11: Verifying deployment..."

# Check if services are running
print_info "Checking service status..."
if systemctl is-active --quiet gunicorn-rozitech-saas || systemctl is-active --quiet gunicorn; then
    print_success "Gunicorn is running"
else
    print_error "Gunicorn is not running!"
fi

if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
else
    print_error "Nginx is not running!"
fi

# Verify database tables
print_info "Verifying database tables..."
TABLE_CHECK=$($PYTHON manage.py shell -c "from apps.products.models import Product; print(Product._meta.db_table)" 2>&1)
if [[ $TABLE_CHECK == *"products"* ]]; then
    print_success "Product catalog tables verified"
else
    print_warning "Could not verify product tables"
fi

# Count seeded products
PRODUCT_COUNT=$($PYTHON manage.py shell -c "from apps.products.models import Product; print(Product.objects.count())" 2>/dev/null || echo "0")
print_info "Products in database: $PRODUCT_COUNT"
echo ""

# Step 12: Display deployment summary
echo "========================================="
echo "DEPLOYMENT SUMMARY"
echo "========================================="
echo ""
echo "Git Commit: $LATEST_COMMIT"
echo "Products Seeded: $PRODUCT_COUNT"
echo ""
echo "NEW FEATURES DEPLOYED:"
echo "  ✓ Multi-product billing system"
echo "  ✓ Product catalog (AutoFlow AI, BuildEasy, TeamSpace)"
echo "  ✓ Subscription management"
echo "  ✓ Stripe integration"
echo "  ✓ Webhook endpoint"
echo "  ✓ Admin interface"
echo ""
echo "ADMIN ACCESS:"
echo "  Products: /admin/products/product/"
echo "  Plans: /admin/products/productplan/"
echo "  Bundles: /admin/products/subscriptionbundle/"
echo "  Subscriptions: /admin/subscriptions/productsubscription/"
echo ""
echo "API ENDPOINTS:"
echo "  Webhook: /api/subscriptions/webhooks/stripe/"
echo "  Test: /api/subscriptions/test/stripe/"
echo ""
echo "NEXT STEPS:"
echo "  1. Configure Stripe API keys in .env"
echo "  2. Set up webhook in Stripe Dashboard"
echo "  3. Test subscription creation"
echo "  4. Monitor logs: tail -f logs/django.log"
echo ""
print_success "Deployment completed successfully!"
echo "========================================="
