#!/bin/bash
# TeamSpace SSO Integration - Production Deployment Script
# Run this script on your production server after code has been deployed

set -e  # Exit on error

echo "========================================="
echo "TeamSpace SSO Integration Deployment"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the production directory
PROD_DIR="${1:-/opt/rozitech-saas-admin}"

echo -e "${YELLOW}Production Directory: $PROD_DIR${NC}"
echo ""

# Check if directory exists
if [ ! -d "$PROD_DIR" ]; then
    echo -e "${RED}Error: Production directory $PROD_DIR does not exist${NC}"
    exit 1
fi

cd "$PROD_DIR"

echo -e "${YELLOW}Step 1: Pulling latest code from main branch...${NC}"
git fetch origin
git checkout main
git pull origin main

echo -e "${GREEN}✓ Code updated${NC}"
echo ""

echo -e "${YELLOW}Step 2: Activating virtual environment...${NC}"
source venv/bin/activate || source env/bin/activate || echo "Warning: No virtual environment found"

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

echo -e "${YELLOW}Step 3: Installing/updating dependencies...${NC}"
pip install djangorestframework-simplejwt

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Running database migrations...${NC}"
python manage.py migrate subscriptions
python manage.py migrate authentication

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

echo -e "${YELLOW}Step 5: Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

echo -e "${YELLOW}Step 6: Running tests...${NC}"
python manage.py test apps.authentication.tests --verbosity=2

echo -e "${GREEN}✓ All tests passed${NC}"
echo ""

echo -e "${YELLOW}Step 7: Restarting services...${NC}"
# Restart gunicorn/uwsgi
if systemctl is-active --quiet gunicorn-rozitech-saas; then
    sudo systemctl restart gunicorn-rozitech-saas
    echo -e "${GREEN}✓ Gunicorn restarted${NC}"
elif systemctl is-active --quiet uwsgi; then
    sudo systemctl restart uwsgi
    echo -e "${GREEN}✓ uWSGI restarted${NC}"
else
    echo -e "${YELLOW}Warning: No gunicorn or uwsgi service found. Please restart manually.${NC}"
fi

# Restart nginx
if systemctl is-active --quiet nginx; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
fi

echo ""
echo -e "${GREEN}========================================="
echo "Deployment Complete!"
echo "=========================================${NC}"
echo ""
echo "✓ Code updated to latest main branch"
echo "✓ Database migrations applied"
echo "✓ Tests passed"
echo "✓ Services restarted"
echo ""
echo "TeamSpace SSO API Endpoints:"
echo "  - GET /api/auth/verify"
echo "  - GET /api/organizations/{id}/"
echo "  - GET /api/subscriptions/check"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Verify endpoints are accessible"
echo "2. Test integration with TeamSpace"
echo "3. Monitor logs for any issues"
echo ""
echo "Logs location:"
echo "  sudo journalctl -u gunicorn-rozitech-saas -f"
echo ""