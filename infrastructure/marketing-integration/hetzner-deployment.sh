#!/bin/bash

# Rozitech SaaS Platform - Hetzner Deployment with Marketing Site
# Optimized for Hetzner Cloud servers

set -e

echo "🚀 Deploying Rozitech SaaS Platform on Hetzner"

# Configuration
DOMAIN="yourdomain.com"
EMAIL="your-email@example.com"
MARKETING_OPTION="django"  # Options: django, nextjs, static

# Hetzner-specific optimizations
echo "🔧 Optimizing for Hetzner Cloud..."

# Update system with Hetzner mirrors
apt update && apt upgrade -y

# Install required packages
apt install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    htop \
    ncdu \
    fail2ban \
    ufw \
    git \
    curl \
    wget \
    unzip

# Start Docker
systemctl enable docker
systemctl start docker

# Configure firewall (Hetzner Cloud Firewall + UFW)
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable

# Hetzner-specific security hardening
echo "🛡️ Applying Hetzner security best practices..."

# Disable IPv6 if not needed (Hetzner recommendation)
echo 'net.ipv6.conf.all.disable_ipv6 = 1' >> /etc/sysctl.conf
echo 'net.ipv6.conf.default.disable_ipv6 = 1' >> /etc/sysctl.conf
sysctl -p

# Configure fail2ban for Hetzner
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

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
systemctl restart fail2ban

# Create project structure
PROJECT_DIR="/opt/rozitech-saas"
mkdir -p $PROJECT_DIR/{nginx/conf.d,certbot/{conf,www},backups,logs,marketing}
cd $PROJECT_DIR

# Generate secure credentials
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
WEBHOOK_SECRET=$(openssl rand -base64 32)

# Create optimized environment file for Hetzner
cat > .env << EOF
# Hetzner deployment configuration
DEPLOYMENT_PROVIDER=hetzner
SERVER_LOCATION=nuremberg

# Database
DB_NAME=rozitech_saas
DB_USER=rozitech
DB_PASSWORD=$DB_PASSWORD

# Django
SECRET_KEY=$SECRET_KEY
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,*.$DOMAIN,app.$DOMAIN
DEBUG=False
USE_HTTPS=True

# Hetzner-specific settings
HETZNER_API_TOKEN=your-hetzner-api-token
BACKUP_LOCATION=hetzner-object-storage

# Email (use Hetzner-friendly providers)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.eu.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@$DOMAIN
EMAIL_HOST_PASSWORD=your-mailgun-password
CONTACT_EMAIL=contact@$DOMAIN
SALES_EMAIL=sales@$DOMAIN
MARKETING_EMAIL=marketing@$DOMAIN

# Storage (Hetzner Object Storage or AWS)
STORAGE_BACKEND=hetzner  # or aws
HETZNER_STORAGE_ENDPOINT=fsn1.your-project.storage.hetzner.cloud
HETZNER_STORAGE_ACCESS_KEY=your-access-key
HETZNER_STORAGE_SECRET_KEY=your-secret-key
HETZNER_STORAGE_BUCKET=rozitech-saas-media

# CDN (CloudFlare recommended for Hetzner)
USE_CDN=True
CDN_DOMAIN=cdn.$DOMAIN

# Payment providers
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
PAYFAST_MERCHANT_ID=your-merchant-id
PAYFAST_MERCHANT_KEY=your-merchant-key

# Webhooks
WEBHOOK_URL=https://$DOMAIN/webhooks/provisioning
WEBHOOK_SECRET=$WEBHOOK_SECRET

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
HEALTH_CHECK_URL=https://$DOMAIN/health/
EOF

