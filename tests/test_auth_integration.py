"""
Integration tests for Auth Server authentication
Tests the complete auth flow with the remote Rozitech Auth Server
"""
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APITestCase, APIClient
from core.auth_client import AuthServerClient, get_auth_client
from core.authentication import RemoteJWTAuthentication

User = get_user_model()


class TestAuthServerClient(APITestCase):
    """Test AuthServerClient functionality"""

    def setUp(self):
        self.client = AuthServerClient()
        self.mock_response = MagicMock()

    @patch('requests.request')
    def test_verify_token_success(self, mock_request):
        """Test successful token verification"""
        # Mock successful response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'user': {
                'id': 'user-123',
                'email': 'test@example.com',
                'firstName': 'John',
                'lastName': 'Doe'
            },
            'organization': {
                'id': 'org-123',
                'name': 'Test Org'
            }
        }
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.verify_token('valid_token_123')

        # Verify
        self.assertEqual(result['user']['email'], 'test@example.com')
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'GET')
        self.assertIn('/api/auth/me', call_args[0][1])

    @patch('requests.request')
    def test_verify_token_invalid(self, mock_request):
        """Test token verification with invalid token"""
        # Mock 401 response
        self.mock_response.status_code = 401
        self.mock_response.json.return_value = {'error': 'Invalid token'}
        mock_request.return_value = self.mock_response

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.verify_token('invalid_token')

        self.assertIn('Invalid or expired token', str(context.exception))

    @patch('requests.request')
    def test_verify_token_timeout(self, mock_request):
        """Test token verification with timeout"""
        import requests
        mock_request.side_effect = requests.exceptions.Timeout()

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.verify_token('any_token')

        self.assertIn('timeout', str(context.exception).lower())

    @patch('requests.request')
    def test_verify_token_connection_error(self, mock_request):
        """Test token verification with connection error"""
        import requests
        mock_request.side_effect = requests.exceptions.ConnectionError()

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.verify_token('any_token')

        self.assertIn('unavailable', str(context.exception).lower())

    @patch('requests.request')
    def test_refresh_token_success(self, mock_request):
        """Test successful token refresh"""
        # Mock successful response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'accessToken': 'new_access_token',
            'refreshToken': 'new_refresh_token'
        }
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.refresh_token('refresh_token_123')

        # Verify
        self.assertEqual(result['accessToken'], 'new_access_token')
        mock_request.assert_called_once()

    @patch('requests.request')
    def test_login_success(self, mock_request):
        """Test successful login"""
        # Mock successful response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'accessToken': 'access_token',
            'refreshToken': 'refresh_token',
            'user': {
                'email': 'test@example.com',
                'firstName': 'John'
            }
        }
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.login('test@example.com', 'password123')

        # Verify
        self.assertIn('accessToken', result)
        self.assertIn('user', result)

    @patch('requests.request')
    def test_login_invalid_credentials(self, mock_request):
        """Test login with invalid credentials"""
        # Mock 401 response
        self.mock_response.status_code = 401
        mock_request.return_value = self.mock_response

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.login('test@example.com', 'wrongpassword')

        self.assertIn('Invalid email or password', str(context.exception))

    @patch('requests.request')
    def test_signup_success(self, mock_request):
        """Test successful signup"""
        # Mock successful response
        self.mock_response.status_code = 201
        self.mock_response.json.return_value = {
            'userId': 'user-123',
            'email': 'newuser@example.com'
        }
        mock_request.return_value = self.mock_response

        # Test
        user_data = {
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'firstName': 'New',
            'lastName': 'User',
            'company': 'Test Company'
        }
        result = self.client.signup(user_data)

        # Verify
        self.assertIn('userId', result)

    @patch('requests.request')
    def test_health_check(self, mock_request):
        """Test health check endpoint"""
        # Mock successful response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'status': 'healthy',
            'version': '1.0.0'
        }
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.health_check()

        # Verify
        self.assertEqual(result['status'], 'healthy')


