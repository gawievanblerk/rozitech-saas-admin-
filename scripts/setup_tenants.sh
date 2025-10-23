#!/bin/bash

# Setup script for django-tenants on rozitech-saas-admin
# This must be run ONCE before deploying the admin service

set -e

echo "=========================================="
echo "Django-Tenants Setup Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please create it first:"
    echo "  python3 -m venv venv"
    exit 1
fi

print_info "Step 1: Creating public schema with shared apps..."
echo "=== Starting migration"
python manage.py migrate_schemas --shared

print_success "Public schema created!"
echo ""

print_info "Step 2: Creating public tenant organization..."
python manage.py create_public_tenant

print_success "Public tenant created!"
echo ""

print_info "Step 3: Running tenant-specific migrations..."
python manage.py migrate_schemas

print_success "All schemas migrated!"
echo ""

print_success "=========================================="
print_success "Django-Tenants setup complete!"
print_success "=========================================="
echo ""
echo "You can now deploy the admin service normally."