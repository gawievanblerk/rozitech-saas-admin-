"""
Tests for TeamSpace SSO integration API endpoints
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.tenants.models import Organization, OrganizationUser
from apps.subscriptions.models import Subscription, PricingPlan
from datetime import datetime, timedelta
from django.utils import timezone


class TokenVerificationEndpointTests(TestCase):
    """Test suite for GET /api/auth/verify endpoint"""

    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            email='org@example.com'
        )

        # Create organization membership
        self.org_membership = OrganizationUser.objects.create(
            organization=self.organization,
            user=self.user,
            role='admin',
            is_active=True
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_verify_token_success(self):
        """Test successful token verification"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get('/api/auth/verify')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['user']['username'], 'testuser')
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertEqual(response.data['user']['role'], 'admin')

    def test_verify_token_unauthorized(self):
        """Test token verification without authentication"""
        response = self.client.get('/api/auth/verify')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/auth/verify')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrganizationDetailEndpointTests(TestCase):
    """Test suite for GET /api/organizations/{id} endpoint"""

    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            email='org@example.com'
        )

        # Create organization membership
        self.org_membership = OrganizationUser.objects.create(
            organization=self.organization,
            user=self.user,
            role='member',
            is_active=True
        )

        # Create pricing plan
        self.plan = PricingPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price=99.00,
            currency='ZAR'
        )

        # Create subscription
        self.subscription = Subscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status='active',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=30)
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_organization_success(self):
        """Test successful retrieval of organization details"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(f'/api/organizations/{self.organization.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['organization']['name'], 'Test Organization')
        self.assertIsNotNone(response.data['organization']['subscription'])

    def test_get_organization_no_access(self):
        """Test organization retrieval without access"""
        # Create another organization without membership
        other_org = Organization.objects.create(
            name='Other Organization',
            slug='other-org',
            email='other@example.com'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(f'/api/organizations/{other_org.id}/')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])

    def test_get_organization_not_found(self):
        """Test organization retrieval with non-existent but valid UUID"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        # Use a valid UUID format that doesn't exist in the database
        import uuid
        non_existent_uuid = uuid.uuid4()
        response = self.client.get(f'/api/organizations/{non_existent_uuid}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SubscriptionCheckEndpointTests(TestCase):
    """Test suite for GET /api/subscriptions/check endpoint"""

    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            slug='test-org',
            email='org@example.com',
            tier='professional',
            max_users=50,
            max_storage_gb=100
        )

        # Create organization membership
        self.org_membership = OrganizationUser.objects.create(
            organization=self.organization,
            user=self.user,
            role='member',
            is_active=True
        )

        # Create pricing plan
        self.plan = PricingPlan.objects.create(
            name='Professional Plan',
            slug='professional',
            price=299.00,
            currency='ZAR'
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_check_active_subscription(self):
        """Test subscription check with active subscription"""
        # Create active subscription
        subscription = Subscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status='active',
            product_code='teamspace',
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=30)
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(
            f'/api/subscriptions/check?organizationId={self.organization.id}&productCode=teamspace'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['hasActiveSubscription'])
        self.assertEqual(response.data['subscription']['status'], 'active')
        self.assertEqual(response.data['subscription']['productCode'], 'teamspace')

    def test_check_expired_subscription(self):
        """Test subscription check with expired subscription"""
        subscription = Subscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            status='expired',
            product_code='teamspace',
            current_period_start=timezone.now() - timedelta(days=60),
            current_period_end=timezone.now() - timedelta(days=30),
            next_billing_date=timezone.now() - timedelta(days=30)
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(
            f'/api/subscriptions/check?organizationId={self.organization.id}&productCode=teamspace'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(response.data['hasActiveSubscription'])
        self.assertEqual(response.data['subscription']['status'], 'expired')

    def test_check_no_subscription(self):
        """Test subscription check without any subscription"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(
            f'/api/subscriptions/check?organizationId={self.organization.id}&productCode=teamspace'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(response.data['hasActiveSubscription'])
        self.assertIn('message', response.data)

    def test_check_subscription_missing_params(self):
        """Test subscription check with missing parameters"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # Missing productCode
        response = self.client.get(
            f'/api/subscriptions/check?organizationId={self.organization.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing organizationId
        response = self.client.get('/api/subscriptions/check?productCode=teamspace')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_subscription_no_access(self):
        """Test subscription check without organization access"""
        # Create another organization without membership
        other_org = Organization.objects.create(
            name='Other Organization',
            slug='other-org',
            email='other@example.com'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(
            f'/api/subscriptions/check?organizationId={other_org.id}&productCode=teamspace'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
