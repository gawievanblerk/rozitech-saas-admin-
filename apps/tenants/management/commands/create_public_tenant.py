"""
Management command to create the public tenant for django-tenants
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.tenants.models import Organization, Domain


class Command(BaseCommand):
    help = 'Create the public tenant (required for django-tenants)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Creating public tenant for django-tenants...'))

        # Check if public tenant already exists
        if Organization.objects.filter(schema_name='public').exists():
            self.stdout.write(self.style.WARNING('Public tenant already exists!'))
            public_tenant = Organization.objects.get(schema_name='public')
            self.stdout.write(self.style.SUCCESS(f'Public tenant: {public_tenant.name}'))
            return

        # Create the public tenant
        try:
            public_tenant = Organization.objects.create(
                schema_name='public',
                name='Rozitech Public',
                slug='public',
                email='admin@rozitech.com',
                tier='enterprise',
                status='active',
                is_active=True,
                auto_create_schema=True,
                auto_drop_schema=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Created public tenant: {public_tenant.name}'))

            # Create a domain for the public tenant
            domain = Domain.objects.create(
                tenant=public_tenant,
                domain='localhost',
                is_primary=True,
                is_verified=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created public domain: {domain.domain}'))

            self.stdout.write(self.style.SUCCESS('✅ Public tenant setup complete!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to create public tenant: {str(e)}'))
            raise
