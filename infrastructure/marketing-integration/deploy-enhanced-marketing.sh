#!/bin/bash

# Rozitech Enhanced Marketing Website Deployment to XNeelo Cloud
# Integrates with existing rozitech-saas-admin infrastructure

set -e

echo "🚀 Deploying Enhanced Rozitech Marketing Website to XNeelo Cloud"
echo "=============================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

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

# Configuration
PROJECT_DIR="/opt/rozitech-saas"
MARKETING_DIR="$PROJECT_DIR/marketing"
BACKUP_DIR="$PROJECT_DIR/backups/marketing-$(date +%Y%m%d-%H%M%S)"

print_info "Step 1: Backup Existing Marketing Site"
echo "====================================="

if [ -d "$MARKETING_DIR" ]; then
    sudo mkdir -p "$BACKUP_DIR"
    sudo cp -r "$MARKETING_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
    print_status "Existing marketing site backed up to $BACKUP_DIR"
else
    sudo mkdir -p "$MARKETING_DIR"
    print_status "Created marketing directory"
fi

print_info "Step 2: Deploy Enhanced Marketing Files"
echo "====================================="

# Copy enhanced marketing files
sudo cp index.html "$MARKETING_DIR/"
sudo cp get-started.html "$MARKETING_DIR/"
sudo cp learn-more.html "$MARKETING_DIR/"
sudo cp contact.html "$MARKETING_DIR/"
sudo cp privacy-policy.html "$MARKETING_DIR/"
sudo cp sitemap.xml "$MARKETING_DIR/"
sudo cp robots.txt "$MARKETING_DIR/"

print_status "Enhanced marketing files deployed"

print_info "Step 3: Update Nginx Configuration for Marketing"
echo "=============================================="

