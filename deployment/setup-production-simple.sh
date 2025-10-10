#!/bin/bash
# Simple Production Setup for TeamSpace SSO API
# This script sets up the Django app with minimal configuration
# Run this on the production server: /opt/rozitech-saas-admin

set -e  # Exit on error

echo "========================================="
echo "TeamSpace SSO API - Simple Production Setup"
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

echo -e "${YELLOW}Step 1: Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

echo -e "${YELLOW}Step 2: Setting Django settings to quickstart (simple SQLite setup)...${NC}"
export DJANGO_SETTINGS_MODULE=config.settings.quickstart

echo -e "${GREEN}✓ Django settings configured${NC}"
echo ""

echo -e "${YELLOW}Step 3: Running database migrations...${NC}"
python manage.py migrate

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Creating superuser (for admin access)...${NC}"
echo "You can create a superuser later with: python manage.py createsuperuser"
echo ""

echo -e "${YELLOW}Step 5: Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}✓ Static files collected${NC}"
echo ""

echo -e "${YELLOW}Step 6: Running tests...${NC}"
python manage.py test apps.authentication.tests --verbosity=2

echo -e "${GREEN}✓ All tests passed${NC}"
echo ""

echo -e "${GREEN}========================================="
echo "Setup Complete!"
echo "=========================================${NC}"
echo ""
echo "Next Steps:"
echo ""
echo "1. Create Gunicorn systemd service:"
echo "   sudo nano /etc/systemd/system/rozitech-saas-admin.service"
echo ""
echo "2. Add this content to the service file:"
echo "   [Unit]"
echo "   Description=Rozitech SaaS Admin - TeamSpace SSO API"
echo "   After=network.target"
echo ""
echo "   [Service]"
echo "   Type=notify"
echo "   User=root"
echo "   Group=root"
echo "   RuntimeDirectory=gunicorn"
echo "   WorkingDirectory=/opt/rozitech-saas-admin"
echo "   Environment=\"DJANGO_SETTINGS_MODULE=config.settings.quickstart\""
echo "   ExecStart=/opt/rozitech-saas-admin/venv/bin/gunicorn \\"
echo "       --workers 3 \\"
echo "       --bind unix:/run/gunicorn.sock \\"
echo "       config.wsgi:application"
echo "   ExecReload=/bin/kill -s HUP \$MAINPID"
echo "   KillMode=mixed"
echo "   TimeoutStopSec=5"
echo "   PrivateTmp=true"
echo ""
echo "   [Install]"
echo "   WantedBy=multi-user.target"
echo ""
echo "3. Enable and start the service:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable rozitech-saas-admin"
echo "   sudo systemctl start rozitech-saas-admin"
echo "   sudo systemctl status rozitech-saas-admin"
echo ""
echo "4. Configure Nginx to proxy to Gunicorn:"
echo "   sudo nano /etc/nginx/sites-available/rozitech-saas-admin"
echo ""
echo "5. Test the API endpoints:"
echo "   curl -I http://localhost:8000/api/docs/"
echo ""
