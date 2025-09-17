#!/bin/bash

# Rozitech SaaS Platform - Quick Hetzner Server Setup Commands
# Run these commands on your fresh Hetzner server after initial creation

set -e

echo "🚀 Rozitech SaaS Platform - Server Quick Setup"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

print_info "Step 1: System Update and Basic Packages"
echo "========================================"

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y \
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
    python3-certbot-nginx

print_status "System updated and essential packages installed"

print_info "Step 2: Configure Firewall"
echo "=========================="

# Configure UFW firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

print_status "Firewall configured"

print_info "Step 3: Configure Fail2ban"
echo "=========================="

# Configure fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
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
EOF

systemctl enable fail2ban
systemctl start fail2ban

print_status "Fail2ban configured and started"

print_info "Step 4: Install Docker"
echo "====================="

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Start and enable Docker
systemctl start docker
systemctl enable docker

print_status "Docker installed and started"

print_info "Step 5: Install Docker Compose"
echo "============================="

# Install Docker Compose
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

print_status "Docker Compose installed"

print_info "Step 6: Create Project Directory"
echo "==============================="

# Create project directory
mkdir -p /opt/rozitech-saas
chown root:root /opt/rozitech-saas
chmod 755 /opt/rozitech-saas

print_status "Project directory created: /opt/rozitech-saas"

print_info "Step 7: Configure System Limits"
echo "==============================="

# Increase system limits for better performance
cat >> /etc/security/limits.conf << 'EOF'
# Rozitech SaaS Platform limits
root soft nofile 65536
root hard nofile 65536
* soft nofile 65536
* hard nofile 65536
EOF

# Increase vm.max_map_count for Elasticsearch (if needed later)
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf

print_status "System limits configured"

print_info "Step 8: Create Swap File (Recommended)"
echo "====================================="

# Check if swap already exists
if [ $(swapon --show | wc -l) -eq 0 ]; then
    # Create 2GB swap file
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Make swap permanent
    echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    
    # Configure swappiness
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    
    print_status "2GB swap file created and configured"
else
    print_status "Swap already configured"
fi

print_info "Step 9: Install Monitoring Tools"
echo "==============================="

# Install htop, iotop, nethogs for monitoring
apt install -y htop iotop nethogs

print_status "Monitoring tools installed"

print_info "Step 10: Configure Log Rotation"
echo "==============================="

# Configure logrotate for application logs
cat > /etc/logrotate.d/rozitech-saas << 'EOF'
/opt/rozitech-saas/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0644 root root
    postrotate
        /usr/bin/docker-compose -f /opt/rozitech-saas/docker-compose.yml restart web || true
    endscript
}
EOF

print_status "Log rotation configured"

print_info "Step 11: Install S3 Tools (for Hetzner Object Storage)"
echo "====================================================="

# Install s3cmd for Hetzner Object Storage
apt install -y s3cmd

print_status "S3 tools installed"

print_info "Step 12: Display System Information"
echo "==================================="

echo ""
echo "🎉 Server Setup Complete!"
echo "========================"
echo ""
echo "📊 System Information:"
echo "  - OS: $(lsb_release -d | cut -f2)"
echo "  - Kernel: $(uname -r)"
echo "  - CPU: $(nproc) cores"
echo "  - RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  - Disk: $(df -h / | tail -1 | awk '{print $2}')"
echo "  - Docker: $(docker --version)"
echo "  - Docker Compose: $(docker-compose --version)"
echo ""
echo "🔧 Services Status:"
echo "  - UFW Firewall: $(ufw status | head -1)"
echo "  - Fail2ban: $(systemctl is-active fail2ban)"
echo "  - Docker: $(systemctl is-active docker)"
echo "  - Nginx: $(systemctl is-active nginx)"
echo ""
echo "📂 Project Directory: /opt/rozitech-saas"
echo ""
echo "🔑 Next Steps:"
echo "  1. Add GitHub Actions SSH key to ~/.ssh/authorized_keys"
echo "  2. Configure DNS records for your domains"
echo "  3. Continue with CI/CD setup"
echo ""
echo "💡 Useful Commands:"
echo "  - Check logs: journalctl -fu docker"
echo "  - Monitor resources: htop"
echo "  - Check disk usage: ncdu /"
echo "  - Firewall status: ufw status"
echo "  - Docker stats: docker stats"
echo ""

print_status "All setup tasks completed successfully!"