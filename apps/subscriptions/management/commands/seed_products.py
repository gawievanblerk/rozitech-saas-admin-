"""
Management command to seed initial products and pricing plans
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from apps.subscriptions.models import PricingPlan
from apps.products.models import Product, ProductPlan, SubscriptionBundle, BundleProduct


class Command(BaseCommand):
    help = 'Seeds initial products (AutoFlow AI, BuildEasy, TeamSpace) with pricing plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing products...'))
            Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Products cleared'))

        with transaction.atomic():
            # Create base pricing plans first
            self.stdout.write('Creating base pricing plans...')
            base_plans = self.create_base_plans()

            # Create products
            self.stdout.write('Creating products...')
            products = self.create_products()

            # Create product plans
            self.stdout.write('Creating product plans...')
            product_plans = self.create_product_plans(products, base_plans)

            # Create bundles
            self.stdout.write('Creating subscription bundles...')
            bundles = self.create_bundles(product_plans)

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully seeded:'))
        self.stdout.write(f'  - {len(products)} products')
        self.stdout.write(f'  - {len(product_plans)} product plans')
        self.stdout.write(f'  - {len(bundles)} subscription bundles')

    def create_base_plans(self):
        """Create base pricing plan tiers"""
        plans = {
            'starter': PricingPlan.objects.get_or_create(
                slug='starter',
                defaults={
                    'name': 'Starter',
                    'price': Decimal('24.00'),
                    'currency': 'USD',
                    'billing_interval': 'monthly',
                    'plan_type': 'standard',
                    'max_users': 5,
                    'max_storage_gb': 10,
                    'max_api_calls_per_month': 10000,
                    'max_projects': 3,
                    'trial_period_days': 14,
                    'is_active': True,
                    'is_public': True,
                    'features': ['Basic support', 'Email notifications'],
                    'feature_limits': {}
                }
            )[0],
            'professional': PricingPlan.objects.get_or_create(
                slug='professional',
                defaults={
                    'name': 'Professional',
                    'price': Decimal('49.00'),
                    'currency': 'USD',
                    'billing_interval': 'monthly',
                    'plan_type': 'standard',
                    'max_users': 25,
                    'max_storage_gb': 100,
                    'max_api_calls_per_month': 100000,
                    'max_projects': 25,
                    'trial_period_days': 14,
                    'is_active': True,
                    'is_public': True,
                    'features': ['Priority support', 'Email notifications', 'API access'],
                    'feature_limits': {}
                }
            )[0],
            'enterprise': PricingPlan.objects.get_or_create(
                slug='enterprise',
                defaults={
                    'name': 'Enterprise',
                    'price': Decimal('99.00'),
                    'currency': 'USD',
                    'billing_interval': 'monthly',
                    'plan_type': 'standard',
                    'max_users': 0,  # Unlimited
                    'max_storage_gb': 0,  # Unlimited
                    'max_api_calls_per_month': 0,  # Unlimited
                    'max_projects': 0,  # Unlimited
                    'trial_period_days': 14,
                    'is_active': True,
                    'is_public': True,
                    'features': ['24/7 support', 'Email notifications', 'API access', 'Custom integrations'],
                    'feature_limits': {}
                }
            )[0],
        }

        self.stdout.write(f'  ✓ Created {len(plans)} base pricing plans')
        return plans

    def create_products(self):
        """Create the three main products"""
        products = {}

        # AutoFlow AI
        products['autoflow'], created = Product.objects.get_or_create(
            code='autoflow',
            defaults={
                'name': 'AutoFlow AI',
                'slug': 'autoflow-ai',
                'tagline': 'Intelligent Workflow Automation',
                'description': 'Automate your business workflows with AI-powered task orchestration, smart routing, and predictive analytics.',
                'billing_type': 'hybrid',
                'status': 'active',
                'icon': '🤖',
                'color': '#4F46E5',
                'features': [
                    'AI-powered task automation',
                    'Visual workflow builder',
                    'Smart routing & escalation',
                    'Predictive analytics',
                    'Integration hub (1000+ apps)',
                    'Real-time monitoring'
                ],
                'metadata': {
                    'category': 'automation',
                    'target_audience': 'operations_teams'
                },
                'is_active': True,
                'is_public': True,
                'requires_approval': False,
                'sort_order': 1
            }
        )

        # BuildEasy
        products['buildeasy'], created = Product.objects.get_or_create(
            code='buildeasy',
            defaults={
                'name': 'BuildEasy',
                'slug': 'buildeasy',
                'tagline': 'No-Code Application Builder',
                'description': 'Build professional web and mobile applications without writing code. Drag-and-drop interface with powerful backend.',
                'billing_type': 'per_user',
                'status': 'active',
                'icon': '🏗️',
                'color': '#10B981',
                'features': [
                    'Drag-and-drop app builder',
                    'Pre-built templates',
                    'Custom database design',
                    'API generation',
                    'User authentication',
                    'Mobile responsive',
                    'White-label deployment'
                ],
                'metadata': {
                    'category': 'development',
                    'target_audience': 'business_users'
                },
                'is_active': True,
                'is_public': True,
                'requires_approval': False,
                'sort_order': 2
            }
        )

        # TeamSpace
        products['teamspace'], created = Product.objects.get_or_create(
            code='teamspace',
            defaults={
                'name': 'TeamSpace',
                'slug': 'teamspace',
                'tagline': 'Unified Team Collaboration',
                'description': 'All-in-one workspace for teams. Chat, video calls, file sharing, task management, and knowledge base.',
                'billing_type': 'per_user',
                'status': 'active',
                'icon': '👥',
                'color': '#F59E0B',
                'features': [
                    'Team chat & channels',
                    'Video conferencing',
                    'File sharing & storage',
                    'Task & project management',
                    'Knowledge base wiki',
                    'Calendar & scheduling',
                    'Guest access'
                ],
                'metadata': {
                    'category': 'collaboration',
                    'target_audience': 'all_teams'
                },
                'is_active': True,
                'is_public': True,
                'requires_approval': False,
                'sort_order': 3
            }
        )

        self.stdout.write(f'  ✓ Created {len(products)} products')
        return products

    def create_product_plans(self, products, base_plans):
        """Link products to pricing plans with product-specific config"""
        product_plans = {}

        # AutoFlow AI Plans
        product_plans['autoflow_starter'] = ProductPlan.objects.get_or_create(
            product=products['autoflow'],
            base_plan=base_plans['starter'],
            defaults={
                'product_limits': {
                    'tasks_per_month': 5000,
                    'workflows': 10,
                    'integrations': 5
                },
                'product_features': ['Basic workflows', 'Email support'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        product_plans['autoflow_professional'] = ProductPlan.objects.get_or_create(
            product=products['autoflow'],
            base_plan=base_plans['professional'],
            defaults={
                'product_limits': {
                    'tasks_per_month': 25000,
                    'workflows': 100,
                    'integrations': 50
                },
                'product_features': ['Advanced workflows', 'AI routing', 'Priority support'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        product_plans['autoflow_enterprise'] = ProductPlan.objects.get_or_create(
            product=products['autoflow'],
            base_plan=base_plans['enterprise'],
            defaults={
                'product_limits': {
                    'tasks_per_month': 0,  # Unlimited
                    'workflows': 0,
                    'integrations': 0
                },
                'product_features': ['Custom workflows', 'AI routing', 'Dedicated support', 'SLA'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        # BuildEasy Plans
        product_plans['buildeasy_starter'] = ProductPlan.objects.get_or_create(
            product=products['buildeasy'],
            base_plan=base_plans['starter'],
            defaults={
                'product_limits': {
                    'apps': 3,
                    'database_records': 10000,
                    'api_calls_per_day': 1000
                },
                'product_features': ['Basic templates', 'Standard database'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        product_plans['buildeasy_professional'] = ProductPlan.objects.get_or_create(
            product=products['buildeasy'],
            base_plan=base_plans['professional'],
            defaults={
                'product_limits': {
                    'apps': 25,
                    'database_records': 100000,
                    'api_calls_per_day': 10000
                },
                'product_features': ['Premium templates', 'Advanced database', 'Custom APIs'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        product_plans['buildeasy_enterprise'] = ProductPlan.objects.get_or_create(
            product=products['buildeasy'],
            base_plan=base_plans['enterprise'],
            defaults={
                'product_limits': {
                    'apps': 0,  # Unlimited
                    'database_records': 0,
                    'api_calls_per_day': 0
                },
                'product_features': ['All templates', 'Enterprise database', 'Custom APIs', 'White-label'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        # TeamSpace Plans
        product_plans['teamspace_starter'] = ProductPlan.objects.get_or_create(
            product=products['teamspace'],
            base_plan=base_plans['starter'],
            defaults={
                'product_limits': {
                    'storage_gb': 50,
                    'video_hours_per_month': 10,
                    'guests': 5
                },
                'product_features': ['Team chat', 'Basic video', 'File sharing'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        product_plans['teamspace_professional'] = ProductPlan.objects.get_or_create(
            product=products['teamspace'],
            base_plan=base_plans['professional'],
            defaults={
                'product_limits': {
                    'storage_gb': 500,
                    'video_hours_per_month': 100,
                    'guests': 50
                },
                'product_features': ['Team chat', 'HD video', 'Advanced file sharing', 'Wiki'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        product_plans['teamspace_enterprise'] = ProductPlan.objects.get_or_create(
            product=products['teamspace'],
            base_plan=base_plans['enterprise'],
            defaults={
                'product_limits': {
                    'storage_gb': 0,  # Unlimited
                    'video_hours_per_month': 0,
                    'guests': 0
                },
                'product_features': ['Team chat', '4K video', 'Unlimited storage', 'Advanced wiki', 'SSO'],
                'is_available_standalone': True,
                'is_available_in_bundle': True,
                'is_active': True
            }
        )[0]

        self.stdout.write(f'  ✓ Created {len(product_plans)} product plans')
        return product_plans

    def create_bundles(self, product_plans):
        """Create pre-defined subscription bundles"""
        bundles = {}

        # Starter Bundle (AutoFlow + TeamSpace)
        bundles['starter'], created = SubscriptionBundle.objects.get_or_create(
            code='starter_bundle',
            defaults={
                'name': 'Starter Bundle',
                'slug': 'starter-bundle',
                'tagline': 'Perfect for small teams getting started',
                'description': 'Automate workflows and collaborate seamlessly with AutoFlow AI and TeamSpace.',
                'base_price': Decimal('54.00'),  # Regular would be $24 + $24 = $48, bundle is $54 (includes more users)
                'currency': 'USD',
                'billing_interval': 'monthly',
                'discount_type': 'percentage',
                'discount_value': Decimal('10.00'),
                'included_users': 5,
                'features': [
                    'AutoFlow AI Starter',
                    'TeamSpace Starter',
                    '5 users included',
                    '14-day free trial'
                ],
                'metadata': {'recommended_for': 'small_teams'},
                'is_active': True,
                'is_public': True,
                'is_featured': True,
                'sort_order': 1
            }
        )

        if created:
            BundleProduct.objects.create(
                bundle=bundles['starter'],
                product=product_plans['autoflow_starter'].product,
                product_plan=product_plans['autoflow_starter'],
                is_required=True,
                sort_order=1
            )
            BundleProduct.objects.create(
                bundle=bundles['starter'],
                product=product_plans['teamspace_starter'].product,
                product_plan=product_plans['teamspace_starter'],
                is_required=True,
                sort_order=2
            )

        # Professional Bundle (All 3 Products)
        bundles['professional'], created = SubscriptionBundle.objects.get_or_create(
            code='professional_bundle',
            defaults={
                'name': 'Professional Bundle',
                'slug': 'professional-bundle',
                'tagline': 'Complete platform for growing businesses',
                'description': 'Get AutoFlow AI, BuildEasy, and TeamSpace with professional features and priority support.',
                'base_price': Decimal('135.00'),  # Regular would be $49 + $49 + $49 = $147, bundle is $135 (8% discount)
                'currency': 'USD',
                'billing_interval': 'monthly',
                'discount_type': 'percentage',
                'discount_value': Decimal('18.00'),
                'included_users': 25,
                'features': [
                    'AutoFlow AI Professional',
                    'BuildEasy Professional',
                    'TeamSpace Professional',
                    '25 users included',
                    'Priority support',
                    '14-day free trial'
                ],
                'metadata': {'recommended_for': 'growing_businesses'},
                'is_active': True,
                'is_public': True,
                'is_featured': True,
                'sort_order': 2
            }
        )

        if created:
            BundleProduct.objects.create(
                bundle=bundles['professional'],
                product=product_plans['autoflow_professional'].product,
                product_plan=product_plans['autoflow_professional'],
                is_required=True,
                sort_order=1
            )
            BundleProduct.objects.create(
                bundle=bundles['professional'],
                product=product_plans['buildeasy_professional'].product,
                product_plan=product_plans['buildeasy_professional'],
                is_required=True,
                sort_order=2
            )
            BundleProduct.objects.create(
                bundle=bundles['professional'],
                product=product_plans['teamspace_professional'].product,
                product_plan=product_plans['teamspace_professional'],
                is_required=True,
                sort_order=3
            )

        # Enterprise Bundle (All 3 Products - Enterprise Tier)
        bundles['enterprise'], created = SubscriptionBundle.objects.get_or_create(
            code='enterprise_bundle',
            defaults={
                'name': 'Enterprise Bundle',
                'slug': 'enterprise-bundle',
                'tagline': 'Unlimited power for large organizations',
                'description': 'Enterprise-grade features, unlimited users, dedicated support, and custom SLAs.',
                'base_price': Decimal('249.00'),  # Regular would be $99 + $99 + $99 = $297, bundle is $249 (16% discount)
                'currency': 'USD',
                'billing_interval': 'monthly',
                'discount_type': 'percentage',
                'discount_value': Decimal('24.00'),
                'included_users': 0,  # Unlimited
                'features': [
                    'AutoFlow AI Enterprise',
                    'BuildEasy Enterprise',
                    'TeamSpace Enterprise',
                    'Unlimited users',
                    '24/7 dedicated support',
                    'Custom SLA',
                    'White-label options',
                    '30-day free trial'
                ],
                'metadata': {'recommended_for': 'enterprises'},
                'is_active': True,
                'is_public': True,
                'is_featured': False,
                'sort_order': 3
            }
        )

        if created:
            BundleProduct.objects.create(
                bundle=bundles['enterprise'],
                product=product_plans['autoflow_enterprise'].product,
                product_plan=product_plans['autoflow_enterprise'],
                is_required=True,
                sort_order=1
            )
            BundleProduct.objects.create(
                bundle=bundles['enterprise'],
                product=product_plans['buildeasy_enterprise'].product,
                product_plan=product_plans['buildeasy_enterprise'],
                is_required=True,
                sort_order=2
            )
            BundleProduct.objects.create(
                bundle=bundles['enterprise'],
                product=product_plans['teamspace_enterprise'].product,
                product_plan=product_plans['teamspace_enterprise'],
                is_required=True,
                sort_order=3
            )

        self.stdout.write(f'  ✓ Created {len(bundles)} subscription bundles')
        return bundles
