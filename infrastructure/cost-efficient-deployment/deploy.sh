#!/bin/bash

# Rozitech SaaS Platform - Cost-Efficient Deployment Script
# This script sets up the entire platform on a single VPS

set -e

echo "🚀 Starting Rozitech SaaS Platform Deployment"

# Configuration
DOMAIN="yourdomain.com"
EMAIL="your-email@example.com"
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Docker and Docker Compose
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $SUDO_USER
fi

if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install additional tools
echo "🛠️ Installing additional tools..."
apt install -y htop ncdu fail2ban ufw git certbot

# Configure firewall
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable

# Configure fail2ban
echo "🛡️ Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Create project directory
PROJECT_DIR="/opt/rozitech-saas"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Create environment file
echo "🔐 Creating environment configuration..."
cat > .env << EOF
# Database
DB_NAME=rozitech_saas
DB_USER=rozitech
DB_PASSWORD=$DB_PASSWORD

# Django
SECRET_KEY=$SECRET_KEY
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,*.$DOMAIN
DEBUG=False

# Email (configure with your provider)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Storage (configure with your provider)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=rozitech-saas-media
AWS_S3_REGION_NAME=us-east-1

# Payment providers
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
PAYFAST_MERCHANT_ID=your-merchant-id
PAYFAST_MERCHANT_KEY=your-merchant-key

# Webhooks
WEBHOOK_URL=https://your-webhook-endpoint.com/webhooks
WEBHOOK_SECRET=your-webhook-secret

# Monitoring (optional)
SENTRY_DSN=https://your-sentry-dsn
EOF

# Create backup and log directories
mkdir -p backups logs

# Set up log rotation
cat > /etc/logrotate.d/rozitech << EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0644 root root
    postrotate
        docker-compose -f $PROJECT_DIR/docker-compose.prod.yml exec web python manage.py clearsessions
    endscript
}
EOF

# Create systemd service for auto-start
cat > /etc/systemd/system/rozitech-saas.service << EOF
[Unit]
Description=Rozitech SaaS Platform
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl enable rozitech-saas.service

# Set up SSL certificate (initial HTTP-only setup)
echo "🔒 Setting up SSL certificates..."
# Update nginx config with your actual domain
sed -i "s/yourdomain.com/$DOMAIN/g" nginx/conf.d/rozitech.conf

# Start services initially without SSL for certificate generation
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 30

# Run initial setup
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml run --rm web python manage.py createsuperuser --noinput --username admin --email admin@$DOMAIN || true

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Generate SSL certificate
echo "🔒 Generating SSL certificate..."
certbot certonly --webroot -w ./certbot/www -d $DOMAIN -d www.$DOMAIN --email $EMAIL --agree-tos --no-eff-email

# Reload nginx with SSL
docker-compose -f docker-compose.prod.yml restart nginx

# Set up automated backups
echo "💾 Setting up automated backups..."
cat > /etc/cron.d/rozitech-backup << EOF
# Daily database backup at 2 AM
0 2 * * * root cd $PROJECT_DIR && docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U rozitech rozitech_saas | gzip > backups/backup_\$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz

# Weekly cleanup - keep only last 4 weeks
0 3 * * 0 root find $PROJECT_DIR/backups -name "backup_*.sql.gz" -mtime +28 -delete

# Daily log cleanup
0 1 * * * root docker system prune -f
EOF

# Create monitoring script
cat > $PROJECT_DIR/monitor.sh << 'EOF'
#!/bin/bash
# Simple monitoring script

cd /opt/rozitech-saas

# Check if services are running
if ! docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "$(date): Some services are down, restarting..." >> logs/monitor.log
    docker-compose -f docker-compose.prod.yml up -d
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): Disk usage is ${DISK_USAGE}%" >> logs/monitor.log
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 90 ]; then
    echo "$(date): Memory usage is ${MEMORY_USAGE}%" >> logs/monitor.log
fi
EOF

chmod +x $PROJECT_DIR/monitor.sh

# Add monitoring to cron
echo "*/5 * * * * root $PROJECT_DIR/monitor.sh" >> /etc/cron.d/rozitech-backup

echo "✅ Deployment completed!"
echo ""
echo "🎉 Your Rozitech SaaS Platform is now running!"
echo ""
echo "📍 URLs:"
echo "  - Main site: https://$DOMAIN"
echo "  - Admin: https://$DOMAIN/admin"
echo "  - API: https://$DOMAIN/api"
echo ""
echo "🔐 Credentials:"
echo "  - Admin username: admin"
echo "  - Admin password: (you'll need to set this manually)"
echo "  - Database password: $DB_PASSWORD"
echo ""
echo "📁 Important directories:"
echo "  - Project: $PROJECT_DIR"
echo "  - Backups: $PROJECT_DIR/backups"
echo "  - Logs: $PROJECT_DIR/logs"
echo ""
echo "🔧 Next steps:"
echo "  1. Set admin password: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml exec web python manage.py changepassword admin"
echo "  2. Configure email settings in .env"
echo "  3. Set up payment provider credentials"
echo "  4. Configure domain DNS to point to this server"
echo "  5. Test tenant creation and provisioning"
echo ""
echo "💡 Useful commands:"
echo "  - View logs: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml logs -f"
echo "  - Restart services: systemctl restart rozitech-saas"
echo "  - Shell access: docker-compose -f $PROJECT_DIR/docker-compose.prod.yml exec web bash"
echo "  - Database backup: $PROJECT_DIR/monitor.sh"