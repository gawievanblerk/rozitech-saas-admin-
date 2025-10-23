# Unified Billing System - Deployment Guide

**Date:** October 13, 2025
**Version:** 1.0
**Status:** Ready for Production Deployment

---

## Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
# SSH to your server
ssh user@your-production-server

# Navigate to project
cd /opt/rozitech-saas-admin

# Run deployment script
./deployment/deploy-unified-billing.sh
```

The script will:
- ✅ Create backup
- ✅ Pull latest code
- ✅ Run migrations
- ✅ Seed products (optional)
- ✅ Collect static files
- ✅ Restart services
- ✅ Verify deployment

---

## Option 2: Manual Deployment

### Step-by-Step Instructions

#### 1. Connect to Production Server

```bash
ssh user@154.65.107.211
# or whatever your production server is
```

#### 2. Navigate to Project Directory

```bash
cd /opt/rozitech-saas-admin
```

#### 3. Create Backup

```bash
# Create backup directory
mkdir -p backups/pre-unified-billing-$(date +%Y%m%d)

# Backup current code
cp -r apps/subscriptions backups/pre-unified-billing-$(date +%Y%m%d)/
cp -r config/settings backups/pre-unified-billing-$(date +%Y%m%d)/
```

#### 4. Pull Latest Code

```bash
# Fetch latest changes
git fetch origin

# Switch to main branch
git checkout main

# Pull latest code
git pull origin main

# Verify commit
git log -1 --oneline
# Should show: "Add unified multi-product billing system"
```

#### 5. Activate Virtual Environment

```bash
source venv/bin/activate
# or
source env/bin/activate
```

#### 6. Install Dependencies

```bash
# Install Stripe library
pip install stripe
```

#### 7. Run Database Migrations

```bash
# Run products migrations (shared schema)
python manage.py migrate products

# Run subscriptions migrations (tenant schemas)
python manage.py migrate subscriptions

# Run all pending migrations
python manage.py migrate
```

**Expected Output:**
```
Running migrations:
  Applying products.0001_initial... OK
  Applying subscriptions.0004_tenant_product_subscriptions... OK
```

#### 8. Seed Product Catalog

```bash
# Populate products, plans, and bundles
python manage.py seed_products
```

**Expected Output:**
```
Creating base pricing plans...
  ✓ Created 3 base pricing plans
Creating products...
  ✓ Created 3 products
Creating product plans...
  ✓ Created 9 product plans
Creating subscription bundles...
  ✓ Created 3 subscription bundles

Successfully seeded:
  - 3 products
  - 9 product plans
  - 3 subscription bundles
```

#### 9. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### 10. Configure Stripe (IMPORTANT)

Edit your `.env` file:

```bash
nano .env
```

Add these lines:

```bash
# Stripe Configuration
STRIPE_API_KEY=sk_test_your_test_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

**Get Stripe Keys:**
1. Log in to https://dashboard.stripe.com
2. Go to Developers → API keys
3. Copy test mode keys (use live keys for production)
4. For webhook secret: Developers → Webhooks → Add endpoint

**Webhook URL:** `https://your-domain.com/api/subscriptions/webhooks/stripe/`

#### 11. Restart Services

```bash
# Restart Gunicorn
sudo systemctl restart gunicorn-rozitech-saas

# Reload Nginx
sudo systemctl reload nginx
```

#### 12. Verify Deployment

```bash
# Check service status
sudo systemctl status gunicorn-rozitech-saas
sudo systemctl status nginx

# Verify products in database
python manage.py shell -c "from apps.products.models import Product; print(f'Products: {Product.objects.count()}')"

# Check logs
tail -f logs/django.log
```

---

## Verification Checklist

After deployment, verify these endpoints:

### Admin Interface

- [ ] **Products:** https://your-domain.com/admin/products/product/
  - Should show 3 products (AutoFlow AI, BuildEasy, TeamSpace)

- [ ] **Product Plans:** https://your-domain.com/admin/products/productplan/
  - Should show 9 pricing plans

- [ ] **Bundles:** https://your-domain.com/admin/products/subscriptionbundle/
  - Should show 3 bundles with discount calculations

- [ ] **Subscriptions:** https://your-domain.com/admin/subscriptions/productsubscription/
  - Empty initially (will populate when customers subscribe)

### API Endpoints

```bash
# Test Stripe connection (internal endpoint)
curl -X POST https://your-domain.com/api/subscriptions/test/stripe/

# Expected response:
# {"status":"success","test_mode":true,"message":"Stripe connection successful"}
```

### Database Tables

Run this in Django shell:

