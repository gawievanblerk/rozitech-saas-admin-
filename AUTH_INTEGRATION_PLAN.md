# Auth Server Integration Plan
## Rozitech SaaS Admin → Rozitech Auth Server

**Date:** October 13, 2025
**Auth Server:** http://154.65.107.211:4000 (production)
**SaaS Admin:** Django/Python application with Django REST Framework

---

## Current State Analysis

### ✅ What's Already Built

1. **SaaS Admin** (`rozitech-saas-admin`)
   - Django REST Framework application
   - JWT authentication using `rest_framework_simplejwt`
   - Authentication views in `apps/authentication/views.py`:
     - `TokenVerificationView` - Verify JWT tokens
     - `OrganizationDetailView` - Get org details
     - `SubscriptionCheckView` - Check subscription status
   - Already configured for external auth service
   - Current auth service URL: `http://localhost:3001`

2. **Auth Server** (`rozitech-auth-server`)
   - Node.js/Express application
   - Deployed at: `154.65.107.211:4000`
   - JWT tokens (access + refresh)
   - Endpoints ready:
     - POST `/api/auth/signup`
     - POST `/api/auth/login`
     - POST `/api/auth/logout`
     - POST `/api/auth/refresh`
     - GET `/api/auth/me`
     - POST `/api/auth/verify-email`
     - POST `/api/auth/forgot-password`
     - POST `/api/auth/reset-password`

### Current Architecture

```
┌─────────────────┐
│  SaaS Admin     │
│  (Django)       │──→ JWT Verification (self-contained)
│  Port 3002      │──→ User/Org Management (local DB)
└─────────────────┘
```

---

## Target Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  SaaS Admin     │         │  Auth Server     │
│  (Django)       │◄────────┤  (Node.js)       │
│  Port 3002      │  JWT    │  Port 4000       │
│                 │  Token  │                  │
│  • Verify Token │         │  • Login         │
│  • Get User     │         │  • Signup        │
│  • Check Perms  │         │  • Refresh       │
│  • Org/Sub Mgmt │         │  • Verify Email  │
└─────────────────┘         └──────────────────┘
```

---

## Integration Strategy

### Option 1: Remote JWT Verification (Recommended)
**Description:** SaaS Admin calls Auth Server to verify tokens

**Pros:**
- Centralized authentication
- Token revocation works immediately
- Single source of truth
- Easier to add OAuth/SSO later

**Cons:**
- Extra network call per request
- Requires auth server availability

**Implementation:**
1. Update `.env` to point to auth server: `AUTH_SERVICE_URL=http://154.65.107.211:4000`
2. Create auth client library to call auth server APIs
3. Update JWT authentication backend to verify with remote server
4. Handle token refresh automatically

### Option 2: Shared JWT Secret (Faster but less secure)
**Description:** Both services use same JWT secret to verify tokens locally

**Pros:**
- No extra network calls
- Faster verification

**Cons:**
- Must keep secrets in sync
- No token revocation support
- Harder to rotate secrets

**Recommendation:** Use Option 1 for better security and centralized control

---

## Implementation Plan

### Phase 1: Auth Client Library ✅

Create `core/auth_client.py`:
```python
import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

class AuthServerClient:
    def __init__(self):
        self.base_url = settings.AUTH_SERVICE_URL

    def verify_token(self, access_token):
        """Verify JWT token with auth server"""
        try:
            response = requests.get(
                f"{self.base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            raise AuthenticationFailed("Invalid token")
        except requests.RequestException as e:
            raise AuthenticationFailed(f"Auth server unreachable: {e}")

    def refresh_token(self, refresh_token):
        """Refresh access token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refreshToken": refresh_token},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            raise AuthenticationFailed("Cannot refresh token")
        except requests.RequestException as e:
            raise AuthenticationFailed(f"Auth server unreachable: {e}")
```

### Phase 2: Custom Authentication Backend ✅

Create `core/authentication.py`:
```python
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from core.auth_client import AuthServerClient

User = get_user_model()

class RemoteJWTAuthentication(BaseAuthentication):
    """
    Authenticate by verifying JWT token with remote auth server
    """
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        client = AuthServerClient()

        try:
            # Verify token with auth server
            user_data = client.verify_token(token)

            # Get or create local user for permission/org management
            user, created = User.objects.get_or_create(
                email=user_data['user']['email'],
                defaults={
                    'username': user_data['user']['email'],
                    'first_name': user_data['user'].get('firstName', ''),
                    'last_name': user_data['user'].get('lastName', '')
                }
            )

            return (user, token)

        except AuthenticationFailed:
            raise
        except Exception as e:
            raise AuthenticationFailed(f"Authentication error: {e}")
```

### Phase 3: Update Settings ✅

Update `config/settings/base.py`:
```python
# Authentication
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'core.authentication.RemoteJWTAuthentication',  # Primary
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # Fallback
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Auth Server Configuration
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:4000')
AUTH_SERVICE_TIMEOUT = int(os.getenv('AUTH_SERVICE_TIMEOUT', '5'))
```

### Phase 4: Update Environment Variables ✅

Update `.env`:
```bash
# Auth Server (Production)
AUTH_SERVICE_URL=http://154.65.107.211:4000

# Or for local testing via SSH tunnel
AUTH_SERVICE_URL=http://localhost:4000
```

