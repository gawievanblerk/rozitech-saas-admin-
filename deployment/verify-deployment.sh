#!/bin/bash

# Deployment Verification Script for Xneelo Server
SERVER_IP="154.65.107.234"

echo "🔍 Verifying Rozitech SaaS Deployment on Xneelo"
echo "=============================================="

# Check if server is reachable
echo -n "1. Checking server connectivity... "
if ping -c 1 $SERVER_IP &> /dev/null; then
    echo "✅ Server is reachable"
else
    echo "❌ Cannot reach server"
    exit 1
fi

# Check health endpoint
echo -n "2. Checking health endpoint... "
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP/health/)
if [ "$HEALTH_CHECK" == "200" ]; then
    echo "✅ Health check passed"
    curl -s http://$SERVER_IP/health/ | python3 -m json.tool
else
    echo "❌ Health check failed (HTTP $HEALTH_CHECK)"
fi

# Check nginx
echo -n "3. Checking Nginx... "
NGINX_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP/)
if [ "$NGINX_CHECK" != "000" ]; then
    echo "✅ Nginx is responding (HTTP $NGINX_CHECK)"
else
    echo "❌ Nginx is not responding"
fi

# Check if Docker containers are running
echo ""
echo "4. Docker container status on server:"
ssh ubuntu@$SERVER_IP "sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo ""
echo "5. Recent Docker logs:"
ssh ubuntu@$SERVER_IP "sudo docker-compose -f /opt/rozitech-saas/docker-compose.yml logs --tail=20"

echo ""
echo "=============================================="
echo "📊 Deployment Summary:"
echo "- Server IP: $SERVER_IP"
echo "- Health Check URL: http://$SERVER_IP/health/"
echo "- Admin URL: http://$SERVER_IP/admin/"
echo ""
echo "🔗 Access your application at:"
echo "- http://$SERVER_IP"
echo "- http://rozitech.com (after DNS configuration)"
echo "- http://rozitech.co.za (after DNS configuration)"
echo ""