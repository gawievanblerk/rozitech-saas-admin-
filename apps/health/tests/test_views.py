from django.test import TestCase, Client
from django.urls import reverse
import json


class HealthCheckViewTest(TestCase):
    """Test cases for health check endpoints"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_simple_health_check(self):
        """Test simple health check endpoint returns 200"""
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_simple_health_check_response_format(self):
        """Test simple health check returns correct JSON structure"""
        response = self.client.get('/health/')
        data = json.loads(response.content)

        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('service', data)
        self.assertEqual(data['service'], 'rozitech-saas-admin')

    def test_simple_health_check_includes_timestamp(self):
        """Test that health check includes timestamp"""
        response = self.client.get('/health/')
        data = json.loads(response.content)

        self.assertIn('timestamp', data)
        self.assertIsInstance(data['timestamp'], (int, float))

    def test_simple_health_check_includes_version(self):
        """Test that health check includes version"""
        response = self.client.get('/health/')
        data = json.loads(response.content)

        self.assertIn('version', data)
        self.assertIsInstance(data['version'], str)

    def test_full_health_check(self):
        """Test full health check endpoint"""
        response = self.client.get('/health/full/')

        # May return 200 or 500 depending on dependencies
        self.assertIn(response.status_code, [200, 500, 503])
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_full_health_check_response_format(self):
        """Test full health check returns correct JSON structure"""
        response = self.client.get('/health/full/')
        data = json.loads(response.content)

        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIsInstance(data['checks'], dict)

    def test_full_health_check_database_check(self):
        """Test that full health check includes database check"""
        response = self.client.get('/health/full/')
        data = json.loads(response.content)

        self.assertIn('database', data['checks'])
        self.assertIsInstance(data['checks']['database'], dict)

    def test_auth_server_status_endpoint(self):
        """Test auth server status endpoint"""
        response = self.client.get('/health/auth-server-status/')

        # May return 200 or 500 depending on auth server availability
        self.assertIn(response.status_code, [200, 500, 503])
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_check_no_authentication_required(self):
        """Test that health checks don't require authentication"""
        # Simple health check should work without auth
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)

    def test_health_check_accepts_get_only(self):
        """Test that health check only accepts GET requests"""
        response = self.client.post('/health/')
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_full_health_check_includes_timestamp(self):
        """Test that full health check includes timestamp"""
        response = self.client.get('/health/full/')
        data = json.loads(response.content)

        self.assertIn('timestamp', data)

    def test_health_check_response_time(self):
        """Test that simple health check responds quickly"""
        import time

        start_time = time.time()
        response = self.client.get('/health/')
        end_time = time.time()

        response_time = end_time - start_time

        # Should respond in less than 1 second
        self.assertLess(response_time, 1.0)
        self.assertEqual(response.status_code, 200)


class HealthCheckIntegrationTest(TestCase):
    """Integration tests for health check functionality"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_health_check_load_balancer_compatible(self):
        """Test that health check is compatible with load balancers"""
        response = self.client.get('/health/')

        # Load balancers typically look for 200 status
        self.assertEqual(response.status_code, 200)
        # And JSON content type
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_health_check_monitoring_compatible(self):
        """Test that health check provides monitoring-friendly output"""
        response = self.client.get('/health/')
        data = json.loads(response.content)

        # Should have clear status indicator
        self.assertIn('status', data)
        self.assertIn(data['status'], ['healthy', 'unhealthy', 'degraded'])

    def test_full_health_check_provides_detailed_status(self):
        """Test that full health check provides component status"""
        response = self.client.get('/health/full/')
        data = json.loads(response.content)

        # Should have checks for major components
        self.assertIn('checks', data)
        checks = data['checks']

        # Each check should have a status
        for component, check_data in checks.items():
            self.assertIn('status', check_data)

    def test_health_endpoints_listed(self):
        """Test that all expected health endpoints exist"""
        endpoints = [
            '/health/',
            '/health/full/',
            '/health/auth-server-status/'
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Should not return 404
            self.assertNotEqual(response.status_code, 404)

    def test_health_check_cors_headers(self):
        """Test that health check includes appropriate CORS headers if configured"""
        response = self.client.get('/health/')

        # Should allow health checks from monitoring tools
        # If CORS is configured, these headers should be present
        if 'Access-Control-Allow-Origin' in response:
            self.assertIsNotNone(response['Access-Control-Allow-Origin'])

    def test_consecutive_health_checks(self):
        """Test that multiple consecutive health checks work"""
        for _ in range(5):
            response = self.client.get('/health/')
            self.assertEqual(response.status_code, 200)

    def test_health_check_different_paths(self):
        """Test accessing health check with and without trailing slash"""
        response_with_slash = self.client.get('/health/')
        response_without_slash = self.client.get('/health')

        # At least one should work
        statuses = [response_with_slash.status_code, response_without_slash.status_code]
        self.assertIn(200, statuses)