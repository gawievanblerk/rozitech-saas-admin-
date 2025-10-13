# Generated manually for product catalog (SHARED models)

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('subscriptions', '0002_subscription_product_code'),
    ]

    operations = [
        # Create Product model
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(help_text="Unique product code (e.g., 'autoflow', 'buildeasy', 'teamspace')", max_length=50, unique=True)),
                ('name', models.CharField(help_text='Product display name', max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('tagline', models.CharField(blank=True, max_length=255)),
                ('billing_type', models.CharField(choices=[('fixed', 'Fixed Price'), ('per_user', 'Per User'), ('usage_based', 'Usage Based'), ('hybrid', 'Hybrid (Base + Usage)')], default='fixed', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('beta', 'Beta'), ('deprecated', 'Deprecated'), ('coming_soon', 'Coming Soon')], default='active', max_length=20)),
                ('icon', models.CharField(blank=True, help_text='Icon identifier or emoji', max_length=50)),
                ('color', models.CharField(default='#000000', help_text='Brand color (hex)', max_length=7)),
                ('features', models.JSONField(default=list, help_text='List of product features')),
                ('metadata', models.JSONField(default=dict, help_text='Additional product metadata')),
                ('is_active', models.BooleanField(default=True)),
                ('is_public', models.BooleanField(default=True, help_text='Whether this product is publicly available')),
                ('requires_approval', models.BooleanField(default=False, help_text='Whether subscription requires manual approval')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('launched_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'db_table': 'products',
                'ordering': ['sort_order', 'name'],
            },
        ),

        # Create ProductPlan model
        migrations.CreateModel(
            name='ProductPlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('product_limits', models.JSONField(default=dict, help_text='Product-specific limits (e.g., tasks for AutoFlow, apps for BuildEasy)')),
                ('product_features', models.JSONField(default=list, help_text='Product-specific features enabled in this plan')),
                ('is_available_standalone', models.BooleanField(default=True, help_text='Can be purchased individually')),
                ('is_available_in_bundle', models.BooleanField(default=True, help_text='Can be included in bundles')),
                ('is_active', models.BooleanField(default=True)),
                ('stripe_price_id', models.CharField(blank=True, help_text='Stripe Price ID for this product plan', max_length=255)),
                ('stripe_product_id', models.CharField(blank=True, help_text='Stripe Product ID', max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('base_plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='product_plans', to='subscriptions.pricingplan')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_plans', to='products.product')),
            ],
            options={
                'verbose_name': 'Product Plan',
                'verbose_name_plural': 'Product Plans',
                'db_table': 'product_plans',
                'ordering': ['product', 'base_plan__price'],
                'unique_together': {('product', 'base_plan')},
            },
        ),

        # Create SubscriptionBundle model
        migrations.CreateModel(
            name='SubscriptionBundle',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(help_text="Unique bundle code (e.g., 'starter_bundle', 'pro_bundle')", max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('tagline', models.CharField(blank=True, max_length=255)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('billing_interval', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually')], default='monthly', max_length=20)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage Discount'), ('fixed', 'Fixed Amount Discount')], default='percentage', max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='Percentage (0-100) or fixed amount depending on discount_type', max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('included_users', models.PositiveIntegerField(default=0, help_text='Number of users included in base price (0 = unlimited)')),
                ('features', models.JSONField(default=list)),
                ('metadata', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('is_public', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('stripe_product_id', models.CharField(blank=True, max_length=255)),
                ('stripe_price_id', models.CharField(blank=True, max_length=255)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Subscription Bundle',
                'verbose_name_plural': 'Subscription Bundles',
                'db_table': 'subscription_bundles',
                'ordering': ['sort_order', 'name'],
            },
        ),

        # Create BundleProduct model (through table)
        migrations.CreateModel(
            name='BundleProduct',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_required', models.BooleanField(default=True, help_text='Whether this product is required in the bundle')),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bundle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bundle_products', to='products.subscriptionbundle')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bundle_memberships', to='products.product')),
                ('product_plan', models.ForeignKey(help_text='Specific plan tier included in this bundle', on_delete=django.db.models.deletion.PROTECT, related_name='bundle_inclusions', to='products.productplan')),
            ],
            options={
                'verbose_name': 'Bundle Product',
                'verbose_name_plural': 'Bundle Products',
                'db_table': 'bundle_products',
                'ordering': ['sort_order', 'product__name'],
                'unique_together': {('bundle', 'product')},
            },
        ),
    ]
