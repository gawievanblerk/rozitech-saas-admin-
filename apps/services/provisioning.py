"""
Service provisioning automation framework
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from django.conf import settings
from django.utils import timezone
from django.db import transaction
import subprocess
import requests
import json
from dataclasses import dataclass
from enum import Enum

from apps.services.models import TenantService, Service, ServiceDependency, ServiceAlert

logger = logging.getLogger(__name__)


class ProvisioningStatus(Enum):
    """Provisioning status enumeration"""
    PENDING = 'pending'
    VALIDATING = 'validating'
    PREPARING = 'preparing'
    DEPLOYING = 'deploying'
    CONFIGURING = 'configuring'
    VERIFYING = 'verifying'
    COMPLETED = 'completed'
    FAILED = 'failed'
    ROLLING_BACK = 'rolling_back'


@dataclass
class ProvisioningConfig:
    """Configuration for service provisioning"""
    tenant_id: str
    service_id: str
    instance_name: str
    environment: str = 'production'
    region: str = 'us-east-1'
    resource_allocation: Dict[str, Any] = None
    custom_config: Dict[str, Any] = None
    auto_scaling_enabled: bool = True
    monitoring_enabled: bool = True
    backup_enabled: bool = True
    
    def __post_init__(self):
        if self.resource_allocation is None:
            self.resource_allocation = {}
        if self.custom_config is None:
            self.custom_config = {}


@dataclass
class ProvisioningResult:
    """Result of provisioning operation"""
    success: bool
    status: ProvisioningStatus
    tenant_service_id: Optional[str] = None
    public_url: Optional[str] = None
    internal_url: Optional[str] = None
    admin_url: Optional[str] = None
    api_key: Optional[str] = None
    error_message: Optional[str] = None
    provisioning_logs: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.provisioning_logs is None:
            self.provisioning_logs = []
        if self.metadata is None:
            self.metadata = {}


class BaseProvisioningProvider(ABC):
    """Base class for service provisioning providers"""
    
    def __init__(self, config: ProvisioningConfig):
        self.config = config
        self.logs = []
        self.tenant_service = None
        
    def log(self, message: str, level: str = 'INFO', metadata: Dict = None):
        """Add log entry"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'level': level,
            'message': message,
            'metadata': metadata or {}
        }
        self.logs.append(log_entry)
        
        # Also log to Django logger
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.config.tenant_id}:{self.config.service_id}] {message}")
    
    @abstractmethod
    def validate_prerequisites(self) -> bool:
        """Validate prerequisites before provisioning"""
        pass
    
    @abstractmethod
    def provision_infrastructure(self) -> Dict[str, Any]:
        """Provision infrastructure resources"""
        pass
    
    @abstractmethod
    def deploy_application(self, infrastructure: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy the application"""
        pass
    
    @abstractmethod
    def configure_service(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the service"""
        pass
    
    @abstractmethod
    def verify_deployment(self, configuration: Dict[str, Any]) -> bool:
        """Verify the deployment is successful"""
        pass
    
    @abstractmethod
    def cleanup_on_failure(self):
        """Cleanup resources on provisioning failure"""
        pass
    
    def provision(self) -> ProvisioningResult:
        """Main provisioning workflow"""
        try:
            # Create TenantService record
            with transaction.atomic():
                from apps.tenants.models import Tenant
                self.tenant_service = TenantService.objects.create(
                    tenant_id=self.config.tenant_id,
                    service_id=self.config.service_id,
                    instance_name=self.config.instance_name,
                    status='provisioning',
                    configuration=self.config.custom_config,
                    allocated_cpu_cores=self.config.resource_allocation.get('cpu_cores', 1),
                    allocated_memory_gb=self.config.resource_allocation.get('memory_gb', 2),
                    allocated_storage_gb=self.config.resource_allocation.get('storage_gb', 10),
                    auto_scaling_enabled=self.config.auto_scaling_enabled,
                    provisioning_logs=[]
                )
                
            self.log("Starting service provisioning")
            
            # Step 1: Validate prerequisites
            self.log("Validating prerequisites")
            self._update_status('validating')
            if not self.validate_prerequisites():
                raise Exception("Prerequisites validation failed")
            
            # Step 2: Provision infrastructure
            self.log("Provisioning infrastructure")
            self._update_status('preparing')
            infrastructure = self.provision_infrastructure()
            
            # Step 3: Deploy application
            self.log("Deploying application")
            self._update_status('deploying')
            deployment = self.deploy_application(infrastructure)
            
            # Step 4: Configure service
            self.log("Configuring service")
            self._update_status('configuring')
            configuration = self.configure_service(deployment)
            
            # Step 5: Verify deployment
            self.log("Verifying deployment")
            self._update_status('verifying')
            if not self.verify_deployment(configuration):
                raise Exception("Deployment verification failed")
            
            # Update TenantService with results
            self._update_status('active')
            self.tenant_service.public_url = configuration.get('public_url')
            self.tenant_service.internal_url = configuration.get('internal_url')
            self.tenant_service.admin_url = configuration.get('admin_url')
            self.tenant_service.api_key = configuration.get('api_key')
            self.tenant_service.activated_at = timezone.now()
            self.tenant_service.save()
            
            self.log("Service provisioning completed successfully", level='SUCCESS')
            
            return ProvisioningResult(
                success=True,
                status=ProvisioningStatus.COMPLETED,
                tenant_service_id=str(self.tenant_service.id),
                public_url=configuration.get('public_url'),
                internal_url=configuration.get('internal_url'),
                admin_url=configuration.get('admin_url'),
                api_key=configuration.get('api_key'),
                provisioning_logs=self.logs,
                metadata=configuration
            )
            
        except Exception as e:
            self.log(f"Provisioning failed: {str(e)}", level='ERROR')
            self._update_status('failed')
            
            # Attempt cleanup
            try:
                self.log("Attempting cleanup after failure")
                self.cleanup_on_failure()
            except Exception as cleanup_error:
                self.log(f"Cleanup failed: {str(cleanup_error)}", level='ERROR')
            
            return ProvisioningResult(
                success=False,
                status=ProvisioningStatus.FAILED,
                tenant_service_id=str(self.tenant_service.id) if self.tenant_service else None,
                error_message=str(e),
                provisioning_logs=self.logs
            )
    
    def _update_status(self, status: str):
        """Update TenantService status and logs"""
        if self.tenant_service:
            self.tenant_service.status = status
            self.tenant_service.provisioning_logs = self.logs
            self.tenant_service.save()


class DockerProvisioningProvider(BaseProvisioningProvider):
    """Docker-based provisioning provider"""
    
    def validate_prerequisites(self) -> bool:
        """Validate Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log("Docker is not available", level='ERROR')
                return False
            
            # Check if service has Docker image configured
            service = Service.objects.get(id=self.config.service_id)
            if not service.docker_image:
                self.log("Service does not have Docker image configured", level='ERROR')
                return False
            
            self.log("Prerequisites validated successfully")
            return True
            
        except Exception as e:
            self.log(f"Prerequisites validation error: {str(e)}", level='ERROR')
            return False
    
    def provision_infrastructure(self) -> Dict[str, Any]:
        """Provision Docker network and volumes"""
        service = Service.objects.get(id=self.config.service_id)
        
        # Create Docker network
        network_name = f"rozitech_{self.config.tenant_id}_{self.config.instance_name}"
        subprocess.run(['docker', 'network', 'create', network_name], check=True)
        self.log(f"Created Docker network: {network_name}")
        
        # Create volumes
        volumes = {}
        if service.requires_file_storage:
            volume_name = f"rozitech_storage_{self.config.tenant_id}_{self.config.instance_name}"
            subprocess.run(['docker', 'volume', 'create', volume_name], check=True)
            volumes['storage'] = volume_name
            self.log(f"Created Docker volume: {volume_name}")
        
        return {
            'network': network_name,
            'volumes': volumes
        }
    
    def deploy_application(self, infrastructure: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy Docker container"""
        service = Service.objects.get(id=self.config.service_id)
        
        # Prepare container name
        container_name = f"rozitech_{self.config.tenant_id}_{self.config.instance_name}"
        
        # Prepare environment variables
        env_vars = {
            'TENANT_ID': self.config.tenant_id,
            'SERVICE_ID': self.config.service_id,
            'INSTANCE_NAME': self.config.instance_name,
            **service.environment_variables,
            **self.config.custom_config.get('environment', {})
        }
        
        # Build docker run command
        docker_cmd = [
            'docker', 'run', '-d',
            '--name', container_name,
            '--network', infrastructure['network'],
            '--restart', 'unless-stopped'
        ]
        
        # Add environment variables
        for key, value in env_vars.items():
            docker_cmd.extend(['-e', f'{key}={value}'])
        
        # Add volumes
        for volume_type, volume_name in infrastructure['volumes'].items():
            if volume_type == 'storage':
                docker_cmd.extend(['-v', f'{volume_name}:/data'])
        
        # Add resource limits
        if self.config.resource_allocation:
            cpu_cores = self.config.resource_allocation.get('cpu_cores', 1)
            memory_gb = self.config.resource_allocation.get('memory_gb', 2)
            docker_cmd.extend([
                '--cpus', str(cpu_cores),
                '--memory', f'{memory_gb}g'
            ])
        
        # Add image
        docker_cmd.append(service.docker_image)
        
        # Run container
        result = subprocess.run(docker_cmd, capture_output=True, text=True, check=True)
        container_id = result.stdout.strip()
        
        self.log(f"Deployed Docker container: {container_name} ({container_id})")
        
        # Get container info
        inspect_result = subprocess.run(
            ['docker', 'inspect', container_id],
            capture_output=True,
            text=True,
            check=True
        )
        container_info = json.loads(inspect_result.stdout)[0]
        
        return {
            'container_id': container_id,
            'container_name': container_name,
            'container_info': container_info
        }
    
    def configure_service(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the service"""
        container_info = deployment['container_info']
        
        # Get container IP
        container_ip = container_info['NetworkSettings']['Networks'].get(
            list(container_info['NetworkSettings']['Networks'].keys())[0], {}
        ).get('IPAddress')
        
        # Generate URLs
        base_domain = settings.BASE_DOMAIN if hasattr(settings, 'BASE_DOMAIN') else 'localhost'
        instance_subdomain = f"{self.config.instance_name}.{self.config.tenant_id}"
        
        configuration = {
            'container_id': deployment['container_id'],
            'container_name': deployment['container_name'],
            'internal_url': f"http://{container_ip}:8000",
            'public_url': f"https://{instance_subdomain}.{base_domain}",
            'admin_url': f"https://{instance_subdomain}.{base_domain}/admin",
            'api_key': self._generate_api_key()
        }
        
        self.log(f"Service configured: {configuration['public_url']}")
        
        return configuration
    
    def verify_deployment(self, configuration: Dict[str, Any]) -> bool:
        """Verify the deployment is successful"""
        try:
            # Check container is running
            result = subprocess.run(
                ['docker', 'ps', '-q', '-f', f"name={configuration['container_name']}"],
                capture_output=True,
                text=True
            )
            
            if not result.stdout.strip():
                self.log("Container is not running", level='ERROR')
                return False
            
            # Try to make a health check request (if health check URL is configured)
            service = Service.objects.get(id=self.config.service_id)
            if service.health_check_url:
                health_url = configuration['internal_url'] + service.health_check_url
                try:
                    response = requests.get(health_url, timeout=10)
                    if response.status_code == 200:
                        self.log("Health check passed")
                        return True
                except:
                    pass
            
            # If no health check URL, just verify container is running
            self.log("Deployment verified (container running)")
            return True
            
        except Exception as e:
            self.log(f"Verification failed: {str(e)}", level='ERROR')
            return False
    
    def cleanup_on_failure(self):
        """Cleanup Docker resources on failure"""
        if self.tenant_service:
            container_name = f"rozitech_{self.config.tenant_id}_{self.config.instance_name}"
            network_name = f"rozitech_{self.config.tenant_id}_{self.config.instance_name}"
            volume_name = f"rozitech_storage_{self.config.tenant_id}_{self.config.instance_name}"
            
            # Stop and remove container
            subprocess.run(['docker', 'stop', container_name], capture_output=True)
            subprocess.run(['docker', 'rm', container_name], capture_output=True)
            
            # Remove network
            subprocess.run(['docker', 'network', 'rm', network_name], capture_output=True)
            
            # Remove volume
            subprocess.run(['docker', 'volume', 'rm', volume_name], capture_output=True)
            
            self.log("Cleanup completed")
    
    def _generate_api_key(self) -> str:
        """Generate API key for service"""
        import secrets
        return secrets.token_urlsafe(32)


class KubernetesProvisioningProvider(BaseProvisioningProvider):
    """Kubernetes-based provisioning provider"""
    
    def validate_prerequisites(self) -> bool:
        """Validate Kubernetes is available"""
        try:
            result = subprocess.run(['kubectl', 'version', '--client'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log("kubectl is not available", level='ERROR')
                return False
            
            self.log("Prerequisites validated successfully")
            return True
            
        except Exception as e:
            self.log(f"Prerequisites validation error: {str(e)}", level='ERROR')
            return False
    
    def provision_infrastructure(self) -> Dict[str, Any]:
        """Provision Kubernetes namespace and resources"""
        namespace = f"rozitech-{self.config.tenant_id}"
        
        # Create namespace manifest
        namespace_manifest = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': namespace,
                'labels': {
                    'tenant': self.config.tenant_id,
                    'managed-by': 'rozitech-saas'
                }
            }
        }
        
        # Apply namespace
        self._apply_manifest(namespace_manifest)
        self.log(f"Created Kubernetes namespace: {namespace}")
        
        return {'namespace': namespace}
    
    def deploy_application(self, infrastructure: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy Kubernetes deployment and service"""
        service = Service.objects.get(id=self.config.service_id)
        namespace = infrastructure['namespace']
        deployment_name = f"{self.config.instance_name}-deployment"
        
        # Create deployment manifest
        deployment_manifest = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': deployment_name,
                'namespace': namespace
            },
            'spec': {
                'replicas': self.config.resource_allocation.get('min_instances', 1),
                'selector': {
                    'matchLabels': {
                        'app': self.config.instance_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': self.config.instance_name,
                            'tenant': self.config.tenant_id,
                            'service': self.config.service_id
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': self.config.instance_name,
                            'image': service.docker_image,
                            'resources': {
                                'requests': {
                                    'cpu': f"{self.config.resource_allocation.get('cpu_cores', 0.5)}",
                                    'memory': f"{self.config.resource_allocation.get('memory_gb', 1)}Gi"
                                },
                                'limits': {
                                    'cpu': f"{self.config.resource_allocation.get('cpu_cores', 0.5) * 2}",
                                    'memory': f"{self.config.resource_allocation.get('memory_gb', 1) * 2}Gi"
                                }
                            },
                            'env': self._prepare_env_vars()
                        }]
                    }
                }
            }
        }
        
        # Apply deployment
        self._apply_manifest(deployment_manifest)
        self.log(f"Created Kubernetes deployment: {deployment_name}")
        
        # Create service manifest
        service_name = f"{self.config.instance_name}-service"
        service_manifest = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': service_name,
                'namespace': namespace
            },
            'spec': {
                'selector': {
                    'app': self.config.instance_name
                },
                'ports': [{
                    'port': 80,
                    'targetPort': 8000
                }],
                'type': 'ClusterIP'
            }
        }
        
        # Apply service
        self._apply_manifest(service_manifest)
        self.log(f"Created Kubernetes service: {service_name}")
        
        return {
            'deployment_name': deployment_name,
            'service_name': service_name,
            'namespace': namespace
        }
    
    def configure_service(self, deployment: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the service with ingress"""
        base_domain = settings.BASE_DOMAIN if hasattr(settings, 'BASE_DOMAIN') else 'cluster.local'
        instance_subdomain = f"{self.config.instance_name}.{self.config.tenant_id}"
        
        # Create ingress manifest
        ingress_name = f"{self.config.instance_name}-ingress"
        ingress_manifest = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': ingress_name,
                'namespace': deployment['namespace'],
                'annotations': {
                    'kubernetes.io/ingress.class': 'nginx',
                    'cert-manager.io/cluster-issuer': 'letsencrypt-prod'
                }
            },
            'spec': {
                'tls': [{
                    'hosts': [f"{instance_subdomain}.{base_domain}"],
                    'secretName': f"{self.config.instance_name}-tls"
                }],
                'rules': [{
                    'host': f"{instance_subdomain}.{base_domain}",
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': deployment['service_name'],
                                    'port': {
                                        'number': 80
                                    }
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        # Apply ingress
        self._apply_manifest(ingress_manifest)
        self.log(f"Created Kubernetes ingress: {ingress_name}")
        
        configuration = {
            'deployment_name': deployment['deployment_name'],
            'service_name': deployment['service_name'],
            'ingress_name': ingress_name,
            'namespace': deployment['namespace'],
            'internal_url': f"http://{deployment['service_name']}.{deployment['namespace']}.svc.cluster.local",
            'public_url': f"https://{instance_subdomain}.{base_domain}",
            'admin_url': f"https://{instance_subdomain}.{base_domain}/admin",
            'api_key': self._generate_api_key()
        }
        
        self.log(f"Service configured: {configuration['public_url']}")
        
        return configuration
    
    def verify_deployment(self, configuration: Dict[str, Any]) -> bool:
        """Verify the deployment is successful"""
        try:
            # Check deployment status
            result = subprocess.run(
                ['kubectl', 'get', 'deployment', configuration['deployment_name'], 
                 '-n', configuration['namespace'], '-o', 'json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.log("Deployment not found", level='ERROR')
                return False
            
            deployment_status = json.loads(result.stdout)
            ready_replicas = deployment_status['status'].get('readyReplicas', 0)
            
            if ready_replicas > 0:
                self.log(f"Deployment verified: {ready_replicas} replicas ready")
                return True
            else:
                self.log("No ready replicas", level='ERROR')
                return False
                
        except Exception as e:
            self.log(f"Verification failed: {str(e)}", level='ERROR')
            return False
    
    def cleanup_on_failure(self):
        """Cleanup Kubernetes resources on failure"""
        if self.tenant_service:
            namespace = f"rozitech-{self.config.tenant_id}"
            
            # Delete namespace (will delete all resources within)
            subprocess.run(['kubectl', 'delete', 'namespace', namespace], capture_output=True)
            
            self.log("Cleanup completed")
    
    def _apply_manifest(self, manifest: Dict):
        """Apply Kubernetes manifest"""
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(manifest, f)
            temp_path = f.name
        
        try:
            subprocess.run(['kubectl', 'apply', '-f', temp_path], check=True)
        finally:
            import os
            os.unlink(temp_path)
    
    def _prepare_env_vars(self) -> List[Dict[str, str]]:
        """Prepare environment variables for container"""
        service = Service.objects.get(id=self.config.service_id)
        
        env_vars = []
        all_vars = {
            'TENANT_ID': self.config.tenant_id,
            'SERVICE_ID': self.config.service_id,
            'INSTANCE_NAME': self.config.instance_name,
            **service.environment_variables,
            **self.config.custom_config.get('environment', {})
        }
        
        for key, value in all_vars.items():
            env_vars.append({'name': key, 'value': str(value)})
        
        return env_vars
    
    def _generate_api_key(self) -> str:
        """Generate API key for service"""
        import secrets
        return secrets.token_urlsafe(32)


class ProvisioningFactory:
    """Factory for creating provisioning providers"""
    
    PROVIDERS = {
        'docker': DockerProvisioningProvider,
        'kubernetes': KubernetesProvisioningProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_type: str, config: ProvisioningConfig) -> BaseProvisioningProvider:
        """Get provisioning provider instance"""
        provider_class = cls.PROVIDERS.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provisioning provider: {provider_type}")
        
        return provider_class(config)