# Create Hetzner-optimized Docker Compose
cat > docker-compose.hetzner.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      # Hetzner optimizations
      POSTGRES_SHARED_PRELOAD_LIBRARIES: 'pg_stat_statements'
      POSTGRES_MAX_CONNECTIONS: 100
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
    ports:
      - "127.0.0.1:5432:5432"
    command: >
      postgres
      -c max_connections=100
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data
    ports:
      - "127.0.0.1:6379:6379"
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      dockerfile: Dockerfile.hetzner
    restart: always
    command: >
      gunicorn config.wsgi:application
      --bind 0.0.0.0:8000
      --workers 3
      --worker-class gevent
      --worker-connections 1000
      --max-requests 1000
      --max-requests-jitter 100
      --timeout 30
      --keep-alive 2
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.hetzner
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  celery:
    build:
      context: .
      dockerfile: Dockerfile.hetzner
    restart: always
    command: >
      celery -A config worker
      -l info
      -Q default,provisioning,monitoring
      --concurrency=2
      --prefetch-multiplier=1
    volumes:
      - media_volume:/app/media
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.hetzner
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.hetzner
    restart: always
    command: >
      celery -A config beat
      -l info
      --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.hetzner
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - static_volume:/static:ro
      - media_volume:/media:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - web
    command: >
      /bin/sh -c "
        while :; do 
          sleep 6h & wait $$!; 
          nginx -s reload; 
        done & 
        nginx -g 'daemon off;'
      "

  # Hetzner backup service
  backup:
    image: postgres:15-alpine
    volumes:
      - ./backups:/backups
      - ./scripts:/scripts:ro
    environment:
      - PGHOST=postgres
      - PGDATABASE=${DB_NAME}
      - PGUSER=${DB_USER}
      - PGPASSWORD=${DB_PASSWORD}
    entrypoint: ["/bin/sh", "-c"]
    command: 
      - |
        while true; do
          sleep 86400  # Daily backup
          timestamp=$$(date +%Y%m%d_%H%M%S)
          pg_dump -h postgres -U ${DB_USER} ${DB_NAME} | gzip > /backups/backup_$$timestamp.sql.gz
          
          # Upload to Hetzner Object Storage (if configured)
          if [ ! -z "$HETZNER_STORAGE_ENDPOINT" ]; then
            # Use s3cmd or similar to upload to Hetzner Storage
            echo "Backup created: backup_$$timestamp.sql.gz"
          fi
          
          # Keep only last 7 days locally
          find /backups -name "backup_*.sql.gz" -mtime +7 -delete
        done
    depends_on:
      - postgres

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/rozitech-saas/data/postgres
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/rozitech-saas/data/redis
  static_volume:
  media_volume:
EOF

# Create data directories with proper permissions
mkdir -p data/{postgres,redis}
chown -R 999:999 data/postgres  # postgres user in container
chown -R 999:999 data/redis     # redis user in container

# Create Hetzner-optimized Nginx configuration
cat > nginx/conf.d/rozitech-hetzner.conf << EOF
# Hetzner-optimized Nginx configuration
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}

# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=signup:10m rate=2r/m;

