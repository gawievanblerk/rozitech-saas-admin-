#!/bin/bash

# Rozitech SaaS Platform - Custom Hetzner Deployment
# Optimized for rozitech.com and rozitech.co.za domains

set -e

echo "🚀 Deploying Rozitech SaaS Platform on Hetzner"
echo "🌍 Domains: rozitech.com (international) & rozitech.co.za (South Africa)"

# Configuration
PRIMARY_DOMAIN="rozitech.com"
SECONDARY_DOMAIN="rozitech.co.za"
EMAIL="admin@rozitech.com"
COMPANY_NAME="Rozitech"

# Generate secure credentials
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 64)
WEBHOOK_SECRET=$(openssl rand -base64 32)
API_SECRET=$(openssl rand -base64 32)

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "📦 Updating system packages..."
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
    unzip \
    s3cmd \
    rsync

# Start Docker
systemctl enable docker
systemctl start docker
usermod -aG docker $SUDO_USER 2>/dev/null || true

# Configure firewall
echo "🔥 Configuring firewall for Rozitech domains..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
# Allow mail server ports (if hosting on same server)
ufw allow 25/tcp
ufw allow 587/tcp
ufw allow 993/tcp
ufw allow 995/tcp
ufw --force enable

# Configure fail2ban
echo "🛡️ Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
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

[postfix-sasl]
enabled = true
filter = postfix-sasl
port = smtp,465,submission
logpath = /var/log/mail.log
maxretry = 3
EOF

systemctl enable fail2ban
systemctl restart fail2ban

# Create project structure
PROJECT_DIR="/opt/rozitech-saas"
mkdir -p $PROJECT_DIR/{nginx/conf.d,certbot/{conf,www},backups,logs,marketing,mail}
cd $PROJECT_DIR

# Create optimized environment file for Rozitech
cat > .env << EOF
# Rozitech SaaS Platform Configuration
COMPANY_NAME=Rozitech
DEPLOYMENT_PROVIDER=hetzner
SERVER_LOCATION=nuremberg

# Domains
PRIMARY_DOMAIN=$PRIMARY_DOMAIN
SECONDARY_DOMAIN=$SECONDARY_DOMAIN
APP_DOMAIN=app.$PRIMARY_DOMAIN
ADMIN_DOMAIN=admin.$PRIMARY_DOMAIN

# Database
DB_NAME=rozitech_saas
DB_USER=rozitech
DB_PASSWORD=$DB_PASSWORD

# Django
SECRET_KEY=$SECRET_KEY
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=$PRIMARY_DOMAIN,www.$PRIMARY_DOMAIN,$SECONDARY_DOMAIN,www.$SECONDARY_DOMAIN,app.$PRIMARY_DOMAIN,admin.$PRIMARY_DOMAIN,*.$PRIMARY_DOMAIN,*.$SECONDARY_DOMAIN
DEBUG=False
USE_HTTPS=True

# Email Configuration (using your mail servers)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.$PRIMARY_DOMAIN
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@$PRIMARY_DOMAIN
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=Rozitech SaaS <noreply@$PRIMARY_DOMAIN>

# Business email addresses
CONTACT_EMAIL=contact@$PRIMARY_DOMAIN
SALES_EMAIL=sales@$PRIMARY_DOMAIN
SUPPORT_EMAIL=support@$PRIMARY_DOMAIN
MARKETING_EMAIL=marketing@$PRIMARY_DOMAIN
ADMIN_EMAIL=admin@$PRIMARY_DOMAIN

# South African specific emails
CONTACT_ZA_EMAIL=contact@$SECONDARY_DOMAIN
SALES_ZA_EMAIL=sales@$SECONDARY_DOMAIN
SUPPORT_ZA_EMAIL=support@$SECONDARY_DOMAIN

