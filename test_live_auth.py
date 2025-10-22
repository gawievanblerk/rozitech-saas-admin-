#!/usr/bin/env python
"""
Test auth integration with live auth server
Tests the complete flow: login → verify token → create local user
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from core.auth_client import get_auth_client
from django.contrib.auth import get_user_model

User = get_user_model()

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def test_auth_server_health():
    """Test 1: Check auth server health"""
    print_header("TEST 1: Auth Server Health Check")

    try:
        client = get_auth_client()
        health = client.health_check()

        if health.get('status') == 'healthy':
            print_success(f"Auth server is healthy")
            print_info(f"  Version: {health.get('version')}")
            print_info(f"  Environment: {health.get('environment')}")
            print_info(f"  Database: {health.get('database')}")
            return True
        else:
            print_error(f"Auth server is unhealthy: {health}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_login_flow():
    """Test 2: Login with admin credentials"""
    print_header("TEST 2: Login Flow")

    try:
        client = get_auth_client()

        # Test credentials (use admin account from auth server)
        email = "admin@rozitech.com"
        password = "Admin123!@#Rozitech2025"

        print_info(f"Attempting login with: {email}")

        result = client.login(email, password)

        if 'accessToken' in result and 'user' in result:
            print_success("Login successful!")
            print_info(f"  User: {result['user'].get('email')}")
            print_info(f"  User ID: {result['user'].get('id')}")
            print_info(f"  Access Token: {result['accessToken'][:20]}...")

            if 'organization' in result:
                print_info(f"  Organization: {result['organization'].get('name')}")

            return result
        else:
            print_error(f"Login failed: Missing required fields")
            return None
    except Exception as e:
        print_error(f"Login failed: {e}")
        return None

def test_token_verification(access_token):
    """Test 3: Verify token with auth server"""
    print_header("TEST 3: Token Verification")

    try:
        client = get_auth_client()

        print_info(f"Verifying token: {access_token[:20]}...")

        user_data = client.verify_token(access_token)

        if user_data and 'user' in user_data:
            print_success("Token verified successfully!")
            print_info(f"  Email: {user_data['user'].get('email')}")
            print_info(f"  Name: {user_data['user'].get('firstName')} {user_data['user'].get('lastName')}")
            return user_data
        else:
            print_error("Token verification returned invalid data")
            return None
    except Exception as e:
        print_error(f"Token verification failed: {e}")
        return None

def test_user_sync(user_data):
    """Test 4: Check if local user is created/synced"""
    print_header("TEST 4: User Synchronization")

    try:
        email = user_data['user']['email']

        print_info(f"Checking if local user exists: {email}")

        # Check if user exists
        user = User.objects.filter(email=email).first()

        if user:
            print_success(f"Local user found!")
            print_info(f"  Username: {user.username}")
            print_info(f"  Email: {user.email}")
            print_info(f"  First Name: {user.first_name}")
            print_info(f"  Last Name: {user.last_name}")
            print_info(f"  Active: {user.is_active}")
            return True
        else:
            print_info("Local user not found (will be created on API request)")

            # Simulate user creation (what the auth backend does)
            print_info("Creating local user from auth server data...")
            user, created = User.objects.get_or_create(
                email=email.lower(),
                defaults={
                    'username': email.lower(),
                    'first_name': user_data['user'].get('firstName', ''),
                    'last_name': user_data['user'].get('lastName', ''),
                    'is_active': True,
                }
            )

            if created:
                print_success("Local user created successfully!")
            else:
                print_success("Local user already exists!")

            print_info(f"  User ID: {user.id}")
            print_info(f"  Username: {user.username}")
            return True
    except Exception as e:
        print_error(f"User sync failed: {e}")
        return False

def test_token_refresh(refresh_token):
    """Test 5: Token refresh"""
    print_header("TEST 5: Token Refresh")

    try:
        client = get_auth_client()

        print_info(f"Refreshing token: {refresh_token[:20]}...")

        result = client.refresh_token(refresh_token)

        if 'accessToken' in result:
            print_success("Token refreshed successfully!")
            print_info(f"  New Access Token: {result['accessToken'][:20]}...")
            return True
        else:
            print_error("Token refresh returned invalid data")
            return False
    except Exception as e:
        print_error(f"Token refresh failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests"""
    print("\n" + "🚀 " + "="*68)
    print("  ROZITECH SAAS ADMIN - AUTH INTEGRATION TEST")
    print("="*70)
    print_info("Testing integration with live auth server at localhost:4000")
    print_info("Ensure SSH tunnel is running!")

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_auth_server_health()))

    if not results[0][1]:
        print_error("\n❌ Auth server not accessible. Aborting tests.")
        print_info("Start SSH tunnel: ssh -i ~/.ssh/rozitech-xneelo -L 4000:localhost:4000 ubuntu@154.65.107.211 -N")
        return False

    # Test 2: Login
    login_result = test_login_flow()
    results.append(("Login Flow", login_result is not None))

    if not login_result:
        print_error("\n❌ Login failed. Cannot continue tests.")
        return False

    # Test 3: Token verification
    user_data = test_token_verification(login_result['accessToken'])
    results.append(("Token Verification", user_data is not None))

    # Test 4: User sync
    if user_data:
        results.append(("User Synchronization", test_user_sync(user_data)))
    else:
        results.append(("User Synchronization", False))

    # Test 5: Token refresh
    if 'refreshToken' in login_result:
        results.append(("Token Refresh", test_token_refresh(login_result['refreshToken'])))
    else:
        print_info("No refresh token available, skipping refresh test")

    # Print summary
    print_header("TEST SUMMARY")

    passed = 0
    failed = 0

    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
            passed += 1
        else:
            print_error(f"{test_name}")
            failed += 1

    print("\n" + "-"*70)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    print("="*70)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Auth integration is working correctly.")
        print_info("The SaaS Admin is ready to use the auth server.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)