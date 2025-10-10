# Server Setup Guide - TeamSpace SSO API
## Production Deployment on 154.65.107.234

This guide walks through setting up the Rozitech SaaS Admin platform to serve the TeamSpace SSO API endpoints.

---

## Current Status
✅ Repository cloned to `/opt/rozitech-saas-admin`
✅ Virtual environment created
✅ Dependencies installed
⏳ Ready for configuration and service setup

---

## Step 1: Run Database Migrations

```bash
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, tenants, subscriptions, authentication
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying subscriptions.0002_subscription_product_code... OK
  Applying authentication.0001_initial... OK
```

---

## Step 2: Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user. You can skip this for now and do it later.

---

## Step 3: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

**Expected output:**
```
Copying static files...
123 static files copied to '/opt/rozitech-saas-admin/staticfiles'
```

---

## Step 4: Run Tests (Verify Everything Works)

```bash
python manage.py test apps.authentication.tests --verbosity=2
```

**Expected output:**
```
test_invalid_token (apps.authentication.tests.TokenVerificationEndpointTests) ... ok
test_missing_authorization (apps.authentication.tests.TokenVerificationEndpointTests) ... ok
test_valid_token (apps.authentication.tests.TokenVerificationEndpointTests) ... ok
...
Ran 11 tests in 0.XXXs

OK
```

---

## Step 5: Install Gunicorn (If Not Already Installed)

```bash
pip install gunicorn
```

---

## Step 6: Create Gunicorn Log Directory

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown root:root /var/log/gunicorn
```

---

## Step 7: Create Systemd Service for Gunicorn

```bash
sudo nano /etc/systemd/system/rozitech-saas-admin.service
```

**Paste this content:**

```ini
[Unit]
Description=Rozitech SaaS Admin - TeamSpace SSO API
After=network.target

[Service]
Type=notify
User=root
Group=root
RuntimeDirectory=gunicorn
WorkingDirectory=/opt/rozitech-saas-admin
Environment="DJANGO_SETTINGS_MODULE=config.settings.quickstart"
ExecStart=/opt/rozitech-saas-admin/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn-rozitech-saas.sock \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, Y, Enter).

---

## Step 8: Enable and Start Gunicorn Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable rozitech-saas-admin
sudo systemctl start rozitech-saas-admin
sudo systemctl status rozitech-saas-admin
```

**Expected output:**
```
● rozitech-saas-admin.service - Rozitech SaaS Admin - TeamSpace SSO API
     Loaded: loaded (/etc/systemd/system/rozitech-saas-admin.service; enabled)
     Active: active (running) since ...
```

**If there are errors, check logs:**
```bash
sudo journalctl -u rozitech-saas-admin -n 50
```

---

## Step 9: Configure Nginx

### Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/rozitech-saas-admin
```

**Paste this content:**

```nginx
upstream rozitech_saas_admin {
    server unix:/run/gunicorn-rozitech-saas.sock fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name 154.65.107.234 saas.rozitech.com admin.rozitech.com;

    access_log /var/log/nginx/rozitech-saas-admin-access.log;
    error_log /var/log/nginx/rozitech-saas-admin-error.log;

    client_max_body_size 10M;

    location /static/ {
        alias /opt/rozitech-saas-admin/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/rozitech-saas-admin/media/;
        expires 7d;
    }

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

        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://teamspace.rozitech.com' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }

        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
        send_timeout 120;
    }
}
```

### Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/rozitech-saas-admin /etc/nginx/sites-enabled/
```

### Test Nginx Configuration

```bash
sudo nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Reload Nginx

```bash
sudo systemctl reload nginx
```

---

## Step 10: Verify Deployment

### Check Services are Running

```bash
sudo systemctl status rozitech-saas-admin
sudo systemctl status nginx
```

Both should show "active (running)".

### Test API Endpoints from Server

```bash
# Test API documentation
curl -I http://localhost/api/docs/

# Should return: HTTP/1.1 200 OK
```

### Test from External Network

From your local machine:

```bash
# Test API docs (should be accessible)
curl -I http://154.65.107.234/api/docs/

# Test auth endpoint (should return 401 without token)
curl -I http://154.65.107.234/api/auth/verify
```

---

## Step 11: Test TeamSpace SSO Endpoints

### Create Test User and Token

On the server:

```bash
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py shell
```

In the Python shell:

