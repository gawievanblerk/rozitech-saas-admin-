"""
Auth Server Client
Handles communication with the Rozitech Auth Server for authentication operations
"""
import requests
import logging
from typing import Dict, Optional
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)


class AuthServerClient:
    """
    Client for interacting with the Rozitech Auth Server
    """

    def __init__(self):
        self.base_url = getattr(settings, 'AUTH_SERVICE_URL', 'http://localhost:4000')
        self.timeout = getattr(settings, 'AUTH_SERVICE_TIMEOUT', 5)
        logger.info(f"AuthServerClient initialized with base_url: {self.base_url}")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request to auth server with error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            AuthenticationFailed: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        try:
            response = requests.request(method, url, **kwargs)
            return response
        except requests.exceptions.Timeout:
            logger.error(f"Auth server timeout: {url}")
            raise AuthenticationFailed("Authentication service timeout")
        except requests.exceptions.ConnectionError:
            logger.error(f"Auth server connection error: {url}")
            raise AuthenticationFailed("Authentication service unavailable")
        except requests.exceptions.RequestException as e:
            logger.error(f"Auth server request error: {e}")
            raise AuthenticationFailed(f"Authentication service error: {str(e)}")

    def verify_token(self, access_token: str) -> Dict:
        """
        Verify JWT access token with auth server

        Args:
            access_token: JWT access token to verify

        Returns:
            Dict containing user information:
            {
                'user': {
                    'id': str,
                    'email': str,
                    'firstName': str,
                    'lastName': str,
                    ...
                },
                'organization': {...},
                'licenses': {...}
            }

        Raises:
            AuthenticationFailed: If token is invalid or verification fails
        """
        logger.debug(f"Verifying token with auth server: {access_token[:20]}...")

        response = self._make_request(
            'GET',
            '/api/auth/me',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if response.status_code == 200:
            data = response.json()
            # Handle wrapped response format {success, data}
            if 'data' in data and isinstance(data['data'], dict):
                user_email = data['data'].get('user', {}).get('email')
                logger.info(f"Token verified successfully for user: {user_email}")
                return data['data']
            user_email = data.get('user', {}).get('email')
            logger.info(f"Token verified successfully for user: {user_email}")
            return data
        elif response.status_code == 401:
            logger.warning("Token verification failed: Invalid or expired token")
            raise AuthenticationFailed("Invalid or expired token")
        elif response.status_code == 403:
            logger.warning("Token verification failed: Forbidden")
            raise AuthenticationFailed("Access forbidden")
        else:
            logger.error(f"Token verification failed with status {response.status_code}: {response.text}")
            raise AuthenticationFailed(f"Token verification failed: {response.status_code}")

    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: JWT refresh token

        Returns:
            Dict containing new tokens:
            {
                'accessToken': str,
                'refreshToken': str (optional, if rotated)
            }

        Raises:
            AuthenticationFailed: If refresh fails
        """
        logger.debug("Refreshing access token...")

        response = self._make_request(
            'POST',
            '/api/auth/refresh',
            json={'refreshToken': refresh_token},
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            logger.info("Token refreshed successfully")
            return data
        elif response.status_code == 401:
            logger.warning("Token refresh failed: Invalid refresh token")
            raise AuthenticationFailed("Invalid or expired refresh token")
        else:
            logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
            raise AuthenticationFailed(f"Token refresh failed: {response.status_code}")

    def login(self, email: str, password: str) -> Dict:
        """
        Login user with email and password

        Args:
            email: User email
            password: User password

        Returns:
            Dict containing tokens and user info:
            {
                'accessToken': str,
                'refreshToken': str,
                'user': {...},
                'organization': {...}
            }

        Raises:
            AuthenticationFailed: If login fails
        """
        logger.debug(f"Logging in user: {email}")

        response = self._make_request(
            'POST',
            '/api/auth/login',
            json={'email': email, 'password': password},
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"User logged in successfully: {email}")
            # Handle wrapped response format {success, data}
            if 'data' in data and isinstance(data['data'], dict):
                return data['data']
            return data
        elif response.status_code == 401:
            logger.warning(f"Login failed for user: {email}")
            raise AuthenticationFailed("Invalid email or password")
        elif response.status_code == 403:
            logger.warning(f"Login forbidden for user: {email}")
            raise AuthenticationFailed("Account not verified or inactive")
        else:
            logger.error(f"Login failed with status {response.status_code}: {response.text}")
            raise AuthenticationFailed(f"Login failed: {response.status_code}")

    def logout(self, refresh_token: str) -> bool:
        """
        Logout user by invalidating refresh token

        Args:
            refresh_token: JWT refresh token to invalidate

        Returns:
            bool: True if logout successful

        Raises:
            AuthenticationFailed: If logout fails
        """
        logger.debug("Logging out user...")

        response = self._make_request(
            'POST',
            '/api/auth/logout',
            json={'refreshToken': refresh_token},
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            logger.info("User logged out successfully")
            return True
        else:
            logger.warning(f"Logout returned status {response.status_code}")
            # Don't raise exception for logout failures
            return False

    def signup(self, user_data: Dict) -> Dict:
        """
        Register new user

        Args:
            user_data: Dict containing user registration data:
                {
                    'email': str,
                    'password': str,
                    'firstName': str,
                    'lastName': str,
                    'company': str,
                    'phone': str (optional),
                    'products': list (optional)
                }

        Returns:
            Dict containing user info and verification details

        Raises:
            AuthenticationFailed: If signup fails
        """
        logger.debug(f"Signing up user: {user_data.get('email')}")

        response = self._make_request(
            'POST',
            '/api/auth/signup',
            json=user_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 201:
            data = response.json()
            logger.info(f"User signed up successfully: {user_data.get('email')}")
            return data
        elif response.status_code == 400:
            error_data = response.json()
            logger.warning(f"Signup validation failed: {error_data}")
            raise AuthenticationFailed(error_data.get('message', 'Invalid signup data'))
        elif response.status_code == 409:
            logger.warning(f"Signup failed: Email already exists")
            raise AuthenticationFailed("Email already exists")
        else:
            logger.error(f"Signup failed with status {response.status_code}: {response.text}")
            raise AuthenticationFailed(f"Signup failed: {response.status_code}")

    def verify_email(self, email: str, verification_code: str) -> Dict:
        """
        Verify user email with verification code

        Args:
            email: User email
            verification_code: Email verification code

        Returns:
            Dict containing verification result

        Raises:
            AuthenticationFailed: If verification fails
        """
        logger.debug(f"Verifying email: {email}")

        response = self._make_request(
            'POST',
            '/api/auth/verify-email',
            json={'email': email, 'code': verification_code},
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Email verified successfully: {email}")
            return data
        elif response.status_code == 400:
            logger.warning(f"Email verification failed: Invalid or expired code")
            raise AuthenticationFailed("Invalid or expired verification code")
        else:
            logger.error(f"Email verification failed with status {response.status_code}")
            raise AuthenticationFailed(f"Email verification failed: {response.status_code}")

    def request_password_reset(self, email: str) -> bool:
        """
        Request password reset for user

        Args:
            email: User email

        Returns:
            bool: True if request successful (always returns true for security)
        """
        logger.debug(f"Requesting password reset for: {email}")

        response = self._make_request(
            'POST',
            '/api/auth/forgot-password',
            json={'email': email},
            headers={'Content-Type': 'application/json'}
        )

        # Always return true for security (don't reveal if email exists)
        logger.info(f"Password reset requested for: {email}")
        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token

        Args:
            token: Password reset token
            new_password: New password

        Returns:
            bool: True if reset successful

        Raises:
            AuthenticationFailed: If reset fails
        """
        logger.debug("Resetting password...")

        response = self._make_request(
            'POST',
            '/api/auth/reset-password',
            json={'token': token, 'password': new_password},
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            logger.info("Password reset successfully")
            return True
        elif response.status_code == 400:
            logger.warning("Password reset failed: Invalid or expired token")
            raise AuthenticationFailed("Invalid or expired reset token")
        else:
            logger.error(f"Password reset failed with status {response.status_code}")
            raise AuthenticationFailed(f"Password reset failed: {response.status_code}")

    def health_check(self) -> Dict:
        """
        Check auth server health status

        Returns:
            Dict containing health status
        """
        try:
            response = self._make_request('GET', '/health')
            if response.status_code == 200:
                return response.json()
            return {'status': 'unhealthy', 'statusCode': response.status_code}
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unreachable', 'error': str(e)}


# Singleton instance
_auth_client = None


def get_auth_client() -> AuthServerClient:
    """
    Get singleton instance of AuthServerClient

    Returns:
        AuthServerClient instance
    """
    global _auth_client
    if _auth_client is None:
        _auth_client = AuthServerClient()
    return _auth_client
