# TeamSpace SSO Integration - Deployment Guide

## Overview
This document outlines the steps to deploy the TeamSpace SSO integration API endpoints to production.

## ✅ Completed Implementation

The following has been successfully implemented and tested:

### API Endpoints
1. **GET /api/auth/verify** - Token verification endpoint
2. **GET /api/organizations/{id}/** - Organization details endpoint
3. **GET /api/subscriptions/check** - Subscription validation endpoint

### Database Changes
- Added `product_code` field to Subscription model
- Migration created: `apps/subscriptions/migrations/0002_subscription_product_code.py`

### Configuration
- CORS configured for `https://teamspace.rozitech.com`
- JWT authentication enabled
- All 11 tests passing

---

## 🚀 Deployment Steps

### Step 1: Update Environment Variables

Add or verify these environment variables in your production `.env` file:

```bash
# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://teamspace.rozitech.com

# JWT Configuration (if not already set)
JWT_SECRET=<your-production-jwt-secret>

# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.production  # or your production settings module
```

### Step 2: Run Database Migrations

On your production database, run:

```bash
# Activate virtual environment
source venv/bin/activate  # or your venv path

# Set production settings
export DJANGO_SETTINGS_MODULE=config.settings.production

# Run migrations
python manage.py migrate subscriptions
python manage.py migrate authentication

# Verify migrations applied
python manage.py showmigrations
```

### Step 3: Verify JWT Authentication

Ensure JWT authentication is properly configured in production settings:

```python
# In config/settings/production.py (or equivalent)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Step 4: Deploy Code

Follow your standard GitLab CI/CD deployment process:

```bash
# Create feature branch
git checkout -b feature/GVB.TEAM-XXX-teamspace-sso-integration

# Stage changes
git add .

# Commit changes
git commit -m "Add TeamSpace SSO integration API endpoints

- Implement token verification endpoint (GET /api/auth/verify)
- Implement organization details endpoint (GET /api/organizations/{id}/)
- Implement subscription check endpoint (GET /api/subscriptions/check)
- Add product_code field to Subscription model
- Configure CORS for teamspace.rozitech.com
- Add comprehensive test suite (11 tests, all passing)"

# Push to remote
git push -u origin feature/GVB.TEAM-XXX-teamspace-sso-integration
```

### Step 5: Create Merge Request

Create a merge request via GitLab with:
- Target branch: `develop`
- Description: Reference this deployment guide
- Reviewers: As per team process

### Step 6: Test in Development/Test Environment

Before production deployment, test the endpoints in your test environment:

```bash
# 1. Test token verification
curl -X GET https://test.rozitech.com/api/auth/verify \
  -H "Authorization: Bearer YOUR_TEST_JWT_TOKEN"

# 2. Test organization details
curl -X GET https://test.rozitech.com/api/organizations/YOUR_ORG_UUID/ \
  -H "Authorization: Bearer YOUR_TEST_JWT_TOKEN"

# 3. Test subscription check
curl -X GET "https://test.rozitech.com/api/subscriptions/check?organizationId=YOUR_ORG_UUID&productCode=teamspace" \
  -H "Authorization: Bearer YOUR_TEST_JWT_TOKEN"
```

### Step 7: Production Deployment

Once approved and tested:

1. Merge to `develop` branch
2. GitLab CI will run tests automatically
3. Deploy to production via your CI/CD pipeline
4. Run migrations on production database
5. Verify endpoints are accessible

---

## 🧪 Testing Checklist

After deployment, verify:

- [ ] Migrations applied successfully
- [ ] Token verification endpoint returns 200 with valid JWT
- [ ] Token verification endpoint returns 401 with invalid/missing JWT
- [ ] Organization endpoint returns organization details with valid access
- [ ] Organization endpoint returns 403 when user has no access
- [ ] Organization endpoint returns 404 for non-existent organization
- [ ] Subscription check returns active subscription status
- [ ] Subscription check returns false for expired subscriptions
- [ ] Subscription check validates product_code correctly
- [ ] CORS headers allow requests from teamspace.rozitech.com

---

## 📝 API Documentation

### Endpoint 1: Token Verification

**Request:**
```http
GET /api/auth/verify
Authorization: Bearer {jwt_token}
```

**Success Response (200):**
```json
{
  "success": true,
  "user": {
    "id": "user_id",
    "username": "john_doe",
    "email": "john@example.com",
    "fullName": "John Doe",
    "name": "John Doe",
    "avatarUrl": "",
    "role": "admin"
  }
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": "Invalid or expired token"
}
```

---

### Endpoint 2: Organization Details

**Request:**
```http
GET /api/organizations/{organization_id}/
Authorization: Bearer {jwt_token}
```

**Success Response (200):**
```json
{
  "success": true,
  "organization": {
    "id": "org_uuid",
    "name": "Organization Name",
    "subscription": {
      "id": "sub_uuid",
      "status": "active"
    },
    "settings": {
      "timezone": "UTC",
      "locale": "en-US"
    }
  }
}
```

**Error Responses:**
- **403 Forbidden:** User doesn't have access to organization
- **404 Not Found:** Organization doesn't exist

---

### Endpoint 3: Subscription Check

**Request:**
```http
GET /api/subscriptions/check?organizationId={org_id}&productCode=teamspace
Authorization: Bearer {jwt_token}
```

**Success Response (200) - Active:**
```json
{
  "success": true,
  "hasActiveSubscription": true,
  "subscription": {
    "id": "sub_uuid",
    "status": "active",
    "productCode": "teamspace",
    "tier": "professional",
    "expiresAt": "2025-12-31T23:59:59Z",
    "limits": {
      "maxUsers": 50,
      "maxStorage": 107374182400
    }
  }
}
```

**Success Response (200) - No Active:**
```json
{
  "success": true,
  "hasActiveSubscription": false,
  "message": "No active teamspace subscription found"
}
```

**Error Responses:**
- **400 Bad Request:** Missing required parameters
- **403 Forbidden:** User doesn't have access to organization
- **404 Not Found:** Organization doesn't exist

---

## 🔧 Configuration Files Modified

1. `apps/authentication/` - New app created
   - `views.py` - API endpoint implementations
   - `serializers.py` - Response serializers
   - `urls.py` - URL routing
   - `tests.py` - Comprehensive test suite
   - `apps.py` - App configuration

2. `apps/subscriptions/models.py` - Added `product_code` field

3. `apps/subscriptions/urls.py` - Added subscription check endpoint

4. `apps/tenants/urls.py` - Added organization details endpoint

5. `config/urls.py` - Added TeamSpace SSO routes

6. `config/simple_urls.py` - Added TeamSpace SSO routes for quickstart

7. `config/settings/base.py` - Added CORS configuration

8. `config/settings/quickstart.py` - Added CORS and JWT configuration

---

## 🔐 Security Notes

1. **JWT Tokens:** Ensure JWT_SECRET is strong and different in production
2. **CORS:** Only `teamspace.rozitech.com` is allowed (configured)
3. **Authentication:** All endpoints require valid JWT authentication
4. **Authorization:** Users can only access organizations they belong to
5. **HTTPS:** Ensure all production endpoints use HTTPS only

---

## 📞 Support

For issues or questions:
- Check test suite: `python manage.py test apps.authentication.tests`
- Review API documentation: `/api/docs/`
- Contact: Platform Team

---

## 📅 Deployment Information

- **Implementation Date:** 2025-10-10
- **Version:** 1.0.0
- **Status:** Ready for Production
- **Tests:** 11/11 passing ✅