```python
from django.contrib.auth.models import User
from apps.tenants.models import Organization, OrganizationUser
from apps.subscriptions.models import Subscription, PricingPlan
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
from django.utils import timezone

# Create test user
user = User.objects.create_user(
    username='testuser',
    email='test@rozitech.com',
    password='testpass123',
    first_name='Test',
    last_name='User'
)

# Create organization
org = Organization.objects.create(
    name='Test Organization',
    slug='test-org',
    is_active=True
)

# Add user to organization
org_user = OrganizationUser.objects.create(
    organization=org,
    user=user,
    role='admin',
    is_active=True
)

# Create pricing plan
plan = PricingPlan.objects.create(
    name='Test Plan',
    price=99.99,
    billing_cycle='monthly',
    is_active=True
)

# Create active subscription
subscription = Subscription.objects.create(
    organization=org,
    plan=plan,
    status='active',
    product_code='teamspace',
    start_date=timezone.now(),
    end_date=timezone.now() + timedelta(days=30)
)

# Generate JWT token
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f"\n===== TEST CREDENTIALS =====")
print(f"Username: testuser")
print(f"Password: testpass123")
print(f"Organization ID: {org.id}")
print(f"Access Token: {access_token}")
print(f"===========================\n")

# Exit shell
exit()
```

### Test with cURL

```bash
# Replace YOUR_TOKEN with the access token from above
TOKEN="YOUR_TOKEN_HERE"
ORG_ID="YOUR_ORG_ID_HERE"

# Test 1: Token verification
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost/api/auth/verify

# Test 2: Organization details
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost/api/organizations/$ORG_ID/

# Test 3: Subscription check
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost/api/subscriptions/check?organization_id=$ORG_ID&product_code=teamspace"
```

---

## Success Indicators

✅ Gunicorn service running: `sudo systemctl status rozitech-saas-admin`
✅ Nginx running: `sudo systemctl status nginx`
✅ API docs accessible: `http://154.65.107.234/api/docs/`
✅ Token verification returns 401 without auth
✅ Token verification returns user data with valid JWT
✅ Organization endpoint returns org details
✅ Subscription check validates active subscriptions

---

## Troubleshooting

### Gunicorn won't start

```bash
# Check logs
sudo journalctl -u rozitech-saas-admin -n 100

# Check if socket file exists
ls -la /run/gunicorn-rozitech-saas.sock

# Test gunicorn manually
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

### Nginx 502 Bad Gateway

```bash
# Check if gunicorn is running
sudo systemctl status rozitech-saas-admin

# Check nginx error logs
sudo tail -f /var/log/nginx/rozitech-saas-admin-error.log

# Check permissions on socket
ls -la /run/gunicorn-rozitech-saas.sock
```

### Database errors

```bash
# Re-run migrations
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py migrate --run-syncdb
```

### CORS errors from TeamSpace

Check that:
1. Nginx CORS headers are configured correctly
2. TeamSpace is using `https://teamspace.rozitech.com`
3. Requests include `Authorization: Bearer <token>` header

---

## Monitoring

### View Application Logs

```bash
# Gunicorn logs
sudo tail -f /var/log/gunicorn/access.log
sudo tail -f /var/log/gunicorn/error.log

# Nginx logs
sudo tail -f /var/log/nginx/rozitech-saas-admin-access.log
sudo tail -f /var/log/nginx/rozitech-saas-admin-error.log

# Systemd logs
sudo journalctl -u rozitech-saas-admin -f
```

---

## API Endpoints

Once deployed, these endpoints will be available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/verify` | GET | Verify JWT token and return user info |
| `/api/organizations/{id}/` | GET | Get organization details |
| `/api/subscriptions/check` | GET | Check subscription status |
| `/api/docs/` | GET | Interactive API documentation |
| `/admin/` | GET | Django admin panel |

---

## Next Steps

1. Set up SSL certificate with Let's Encrypt (certbot)
2. Configure monitoring (optional)
3. Set up automated backups for SQLite database
4. Document TeamSpace integration on their end
5. Create production users and organizations
6. Test full integration flow with TeamSpace

---

## Quick Reference Commands

```bash
# Restart services
sudo systemctl restart rozitech-saas-admin
sudo systemctl reload nginx

# View logs
sudo journalctl -u rozitech-saas-admin -f

# Django management
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py <command>

# Update code
cd /opt/rozitech-saas-admin
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart rozitech-saas-admin
```