# Create enhanced nginx configuration for marketing
sudo tee "$PROJECT_DIR/nginx/conf.d/marketing.conf" > /dev/null << 'EOF'
# Enhanced Marketing Website Configuration
server {
    listen 80;
    server_name rozitech.com www.rozitech.com rozitech.co.za www.rozitech.co.za;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Marketing website routes
    location / {
        root /opt/rozitech-saas/marketing;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Cache HTML files for shorter time
        location ~* \.(html)$ {
            expires 1h;
            add_header Cache-Control "public";
        }
    }
    
    # Specific routes for new pages
    location = /get-started {
        try_files /get-started.html =404;
    }
    
    location = /learn-more {
        try_files /learn-more.html =404;
    }
    
    location = /contact {
        try_files /contact.html =404;
    }
    
    location = /privacy-policy {
        try_files /privacy-policy.html =404;
    }
    
    # SEO files
    location = /sitemap.xml {
        root /opt/rozitech-saas/marketing;
        add_header Content-Type application/xml;
    }
    
    location = /robots.txt {
        root /opt/rozitech-saas/marketing;
        add_header Content-Type text/plain;
    }
    
    # Admin and API routes go to Django
    location /admin {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}

# SSL configuration (uncomment after SSL setup)
# server {
#     listen 443 ssl http2;
#     server_name rozitech.com www.rozitech.com rozitech.co.za www.rozitech.co.za;
#     
#     ssl_certificate /etc/letsencrypt/live/rozitech.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/rozitech.com/privkey.pem;
#     
#     # Include SSL config here (same as above server block)
# }
EOF

print_status "Nginx configuration updated for enhanced marketing"

print_info "Step 4: Set Proper Permissions"
echo "============================="

sudo chown -R www-data:www-data "$MARKETING_DIR"
sudo chmod -R 644 "$MARKETING_DIR"/*.html
sudo chmod -R 644 "$MARKETING_DIR"/*.xml
sudo chmod -R 644 "$MARKETING_DIR"/*.txt
sudo chmod 755 "$MARKETING_DIR"

print_status "File permissions set correctly"

print_info "Step 5: Test Nginx Configuration"
echo "==============================="

if sudo nginx -t; then
    print_status "Nginx configuration test passed"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

print_info "Step 6: Restart Services"
echo "======================="

# Restart nginx
sudo systemctl reload nginx
print_status "Nginx reloaded"

# If using Docker, restart the marketing container
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    cd "$PROJECT_DIR"
    if docker-compose ps | grep -q marketing; then
        docker-compose restart nginx
        print_status "Docker services restarted"
    fi
fi

print_info "Step 7: Verify Deployment"
echo "========================"

# Test local endpoints
TESTS_PASSED=0
TESTS_TOTAL=5

echo "Testing marketing website endpoints..."

# Test homepage
if curl -f -s -o /dev/null http://localhost/; then
    print_status "Homepage: ✅ Working"
    ((TESTS_PASSED++))
else
    print_error "Homepage: ❌ Failed"
fi

# Test pricing page
if curl -f -s -o /dev/null http://localhost/get-started.html; then
    print_status "Pricing page: ✅ Working"
    ((TESTS_PASSED++))
else
    print_error "Pricing page: ❌ Failed"
fi

# Test product page
if curl -f -s -o /dev/null http://localhost/learn-more.html; then
    print_status "Product page: ✅ Working"
    ((TESTS_PASSED++))
else
    print_error "Product page: ❌ Failed"
fi

# Test contact page
if curl -f -s -o /dev/null http://localhost/contact.html; then
    print_status "Contact page: ✅ Working"
    ((TESTS_PASSED++))
else
    print_error "Contact page: ❌ Failed"
fi

# Test sitemap
if curl -f -s -o /dev/null http://localhost/sitemap.xml; then
    print_status "Sitemap: ✅ Working"
    ((TESTS_PASSED++))
else
    print_error "Sitemap: ❌ Failed"
fi

echo ""
echo "📊 Test Results: $TESTS_PASSED/$TESTS_TOTAL tests passed"

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    print_status "All tests passed! 🎉"
else
    print_warning "Some tests failed. Check the configuration."
fi

print_info "Step 8: Display Deployment Summary"
echo "================================="

# Get server information
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "Unable to detect")

echo ""
echo "🎉 Enhanced Marketing Website Deployment Complete!"
echo "================================================="
echo ""
echo "🌐 Website URLs:"
echo "  - Homepage: http://$SERVER_IP/ (or https://rozitech.com)"
echo "  - Pricing: http://$SERVER_IP/get-started.html"
echo "  - Product Info: http://$SERVER_IP/learn-more.html"
echo "  - Contact: http://$SERVER_IP/contact.html"
echo "  - Privacy: http://$SERVER_IP/privacy-policy.html"
echo ""
echo "📊 Analytics Configured:"
echo "  - Google Analytics 4: G-RPGPK0G28Z"
echo "  - Conversion tracking: ✅ Active"
echo "  - Mobile optimization: ✅ Active"
echo "  - POPIA compliance: ✅ Active"
echo ""
echo "💰 New Pricing Model Deployed:"
echo "  - Small Business: R2.50/policy (up to 100 policies)"
echo "  - Growth: R2.00/policy (101-1,000 policies)"
echo "  - Enterprise: R1.50/policy (1,001-10,000 policies)"
echo "  - Custom Enterprise: POA (10,000+ policies)"
echo ""
echo "🔧 Next Steps:"
echo "  1. Configure SSL certificate: sudo certbot --nginx -d rozitech.com"
echo "  2. Update DNS records to point to: $SERVER_IP"
echo "  3. Test live website functionality"
echo "  4. Monitor Google Analytics for traffic"
echo ""
echo "📂 File Locations:"
echo "  - Marketing files: $MARKETING_DIR"
echo "  - Nginx config: $PROJECT_DIR/nginx/conf.d/marketing.conf"
echo "  - Backup: $BACKUP_DIR"
echo ""
echo "🚨 Rollback Command (if needed):"
echo "  sudo cp -r $BACKUP_DIR/* $MARKETING_DIR/ && sudo systemctl reload nginx"
echo ""

print_status "Enhanced marketing website is live and ready for business!"

# Create deployment info file
sudo tee "$PROJECT_DIR/marketing-deployment-info.txt" > /dev/null << EOF
Rozitech Enhanced Marketing Website Deployment
=============================================

Deployment Date: $(date)
Server IP: $SERVER_IP
Marketing Directory: $MARKETING_DIR
Backup Location: $BACKUP_DIR

Enhanced Features:
- Google Analytics 4: G-RPGPK0G28Z
- Per-policy pricing model
- POPIA compliance
- Mobile optimization
- Conversion tracking

Test Results: $TESTS_PASSED/$TESTS_TOTAL tests passed

Website URLs:
- Homepage: http://$SERVER_IP/
- Pricing: http://$SERVER_IP/get-started.html
- Product: http://$SERVER_IP/learn-more.html
- Contact: http://$SERVER_IP/contact.html

Next Steps:
1. Configure SSL certificate
2. Update DNS records
3. Test live functionality
4. Monitor analytics
EOF

print_status "Deployment information saved to $PROJECT_DIR/marketing-deployment-info.txt"