class TestRemoteJWTAuthentication(APITestCase):
    """Test RemoteJWTAuthentication backend"""

    def setUp(self):
        self.factory = RequestFactory()
        self.auth = RemoteJWTAuthentication()

    def test_get_authorization_header(self):
        """Test extraction of Authorization header"""
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer token123')
        header = self.auth.get_authorization_header(request)
        self.assertEqual(header, 'Bearer token123')

    def test_get_authorization_header_missing(self):
        """Test missing Authorization header"""
        request = self.factory.get('/')
        header = self.auth.get_authorization_header(request)
        self.assertIsNone(header)

    def test_extract_token_success(self):
        """Test successful token extraction"""
        token = self.auth.extract_token('Bearer abc123xyz')
        self.assertEqual(token, 'abc123xyz')

    def test_extract_token_no_bearer(self):
        """Test token extraction without Bearer keyword"""
        token = self.auth.extract_token('abc123xyz')
        self.assertIsNone(token)

    def test_extract_token_no_token(self):
        """Test token extraction with only Bearer"""
        with self.assertRaises(AuthenticationFailed):
            self.auth.extract_token('Bearer')

    def test_extract_token_with_spaces(self):
        """Test token extraction with spaces in token"""
        with self.assertRaises(AuthenticationFailed):
            self.auth.extract_token('Bearer abc 123 xyz')

    @patch('core.authentication.get_auth_client')
    def test_authenticate_success(self, mock_get_client):
        """Test successful authentication"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.verify_token.return_value = {
            'user': {
                'id': 'user-123',
                'email': 'test@example.com',
                'firstName': 'John',
                'lastName': 'Doe'
            }
        }
        mock_get_client.return_value = mock_client

        # Create request
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer valid_token')

        # Test
        user, token = self.auth.authenticate(request)

        # Verify
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(token, 'valid_token')
        mock_client.verify_token.assert_called_once_with('valid_token')

    @patch('core.authentication.get_auth_client')
    def test_authenticate_creates_user(self, mock_get_client):
        """Test that authentication creates local user"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.verify_token.return_value = {
            'user': {
                'id': 'user-new',
                'email': 'newuser@example.com',
                'firstName': 'Jane',
                'lastName': 'Smith'
            }
        }
        mock_get_client.return_value = mock_client

        # Verify user doesn't exist
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())

        # Create request
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer valid_token')

        # Test
        user, token = self.auth.authenticate(request)

        # Verify user was created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Smith')

    @patch('core.authentication.get_auth_client')
    def test_authenticate_updates_existing_user(self, mock_get_client):
        """Test that authentication updates existing user info"""
        # Create existing user
        existing_user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            first_name='OldFirst',
            last_name='OldLast'
        )

        # Setup mock with updated info
        mock_client = MagicMock()
        mock_client.verify_token.return_value = {
            'user': {
                'id': 'user-123',
                'email': 'test@example.com',
                'firstName': 'NewFirst',
                'lastName': 'NewLast'
            }
        }
        mock_get_client.return_value = mock_client

        # Create request
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer valid_token')

        # Test
        user, token = self.auth.authenticate(request)

        # Verify user was updated
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'NewFirst')
        self.assertEqual(user.last_name, 'NewLast')

    def test_authenticate_no_header(self):
        """Test authentication without Authorization header"""
        request = self.factory.get('/')
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    @patch('core.authentication.get_auth_client')
    def test_authenticate_invalid_token(self, mock_get_client):
        """Test authentication with invalid token"""
        # Setup mock to raise AuthenticationFailed
        mock_client = MagicMock()
        mock_client.verify_token.side_effect = AuthenticationFailed('Invalid token')
        mock_get_client.return_value = mock_client

        # Create request
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer invalid_token')

        # Test
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @patch('core.authentication.cache')
    @patch('core.authentication.get_auth_client')
    def test_token_caching(self, mock_get_client, mock_cache):
        """Test that token verification results are cached"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.verify_token.return_value = {
            'user': {
                'email': 'test@example.com',
                'firstName': 'John',
                'lastName': 'Doe'
            }
        }
        mock_get_client.return_value = mock_client
        mock_cache.get.return_value = None  # No cache hit first time

        # Create request
        request = self.factory.get('/', HTTP_AUTHORIZATION='Bearer cached_token')

        # Test
        self.auth.authenticate(request)

        # Verify cache was set
        mock_cache.set.assert_called_once()
        cache_key = mock_cache.set.call_args[0][0]
        self.assertIn('auth_token_', cache_key)


class TestAuthIntegrationEndToEnd(APITestCase):
    """End-to-end integration tests"""

    def setUp(self):
        self.client = APIClient()

    @patch('core.auth_client.requests.request')
    def test_full_auth_flow(self, mock_request):
        """Test complete authentication flow"""
        # Mock auth server response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'user': {
                'id': 'user-e2e',
                'email': 'e2e@example.com',
                'firstName': 'E2E',
                'lastName': 'Test'
            },
            'organization': {
                'id': 'org-e2e',
                'name': 'E2E Org'
            }
        }
        mock_request.return_value = mock_response

        # Make authenticated request to any protected endpoint
        response = self.client.get(
            '/api/auth/verify',
            HTTP_AUTHORIZATION='Bearer test_token_e2e'
        )

        # Verify user was created and authenticated
        self.assertTrue(User.objects.filter(email='e2e@example.com').exists())


@pytest.mark.django_db
class TestAuthServerClientSingleton:
    """Test singleton pattern for AuthServerClient"""

    def test_get_auth_client_returns_same_instance(self):
        """Test that get_auth_client returns singleton instance"""
        client1 = get_auth_client()
        client2 = get_auth_client()

        assert client1 is client2