### Phase 5: Frontend Integration ✅

Update frontend login flow to use auth server:

**Before (Direct Django auth):**
```javascript
POST /api/auth/login → Django handles auth
```

**After (Auth server):**
```javascript
1. POST http://154.65.107.211:4000/api/auth/login
   ↓ Receives: { accessToken, refreshToken, user }

2. Store tokens in localStorage/cookies

3. All API calls to SaaS Admin include:
   Authorization: Bearer <accessToken>

4. SaaS Admin verifies token with auth server
```

---

## Testing Plan

### 1. Local Testing (via SSH Tunnel)

```bash
# Terminal 1: Start SSH tunnel
ssh -i ~/.ssh/rozitech-xneelo -L 4000:localhost:4000 ubuntu@154.65.107.211 -N

# Terminal 2: Update SaaS Admin .env
export AUTH_SERVICE_URL=http://localhost:4000

# Terminal 3: Test auth flow
curl -X POST http://localhost:4000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'

# Use returned token with SaaS Admin
curl -X GET http://localhost:3002/api/auth/verify \
  -H "Authorization: Bearer <token>"
```

### 2. Integration Tests

Create `tests/test_auth_integration.py`:
```python
def test_remote_token_verification():
    """Test token verification with auth server"""
    # Get token from auth server
    # Verify with SaaS Admin
    # Check user is created/updated

def test_token_refresh():
    """Test automatic token refresh"""

def test_auth_server_unavailable():
    """Test graceful degradation when auth server down"""
```

### 3. End-to-End Flow

1. User signs up on auth server
2. User logs in → receives JWT
3. User accesses SaaS Admin with JWT
4. SaaS Admin verifies token with auth server
5. User can access org/subscription data
6. Token expires → auto-refresh
7. User logs out → token invalidated

---

## Deployment Checklist

### Development Environment

- [ ] Create auth client library (`core/auth_client.py`)
- [ ] Create custom authentication backend (`core/authentication.py`)
- [ ] Update Django settings
- [ ] Update `.env` with auth server URL
- [ ] Add `requests` to `requirements.txt`
- [ ] Create integration tests
- [ ] Test via SSH tunnel to production auth server

### Production Environment

- [ ] Set `AUTH_SERVICE_URL=http://154.65.107.211:4000` in production `.env`
- [ ] Or better: Set up nginx reverse proxy with SSL
- [ ] Configure auth.rozitech.com → 154.65.107.211:4000
- [ ] Update to `AUTH_SERVICE_URL=https://auth.rozitech.com`
- [ ] Test production auth flow
- [ ] Monitor auth server logs
- [ ] Set up health checks

---

## Security Considerations

### ✅ Good Practices

1. **Token Verification:** Always verify with auth server (don't trust client)
2. **HTTPS:** Use SSL for all auth server communication (set up nginx)
3. **Timeouts:** Set reasonable timeouts (5s) to prevent hanging
4. **Error Handling:** Graceful degradation if auth server unavailable
5. **Caching:** Consider short-lived token cache (1-2 min) for performance

### ⚠️ Watch Out For

1. **Rate Limiting:** Auth server has rate limits (429 after 150 requests)
2. **Network Latency:** Extra 20-50ms per request for token verification
3. **Auth Server Downtime:** Need fallback or circuit breaker pattern
4. **Token Expiry:** Handle 401 responses and auto-refresh tokens

---

## Performance Optimization

### Caching Strategy (Optional)

```python
from django.core.cache import cache

class RemoteJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = self.get_token(request)

        # Check cache first (1-minute TTL)
        cache_key = f"auth_token_{token[:20]}"
        user_data = cache.get(cache_key)

        if not user_data:
            # Verify with auth server
            client = AuthServerClient()
            user_data = client.verify_token(token)
            cache.set(cache_key, user_data, 60)  # Cache for 1 min

        # Rest of authentication...
```

**Benefits:**
- Reduces auth server calls by ~90%
- Faster response times
- Less load on auth server

**Trade-offs:**
- 1-minute delay for token revocation
- Requires Redis/Memcached

---

## Rollback Plan

If integration fails:

1. **Quick Rollback:**
   ```bash
   # Revert to local JWT authentication
   export AUTH_SERVICE_URL=http://localhost:3001
   # Or comment out RemoteJWTAuthentication in settings
   ```

2. **Database Rollback:** No schema changes needed

3. **Code Rollback:**
   ```bash
   git revert <commit-hash>
   ```

---

## Next Steps

1. **Implement auth client library** (30 min)
2. **Create custom authentication backend** (30 min)
3. **Update settings and environment** (15 min)
4. **Write integration tests** (1 hour)
5. **Test locally via SSH tunnel** (30 min)
6. **Deploy to production** (30 min)
7. **Monitor and verify** (ongoing)

**Total Estimated Time:** 3-4 hours

---

## Support & Resources

- **Auth Server API Docs:** http://154.65.107.211:4000/api-docs
- **Auth Server Health:** http://154.65.107.211:4000/health
- **Deployment Report:** `DEPLOYMENT_TEST_REPORT.md`
- **Auth Server Repo:** https://github.com/gawievanblerk/rozitech-auth-server

---

**Ready to proceed?** Let's start with Phase 1: Creating the auth client library.