#!/usr/bin/env python
"""
Create demo data for the SaaS admin platform
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.full_platform')
django.setup()

from django.contrib.auth.models import User
from apps.tenants.models import Organization, OrganizationUser, Domain
from apps.subscriptions.models import PricingPlan, Subscription, Invoice

def create_demo_data():
    print("🎯 Creating demo data for Rozitech SaaS Admin Platform...")
    
    # Create pricing plans
    print("💰 Creating pricing plans...")
    
    free_plan = PricingPlan.objects.create(
        name="Free Tier",
        slug="free",
        description="Perfect for getting started with basic features",
        price=Decimal('0.00'),
        currency='ZAR',
        billing_interval='monthly',
        plan_type='standard',
        trial_period_days=0,
        max_users=5,
        max_storage_gb=1,
        max_api_calls_per_month=1000,
        max_projects=1,
        features=['basic_support', 'community_access'],
        is_active=True,
        is_public=True
    )
    
    starter_plan = PricingPlan.objects.create(
        name="Starter Plan",
        slug="starter",
        description="Great for small teams and growing businesses",
        price=Decimal('299.00'),
        currency='ZAR',
        billing_interval='monthly',
        plan_type='standard',
        trial_period_days=14,
        max_users=25,
        max_storage_gb=10,
        max_api_calls_per_month=10000,
        max_projects=5,
        features=['email_support', 'basic_analytics', 'api_access'],
        is_active=True,
        is_public=True
    )
    
    professional_plan = PricingPlan.objects.create(
        name="Professional Plan",
        slug="professional",
        description="For established businesses requiring advanced features",
        price=Decimal('899.00'),
        currency='ZAR',
        billing_interval='monthly',
        plan_type='standard',
        trial_period_days=30,
        max_users=100,
        max_storage_gb=50,
        max_api_calls_per_month=100000,
        max_projects=25,
        features=['priority_support', 'advanced_analytics', 'custom_integrations', 'webhook_support'],
        is_active=True,
        is_public=True
    )
    
    enterprise_plan = PricingPlan.objects.create(
        name="Enterprise Plan",
        slug="enterprise",
        description="Unlimited power for large organizations",
        price=Decimal('2499.00'),
        currency='ZAR',
        billing_interval='monthly',
        plan_type='enterprise',
        trial_period_days=30,
        max_users=1000,
        max_storage_gb=500,
        max_api_calls_per_month=1000000,
        max_projects=100,
        features=['dedicated_support', 'custom_features', 'sla_guarantee', 'on_premise_deployment'],
        is_active=True,
        is_public=True
    )
    
    print(f"✅ Created {PricingPlan.objects.count()} pricing plans")
    
    # Create demo organizations
    print("🏢 Creating demo organizations...")
    
    # Rozitech (our own company)
    rozitech = Organization.objects.create(
        name="Rozitech (Pty) Ltd",
        slug="rozitech",
        email="admin@rozitech.co.za",
        phone="+27 11 123 4567",
        website="https://rozitech.co.za",
        address_line1="123 Innovation Drive",
        city="Johannesburg",
        country="ZA",
        company_registration="2023/123456/07",
        industry="Technology",
        tier="enterprise",
        status="active",
        is_active=True,
        max_users=1000,
        max_storage_gb=500,
        max_api_calls_per_month=1000000,
        notes="Parent company - unlimited access to all features"
    )
    
    # Demo customer organizations
    ace_insurance = Organization.objects.create(
        name="Ace Insurance Brokers",
        slug="ace-insurance",
        email="admin@aceinsurance.co.za",
        phone="+27 21 555 0123",
        website="https://aceinsurance.co.za",
        address_line1="456 Financial District",
        city="Cape Town",
        country="ZA",
        company_registration="2020/654321/07",
        industry="Insurance",
        tier="professional",
        status="active",
        is_active=True,
        max_users=100,
        max_storage_gb=50,
        max_api_calls_per_month=100000,
        trial_end_date=timezone.now() - timedelta(days=15),  # Trial ended, now paying
        notes="Professional insurance brokerage using our funeral insurance platform"
    )
    
    startup_corp = Organization.objects.create(
        name="StartupCorp",
        slug="startup-corp",
        email="founder@startupcorp.co.za",
        phone="+27 11 987 6543",
        address_line1="789 Startup Hub",
        city="Pretoria",
        country="ZA",
        industry="Technology",
        tier="starter",
        status="trial",
        is_active=True,
        max_users=25,
        max_storage_gb=10,
        max_api_calls_per_month=10000,
        trial_end_date=timezone.now() + timedelta(days=10),  # Trial ending soon
        notes="Growing startup in trial period"
    )
    
    community_org = Organization.objects.create(
        name="Community Funeral Scheme",
        slug="community-funeral",
        email="coordinator@communityfuneral.org.za",
        phone="+27 31 444 5678",
        address_line1="321 Community Center",
        city="Durban",
        country="ZA",
        industry="Non-Profit",
        tier="free",
        status="active",
        is_active=True,
        max_users=5,
        max_storage_gb=1,
        max_api_calls_per_month=1000,
        notes="Community organization using free tier"
    )
    
    print(f"✅ Created {Organization.objects.count()} organizations")
    
    # Create domains
    print("🌐 Creating domains...")
    
    Domain.objects.create(organization=rozitech, domain="admin.rozitech.co.za", is_primary=True, is_verified=True)
    Domain.objects.create(organization=ace_insurance, domain="portal.aceinsurance.co.za", is_primary=True, is_verified=True)
    Domain.objects.create(organization=startup_corp, domain="app.startupcorp.co.za", is_primary=True, is_verified=False)
    
    print(f"✅ Created {Domain.objects.count()} domains")
    
    # Create demo users and organization relationships
    print("👥 Creating users and organization memberships...")
    
    # Get the existing admin user
    admin_user = User.objects.get(username='admin')
    
    # Create additional users
    john = User.objects.create_user(
        username='john.doe',
        email='john.doe@aceinsurance.co.za',
        first_name='John',
        last_name='Doe',
        password='demo123'
    )
    
    sarah = User.objects.create_user(
        username='sarah.founder',
        email='sarah@startupcorp.co.za',
        first_name='Sarah',
        last_name='Johnson',
        password='demo123'
    )
    
    community_admin = User.objects.create_user(
        username='community.admin',
        email='admin@communityfuneral.org.za',
        first_name='Community',
        last_name='Administrator',
        password='demo123'
    )
    
    # Create organization user relationships
    OrganizationUser.objects.create(organization=rozitech, user=admin_user, role='owner', is_active=True)
    OrganizationUser.objects.create(organization=ace_insurance, user=john, role='admin', is_active=True)
    OrganizationUser.objects.create(organization=startup_corp, user=sarah, role='owner', is_active=True)
    OrganizationUser.objects.create(organization=community_org, user=community_admin, role='admin', is_active=True)
    
    print(f"✅ Created {OrganizationUser.objects.count()} organization memberships")
    
    # Create subscriptions
    print("💳 Creating subscriptions...")
    
    # Rozitech enterprise subscription
    rozitech_sub = Subscription.objects.create(
        organization=rozitech,
        plan=enterprise_plan,
        status='active',
        started_at=timezone.now() - timedelta(days=90),
        current_period_start=timezone.now() - timedelta(days=5),
        current_period_end=timezone.now() + timedelta(days=25),
        next_billing_date=timezone.now() + timedelta(days=25),
        auto_renew=True,
        current_usage={
            'users': 15,
            'storage_gb': 45.6,
            'api_calls_this_month': 45670
        }
    )
    
    # Ace Insurance professional subscription
    ace_sub = Subscription.objects.create(
        organization=ace_insurance,
        plan=professional_plan,
        status='active',
        started_at=timezone.now() - timedelta(days=45),
        trial_end_date=timezone.now() - timedelta(days=15),
        current_period_start=timezone.now() - timedelta(days=15),
        current_period_end=timezone.now() + timedelta(days=15),
        next_billing_date=timezone.now() + timedelta(days=15),
        auto_renew=True,
        current_usage={
            'users': 12,
            'storage_gb': 28.3,
            'api_calls_this_month': 23450
        }
    )
    
    # StartupCorp trial subscription
    startup_sub = Subscription.objects.create(
        organization=startup_corp,
        plan=starter_plan,
        status='trial',
        started_at=timezone.now() - timedelta(days=4),
        trial_end_date=timezone.now() + timedelta(days=10),
        current_period_start=timezone.now() - timedelta(days=4),
        current_period_end=timezone.now() + timedelta(days=10),
        next_billing_date=timezone.now() + timedelta(days=10),
        auto_renew=True,
        current_usage={
            'users': 3,
            'storage_gb': 1.2,
            'api_calls_this_month': 567
        }
    )
    
    # Community free subscription
    community_sub = Subscription.objects.create(
        organization=community_org,
        plan=free_plan,
        status='active',
        started_at=timezone.now() - timedelta(days=120),
        current_period_start=timezone.now() - timedelta(days=20),
        current_period_end=timezone.now() + timedelta(days=10),
        next_billing_date=timezone.now() + timedelta(days=10),
        auto_renew=True,
        current_usage={
            'users': 2,
            'storage_gb': 0.4,
            'api_calls_this_month': 156
        }
    )
    
    print(f"✅ Created {Subscription.objects.count()} subscriptions")
    
    # Create some invoices
    print("🧾 Creating invoices...")
    
    # Rozitech invoice (paid)
    Invoice.objects.create(
        invoice_number="INV-2024-001",
        subscription=rozitech_sub,
        organization=rozitech,
        status='paid',
        subtotal=Decimal('2499.00'),
        tax_amount=Decimal('374.85'),  # 15% VAT
        total_amount=Decimal('2873.85'),
        currency='ZAR',
        period_start=timezone.now() - timedelta(days=35),
        period_end=timezone.now() - timedelta(days=5),
        due_date=timezone.now() - timedelta(days=20),
        paid_at=timezone.now() - timedelta(days=18),
        payment_method='credit_card',
        line_items=[
            {
                'description': 'Enterprise Plan - Monthly',
                'quantity': 1,
                'unit_price': '2499.00',
                'total': '2499.00'
            }
        ]
    )
    
    # Ace Insurance invoice (paid)
    Invoice.objects.create(
        invoice_number="INV-2024-002",
        subscription=ace_sub,
        organization=ace_insurance,
        status='paid',
        subtotal=Decimal('899.00'),
        tax_amount=Decimal('134.85'),  # 15% VAT
        total_amount=Decimal('1033.85'),
        currency='ZAR',
        period_start=timezone.now() - timedelta(days=45),
        period_end=timezone.now() - timedelta(days=15),
        due_date=timezone.now() - timedelta(days=10),
        paid_at=timezone.now() - timedelta(days=8),
        payment_method='eft',
        line_items=[
            {
                'description': 'Professional Plan - Monthly',
                'quantity': 1,
                'unit_price': '899.00',
                'total': '899.00'
            }
        ]
    )
    
    # Upcoming invoice for Ace Insurance
    Invoice.objects.create(
        invoice_number="INV-2024-003",
        subscription=ace_sub,
        organization=ace_insurance,
        status='pending',
        subtotal=Decimal('899.00'),
        tax_amount=Decimal('134.85'),
        total_amount=Decimal('1033.85'),
        currency='ZAR',
        period_start=timezone.now() - timedelta(days=15),
        period_end=timezone.now() + timedelta(days=15),
        due_date=timezone.now() + timedelta(days=15),
        line_items=[
            {
                'description': 'Professional Plan - Monthly',
                'quantity': 1,
                'unit_price': '899.00',
                'total': '899.00'
            }
        ]
    )
    
    print(f"✅ Created {Invoice.objects.count()} invoices")
    
    print("\n" + "="*60)
    print("🎉 DEMO DATA CREATION COMPLETE!")
    print("="*60)
    print(f"📊 Summary:")
    print(f"   • {PricingPlan.objects.count()} Pricing Plans")
    print(f"   • {Organization.objects.count()} Organizations")
    print(f"   • {Domain.objects.count()} Domains")
    print(f"   • {User.objects.count()} Users")
    print(f"   • {OrganizationUser.objects.count()} Organization Memberships")
    print(f"   • {Subscription.objects.count()} Subscriptions")
    print(f"   • {Invoice.objects.count()} Invoices")
    print("\n🌐 Access your platform at: http://localhost:8003/admin/")
    print("🔐 Login: admin / admin123")
    print()

if __name__ == "__main__":
    create_demo_data()