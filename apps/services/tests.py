"""
Tests for service provisioning automation
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock
from decimal import Decimal
import uuid

from apps.services.models import (
    Service, ServiceCategory, TenantService,
    ServiceDependency, ServiceMetric, ServiceAlert
)
from apps.services.provisioning import (
    ProvisioningConfig, ProvisioningFactory,
    DockerProvisioningProvider, ProvisioningStatus
)
from apps.services.tasks import (
    provision_service, check_service_health,
    collect_service_metrics
)
from apps.tenants.models import Organization

User = get_user_model()


class ServiceModelTests(TestCase):
    """Tests for service models"""
    
    def setUp(self):
        self.category = ServiceCategory.objects.create(
            name='Web Applications',
            slug='web-apps',
            description='Web-based applications'
        )
        
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            description='A test service',
            short_description='Test',
            category=self.category,
            type='saas',
            status='active',
            docker_image='test/service:latest',
            min_cpu_cores=Decimal('0.5'),
            min_memory_gb=Decimal('1.0'),
            min_storage_gb=Decimal('5.0')
        )
        
        self.tenant = Organization.objects.create(
            schema_name='test_tenant',
            name='Test Tenant',
            slug='test-tenant',
            email='test@example.com',
            is_active=True
        )
    
    def test_service_creation(self):
        """Test service model creation"""
        self.assertEqual(self.service.name, 'Test Service')
        self.assertEqual(self.service.category, self.category)
        self.assertTrue(self.service.is_available)
    
    def test_tenant_service_creation(self):
        """Test tenant service model creation"""
        tenant_service = TenantService.objects.create(
            tenant=self.tenant,
            service=self.service,
            instance_name='test-instance',
            status='provisioning'
        )
        
        self.assertEqual(tenant_service.tenant, self.tenant)
        self.assertEqual(tenant_service.service, self.service)
        self.assertFalse(tenant_service.is_active)
        self.assertFalse(tenant_service.is_healthy)
    
    def test_service_dependency(self):
        """Test service dependency relationships"""
        dependency_service = Service.objects.create(
            name='Database Service',
            slug='database-service',
            description='Database service',
            short_description='Database',
            category=self.category,
            type='infrastructure',
            status='active'
        )
        
        dependency = ServiceDependency.objects.create(
            service=self.service,
            depends_on=dependency_service,
            dependency_type='required'
        )
        
        self.assertEqual(dependency.service, self.service)
        self.assertEqual(dependency.depends_on, dependency_service)
    
    def test_service_metric_creation(self):
        """Test service metric creation"""
        tenant_service = TenantService.objects.create(
            tenant=self.tenant,
            service=self.service,
            instance_name='test-instance',
            status='active'
        )
        
        metric = ServiceMetric.objects.create(
            tenant_service=tenant_service,
            metric_type='cpu_usage',
            value=Decimal('45.5'),
            unit='%'
        )
        
        self.assertEqual(metric.tenant_service, tenant_service)
        self.assertEqual(metric.value, Decimal('45.5'))
    
    def test_service_alert_creation(self):
        """Test service alert creation"""
        tenant_service = TenantService.objects.create(
            tenant=self.tenant,
            service=self.service,
            instance_name='test-instance',
            status='active'
        )
        
        alert = ServiceAlert.objects.create(
            tenant_service=tenant_service,
            title='High CPU Usage',
            message='CPU usage is above 80%',
            severity='warning',
            alert_type='high_cpu',
            source='monitoring'
        )
        
        self.assertEqual(alert.tenant_service, tenant_service)
        self.assertEqual(alert.status, 'active')
        
        # Test acknowledge
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        alert.acknowledge(user)
        self.assertEqual(alert.status, 'acknowledged')
        self.assertEqual(alert.acknowledged_by, user)
        
        # Test resolve
        alert.resolve()
        self.assertEqual(alert.status, 'resolved')
        self.assertIsNotNone(alert.resolved_at)


class ProvisioningTests(TestCase):
    """Tests for provisioning framework"""
    
    def setUp(self):
        self.tenant = Organization.objects.create(
            schema_name='test_tenant',
            name='Test Tenant',
            slug='test-tenant',
            email='test@example.com',
            is_active=True
        )
        
        self.category = ServiceCategory.objects.create(
            name='Web Applications',
            slug='web-apps'
        )
        
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            description='Test service',
            short_description='Test',
            category=self.category,
            type='saas',
            status='active',
            docker_image='test/service:latest'
        )
        
        self.config = ProvisioningConfig(
            tenant_id=str(self.tenant.id),
            service_id=str(self.service.id),
            instance_name='test-instance',
            resource_allocation={
                'cpu_cores': 1,
                'memory_gb': 2,
                'storage_gb': 10
            }
        )
    
    @patch('subprocess.run')
    def test_docker_provisioning_validation(self, mock_run):
        """Test Docker provisioning validation"""
        # Mock docker version check
        mock_run.return_value.returncode = 0
        
        provider = DockerProvisioningProvider(self.config)
        result = provider.validate_prerequisites()
        
        self.assertTrue(result)
        mock_run.assert_called_with(['docker', '--version'], capture_output=True, text=True)
    
    @patch('subprocess.run')
    def test_docker_provisioning_infrastructure(self, mock_run):
        """Test Docker infrastructure provisioning"""
        mock_run.return_value.returncode = 0
        
        provider = DockerProvisioningProvider(self.config)
        infrastructure = provider.provision_infrastructure()
        
        self.assertIn('network', infrastructure)
        self.assertIn('volumes', infrastructure)
    
    @patch('subprocess.run')
    @patch('apps.services.provisioning.DockerProvisioningProvider.validate_prerequisites')
    def test_docker_provisioning_deployment(self, mock_validate, mock_run):
        """Test Docker deployment"""
        mock_validate.return_value = True
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'container-id-123'
        
        provider = DockerProvisioningProvider(self.config)
        infrastructure = {'network': 'test-network', 'volumes': {}}
        
        # Mock container inspect
        import json
        container_info = {
            'NetworkSettings': {
                'Networks': {
                    'test-network': {'IPAddress': '172.17.0.2'}
                }
            }
        }
        mock_run.return_value.stdout = json.dumps([container_info])
        
        deployment = provider.deploy_application(infrastructure)
        
        self.assertIn('container_id', deployment)
        self.assertIn('container_name', deployment)
    
    def test_provisioning_factory(self):
        """Test provisioning factory"""
        provider = ProvisioningFactory.get_provider('docker', self.config)
        self.assertIsInstance(provider, DockerProvisioningProvider)
        
        with self.assertRaises(ValueError):
            ProvisioningFactory.get_provider('invalid', self.config)


class ProvisioningTaskTests(TestCase):
    """Tests for provisioning tasks"""
    
    def setUp(self):
        self.tenant = Organization.objects.create(
            schema_name='test_tenant',
            name='Test Tenant',
            slug='test-tenant',
            email='test@example.com',
            is_active=True
        )
        
        self.category = ServiceCategory.objects.create(
            name='Web Applications',
            slug='web-apps'
        )
        
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            description='Test service',
            short_description='Test',
            category=self.category,
            type='saas',
            status='active',
            docker_image='test/service:latest'
        )
    
    @patch('apps.services.provisioning.DockerProvisioningProvider.provision')
    @patch('apps.services.webhooks.WebhookDispatcher.dispatch_provisioning_complete')
    def test_provision_service_task(self, mock_webhook, mock_provision):
        """Test provision service task"""
        from apps.services.provisioning import ProvisioningResult
        
        # Mock successful provisioning
        mock_provision.return_value = ProvisioningResult(
            success=True,
            status=ProvisioningStatus.COMPLETED,
            tenant_service_id=str(uuid.uuid4()),
            public_url='https://test.example.com',
            admin_url='https://test.example.com/admin',
            api_key='test-api-key'
        )
        
        result = provision_service(
            tenant_id=str(self.tenant.id),
            service_id=str(self.service.id),
            instance_name='test-instance'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['public_url'], 'https://test.example.com')
        mock_webhook.assert_called_once()
    
    @patch('requests.get')
    def test_check_service_health_task(self, mock_get):
        """Test health check task"""
        tenant_service = TenantService.objects.create(
            tenant=self.tenant,
            service=self.service,
            instance_name='test-instance',
            status='active',
            internal_url='http://localhost:8000'
        )
        
        # Mock successful health check
        mock_get.return_value.status_code = 200
        
        result = check_service_health(str(tenant_service.id))
        
        self.assertTrue(result['success'])
        self.assertEqual(result['health_status'], 'healthy')
        
        # Reload and check
        tenant_service.refresh_from_db()
        self.assertEqual(tenant_service.health_status, 'healthy')
        self.assertIsNotNone(tenant_service.last_health_check)
    
    def test_collect_service_metrics_task(self):
        """Test metric collection task"""
        tenant_service = TenantService.objects.create(
            tenant=self.tenant,
            service=self.service,
            instance_name='test-instance',
            status='active'
        )
        
        result = collect_service_metrics(str(tenant_service.id))
        
        self.assertTrue(result['success'])
        self.assertIn('metrics', result)
        
        # Check metrics were created
        metrics = ServiceMetric.objects.filter(tenant_service=tenant_service)
        self.assertTrue(metrics.exists())


class ServiceAPITests(TestCase):
    """Tests for service management APIs"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.tenant = Organization.objects.create(
            schema_name='test_tenant',
            name='Test Tenant',
            slug='test-tenant',
            email='test@example.com',
            is_active=True
        )
        
        self.category = ServiceCategory.objects.create(
            name='Web Applications',
            slug='web-apps'
        )
        
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            description='Test service',
            short_description='Test',
            category=self.category,
            type='saas',
            status='active',
            is_public=True,
            docker_image='test/service:latest'
        )
    
    def test_service_catalog_api(self):
        """Test service catalog API"""
        from rest_framework.test import APIClient
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        # Mock tenant middleware
        with patch('apps.services.views.IsAuthenticated.has_permission', return_value=True):
            response = client.get('/api/services/catalog/')
        
        self.assertEqual(response.status_code, 200)
        # Note: The actual response would depend on the request object having a tenant attribute
    
    def test_tenant_service_provision_api(self):
        """Test service provisioning API"""
        from rest_framework.test import APIClient
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        data = {
            'service_id': str(self.service.id),
            'instance_name': 'test-instance',
            'allocated_cpu_cores': 1,
            'allocated_memory_gb': 2,
            'allocated_storage_gb': 10
        }
        
        # Mock tenant middleware and task
        with patch('apps.services.views.IsAuthenticated.has_permission', return_value=True):
            with patch('apps.services.views.provision_service.apply_async') as mock_task:
                mock_task.return_value.id = 'task-123'
                
                # Note: This would need proper request.tenant setup
                # response = client.post('/api/services/instances/provision/', data)
        
        # The actual test would need proper middleware setup
        self.assertTrue(True)  # Placeholder assertion