# Storage (Hetzner Object Storage)
STORAGE_BACKEND=hetzner
HETZNER_STORAGE_ENDPOINT=fsn1.rozitech.storage.hetzner.cloud
HETZNER_STORAGE_ACCESS_KEY=your-access-key
HETZNER_STORAGE_SECRET_KEY=your-secret-key
HETZNER_STORAGE_BUCKET=rozitech-saas-media

# CDN Configuration
USE_CDN=True
CDN_DOMAIN=cdn.$PRIMARY_DOMAIN
STATIC_URL=https://cdn.$PRIMARY_DOMAIN/static/
MEDIA_URL=https://cdn.$PRIMARY_DOMAIN/media/

# Payment providers (including South African)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
PAYFAST_MERCHANT_ID=your-merchant-id
PAYFAST_MERCHANT_KEY=your-merchant-key
PAYFAST_PASSPHRASE=your-passphrase
YOCO_SECRET_KEY=sk_live_...  # Popular in SA

# Webhooks
WEBHOOK_URL=https://$PRIMARY_DOMAIN/webhooks/provisioning/
WEBHOOK_SECRET=$WEBHOOK_SECRET
API_SECRET=$API_SECRET

# Monitoring & Analytics
SENTRY_DSN=https://your-sentry-dsn
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
HEALTH_CHECK_URL=https://$PRIMARY_DOMAIN/health/

# Regional settings
DEFAULT_TIMEZONE=Africa/Johannesburg
DEFAULT_CURRENCY=ZAR
SECONDARY_CURRENCY=USD
VAT_RATE=0.15  # 15% VAT in South Africa

# Compliance
GDPR_COMPLIANCE=True
POPI_COMPLIANCE=True  # Protection of Personal Information Act (SA)
DATA_RETENTION_DAYS=2555  # 7 years for SA compliance
EOF

# Create Docker Compose for Rozitech
cat > docker-compose.rozitech.yml << 'EOF'
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
      POSTGRES_SHARED_PRELOAD_LIBRARIES: 'pg_stat_statements'
    ports:
      - "127.0.0.1:5432:5432"
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=2GB
      -c maintenance_work_mem=64MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=16MB
      -c default_statistics_target=100
      -c random_page_cost=1.1
      -c effective_io_concurrency=200
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
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --tcp-keepalive 300
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: always
    command: >
      gunicorn config.wsgi:application
      --bind 0.0.0.0:8000
      --workers 4
      --worker-class gevent
      --worker-connections 1000
      --max-requests 2000
      --max-requests-jitter 200
      --timeout 30
      --keep-alive 2
      --preload
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
      - ./logs:/app/logs
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
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
          memory: 1.5G
        reservations:
          memory: 800M

  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: always
    command: >
      celery -A config worker
      -l info
      -Q default,provisioning,monitoring,email
      --concurrency=4
      --prefetch-multiplier=1
      --max-tasks-per-child=1000
    volumes:
      - media_volume:/app/media
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
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
      - DJANGO_SETTINGS_MODULE=config.settings.production
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
          sleep 12h & wait $$!; 
          nginx -s reload; 
        done & 
        nginx -g 'daemon off;'
      "

  # Rozitech backup service
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
          
          # Database backup
          pg_dump -h postgres -U ${DB_USER} ${DB_NAME} | gzip > /backups/db_backup_$$timestamp.sql.gz
          
          # Media backup
          tar -czf /backups/media_backup_$$timestamp.tar.gz -C /app media/
          
          # Log success
          echo "$$(date): Backup completed - db_backup_$$timestamp.sql.gz" >> /backups/backup.log
          
          # Upload to Hetzner Object Storage (if configured)
          if [ ! -z "${HETZNER_STORAGE_ENDPOINT}" ]; then
            s3cmd put /backups/db_backup_$$timestamp.sql.gz s3://rozitech-saas-backups/
            s3cmd put /backups/media_backup_$$timestamp.tar.gz s3://rozitech-saas-backups/
          fi
          
          # Cleanup old backups (keep 30 days)
          find /backups -name "*_backup_*.gz" -mtime +30 -delete
          find /backups -name "*_backup_*.tar.gz" -mtime +30 -delete
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

