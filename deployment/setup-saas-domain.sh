#!/bin/bash
# Setup script for saas.rozitech.com DNS and SSL configuration
# Run this on the production server: 154.65.107.211

set -e

echo "========================================="
echo "SaaS Admin Domain Setup Script"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking DNS resolution for saas.rozitech.com${NC}"
if nslookup saas.rozitech.com | grep -q "154.65.107.211"; then
    echo -e "${GREEN}✓ DNS is correctly configured${NC}"
else
    echo -e "${RED}✗ DNS not configured yet${NC}"
    echo ""
    echo "Please add the following DNS record:"
    echo "  Type: A"
    echo "  Name: saas"
    echo "  Value: 154.65.107.211"
    echo "  TTL: 3600"
    echo ""
    echo "After adding the DNS record, wait a few minutes for propagation and run this script again."
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Creating web root for Let's Encrypt${NC}"
mkdir -p /var/www/rozitech-saas-admin
chown -R www-data:www-data /var/www/rozitech-saas-admin
echo -e "${GREEN}✓ Web root created${NC}"

echo ""
echo -e "${YELLOW}Step 3: Updating nginx configuration${NC}"
# Backup existing config
if [ -f /etc/nginx/sites-available/rozitech-saas-admin ]; then
    cp /etc/nginx/sites-available/rozitech-saas-admin /etc/nginx/sites-available/rozitech-saas-admin.backup.$(date +%Y%m%d-%H%M%S)
    echo -e "${GREEN}✓ Backed up existing config${NC}"
fi

# Copy new config
cp /opt/rozitech-saas-admin/deployment/nginx-saas-admin-updated.conf /etc/nginx/sites-available/rozitech-saas-admin-temp

# Update to use HTTP only first (for certbot)
cat > /etc/nginx/sites-available/rozitech-saas-admin << 'EOF'
# Nginx configuration for Rozitech SaaS Admin - HTTP only (for initial setup)

upstream rozitech_saas_admin {
    server unix:/opt/rozitech-saas-admin/run/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name saas.rozitech.com admin.rozitech.com;

    # Allow Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/rozitech-saas-admin;
    }

    # Logging
    access_log /var/log/nginx/rozitech-saas-admin-access.log;
    error_log /var/log/nginx/rozitech-saas-admin-error.log;

    # Max upload size
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /opt/rozitech-saas-admin/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/rozitech-saas-admin/media/;
        expires 7d;
    }

    # API and application
    location / {
        proxy_pass http://rozitech_saas_admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # CORS headers for TeamSpace
        add_header 'Access-Control-Allow-Origin' 'https://teamspace.rozitech.com' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;

        # Timeouts
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
        send_timeout 120;
    }
}
EOF

echo -e "${GREEN}✓ Nginx config updated${NC}"

echo ""
echo -e "${YELLOW}Step 4: Testing nginx configuration${NC}"
nginx -t
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Nginx config is valid${NC}"
else
    echo -e "${RED}✗ Nginx config has errors${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Reloading nginx${NC}"
systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"

echo ""
echo -e "${YELLOW}Step 6: Obtaining SSL certificate with certbot${NC}"
certbot certonly --webroot -w /var/www/rozitech-saas-admin \
    -d saas.rozitech.com \
    -d admin.rozitech.com \
    --non-interactive --agree-tos \
    --email admin@rozitech.com \
    --keep-until-expiring

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSL certificate obtained${NC}"
else
    echo -e "${RED}✗ Failed to obtain SSL certificate${NC}"
    echo "You may need to run certbot manually"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 7: Installing final nginx configuration with SSL${NC}"
cp /etc/nginx/sites-available/rozitech-saas-admin-temp /etc/nginx/sites-available/rozitech-saas-admin
rm /etc/nginx/sites-available/rozitech-saas-admin-temp

echo ""
echo -e "${YELLOW}Step 8: Testing final nginx configuration${NC}"
nginx -t
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Final nginx config is valid${NC}"
else
    echo -e "${RED}✗ Nginx config has errors${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 9: Reloading nginx with SSL config${NC}"
systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded with SSL${NC}"

echo ""
echo "========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "========================================="
echo ""
echo "Your SaaS Admin API is now available at:"
echo "  - https://saas.rozitech.com"
echo "  - https://admin.rozitech.com"
echo ""
echo "Test endpoints:"
echo "  curl https://saas.rozitech.com/health/"
echo "  curl https://saas.rozitech.com/api/v1/services/"
echo ""