# Generated manually for tenant-specific subscription models

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_add_product_models'),
        ('products', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        # Drop tables created by 0003 migration (they're now in products app)
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS products CASCADE;',
            reverse_sql='-- Tables will be recreated by products app'
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS product_plans CASCADE;',
            reverse_sql='-- Tables will be recreated by products app'
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS subscription_bundles CASCADE;',
            reverse_sql='-- Tables will be recreated by products app'
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS bundle_products CASCADE;',
            reverse_sql='-- Tables will be recreated by products app'
        ),

        # Create ProductSubscription model (TENANT-SPECIFIC)
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
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='products.productplan')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='products.product')),
            ],
            options={
                'verbose_name': 'Product Subscription',
                'verbose_name_plural': 'Product Subscriptions',
                'db_table': 'product_subscriptions',
                'unique_together': {('organization', 'product')},
            },
        ),

        # Create UsageRecord model (TENANT-SPECIFIC)
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

        # Add indexes for ProductSubscription
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

        # Add indexes for UsageRecord
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