# Create data directories
mkdir -p data/{postgres,redis}
chown -R 999:999 data/postgres
chown -R 999:999 data/redis

# Create Rozitech-specific Nginx configuration
cat > nginx/conf.d/rozitech.conf << EOF
# Rozitech.com and Rozitech.co.za Nginx Configuration

# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=api:10m rate=20r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=signup:10m rate=3r/m;
limit_req_zone \$binary_remote_addr zone=contact:10m rate=10r/m;

# Geo-based routing for South Africa
geo \$country {
    default        international;
    196.0.0.0/8    za;
    41.0.0.0/8     za;
    105.0.0.0/8    za;
}

# Upstream servers
upstream django {
    server web:8000;
    keepalive 64;
}

# HTTP to HTTPS redirect for both domains
server {
    listen 80;
    server_name $PRIMARY_DOMAIN www.$PRIMARY_DOMAIN $SECONDARY_DOMAIN www.$SECONDARY_DOMAIN app.$PRIMARY_DOMAIN admin.$PRIMARY_DOMAIN *.$PRIMARY_DOMAIN *.$SECONDARY_DOMAIN;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Main International Site (rozitech.com)
server {
    listen 443 ssl http2;
    server_name $PRIMARY_DOMAIN www.$PRIMARY_DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Country \$country;
    
    # Performance
    client_max_body_size 100M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    keepalive_timeout 65s;
    
    # Static files with long caching
    location /static/ {
        alias /static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
        access_log off;
        
        # Compress static assets
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }
    
    location /media/ {
        alias /media/;
        expires 30d;
        add_header Cache-Control "public";
        access_log off;
    }
    
    # Health checks
    location /health/ {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Country \$country;
        access_log off;
    }
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Country \$country;
        proxy_read_timeout 300;
        proxy_connect_timeout 30;
        proxy_send_timeout 60;
    }
    
    # Authentication
    location ~ ^/(login|register|signup|auth)/ {
        limit_req zone=signup burst=10 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Country \$country;
    }
    
    # Contact forms
    location ~ ^/(contact|demo)/ {
        limit_req zone=contact burst=5 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Country \$country;
    }
    
    # Admin
    location /admin/ {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # All other requests
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Country \$country;
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
}

# South African Site (rozitech.co.za)
server {
    listen 443 ssl http2;
    server_name $SECONDARY_DOMAIN www.$SECONDARY_DOMAIN;
    
    # SSL Configuration (separate certificate)
    ssl_certificate /etc/letsencrypt/live/$SECONDARY_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$SECONDARY_DOMAIN/privkey.pem;
    
    # Same SSL settings as above
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-Country "za";
    
    client_max_body_size 100M;
    
    # Same static file handling
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
    
    # All requests go to Django with SA context
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Country "za";
        proxy_set_header X-Region "south-africa";
    }
}

# App Subdomain (app.rozitech.com)
server {
    listen 443 ssl http2;
    server_name app.$PRIMARY_DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    # App-specific headers
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-App-Domain "true";
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /static/;
        expires 1y;
        access_log off;
    }
    
    location /media/ {
        alias /media/;
        expires 30d;
        access_log off;
    }
    
    location / {
        limit_req zone=api burst=100 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-App-Request "true";
    }
}

# Tenant Subdomains (*.rozitech.com)
server {
    listen 443 ssl http2;
    server_name *.$PRIMARY_DOMAIN;
    
    ssl_certificate /etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /static/;
        expires 1y;
        access_log off;
    }
    
    location /media/ {
        alias /media/;
        expires 30d;
        access_log off;
    }
    
    location / {
        limit_req zone=api burst=50 nodelay;
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Tenant-Request "true";
    }
}
EOF

