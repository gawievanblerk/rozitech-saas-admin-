# Production Deployment Commands
# Run these commands on your production server (154.65.107.234)

## Step 1: Connect to Server
```bash
# Option A: From your local machine
ssh root@154.65.107.234

# Option B: Use Hetzner Cloud Console
# Go to: https://console.hetzner.cloud → Select your server → Open Console
```

## Step 2: Navigate to Application Directory
```bash
cd /opt/rozitech-saas-admin
# Or wherever your app is deployed - check with:
# ls -la /opt/ | grep rozitech
```

## Step 3: Pull Latest Code
```bash
git fetch origin
git checkout main
git pull origin main
```

## Step 4: Activate Virtual Environment
```bash
# Try one of these (depends on your setup):
source venv/bin/activate
# or
source env/bin/activate
# or
source ~/.virtualenvs/rozitech-saas-admin/bin/activate
```

## Step 5: Install New Dependencies
```bash
pip install djangorestframework-simplejwt
```

## Step 6: Run Database Migrations
```bash
# Set production environment
export DJANGO_SETTINGS_MODULE=config.settings.production

# Run migrations
python manage.py migrate subscriptions
python manage.py migrate authentication

# Verify migrations
python manage.py showmigrations | grep -A5 subscriptions
python manage.py showmigrations | grep -A5 authentication
```

## Step 7: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

## Step 8: Run Tests (Optional but Recommended)
```bash
python manage.py test apps.authentication.tests --verbosity=2
```

## Step 9: Restart Application Services
```bash
# Find your service name:
systemctl list-units | grep -i "gunicorn\|uwsgi\|rozitech"

# Restart (use the actual service name you found):
sudo systemctl restart gunicorn-rozitech-saas
# or
sudo systemctl restart uwsgi

# Reload nginx
sudo systemctl reload nginx
```

## Step 10: Verify Deployment
```bash
# Check service status
systemctl status gunicorn-rozitech-saas
# or
systemctl status uwsgi

# Check nginx status
systemctl status nginx

# View logs
journalctl -u gunicorn-rozitech-saas -n 50 --no-pager
```

## Step 11: Test API Endpoints
```bash
# Test from server (replace with your actual domain)
curl -I https://your-domain.com/api/auth/verify
curl -I https://your-domain.com/api/docs/

# Or test from your local machine
curl -I https://154.65.107.234/api/auth/verify
```

---

## Troubleshooting

### If git pull fails:
```bash
git status
git stash  # If there are local changes
git pull origin main
```

### If migrations fail:
```bash
# Check database connection
python manage.py check --database default

# View migration status
python manage.py showmigrations

# Run with verbosity for more info
python manage.py migrate --verbosity=3
```

### If service restart fails:
```bash
# Check logs
journalctl -xe

# Check service file
systemctl cat gunicorn-rozitech-saas

# Manual restart
sudo killall gunicorn
sudo systemctl start gunicorn-rozitech-saas
```

---

## Environment Variables to Check

Ensure your production `.env` file includes:
```bash
# Check current env file
cat .env | grep CORS_ALLOWED_ORIGINS

# Should include:
CORS_ALLOWED_ORIGINS=https://teamspace.rozitech.com,http://localhost:3000
```

---

## Success Indicators

✅ Git pull completed without errors
✅ Migrations applied: 0002_subscription_product_code
✅ Services restarted successfully
✅ API endpoints return HTTP 200/401 (not 404/500)
✅ No errors in application logs

---

## Quick Copy-Paste Version

```bash
cd /opt/rozitech-saas-admin && \
source venv/bin/activate && \
git pull origin main && \
pip install djangorestframework-simplejwt && \
export DJANGO_SETTINGS_MODULE=config.settings.production && \
python manage.py migrate subscriptions && \
python manage.py migrate authentication && \
python manage.py collectstatic --noinput && \
sudo systemctl restart gunicorn-rozitech-saas && \
sudo systemctl reload nginx && \
echo "✅ Deployment Complete!"
```
