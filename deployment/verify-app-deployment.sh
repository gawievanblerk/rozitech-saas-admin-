#!/bin/bash
# Application Deployment Verification Script
# Tests that all services and endpoints are working correctly after deployment

set -e

echo "========================================="
echo "Application Deployment Verification"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Track results
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3

    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_code)"
        ((FAILED++))
    fi
}

# Function to check service
check_service() {
    local name=$1
    local service=$2

    echo -n "Checking $name... "

    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✓ RUNNING${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        ((FAILED++))
    fi
}

echo -e "${YELLOW}=== Service Status ===${NC}"
echo ""

check_service "Gunicorn Service" "rozitech-saas-admin"
check_service "Nginx Service" "nginx"

echo ""
echo -e "${YELLOW}=== Endpoint Tests ===${NC}"
echo ""

# Test endpoints (200 = OK, 401 = Unauthorized but endpoint exists, 404 = Not Found)
test_endpoint "API Documentation" "http://localhost/api/docs/" "200"
test_endpoint "API Schema" "http://localhost/api/schema/" "200"
test_endpoint "Auth Verify (no token)" "http://localhost/api/auth/verify" "401"
test_endpoint "Health Check" "http://localhost/" "200"
test_endpoint "Admin Panel" "http://localhost/admin/" "200"

echo ""
echo -e "${YELLOW}=== File System Checks ===${NC}"
echo ""

# Check important files and directories
check_path() {
    local name=$1
    local path=$2

    echo -n "Checking $name... "

    if [ -e "$path" ]; then
        echo -e "${GREEN}✓ EXISTS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ MISSING${NC}"
        ((FAILED++))
    fi
}

check_path "Application Directory" "/opt/rozitech-saas-admin"
check_path "Virtual Environment" "/opt/rozitech-saas-admin/venv"
check_path "Static Files" "/opt/rozitech-saas-admin/staticfiles"
check_path "Database File" "/opt/rozitech-saas-admin/db.sqlite3"
check_path "Gunicorn Socket" "/run/gunicorn-rozitech-saas.sock"

echo ""
echo -e "${YELLOW}=== Log Files ===${NC}"
echo ""

check_path "Gunicorn Access Log" "/var/log/gunicorn/access.log"
check_path "Gunicorn Error Log" "/var/log/gunicorn/error.log"
check_path "Nginx Access Log" "/var/log/nginx/rozitech-saas-admin-access.log"
check_path "Nginx Error Log" "/var/log/nginx/rozitech-saas-admin-error.log"

echo ""
echo "========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "========================================="
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Deployment is successful.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Test from external network: curl -I http://154.65.107.234/api/docs/"
    echo "2. Create test users and organizations"
    echo "3. Test TeamSpace integration"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review errors above.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "- Check service logs: sudo journalctl -u rozitech-saas-admin -n 50"
    echo "- Check nginx logs: sudo tail -f /var/log/nginx/rozitech-saas-admin-error.log"
    echo "- Verify configuration: sudo nginx -t"
    exit 1
fi
