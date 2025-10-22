# SaaS Domain Setup Guide

This guide will help you set up `saas.rozitech.com` with proper DNS and SSL configuration.

## Prerequisites

- Access to your DNS provider (where rozitech.com is hosted)
- SSH access to production server: `154.65.107.211`
- Certbot installed on the server

## Step-by-Step Instructions

### 1. Add DNS Record

Log in to your DNS provider and add the following A record:

```
Type: A
Name: saas
Host/Value: 154.65.107.211
TTL: 3600 (or Auto)
```

**Verify DNS propagation:**
```bash
nslookup saas.rozitech.com
```

Expected output should show: `154.65.107.211`

### 2. Upload Configuration Files

From your local machine, copy the files to the server:

```bash
scp -i ~/.ssh/rozitech-xneelo \
  deployment/nginx-saas-admin-updated.conf \
  deployment/setup-saas-domain.sh \
  ubuntu@154.65.107.211:/opt/rozitech-saas-admin/deployment/
```

### 3. Run Automated Setup Script

SSH into the server and run the setup script:

```bash
ssh -i ~/.ssh/rozitech-xneelo ubuntu@154.65.107.211

# Switch to root
sudo su

# Navigate to deployment directory
cd /opt/rozitech-saas-admin/deployment

# Run the setup script
./setup-saas-domain.sh
```

The script will:
- ✅ Verify DNS is configured
- ✅ Create web root for Let's Encrypt
- ✅ Update nginx configuration
- ✅ Obtain SSL certificate
- ✅ Configure HTTPS redirect
- ✅ Reload nginx

### 4. Manual Setup (Alternative)

If you prefer manual setup or the script fails:

#### 4.1. Create Web Root
```bash
sudo mkdir -p /var/www/rozitech-saas-admin
sudo chown -R www-data:www-data /var/www/rozitech-saas-admin
```

#### 4.2. Update Nginx Config (HTTP only first)
```bash
sudo cp /etc/nginx/sites-available/rozitech-saas-admin \
     /etc/nginx/sites-available/rozitech-saas-admin.backup

sudo nano /etc/nginx/sites-available/rozitech-saas-admin
```

Update `server_name` line to:
```nginx
server_name saas.rozitech.com admin.rozitech.com;
```

Remove the old IP: `154.65.107.234`

Add location for Let's Encrypt:
```nginx
location /.well-known/acme-challenge/ {
    root /var/www/rozitech-saas-admin;
}
```

#### 4.3. Test and Reload Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
```

#### 4.4. Obtain SSL Certificate
```bash
sudo certbot certonly --webroot \
  -w /var/www/rozitech-saas-admin \
  -d saas.rozitech.com \
  -d admin.rozitech.com \
  --email admin@rozitech.com \
  --agree-tos
```

#### 4.5. Update Nginx with SSL
```bash
sudo cp /opt/rozitech-saas-admin/deployment/nginx-saas-admin-updated.conf \
     /etc/nginx/sites-available/rozitech-saas-admin

sudo nginx -t
sudo systemctl reload nginx
```

## 5. Verify Setup

Test the endpoints:

```bash
# Health check
curl https://saas.rozitech.com/health/

# API documentation
curl https://saas.rozitech.com/api/docs/

# Services API
curl https://saas.rozitech.com/api/v1/services/

# Organizations API
curl https://saas.rozitech.com/api/organizations/tenants/
```

## 6. Update Application Settings

If needed, update the Django settings to include the new domain in ALLOWED_HOSTS:

```bash
# On the server
sudo nano /opt/rozitech-saas-admin/config/settings/production.py
```

Ensure `ALLOWED_HOSTS` includes:
```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '154.65.107.211',
    'saas.rozitech.com',
    'admin.rozitech.com',
]
```

Restart the application:
```bash
sudo systemctl restart rozitech-saas-admin.service
```

## Troubleshooting

### DNS not resolving
- Wait 5-10 minutes for DNS propagation
- Check your DNS provider's dashboard
- Try: `dig saas.rozitech.com +short`

### SSL certificate fails
- Ensure DNS is properly configured first
- Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Verify port 80 is accessible from the internet

### Application not responding
- Check service status: `sudo systemctl status rozitech-saas-admin.service`
- Check gunicorn logs: `sudo tail -f /var/log/gunicorn/error.log`
- Verify socket file exists: `ls -la /opt/rozitech-saas-admin/run/gunicorn.sock`

### CORS errors from TeamSpace
- Ensure CORS headers are configured in nginx
- Check browser console for specific CORS errors
- Verify nginx config includes CORS headers for OPTIONS requests

## Next Steps

After successful setup:
1. Test all API endpoints
2. Update TeamSpace frontend to use `https://saas.rozitech.com`
3. Set up monitoring for the new domain
4. Configure log rotation for access/error logs