"""
Custom Authentication Backend
Authenticates users by verifying JWT tokens with the remote Rozitech Auth Server
"""
import logging
from typing import Optional, Tuple
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from core.auth_client import get_auth_client

logger = logging.getLogger(__name__)
User = get_user_model()


class RemoteJWTAuthentication(BaseAuthentication):
    """
    Authenticate requests by verifying JWT token with remote auth server

    This authentication class:
    1. Extracts JWT token from Authorization header
    2. Verifies token with remote auth server
    3. Creates or updates local user record
    4. Caches verification results for performance
    """

    keyword = 'Bearer'
    cache_ttl = 60  # Cache token verification for 1 minute

    def authenticate(self, request: Request) -> Optional[Tuple[User, str]]:
        """
        Authenticate the request and return a two-tuple of (user, token)

        Args:
            request: The DRF request object

        Returns:
            Tuple of (User, token) if authentication successful, None otherwise

        Raises:
            AuthenticationFailed: If authentication fails
        """
        auth_header = self.get_authorization_header(request)

        if not auth_header:
            return None

        token = self.extract_token(auth_header)

        if not token:
            return None

        # Check cache first for performance
        user_data = self.get_cached_user_data(token)

        if not user_data:
            # Verify token with auth server
            user_data = self.verify_token_with_auth_server(token)
            self.cache_user_data(token, user_data)

        # Get or create local user
        user = self.get_or_create_user(user_data)

        return (user, token)

    def get_authorization_header(self, request: Request) -> Optional[str]:
        """
        Extract Authorization header from request

        Args:
            request: The DRF request object

        Returns:
            Authorization header value or None
        """
        auth_header = request.headers.get('Authorization', '')
        return auth_header if auth_header else None

    def extract_token(self, auth_header: str) -> Optional[str]:
        """
        Extract JWT token from Authorization header

        Args:
            auth_header: Authorization header value (e.g., "Bearer <token>")

        Returns:
            JWT token string or None

        Raises:
            AuthenticationFailed: If header format is invalid
        """
        parts = auth_header.split()

        if len(parts) == 0:
            return None

        if parts[0].lower() != self.keyword.lower():
            return None

        if len(parts) == 1:
            raise AuthenticationFailed('Invalid Authorization header: No token provided')

        if len(parts) > 2:
            raise AuthenticationFailed('Invalid Authorization header: Token contains spaces')

        return parts[1]

    def get_cached_user_data(self, token: str) -> Optional[dict]:
        """
        Get cached user data for token

        Args:
            token: JWT token

        Returns:
            Cached user data dict or None
        """
        cache_key = self.get_cache_key(token)
        user_data = cache.get(cache_key)

        if user_data:
            logger.debug(f"Cache hit for token: {token[:20]}...")
            return user_data

        return None

    def cache_user_data(self, token: str, user_data: dict) -> None:
        """
        Cache user data for token

        Args:
            token: JWT token
            user_data: User data to cache
        """
        cache_key = self.get_cache_key(token)
        cache.set(cache_key, user_data, self.cache_ttl)
        logger.debug(f"Cached user data for token: {token[:20]}...")

    def get_cache_key(self, token: str) -> str:
        """
        Generate cache key for token

        Args:
            token: JWT token

        Returns:
            Cache key string
        """
        # Use first 40 chars of token for cache key (avoid storing full token)
        token_prefix = token[:40] if len(token) > 40 else token
        return f"auth_token_{token_prefix}"

    def verify_token_with_auth_server(self, token: str) -> dict:
        """
        Verify token with remote auth server

        Args:
            token: JWT token to verify

        Returns:
            User data dict from auth server

        Raises:
            AuthenticationFailed: If verification fails
        """
        try:
            auth_client = get_auth_client()
            user_data = auth_client.verify_token(token)

            logger.info(f"Token verified successfully for user: {user_data.get('user', {}).get('email')}")
            return user_data

        except AuthenticationFailed:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise AuthenticationFailed(f"Authentication error: {str(e)}")

    def get_or_create_user(self, user_data: dict) -> User:
        """
        Get or create local user from auth server data

        Args:
            user_data: User data from auth server

        Returns:
            Django User instance

        Raises:
            AuthenticationFailed: If user creation/retrieval fails
        """
        try:
            user_info = user_data.get('user', {})

            if not user_info:
                raise AuthenticationFailed("Invalid user data from auth server")

            email = user_info.get('email')

            if not email:
                raise AuthenticationFailed("No email in user data")

            # Get or create user
            user, created = User.objects.get_or_create(
                email=email.lower(),
                defaults={
                    'username': email.lower(),
                    'first_name': user_info.get('firstName', ''),
                    'last_name': user_info.get('lastName', ''),
                    'is_active': True,
                }
            )

            # Update user info if changed
            if not created:
                updated = False

                if user.first_name != user_info.get('firstName', ''):
                    user.first_name = user_info.get('firstName', '')
                    updated = True

                if user.last_name != user_info.get('lastName', ''):
                    user.last_name = user_info.get('lastName', '')
                    updated = True

                if updated:
                    user.save()
                    logger.debug(f"Updated user info for: {email}")

            if created:
                logger.info(f"Created new local user: {email}")

            return user

        except Exception as e:
            logger.error(f"Error creating/retrieving user: {e}")
            raise AuthenticationFailed(f"User creation error: {str(e)}")

    def authenticate_header(self, request: Request) -> str:
        """
        Return string to use as WWW-Authenticate header in 401 response

        Args:
            request: The DRF request object

        Returns:
            WWW-Authenticate header value
        """
        return self.keyword


class OptionalRemoteJWTAuthentication(RemoteJWTAuthentication):
    """
    Optional authentication - allows unauthenticated requests
    Use this for endpoints that should work for both authenticated and anonymous users
    """

    def authenticate(self, request: Request) -> Optional[Tuple[User, str]]:
        """
        Authenticate if token present, otherwise return None (allow anonymous)

        Args:
            request: The DRF request object

        Returns:
            Tuple of (User, token) if authenticated, None if no token present
        """
        try:
            return super().authenticate(request)
        except AuthenticationFailed:
            # Return None to allow anonymous access
            return None


class CachedRemoteJWTAuthentication(RemoteJWTAuthentication):
    """
    Aggressive caching version of RemoteJWTAuthentication
    Caches for 5 minutes instead of 1 minute
    Use for high-traffic endpoints where eventual consistency is acceptable
    """
    cache_ttl = 300  # 5 minutes