```python
python manage.py shell

from apps.products.models import Product, ProductPlan, SubscriptionBundle
from apps.subscriptions.models_products import ProductSubscription, UsageRecord

# Check counts
print(f"Products: {Product.objects.count()}")  # Should be 3
print(f"Product Plans: {ProductPlan.objects.count()}")  # Should be 9
print(f"Bundles: {SubscriptionBundle.objects.count()}")  # Should be 3

# List products
for p in Product.objects.all():
    print(f"  - {p.name} ({p.code})")
```

---

## Rollback Procedure

If something goes wrong:

```bash
# 1. Switch to previous commit
git log --oneline  # Find previous commit hash
git checkout <previous-commit-hash>

# 2. Reverse migrations
python manage.py migrate subscriptions 0003
python manage.py migrate products zero

# 3. Restart services
sudo systemctl restart gunicorn-rozitech-saas
sudo systemctl reload nginx

# 4. Restore backup
cp -r backups/pre-unified-billing-YYYYMMDD/* ./
```

---

## Troubleshooting

### Issue: Migration Fails

```bash
# Check migration status
python manage.py showmigrations

# Check for errors
python manage.py migrate --traceback

# Common fix: Fake migrations if tables already exist
python manage.py migrate products --fake-initial
```

### Issue: Products Not Seeding

```bash
# Clear existing products first
python manage.py shell -c "from apps.products.models import Product; Product.objects.all().delete()"

# Run seed again
python manage.py seed_products --clear
```

### Issue: Stripe Connection Fails

```bash
# Verify .env file
cat .env | grep STRIPE

# Test in shell
python manage.py shell
>>> from apps.subscriptions.services.stripe_service import StripeService
>>> s = StripeService()
>>> print(s.test_mode)  # Should be True for test keys
```

### Issue: Services Won't Restart

```bash
# Check logs
sudo journalctl -u gunicorn-rozitech-saas -n 50

# Check for Python errors
python manage.py check --deploy

# Restart manually
sudo systemctl stop gunicorn-rozitech-saas
sudo systemctl start gunicorn-rozitech-saas
```

---

## Post-Deployment Tasks

### 1. Configure Stripe Webhook

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter URL: `https://your-domain.com/api/subscriptions/webhooks/stripe/`
4. Select events to listen for:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `payment_method.attached`
   - `payment_method.detached`
5. Copy webhook signing secret
6. Add to `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`
7. Restart services

### 2. Test Webhook Delivery

Using Stripe CLI:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local/staging
stripe listen --forward-to https://your-domain.com/api/subscriptions/webhooks/stripe/

# Trigger test event
stripe trigger customer.subscription.created
```

### 3. Create Test Subscription

```python
python manage.py shell

from apps.subscriptions.services.stripe_service import StripeService
from apps.tenants.models import Organization
from apps.products.models import ProductPlan

# Get service
stripe_service = StripeService()

# Get organization and plan
org = Organization.objects.first()
plan = ProductPlan.objects.filter(product__code='autoflow').first()

# Create subscription
sub = stripe_service.create_subscription(
    organization=org,
    product_plan=plan,
    trial_days=14
)

print(f"Created subscription: {sub.id}")
print(f"Status: {sub.status}")
print(f"Trial ends: {sub.trial_end_date}")
```

### 4. Monitor Logs

```bash
# Watch Django logs
tail -f logs/django.log

# Watch Gunicorn logs
sudo journalctl -u gunicorn-rozitech-saas -f

# Watch Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## Production Readiness Checklist

Before going live with real customers:

- [ ] Stripe API keys changed from test to live mode
- [ ] Webhook endpoint configured in Stripe
- [ ] Webhook signature verification tested
- [ ] SSL certificate valid and up to date
- [ ] Database backups configured
- [ ] Error monitoring set up (Sentry, etc.)
- [ ] Email notifications tested
- [ ] Payment flow tested end-to-end
- [ ] Refund process tested
- [ ] Subscription cancellation tested
- [ ] Usage tracking tested
- [ ] Invoice generation tested

---

## Support

**Documentation:**
- Implementation Summary: `IMPLEMENTATION_SUMMARY.md`
- Billing Plan: `UNIFIED_BILLING_PLAN.md`

**Logs Location:**
- Django: `logs/django.log`
- Gunicorn: `journalctl -u gunicorn-rozitech-saas`
- Nginx: `/var/log/nginx/`

**Admin Interface:**
- URL: `https://your-domain.com/admin/`
- Products: `/admin/products/`
- Subscriptions: `/admin/subscriptions/`

---

## Deployment History

| Date | Version | Changes | Deployed By |
|------|---------|---------|-------------|
| 2025-10-13 | 1.0 | Initial unified billing system | - |

---

**Last Updated:** October 13, 2025
**Next Review:** After first production deployment
