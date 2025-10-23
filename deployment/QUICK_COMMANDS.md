# Quick Reference Commands

## Initial Setup (Run Once)

```bash
# 1. Pull latest code
cd /opt/rozitech-saas-admin
git pull origin main

# 2. Run migrations and collect static
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py migrate
python manage.py collectstatic --noinput

# 3. Install Gunicorn if needed
pip install gunicorn

# 4. Create log directory
sudo mkdir -p /var/log/gunicorn
sudo chown root:root /var/log/gunicorn

# 5. Copy systemd service file
sudo cp deployment/rozitech-saas-admin.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rozitech-saas-admin
sudo systemctl start rozitech-saas-admin

# 6. Copy Nginx config
sudo cp deployment/nginx-rozitech-saas-admin.conf /etc/nginx/sites-available/rozitech-saas-admin
sudo ln -s /etc/nginx/sites-available/rozitech-saas-admin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Daily Operations

### Check Service Status
```bash
sudo systemctl status rozitech-saas-admin
sudo systemctl status nginx
```

### Restart Services
```bash
sudo systemctl restart rozitech-saas-admin
sudo systemctl reload nginx
```

### View Logs
```bash
# Gunicorn logs
sudo tail -f /var/log/gunicorn/error.log
sudo tail -f /var/log/gunicorn/access.log

# Systemd logs
sudo journalctl -u rozitech-saas-admin -f

# Nginx logs
sudo tail -f /var/log/nginx/rozitech-saas-admin-error.log
sudo tail -f /var/log/nginx/rozitech-saas-admin-access.log
```

---

## Deployment / Update

```bash
cd /opt/rozitech-saas-admin
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart rozitech-saas-admin
```

---

## Django Management

```bash
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Run tests
python manage.py test apps.authentication.tests

# Check database
python manage.py showmigrations
```

---

## Test API Endpoints

```bash
# From server
curl -I http://localhost/api/docs/
curl -I http://localhost/api/auth/verify

# From external (replace with actual IP)
curl -I http://154.65.107.234/api/docs/
curl -I http://154.65.107.234/api/auth/verify
```

---

## Troubleshooting

### Gunicorn won't start
```bash
# Check logs
sudo journalctl -u rozitech-saas-admin -n 100

# Test manually
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

### Nginx 502 Bad Gateway
```bash
# Check Gunicorn is running
sudo systemctl status rozitech-saas-admin

# Check socket exists
ls -la /run/gunicorn-rozitech-saas.sock

# Check Nginx error logs
sudo tail -f /var/log/nginx/rozitech-saas-admin-error.log
```

### Database issues
```bash
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py check
python manage.py migrate --run-syncdb
```

### Permission issues
```bash
# Fix ownership
sudo chown -R root:root /opt/rozitech-saas-admin

# Fix socket permissions
sudo chmod 666 /run/gunicorn-rozitech-saas.sock
```

---

## Verification

```bash
# Run verification script
cd /opt/rozitech-saas-admin
bash deployment/verify-app-deployment.sh
```

---

## Create Test Data

```bash
cd /opt/rozitech-saas-admin
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.quickstart
python manage.py shell

# In Python shell:
from django.contrib.auth.models import User
from apps.tenants.models import Organization, OrganizationUser
from apps.subscriptions.models import Subscription, PricingPlan
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone

# Create user
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
    name='TeamSpace Plan',
    price=99.99,
    billing_cycle='monthly',
    is_active=True
)

# Create subscription
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
```

---

## Test with JWT Token

```bash
# Set your token
TOKEN="your-jwt-token-here"
ORG_ID="your-org-id-here"

# Test token verification
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost/api/auth/verify

# Test organization details
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost/api/organizations/$ORG_ID/

# Test subscription check
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost/api/subscriptions/check?organization_id=$ORG_ID&product_code=teamspace"
```

---

## File Locations

| File/Directory | Path |
|----------------|------|
| Application | `/opt/rozitech-saas-admin` |
| Virtual Environment | `/opt/rozitech-saas-admin/venv` |
| Database (SQLite) | `/opt/rozitech-saas-admin/db.sqlite3` |
| Static Files | `/opt/rozitech-saas-admin/staticfiles` |
| Systemd Service | `/etc/systemd/system/rozitech-saas-admin.service` |
| Nginx Config | `/etc/nginx/sites-available/rozitech-saas-admin` |
| Gunicorn Socket | `/run/gunicorn-rozitech-saas.sock` |
| Gunicorn Logs | `/var/log/gunicorn/` |
| Nginx Logs | `/var/log/nginx/rozitech-saas-admin-*.log` |
