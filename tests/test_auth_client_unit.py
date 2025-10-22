"""
Unit tests for Auth Client Library
Tests the auth client without requiring Django database
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock Django settings before importing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

from core.auth_client import AuthServerClient


class TestAuthServerClient(unittest.TestCase):
    """Test AuthServerClient functionality without Django"""

    def setUp(self):
        self.client = AuthServerClient()
        self.mock_response = MagicMock()

    @patch('core.auth_client.requests.request')
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
        self.assertEqual(result['user']['firstName'], 'John')
        mock_request.assert_called_once()

        # Check request details
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], 'GET')
        self.assertIn('/api/auth/me', call_args[0][1])
        self.assertIn('Authorization', call_args[1]['headers'])

    @patch('core.auth_client.requests.request')
    def test_verify_token_invalid(self, mock_request):
        """Test token verification with invalid token"""
        from rest_framework.exceptions import AuthenticationFailed

        # Mock 401 response
        self.mock_response.status_code = 401
        self.mock_response.json.return_value = {'error': 'Invalid token'}
        mock_request.return_value = self.mock_response

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.verify_token('invalid_token')

        self.assertIn('Invalid or expired token', str(context.exception))

    @patch('core.auth_client.requests.request')
    def test_verify_token_timeout(self, mock_request):
        """Test token verification with timeout"""
        from rest_framework.exceptions import AuthenticationFailed
        import requests

        mock_request.side_effect = requests.exceptions.Timeout()

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.verify_token('any_token')

        self.assertIn('timeout', str(context.exception).lower())

    @patch('core.auth_client.requests.request')
    def test_verify_token_connection_error(self, mock_request):
        """Test token verification with connection error"""
        from rest_framework.exceptions import AuthenticationFailed
        import requests

        mock_request.side_effect = requests.exceptions.ConnectionError()

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.verify_token('any_token')

        self.assertIn('unavailable', str(context.exception).lower())

    @patch('core.auth_client.requests.request')
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
        self.assertIn('refreshToken', result)
        mock_request.assert_called_once()

    @patch('core.auth_client.requests.request')
    def test_login_success(self, mock_request):
        """Test successful login"""
        # Mock successful response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'accessToken': 'access_token_abc',
            'refreshToken': 'refresh_token_xyz',
            'user': {
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
        result = self.client.login('test@example.com', 'password123')

        # Verify
        self.assertIn('accessToken', result)
        self.assertIn('refreshToken', result)
        self.assertIn('user', result)
        self.assertEqual(result['user']['email'], 'test@example.com')

    @patch('core.auth_client.requests.request')
    def test_login_invalid_credentials(self, mock_request):
        """Test login with invalid credentials"""
        from rest_framework.exceptions import AuthenticationFailed

        # Mock 401 response
        self.mock_response.status_code = 401
        mock_request.return_value = self.mock_response

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.login('test@example.com', 'wrongpassword')

        self.assertIn('Invalid email or password', str(context.exception))

    @patch('core.auth_client.requests.request')
    def test_signup_success(self, mock_request):
        """Test successful signup"""
        # Mock successful response
        self.mock_response.status_code = 201
        self.mock_response.json.return_value = {
            'userId': 'user-new-123',
            'email': 'newuser@example.com',
            'message': 'User created successfully'
        }
        mock_request.return_value = self.mock_response

        # Test
        user_data = {
            'email': 'newuser@example.com',
            'password': 'Password123!@#',
            'firstName': 'New',
            'lastName': 'User',
            'company': 'Test Company'
        }
        result = self.client.signup(user_data)

        # Verify
        self.assertIn('userId', result)
        self.assertEqual(result['email'], 'newuser@example.com')

    @patch('core.auth_client.requests.request')
    def test_signup_email_exists(self, mock_request):
        """Test signup with existing email"""
        from rest_framework.exceptions import AuthenticationFailed

        # Mock 409 response
        self.mock_response.status_code = 409
        mock_request.return_value = self.mock_response

        # Test
        user_data = {
            'email': 'existing@example.com',
            'password': 'Password123!',
            'firstName': 'Test',
            'lastName': 'User',
            'company': 'Test Co'
        }

        with self.assertRaises(AuthenticationFailed) as context:
            self.client.signup(user_data)

        self.assertIn('Email already exists', str(context.exception))

    @patch('core.auth_client.requests.request')
    def test_logout_success(self, mock_request):
        """Test successful logout"""
        # Mock successful response
        self.mock_response.status_code = 200
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.logout('refresh_token_123')

        # Verify
        self.assertTrue(result)

    @patch('core.auth_client.requests.request')
    def test_health_check_success(self, mock_request):
        """Test health check endpoint"""
        # Mock successful response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'status': 'healthy',
            'version': '1.0.0',
            'environment': 'production'
        }
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.health_check()

        # Verify
        self.assertEqual(result['status'], 'healthy')
        self.assertEqual(result['version'], '1.0.0')

    @patch('core.auth_client.requests.request')
    def test_health_check_unhealthy(self, mock_request):
        """Test health check with unhealthy server"""
        # Mock 503 response
        self.mock_response.status_code = 503
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.health_check()

        # Verify
        self.assertEqual(result['status'], 'unhealthy')
        self.assertEqual(result['statusCode'], 503)

    @patch('core.auth_client.requests.request')
    def test_password_reset_request(self, mock_request):
        """Test password reset request"""
        # Mock successful response
        self.mock_response.status_code = 200
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.request_password_reset('test@example.com')

        # Verify - always returns True for security
        self.assertTrue(result)

    @patch('core.auth_client.requests.request')
    def test_password_reset_success(self, mock_request):
        """Test password reset with valid token"""
        # Mock successful response
        self.mock_response.status_code = 200
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.reset_password('reset_token_123', 'NewPassword123!')

        # Verify
        self.assertTrue(result)

    @patch('core.auth_client.requests.request')
    def test_password_reset_invalid_token(self, mock_request):
        """Test password reset with invalid token"""
        from rest_framework.exceptions import AuthenticationFailed

        # Mock 400 response
        self.mock_response.status_code = 400
        mock_request.return_value = self.mock_response

        # Test
        with self.assertRaises(AuthenticationFailed) as context:
            self.client.reset_password('invalid_token', 'NewPassword123!')

        self.assertIn('Invalid or expired reset token', str(context.exception))

    def test_client_initialization(self):
        """Test client initializes with correct base URL"""
        client = AuthServerClient()
        # Should use default or environment variable
        self.assertIsNotNone(client.base_url)
        self.assertIn('http', client.base_url.lower())

    @patch('core.auth_client.requests.request')
    def test_verify_email_success(self, mock_request):
        """Test email verification"""
        # Mock successful response
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {
            'success': True,
            'message': 'Email verified successfully'
        }
        mock_request.return_value = self.mock_response

        # Test
        result = self.client.verify_email('test@example.com', '123456')

        # Verify
        self.assertTrue(result['success'])


def run_tests():
    """Run all tests and display results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAuthServerClient)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
