from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.tenants.models import Organization

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""

    def setUp(self):
        """Set up test organization"""
        self.org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )

    def test_create_user(self):
        """Test creating a basic user"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.check_password('TestPass123!'))

    def test_create_superuser(self):
        """Test creating a superuser"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_active)

    def test_user_str_representation(self):
        """Test string representation of user"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.assertEqual(str(user), 'test@example.com')

    def test_user_email_unique(self):
        """Test that user emails must be unique"""
        User.objects.create_user(
            email='unique@example.com',
            password='TestPass123!'
        )

        with self.assertRaises(Exception):
            User.objects.create_user(
                email='unique@example.com',
                password='TestPass123!'
            )

    def test_user_email_normalization(self):
        """Test that email is normalized to lowercase"""
        user = User.objects.create_user(
            email='Test@Example.COM',
            password='TestPass123!'
        )
        self.assertEqual(user.email, 'test@example.com')

    def test_user_default_is_active(self):
        """Test that users are active by default"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.assertTrue(user.is_active)

    def test_user_deactivation(self):
        """Test deactivating a user"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        user.is_active = False
        user.save()

        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_user_full_name(self):
        """Test getting user's full name"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.get_full_name(), 'John Doe')

    def test_user_short_name(self):
        """Test getting user's short name"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user.get_short_name(), 'John')

    def test_user_timestamps(self):
        """Test that date_joined is set"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.assertIsNotNone(user.date_joined)

    def test_user_password_hashing(self):
        """Test that passwords are properly hashed"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        # Password should not be stored in plain text
        self.assertNotEqual(user.password, 'TestPass123!')
        # But should verify correctly
        self.assertTrue(user.check_password('TestPass123!'))

    def test_user_password_change(self):
        """Test changing user password"""
        user = User.objects.create_user(
            email='test@example.com',
            password='OldPass123!'
        )

        user.set_password('NewPass123!')
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPass123!'))
        self.assertFalse(user.check_password('OldPass123!'))


class UserBusinessLogicTest(TestCase):
    """Test business logic related to users"""

    def setUp(self):
        """Set up test organization"""
        self.org = Organization.objects.create(
            schema_name='test_org',
            name='Test Organization'
        )

    def test_user_email_verification(self):
        """Test user email verification status"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            is_verified=False
        )
        self.assertFalse(user.is_verified)

        user.is_verified = True
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_user_role_assignment(self):
        """Test assigning roles to users"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            role='admin'
        )
        self.assertEqual(user.role, 'admin')

    def test_user_without_password(self):
        """Test creating user without password (SSO)"""
        user = User.objects.create(
            email='sso@example.com',
            has_usable_password=False
        )
        self.assertFalse(user.has_usable_password())

    def test_filter_active_users(self):
        """Test filtering active users"""
        User.objects.create_user(
            email='active@example.com',
            password='Pass123!',
            is_active=True
        )
        User.objects.create_user(
            email='inactive@example.com',
            password='Pass123!',
            is_active=False
        )

        active_users = User.objects.filter(is_active=True)
        self.assertEqual(active_users.count(), 1)

    def test_filter_verified_users(self):
        """Test filtering verified users"""
        User.objects.create_user(
            email='verified@example.com',
            password='Pass123!',
            is_verified=True
        )
        User.objects.create_user(
            email='unverified@example.com',
            password='Pass123!',
            is_verified=False
        )

        verified_users = User.objects.filter(is_verified=True)
        self.assertEqual(verified_users.count(), 1)

    def test_user_last_login_tracking(self):
        """Test tracking user last login"""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        # Initially last_login should be None
        self.assertIsNone(user.last_login)

    def test_staff_permissions(self):
        """Test staff user permissions"""
        user = User.objects.create_user(
            email='staff@example.com',
            password='Pass123!',
            is_staff=True
        )
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_superuser_permissions(self):
        """Test superuser has all permissions"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_user_search_by_email(self):
        """Test searching users by email"""
        User.objects.create_user(
            email='john@example.com',
            password='Pass123!'
        )
        User.objects.create_user(
            email='jane@example.com',
            password='Pass123!'
        )

        john = User.objects.filter(email__icontains='john')
        self.assertEqual(john.count(), 1)
        self.assertEqual(john.first().email, 'john@example.com')

    def test_user_search_by_name(self):
        """Test searching users by name"""
        User.objects.create_user(
            email='user1@example.com',
            password='Pass123!',
            first_name='Alice',
            last_name='Smith'
        )
        User.objects.create_user(
            email='user2@example.com',
            password='Pass123!',
            first_name='Bob',
            last_name='Johnson'
        )

        alice = User.objects.filter(first_name='Alice')
        self.assertEqual(alice.count(), 1)
        self.assertEqual(alice.first().last_name, 'Smith')