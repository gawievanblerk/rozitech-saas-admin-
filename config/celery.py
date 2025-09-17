"""
Celery configuration for Rozitech SaaS Admin Platform
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('rozitech_saas')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure task routing for different queues
app.conf.task_routes = {
    'apps.services.tasks.provisioning.*': {'queue': 'provisioning'},
    'apps.services.tasks.monitoring.*': {'queue': 'monitoring'},
    'apps.services.tasks.maintenance.*': {'queue': 'maintenance'},
}

# Task time limits
app.conf.task_time_limit = 3600  # 1 hour
app.conf.task_soft_time_limit = 3000  # 50 minutes

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration"""
    print(f'Request: {self.request!r}')