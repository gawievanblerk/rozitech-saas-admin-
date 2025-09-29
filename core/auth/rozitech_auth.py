"""
Rozitech Auth Server Integration for SaaS Admin Platform
"""
import requests
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ImproperlyConfigured
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status

logger = logging.getLogger(__name__)
User = get_user_model()


class RozitechAuthServerClient:
    """Client for communicating with Rozitech Auth Server"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'ROZITECH_AUTH_SERVER_URL', 'http://localhost:4000')
        self.api_key = getattr(settings, 'ROZITECH_AUTH_SERVER_API_KEY', None)
        self.timeout = getattr(settings, 'ROZITECH_AUTH_SERVER_TIMEOUT', 30)
        
        if not self.api_key:
            logger.warning("ROZITECH_AUTH_SERVER_API_KEY not configured")
    
    def verify_token(self, token):
        """Verify JWT token with auth server"""
        try:
            response = requests.get(
                f"{self.base_url}/api/auth/me",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'X-API-Key': self.api_key
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('data', {})
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Auth server request failed: {e}")
            return None
    
    def get_user_details(self, token):
        """Get full user details from auth server"""
        try:
            response = requests.get(
                f"{self.base_url}/api/auth/me",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'X-API-Key': self.api_key
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('data', {})
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Failed to get user details: {e}")
            return None
    
    def health_check(self):
        """Check if auth server is available"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False


class RozitechJWTAuthentication(BaseAuthentication):
    """
    DRF Authentication class that validates JWT tokens with Rozitech Auth Server
    """
    
    def __init__(self):
        self.auth_client = RozitechAuthServerClient()
    
    def authenticate(self, request):
        """
        Authenticate the request using JWT token from Rozitech Auth Server
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        # Verify token with auth server
        user_data = self.auth_client.verify_token(token)
        
        if not user_data:
            raise AuthenticationFailed('Invalid or expired token')
        
        # Get or create Django user
        user = self.get_or_create_user(user_data)
        
        return (user, token)
    
    def get_or_create_user(self, user_data):
        """
        Get or create Django user from auth server data
        """
        try:
            # Extract user info from auth server response
            user_info = user_data.get('user', {})
            email = user_info.get('email')
            user_id = user_info.get('sub') or user_info.get('id')
            
            if not email or not user_id:
                raise AuthenticationFailed('Invalid user data from auth server')
            
            # Try to get existing user by email
            try:
                user = User.objects.get(email=email)
                # Update user info if needed
                self.update_user_from_auth_data(user, user_info)
                return user
            except User.DoesNotExist:
                # Create new user
                return self.create_user_from_auth_data(user_info)
                
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            raise AuthenticationFailed('Failed to authenticate user')
    
    def create_user_from_auth_data(self, user_info):
        """Create new Django user from auth server data"""
        email = user_info.get('email')
        first_name = ''
        last_name = ''
        
        # Handle different response formats
        if 'firstName' in user_info:
            first_name = user_info.get('firstName', '')
            last_name = user_info.get('lastName', '')
        elif 'first_name' in user_info:
            first_name = user_info.get('first_name', '')
            last_name = user_info.get('last_name', '')
        
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        
        # Store auth server user ID in user profile or custom field
        # You might want to add a custom field for this
        logger.info(f"Created new user from auth server: {email}")
        
        return user
    
    def update_user_from_auth_data(self, user, user_info):
        """Update existing Django user with latest auth server data"""
        updated = False
        
        # Update names if available
        if 'firstName' in user_info and user.first_name != user_info['firstName']:
            user.first_name = user_info['firstName']
            updated = True
        
        if 'lastName' in user_info and user.last_name != user_info['lastName']:
            user.last_name = user_info['lastName']
            updated = True
        
        if updated:
            user.save()
            logger.info(f"Updated user info for: {user.email}")
        
        return user


class RozitechAuthBackend(BaseBackend):
    """
    Django authentication backend for Rozitech Auth Server
    """
    
    def __init__(self):
        self.auth_client = RozitechAuthServerClient()
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate against Rozitech Auth Server
        """
        if not username or not password:
            return None
        
        try:
            # Make login request to auth server
            response = requests.post(
                f"{self.auth_client.base_url}/api/auth/login",
                json={
                    'email': username,
                    'password': password
                },
                headers={
                    'Content-Type': 'application/json',
                    'X-API-Key': self.auth_client.api_key
                },
                timeout=self.auth_client.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    user_data = data.get('data', {}).get('user', {})
                    # Create or get Django user
                    auth = RozitechJWTAuthentication()
                    return auth.get_or_create_user({'user': user_data})
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Auth server login failed: {e}")
            return None
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# Utility functions for views and middleware
def get_user_organizations(token):
    """Get user's organizations from auth server"""
    client = RozitechAuthServerClient()
    user_data = client.get_user_details(token)
    
    if user_data and 'organizations' in user_data:
        return user_data['organizations']
    
    return []


def get_user_licenses(token):
    """Get user's product licenses from auth server"""
    client = RozitechAuthServerClient()
    user_data = client.get_user_details(token)
    
    if user_data and 'licenses' in user_data:
        return user_data['licenses']
    
    return {}


def is_auth_server_available():
    """Check if auth server is available"""
    client = RozitechAuthServerClient()
    return client.health_check()