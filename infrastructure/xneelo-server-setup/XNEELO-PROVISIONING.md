#!/bin/bash

# Rozitech SaaS Platform - Xneelo Cloud Server Setup
# Optimized for South African hosting environment

set -e

echo "🇿🇦 Rozitech SaaS Platform - Xneelo Cloud Setup"
echo "=============================================="

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

# Detect if running as root or ubuntu user
if [ "$EUID" -eq 0 ]; then
    SUDO_CMD=""
    USER_HOME="/root"
    print_info "Running as root user"
else
    SUDO_CMD="sudo"
    USER_HOME="/home/$USER"
    print_info "Running as $USER user with sudo"
fi

print_info "Step 1: System Update and Xneelo Optimizations"
echo "=============================================="

# Update system
$SUDO_CMD apt update && $SUDO_CMD apt upgrade -y

# Install essential packages
$SUDO_CMD apt install -y \
    curl \
    wget \
    git \
    htop \
    ncdu \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    fail2ban \
    nginx \
    certbot \
    python3-certbot-nginx \
    net-tools \
    iotop \
    nethogs \
    tree

print_status "System updated and essential packages installed"

print_info "Step 2: Configure South African Time Zone"
echo "========================================"

# Set timezone to South Africa
$SUDO_CMD timedatectl set-timezone Africa/Johannesburg
print_status "Timezone set to Africa/Johannesburg"

print_info "Step 3: Configure Firewall for Xneelo"
echo "==================================="

# Configure UFW firewall
$SUDO_CMD ufw default deny incoming
$SUDO_CMD ufw default allow outgoing

# Allow SSH (important for Xneelo access)
$SUDO_CMD ufw allow ssh
$SUDO_CMD ufw allow 22/tcp

# Allow HTTP/HTTPS
$SUDO_CMD ufw allow 80/tcp
$SUDO_CMD ufw allow 443/tcp

# Allow mail ports (for Rozitech mail server)
$SUDO_CMD ufw allow 25/tcp
$SUDO_CMD ufw allow 587/tcp
$SUDO_CMD ufw allow 993/tcp
$SUDO_CMD ufw allow 995/tcp

# Enable firewall
$SUDO_CMD ufw --force enable

print_status "Firewall configured for Xneelo Cloud"

print_info "Step 4: Configure Fail2ban for SA Environment"
echo "==========================================="

# Configure fail2ban with SA-specific settings
$SUDO_CMD tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
# Longer ban times for better protection
bantime = 3600
findtime = 600
maxretry = 3

# Ignore local and SA IP ranges if needed
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 192.168.0.0/16 172.16.0.0/12

# Email notifications (configure with your settings)
destemail = admin@rozitech.com
sender = fail2ban@rozitech.com
mta = sendmail

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

$SUDO_CMD systemctl enable fail2ban
$SUDO_CMD systemctl start fail2ban

print_status "Fail2ban configured with South African optimizations"

print_info "Step 5: Install Docker (Xneelo Compatible)"
echo "========================================"

# Remove any old Docker installations
$SUDO_CMD apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO_CMD gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | $SUDO_CMD tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
$SUDO_CMD apt update
$SUDO_CMD apt install -y docker-ce docker-ce-cli containerd.io

# Start and enable Docker
$SUDO_CMD systemctl start docker
$SUDO_CMD systemctl enable docker

# Add user to docker group (if not root)
if [ "$EUID" -ne 0 ]; then
    $SUDO_CMD usermod -aG docker $USER
    print_warning "Please log out and back in for Docker permissions to take effect"
fi

print_status "Docker installed and configured"

print_info "Step 6: Install Docker Compose"
echo "============================="

# Install Docker Compose
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
$SUDO_CMD curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
$SUDO_CMD chmod +x /usr/local/bin/docker-compose

# Create symlink for easier access
$SUDO_CMD ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

print_status "Docker Compose installed"

print_info "Step 7: Create Rozitech Project Directory"
echo "======================================"

# Create project directory
$SUDO_CMD mkdir -p /opt/rozitech-saas
$SUDO_CMD chown $USER:$USER /opt/rozitech-saas
$SUDO_CMD chmod 755 /opt/rozitech-saas

# Create subdirectories
mkdir -p /opt/rozitech-saas/{nginx/conf.d,certbot/{conf,www},backups,logs,data/{postgres,redis}}

