from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.tenants.models import Organization, Domain


class OrganizationModelTest(TestCase):
    """Test cases for Organization model"""

    def test_create_organization(self):
        """Test creating a basic organization"""
        org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )
        self.assertEqual(org.name, 'Test Organization')
        self.assertEqual(org.schema_name, 'test_org')
        self.assertTrue(org.is_active)

    def test_organization_str_representation(self):
        """Test string representation of organization"""
        org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )
        self.assertEqual(str(org), 'Test Organization')

    def test_organization_unique_schema_name(self):
        """Test that schema names must be unique"""
        Organization.objects.create(
            schema_name='unique_schema',
            name='Org 1'
        )

        with self.assertRaises(Exception):
            Organization.objects.create(
                schema_name='unique_schema',
                name='Org 2'
            )

    def test_organization_default_is_active(self):
        """Test that organizations are active by default"""
        org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )
        self.assertTrue(org.is_active)

    def test_organization_deactivation(self):
        """Test deactivating an organization"""
        org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )
        org.is_active = False
        org.save()

        org.refresh_from_db()
        self.assertFalse(org.is_active)

    def test_organization_with_subscription(self):
        """Test organization with subscription data"""
        org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization',
            subscription_tier='professional',
            max_users=50
        )
        self.assertEqual(org.subscription_tier, 'professional')
        self.assertEqual(org.max_users, 50)

    def test_organization_timestamps(self):
        """Test that created_at and updated_at are set"""
        org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )
        self.assertIsNotNone(org.created_at)
        self.assertIsNotNone(org.updated_at)

    def test_organization_filtering_active(self):
        """Test filtering active organizations"""
        Organization.objects.create(
            schema_name='active_org',
            name='Active Org',
            is_active=True
        )
        Organization.objects.create(
            schema_name='inactive_org',
            name='Inactive Org',
            is_active=False
        )

        active_orgs = Organization.objects.filter(is_active=True)
        self.assertEqual(active_orgs.count(), 1)


class DomainModelTest(TestCase):
    """Test cases for Domain model"""

    def setUp(self):
        """Set up test organization"""
        self.org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )

    def test_create_domain(self):
        """Test creating a basic domain"""
        domain = Domain.objects.create(
            domain='test.rozitech.com',
            tenant=self.org,
            is_primary=True
        )
        self.assertEqual(domain.domain, 'test.rozitech.com')
        self.assertEqual(domain.tenant, self.org)
        self.assertTrue(domain.is_primary)

    def test_domain_str_representation(self):
        """Test string representation of domain"""
        domain = Domain.objects.create(
            domain='test.rozitech.com',
            tenant=self.org
        )
        self.assertEqual(str(domain), 'test.rozitech.com')

    def test_domain_unique_constraint(self):
        """Test that domain names must be unique"""
        Domain.objects.create(
            domain='unique.rozitech.com',
            tenant=self.org
        )

        org2 = Organization.objects.create(
            schema_name='test_org_2',
            name='Test Organization 2'
        )

        with self.assertRaises(Exception):
            Domain.objects.create(
                domain='unique.rozitech.com',
                tenant=org2
            )

    def test_domain_default_is_primary(self):
        """Test that domains are not primary by default"""
        domain = Domain.objects.create(
            domain='test.rozitech.com',
            tenant=self.org
        )
        self.assertFalse(domain.is_primary)

    def test_domain_verification_status(self):
        """Test domain verification status"""
        domain = Domain.objects.create(
            domain='test.rozitech.com',
            tenant=self.org,
            is_verified=False
        )
        self.assertFalse(domain.is_verified)

        domain.is_verified = True
        domain.save()

        domain.refresh_from_db()
        self.assertTrue(domain.is_verified)

    def test_multiple_domains_per_organization(self):
        """Test that organizations can have multiple domains"""
        Domain.objects.create(
            domain='primary.rozitech.com',
            tenant=self.org,
            is_primary=True
        )
        Domain.objects.create(
            domain='secondary.rozitech.com',
            tenant=self.org,
            is_primary=False
        )

        domains = Domain.objects.filter(tenant=self.org)
        self.assertEqual(domains.count(), 2)

    def test_domain_timestamps(self):
        """Test that created_at is set"""
        domain = Domain.objects.create(
            domain='test.rozitech.com',
            tenant=self.org
        )
        self.assertIsNotNone(domain.created_at)

    def test_organization_property_backwards_compatibility(self):
        """Test that the organization property works for backwards compatibility"""
        domain = Domain.objects.create(
            domain='test.rozitech.com',
            tenant=self.org
        )
        self.assertEqual(domain.organization, self.org)

    def test_filter_primary_domains(self):
        """Test filtering primary domains"""
        Domain.objects.create(
            domain='primary.rozitech.com',
            tenant=self.org,
            is_primary=True
        )
        Domain.objects.create(
            domain='secondary.rozitech.com',
            tenant=self.org,
            is_primary=False
        )

        primary_domains = Domain.objects.filter(is_primary=True)
        self.assertEqual(primary_domains.count(), 1)
        self.assertEqual(primary_domains.first().domain, 'primary.rozitech.com')


class OrganizationBusinessLogicTest(TestCase):
    """Test business logic related to organizations"""

    def test_organization_user_count_limit(self):
        """Test that organization respects user count limits"""
        org = Organization.objects.create(
            schema_name='limited_org',
            name='Limited Organization',
            max_users=5
        )
        self.assertEqual(org.max_users, 5)

    def test_organization_trial_status(self):
        """Test organization trial status"""
        org = Organization.objects.create(
            schema_name='trial_org',
            name='Trial Organization',
            is_trial=True
        )
        self.assertTrue(org.is_trial)

    def test_organization_upgrade(self):
        """Test upgrading organization subscription"""
        org = Organization.objects.create(
            schema_name='upgrade_org',
            name='Upgrade Test',
            subscription_tier='basic',
            max_users=10
        )

        # Upgrade to professional
        org.subscription_tier = 'professional'
        org.max_users = 50
        org.save()

        org.refresh_from_db()
        self.assertEqual(org.subscription_tier, 'professional')
        self.assertEqual(org.max_users, 50)

    def test_organization_with_metadata(self):
        """Test storing additional metadata"""
        org = Organization.objects.create(
            schema_name='metadata_org',
            name='Metadata Test',
            settings={'feature_flags': {'ai_enabled': True}}
        )
        self.assertIn('feature_flags', org.settings)
        self.assertTrue(org.settings['feature_flags']['ai_enabled'])