# Create systemd service for Rozitech
cat > /etc/systemd/system/rozitech-saas.service << EOF
[Unit]
Description=Rozitech SaaS Platform
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker-compose -f docker-compose.rozitech.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.rozitech.yml down
ExecReload=/usr/bin/docker-compose -f docker-compose.rozitech.yml restart
TimeoutStartSec=300
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable rozitech-saas.service

# Create Rozitech monitoring script
cat > monitor-rozitech.sh << 'EOF'
#!/bin/bash
# Rozitech-specific monitoring

LOG_FILE="/opt/rozitech-saas/logs/rozitech-monitor.log"
cd /opt/rozitech-saas

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> $LOG_FILE
}

# Check if services are running
if ! docker-compose -f docker-compose.rozitech.yml ps | grep -q "Up"; then
    log_message "Services down, restarting..."
    docker-compose -f docker-compose.rozitech.yml up -d
fi

# Check domain accessibility
for domain in "rozitech.com" "rozitech.co.za" "app.rozitech.com"; do
    if ! curl -sSf --max-time 10 "https://$domain/health/" > /dev/null; then
        log_message "Domain $domain is not responding"
    fi
done

# Check SSL certificate expiry (30 days warning)
for domain in "rozitech.com" "rozitech.co.za"; do
    expiry_date=$(echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry_date" +%s)
    current_epoch=$(date +%s)
    days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [ $days_until_expiry -lt 30 ]; then
        log_message "SSL certificate for $domain expires in $days_until_expiry days"
    fi
done

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log_message "Disk usage high: ${DISK_USAGE}%"
    # Clean Docker
    docker system prune -f --volumes
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 85 ]; then
    log_message "Memory usage high: ${MEMORY_USAGE}%"
fi

# Check email queue (if using local mail server)
if [ -d "/var/spool/postfix/deferred" ]; then
    DEFERRED_EMAILS=$(find /var/spool/postfix/deferred -type f | wc -l)
    if [ $DEFERRED_EMAILS -gt 50 ]; then
        log_message "High number of deferred emails: $DEFERRED_EMAILS"
    fi
fi

# Check database size
DB_SIZE=$(docker-compose -f docker-compose.rozitech.yml exec -T postgres psql -U rozitech -d rozitech_saas -c "SELECT pg_size_pretty(pg_database_size('rozitech_saas'));" | grep -E "MB|GB" | awk '{print $1}')
log_message "Database size: $DB_SIZE"

# Log system stats
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
log_message "System load: $LOAD_AVG, Memory: ${MEMORY_USAGE}%, Disk: ${DISK_USAGE}%"
EOF

chmod +x monitor-rozitech.sh

# Create backup and maintenance scripts
mkdir -p scripts

cat > scripts/rozitech-backup.sh << 'EOF'
#!/bin/bash
# Rozitech backup script

BACKUP_DIR="/opt/rozitech-saas/backups"
DATE=$(date +%Y%m%d_%H%M%S)

cd /opt/rozitech-saas

# Database backup
docker-compose -f docker-compose.rozitech.yml exec -T postgres pg_dump -U rozitech rozitech_saas | gzip > $BACKUP_DIR/rozitech_db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/rozitech_media_$DATE.tar.gz -C /opt/rozitech-saas media/

# Configuration backup
tar -czf $BACKUP_DIR/rozitech_config_$DATE.tar.gz .env docker-compose.rozitech.yml nginx/

# Upload to Hetzner Object Storage (if configured)
if command -v s3cmd &> /dev/null && [ -f ~/.s3cfg ]; then
    s3cmd put $BACKUP_DIR/rozitech_*_$DATE.* s3://rozitech-backups/
fi

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "rozitech_*" -mtime +30 -delete

echo "$(date): Backup completed - rozitech_*_$DATE.*" >> $BACKUP_DIR/backup.log
EOF

chmod +x scripts/rozitech-backup.sh