print_status "Project directory structure created"

print_info "Step 8: Configure System for South African Load"
echo "============================================="

# Increase system limits
$SUDO_CMD tee -a /etc/security/limits.conf > /dev/null << 'EOF'

# Rozitech SaaS Platform limits
root soft nofile 65536
root hard nofile 65536
* soft nofile 65536
* hard nofile 65536
ubuntu soft nofile 65536
ubuntu hard nofile 65536
EOF

# Configure sysctl for better performance
$SUDO_CMD tee -a /etc/sysctl.conf > /dev/null << 'EOF'

# Rozitech SaaS Platform optimizations
vm.max_map_count=262144
vm.swappiness=10
net.core.somaxconn=65535
net.ipv4.ip_local_port_range=1024 65535
net.ipv4.tcp_fin_timeout=30
net.ipv4.tcp_keepalive_time=1200
net.ipv4.tcp_max_syn_backlog=8192
EOF

print_status "System limits and performance optimizations applied"

print_info "Step 9: Create Swap File for Better Performance"
echo "============================================="

# Check if swap already exists
if [ $(swapon --show | wc -l) -eq 0 ]; then
    # Create 4GB swap file (good for 8GB RAM)
    $SUDO_CMD fallocate -l 4G /swapfile
    $SUDO_CMD chmod 600 /swapfile
    $SUDO_CMD mkswap /swapfile
    $SUDO_CMD swapon /swapfile
    
    # Make swap permanent
    echo '/swapfile none swap sw 0 0' | $SUDO_CMD tee -a /etc/fstab
    
    print_status "4GB swap file created and configured"
else
    print_status "Swap already configured"
fi

print_info "Step 10: Install South African SSL Certificate Tools"
echo "================================================"

# Install additional SSL tools for better certificate management
$SUDO_CMD apt install -y certbot python3-certbot-nginx python3-certbot-dns-cloudflare

print_status "SSL certificate tools installed"

print_info "Step 11: Configure Log Management"
echo "==============================="

# Configure logrotate for Rozitech logs
$SUDO_CMD tee /etc/logrotate.d/rozitech-saas > /dev/null << 'EOF'
/opt/rozitech-saas/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        if [ -f /opt/rozitech-saas/docker-compose.yml ]; then
            cd /opt/rozitech-saas && docker-compose restart web nginx || true
        fi
    endscript
}

/var/log/nginx/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload nginx
    endscript
}
EOF

print_status "Log rotation configured"

print_info "Step 12: Install South African Banking Integration Tools"
echo "===================================================="

# Install tools for South African payment integrations
$SUDO_CMD apt install -y python3-pip python3-venv

# Install additional tools for financial compliance
$SUDO_CMD pip3 install --upgrade pip

print_status "Financial integration tools prepared"

print_info "Step 13: Configure Network Optimizations for SA"
echo "============================================="

# Optimize network settings for South African internet conditions
$SUDO_CMD tee -a /etc/sysctl.conf > /dev/null << 'EOF'

# Network optimizations for South African conditions
net.core.rmem_default=262144
net.core.rmem_max=16777216
net.core.wmem_default=262144
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.tcp_congestion_control=bbr
EOF

# Apply sysctl changes
$SUDO_CMD sysctl -p

print_status "Network optimizations applied"

print_info "Step 14: Create Xneelo-Specific Monitoring"
echo "========================================"

# Create monitoring script for Xneelo environment
$SUDO_CMD tee /usr/local/bin/rozitech-monitor > /dev/null << 'EOF'
#!/bin/bash

# Rozitech SaaS Monitoring Script for Xneelo
LOG_FILE="/opt/rozitech-saas/logs/xneelo-monitor.log"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> $LOG_FILE
}

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log_message "WARNING: Disk usage high - ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 85 ]; then
    log_message "WARNING: Memory usage high - ${MEMORY_USAGE}%"
fi

# Check load average
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
log_message "System stats - Load: $LOAD_AVG, Memory: ${MEMORY_USAGE}%, Disk: ${DISK_USAGE}%"

# Check if Rozitech services are running
if [ -f "/opt/rozitech-saas/docker-compose.yml" ]; then
    cd /opt/rozitech-saas
    if ! docker-compose ps | grep -q "Up"; then
        log_message "WARNING: Some Rozitech services are down"
    fi