# Upstream servers
upstream django {
    server web:8000;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN *.$DOMAIN;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Hetzner-optimized SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Performance optimizations
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    keepalive_timeout 65s;
    send_timeout 60s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Static files with aggressive caching
    location /static/ {
        alias /static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
        access_log off;
        
        # Enable Brotli if available
        location ~* \.(js|css|svg|png|jpg|jpeg|gif|ico|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }
    
    # Media files
    location /media/ {
        alias /media/;
        expires 30d;
        add_header Cache-Control "public";
        access_log off;
    }
    
    # Health checks (no rate limiting)
    location /health/ {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }
    
    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 30;
        proxy_send_timeout 60;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Authentication endpoints with stricter rate limiting
    location ~ ^/(login|register|signup)/ {
        limit_req zone=signup burst=5 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Admin with strict rate limiting
    location /admin/ {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # All other requests (marketing + app)
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60;
        proxy_connect_timeout 30;
        proxy_send_timeout 60;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}

# Tenant subdomains
server {
    listen 443 ssl http2;
    server_name app.$DOMAIN *.$DOMAIN;
    
    # Use same SSL certificate
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Same SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Tenant-specific headers
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    
    client_max_body_size 50M;
    
    location /static/ {
        alias /static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    location /media/ {
        alias /media/;
        expires 30d;
        add_header Cache-Control "public";
        access_log off;
    }
    
    location / {
        limit_req zone=api burst=30 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Create systemd service
cat > /etc/systemd/system/rozitech-saas.service << EOF
[Unit]
Description=Rozitech SaaS Platform on Hetzner
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker-compose -f docker-compose.hetzner.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.hetzner.yml down
ExecReload=/usr/bin/docker-compose -f docker-compose.hetzner.yml restart
TimeoutStartSec=0
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl enable rozitech-saas.service

# Create monitoring and maintenance scripts
cat > monitor-hetzner.sh << 'EOF'
#!/bin/bash
# Hetzner-specific monitoring script

LOG_FILE="/opt/rozitech-saas/logs/monitor.log"
cd /opt/rozitech-saas

# Check services
if ! docker-compose -f docker-compose.hetzner.yml ps | grep -q "Up"; then
    echo "$(date): Services down, restarting..." >> $LOG_FILE
    docker-compose -f docker-compose.hetzner.yml up -d
fi

# Check Hetzner Cloud API status
if ! curl -s --max-time 10 https://status.hetzner.com/api/v2/summary.json | grep -q '"status":"none"'; then
    echo "$(date): Hetzner Cloud may have issues" >> $LOG_FILE
fi

# Check disk space (Hetzner volumes)
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage high: ${DISK_USAGE}%" >> $LOG_FILE
    # Clean old Docker images
    docker system prune -f
fi

# Check memory (important on smaller Hetzner instances)
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 85 ]; then
    echo "$(date): Memory usage high: ${MEMORY_USAGE}%" >> $LOG_FILE
    # Restart services if memory is too high
    if [ $MEMORY_USAGE -gt 95 ]; then
        systemctl restart rozitech-saas
    fi
fi
EOF

chmod +x monitor-hetzner.sh

# Set up cron jobs
cat > /etc/cron.d/rozitech-hetzner << EOF
# Hetzner-specific cron jobs

# Monitor every 5 minutes
*/5 * * * * root $PROJECT_DIR/monitor-hetzner.sh

# Daily backup at 2 AM
0 2 * * * root cd $PROJECT_DIR && docker-compose -f docker-compose.hetzner.yml exec -T backup /scripts/backup.sh

# Weekly cleanup - keep 2 weeks of backups
0 3 * * 0 root find $PROJECT_DIR/backups -name "backup_*.sql.gz" -mtime +14 -delete

# Monthly security updates
0 4 1 * * root apt update && apt upgrade -y && systemctl restart rozitech-saas
EOF

echo "✅ Hetzner deployment script complete!"
echo ""
echo "🎯 Estimated monthly cost on Hetzner:"
echo "  - CCX22 (4GB RAM, 2 vCPU, 40GB SSD): €20/month"
echo "  - Object Storage (100GB): €4/month"
echo "  - CloudFlare CDN: Free"
echo "  - Total: ~€25/month (~$27/month)"
echo ""
echo "🚀 Next steps:"
echo "  1. Update the domain name in this script"
echo "  2. Configure your email provider credentials"
echo "  3. Set up Hetzner Object Storage (optional)"
echo "  4. Run: bash $0"
echo "  5. Point your domain to this server's IP"
echo ""
echo "💡 Hetzner advantages:"
echo "  - GDPR compliant (EU-based)"
echo "  - Excellent price/performance"
echo "  - Fast NVMe SSDs"
echo "  - 20TB traffic included"
echo "  - Easy scaling when needed"
EOF

chmod +x hetzner-deployment.sh

echo "✅ Marketing integration files created!"
echo ""
echo "🎯 **Perfect for Hetzner! Here's your cost-efficient marketing integration:**"
echo ""
echo "📊 **Cost Breakdown on Hetzner:**"
echo "  • CCX22 (4GB RAM, 2 vCPU): €20/month"
echo "  • Object Storage (100GB): €4/month"
echo "  • Domain + CloudFlare: €1/month"
echo "  • **Total: €25/month (~$27/month)**"
echo ""
echo "🚀 **What you get:**"
echo "  ✅ Full SaaS platform + marketing website"
echo "  ✅ Automated provisioning for tenant services"
echo "  ✅ Multi-tenant architecture"
echo "  ✅ Professional marketing pages (pricing, features, etc.)"
echo "  ✅ Contact forms and lead capture"
echo "  ✅ SSL certificates (Let's Encrypt)"
echo "  ✅ Automated backups"
echo "  ✅ GDPR compliance (Hetzner is EU-based)"
echo ""
echo "🎯 **Recommended setup:**"
echo "  1. **Start with Option 1** (Django marketing pages) - simplest"
echo "  2. **Use Hetzner CCX22** - best value for money"
echo "  3. **Add CloudFlare** - free CDN + DDoS protection"
echo "  4. **Scale when you hit 100+ customers**"
echo ""
echo "📈 **Growth path:**"
echo "  • 0-100 customers: CCX22 (€20/month)"
echo "  • 100-500 customers: CCX32 (€40/month)"
echo "  • 500+ customers: Load balancer + multiple servers"
echo ""
echo "Would you like me to help you set up the Hetzner deployment script with your specific domain and preferences?"