# Set up cron jobs
cat > /etc/cron.d/rozitech-saas << EOF
# Rozitech SaaS Platform Cron Jobs

# Monitor services every 5 minutes
*/5 * * * * root $PROJECT_DIR/monitor-rozitech.sh

# Daily backups at 2 AM
0 2 * * * root $PROJECT_DIR/scripts/rozitech-backup.sh

# SSL certificate renewal check (twice daily)
0 0,12 * * * root certbot renew --quiet --nginx

# Weekly log cleanup
0 3 * * 0 root find $PROJECT_DIR/logs -name "*.log" -mtime +7 -exec gzip {} \;

# Monthly system updates (first Sunday at 4 AM)
0 4 * * 0 root [ \$(date +\%d) -le 7 ] && apt update && apt upgrade -y && systemctl restart rozitech-saas

# Database maintenance (monthly)
0 1 1 * * root docker-compose -f $PROJECT_DIR/docker-compose.rozitech.yml exec -T postgres vacuumdb -U rozitech -d rozitech_saas -z
EOF

# Create SSL certificate script
cat > setup-ssl.sh << EOF
#!/bin/bash
# Setup SSL certificates for Rozitech domains

# Generate certificates for both domains
certbot certonly --webroot -w ./certbot/www -d $PRIMARY_DOMAIN -d www.$PRIMARY_DOMAIN --email $EMAIL --agree-tos --no-eff-email
certbot certonly --webroot -w ./certbot/www -d $SECONDARY_DOMAIN -d www.$SECONDARY_DOMAIN --email $EMAIL --agree-tos --no-eff-email

# Reload nginx
docker-compose -f docker-compose.rozitech.yml restart nginx
EOF

chmod +x setup-ssl.sh

echo "✅ Rozitech deployment script complete!"
echo ""
echo "🎯 **Rozitech SaaS Platform Configuration:**"
echo "  📍 Primary Domain: $PRIMARY_DOMAIN (International)"
echo "  📍 Secondary Domain: $SECONDARY_DOMAIN (South Africa)"
echo "  📍 App Domain: app.$PRIMARY_DOMAIN"
echo "  📍 Admin Domain: admin.$PRIMARY_DOMAIN"
echo ""
echo "💰 **Estimated Hetzner Costs:**"
echo "  • CCX22 (4GB RAM, 2 vCPU): €20/month"
echo "  • Object Storage (500GB): €20/month"
echo "  • Backup Storage (100GB): €4/month"
echo "  • **Total: €44/month (~$48/month)**"
echo ""
echo "📧 **Email Configuration:**"
echo "  • Main: contact@$PRIMARY_DOMAIN"
echo "  • Sales: sales@$PRIMARY_DOMAIN"
echo "  • Support: support@$PRIMARY_DOMAIN"
echo "  • South Africa: contact@$SECONDARY_DOMAIN"
echo ""
echo "🚀 **Next Steps:**"
echo "  1. Update DNS records for both domains"
echo "  2. Configure your mail server credentials in .env"
echo "  3. Set up Hetzner Object Storage"
echo "  4. Configure payment gateways (Stripe, PayFast, Yoco)"
echo "  5. Run: bash rozitech-hetzner.sh"
echo "  6. Run: bash setup-ssl.sh"
echo ""
echo "🌍 **Regional Features:**"
echo "  ✅ Geo-detection for South African visitors"
echo "  ✅ ZAR currency support"
echo "  ✅ VAT calculation (15%)"
echo "  ✅ POPI Act compliance"
echo "  ✅ PayFast & Yoco payment integration"
echo "  ✅ Multi-domain tenant support"
echo ""
echo "💡 **Your domains will serve:**"
echo "  • rozitech.com → International customers"
echo "  • rozitech.co.za → South African customers"
echo "  • app.rozitech.com → Main application"
echo "  • *.rozitech.com → Tenant subdomains"
echo "  • admin.rozitech.com → Admin interface"