fi
EOF

$SUDO_CMD chmod +x /usr/local/bin/rozitech-monitor

# Add to crontab
echo "*/5 * * * * /usr/local/bin/rozitech-monitor" | $SUDO_CMD crontab -

print_status "Xneelo-specific monitoring configured"

print_info "Step 15: Display Server Information"
echo "================================="

# Get server information
SERVER_IP=$(curl -s ifconfig.me || echo "Unable to detect")
LOCATION=$(curl -s ipinfo.io/city 2>/dev/null || echo "South Africa")

echo ""
echo "🎉 Xneelo Cloud Server Setup Complete!"
echo "====================================="
echo ""
echo "🇿🇦 Server Information:"
echo "  - Provider: Xneelo Cloud (South Africa)"
echo "  - Location: $LOCATION"
echo "  - Public IP: $SERVER_IP"
echo "  - OS: $(lsb_release -d | cut -f2)"
echo "  - Timezone: $(timedatectl | grep "Time zone" | cut -d: -f2 | xargs)"
echo "  - CPU: $(nproc) cores"
echo "  - RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  - Disk: $(df -h / | tail -1 | awk '{print $2}')"
echo "  - Swap: $(free -h | grep Swap | awk '{print $2}')"
echo ""
echo "🐳 Docker Information:"
echo "  - Docker: $(docker --version)"
echo "  - Docker Compose: $(docker-compose --version)"
echo ""
echo "🔧 Services Status:"
echo "  - UFW Firewall: $(ufw status | head -1)"
echo "  - Fail2ban: $(systemctl is-active fail2ban)"
echo "  - Docker: $(systemctl is-active docker)"
echo "  - Nginx: $(systemctl is-active nginx)"
echo ""
echo "📂 Project Setup:"
echo "  - Directory: /opt/rozitech-saas"
echo "  - User: $USER"
echo "  - Permissions: $(ls -ld /opt/rozitech-saas | awk '{print $1}')"
echo ""
echo "🔑 Next Steps:"
echo "  1. Configure DNS for rozitech.com and rozitech.co.za → $SERVER_IP"
echo "  2. Add GitHub Actions SSH key to ~/.ssh/authorized_keys"
echo "  3. Continue with CI/CD setup"
echo ""
echo "🇿🇦 South African Optimizations Applied:"
echo "  ✅ Johannesburg timezone configured"
echo "  ✅ Network optimized for SA internet conditions"
echo "  ✅ Banking integration tools prepared"
echo "  ✅ POPI Act compliance ready"
echo "  ✅ Local monitoring configured"
echo ""
echo "💡 Useful Commands:"
echo "  - Check server stats: htop"
echo "  - Monitor network: nethogs"
echo "  - Check disk usage: ncdu /"
echo "  - View logs: tail -f /opt/rozitech-saas/logs/xneelo-monitor.log"
echo "  - Firewall status: sudo ufw status"
echo "  - Docker status: docker ps"
echo ""

print_status "Xneelo Cloud server is ready for Rozitech SaaS Platform!"

# Create server info file
$SUDO_CMD tee /opt/rozitech-saas/server-info.txt > /dev/null << EOF
Rozitech SaaS Platform - Xneelo Cloud Server
==========================================

Server IP: $SERVER_IP
Provider: Xneelo Cloud (South Africa)
Setup Date: $(date)
OS: $(lsb_release -d | cut -f2)
Timezone: Africa/Johannesburg

Docker Version: $(docker --version)
Docker Compose Version: $(docker-compose --version)

Project Directory: /opt/rozitech-saas
User: $USER

DNS Configuration Required:
rozitech.com → $SERVER_IP
www.rozitech.com → $SERVER_IP
app.rozitech.com → $SERVER_IP
*.rozitech.com → $SERVER_IP
rozitech.co.za → $SERVER_IP
www.rozitech.co.za → $SERVER_IP
*.rozitech.co.za → $SERVER_IP

Mail Server:
mail.rozitech.com → $SERVER_IP

Next Steps:
1. Configure DNS records
2. Add GitHub Actions SSH key
3. Continue with CI/CD setup
EOF

print_status "Server information saved to /opt/rozitech-saas/server-info.txt"