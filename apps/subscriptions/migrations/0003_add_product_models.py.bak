# Generated manually for multi-product billing system

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_subscription_product_code'),
        ('tenants', '0001_initial'),
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
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_plans', to='subscriptions.product')),
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
                ('bundle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bundle_products', to='subscriptions.subscriptionbundle')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bundle_memberships', to='subscriptions.product')),
                ('product_plan', models.ForeignKey(help_text='Specific plan tier included in this bundle', on_delete=django.db.models.deletion.PROTECT, related_name='bundle_inclusions', to='subscriptions.productplan')),
            ],
            options={
                'verbose_name': 'Bundle Product',
                'verbose_name_plural': 'Bundle Products',
                'db_table': 'bundle_products',
                'ordering': ['sort_order', 'product__name'],
                'unique_together': {('bundle', 'product')},
            },
        ),

        # Create ProductSubscription model
        migrations.CreateModel(
            name='ProductSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('trial', 'Trial'), ('active', 'Active'), ('past_due', 'Past Due'), ('cancelled', 'Cancelled'), ('suspended', 'Suspended'), ('expired', 'Expired'), ('pending_approval', 'Pending Approval')], default='trial', max_length=20)),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('trial_end_date', models.DateTimeField(blank=True, null=True)),
                ('current_period_start', models.DateTimeField()),
                ('current_period_end', models.DateTimeField()),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('cancellation_reason', models.TextField(blank=True)),
                ('next_billing_date', models.DateTimeField()),
                ('auto_renew', models.BooleanField(default=True)),
                ('current_usage', models.JSONField(default=dict, help_text='Current usage metrics for this product (e.g., tasks_executed, storage_used)')),
                ('usage_limit', models.JSONField(default=dict, help_text='Usage limits for this subscription')),
                ('stripe_subscription_id', models.CharField(blank=True, help_text='Stripe Subscription ID', max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_subscriptions', to='tenants.organization')),
                ('parent_subscription', models.ForeignKey(blank=True, help_text='Parent subscription if this is part of a bundle', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_subscriptions', to='subscriptions.subscription')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='subscriptions.productplan')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='subscriptions.product')),
            ],
            options={
                'verbose_name': 'Product Subscription',
                'verbose_name_plural': 'Product Subscriptions',
                'db_table': 'product_subscriptions',
                'unique_together': {('organization', 'product')},
            },
        ),

        # Create UsageRecord model
        migrations.CreateModel(
            name='UsageRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('metric_name', models.CharField(help_text="Name of the metric being tracked (e.g., 'api_calls', 'storage_gb', 'tasks_executed')", max_length=100)),
                ('quantity', models.DecimalField(decimal_places=4, max_digits=15, validators=[django.core.validators.MinValueValidator(0)])),
                ('unit', models.CharField(default='unit', help_text="Unit of measurement (e.g., 'call', 'GB', 'task')", max_length=50)),
                ('unit_price', models.DecimalField(blank=True, decimal_places=4, help_text='Price per unit for usage-based billing', max_digits=10, null=True)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, help_text='Total amount for this usage (quantity * unit_price)', max_digits=10)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField()),
                ('is_billed', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional context about the usage')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usage_records', to='subscriptions.invoice')),
                ('product_subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_records', to='subscriptions.productsubscription')),
            ],
            options={
                'verbose_name': 'Usage Record',
                'verbose_name_plural': 'Usage Records',
                'db_table': 'usage_records',
                'ordering': ['-timestamp'],
            },
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='productsubscription',
            index=models.Index(fields=['organization', 'status'], name='product_subscriptions_org_status_idx'),
        ),
        migrations.AddIndex(
            model_name='productsubscription',
            index=models.Index(fields=['product', 'status'], name='product_subscriptions_prod_status_idx'),
        ),
        migrations.AddIndex(
            model_name='productsubscription',
            index=models.Index(fields=['stripe_subscription_id'], name='product_subscriptions_stripe_idx'),
        ),
        migrations.AddIndex(
            model_name='usagerecord',
            index=models.Index(fields=['product_subscription', 'metric_name', 'timestamp'], name='usage_records_prod_metric_time_idx'),
        ),
        migrations.AddIndex(
            model_name='usagerecord',
            index=models.Index(fields=['is_billed', 'period_end'], name='usage_records_billed_period_idx'),
        ),
        migrations.AddIndex(
            model_name='usagerecord',
            index=models.Index(fields=['timestamp'], name='usage_records_timestamp_idx'),
        ),
    ]