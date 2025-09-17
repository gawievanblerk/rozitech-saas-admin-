#!/bin/bash

# Rozitech Website Deployment Script
# This script deploys the new website pages with functional Get Started and Learn More buttons

set -e  # Exit on any error

echo "🚀 Rozitech Website Deployment"
echo "=================================="

# Check if running from correct directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo "❌ Error: Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to build the application
build_application() {
    echo "🔨 Building Django application..."
    
    # Build Docker image
    docker build -f Dockerfile.production -t rozitech-saas:latest .
    
    if [ $? -eq 0 ]; then
        echo "✅ Application built successfully"
    else
        echo "❌ Error: Failed to build application"
        exit 1
    fi
}

# Function to deploy to production
deploy_production() {
    echo "🌐 Deploying to production..."
    
    # Stop existing containers
    echo "Stopping existing containers..."
    docker-compose -f docker-compose.production.yml down
    
    # Start new containers
    echo "Starting new containers..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to be ready
    echo "Waiting for services to start..."
    sleep 30
    
    # Check if web service is running
    if docker-compose -f docker-compose.production.yml ps | grep -q "rozitech-web.*Up"; then
        echo "✅ Web service is running"
    else
        echo "❌ Error: Web service failed to start"
        docker-compose -f docker-compose.production.yml logs web
        exit 1
    fi
}

# Function to run database migrations
run_migrations() {
    echo "📊 Running database migrations..."
    
    docker-compose -f docker-compose.production.yml exec -T web python manage.py migrate
    
    if [ $? -eq 0 ]; then
        echo "✅ Migrations completed successfully"
    else
        echo "❌ Error: Migrations failed"
        exit 1
    fi
}

# Function to collect static files
collect_static() {
    echo "📦 Collecting static files..."
    
    docker-compose -f docker-compose.production.yml exec -T web python manage.py collectstatic --noinput
    
    if [ $? -eq 0 ]; then
        echo "✅ Static files collected successfully"
    else
        echo "❌ Error: Failed to collect static files"
        exit 1
    fi
}

# Function to test the deployment
test_deployment() {
    echo "🧪 Testing deployment..."
    
    # Test homepage
    echo "Testing homepage..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200"; then
        echo "✅ Homepage is accessible"
    else
        echo "❌ Error: Homepage is not accessible"
        return 1
    fi
    
    # Test Get Started page
    echo "Testing Get Started page..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/get-started/ | grep -q "200"; then
        echo "✅ Get Started page is accessible"
    else
        echo "❌ Error: Get Started page is not accessible"
        return 1
    fi
    
    # Test Learn More page
    echo "Testing Learn More page..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/learn-more/ | grep -q "200"; then
        echo "✅ Learn More page is accessible"
    else
        echo "❌ Error: Learn More page is not accessible"
        return 1
    fi
    
    echo "✅ All tests passed!"
}

# Function to show deployment summary
show_summary() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================="
    echo ""
    echo "📱 Website URLs:"
    echo "   Homepage:     http://rozitech.com/"
    echo "   Get Started:  http://rozitech.com/get-started/"
    echo "   Learn More:   http://rozitech.com/learn-more/"
    echo ""
    echo "🔧 Admin URLs:"
    echo "   Django Admin: http://rozitech.com/admin/"
    echo "   Health Check: http://rozitech.com/health/"
    echo ""
    echo "📋 Features Deployed:"
    echo "   ✅ Functional Get Started button"
    echo "   ✅ Functional Learn More button"
    echo "   ✅ Responsive design (mobile/desktop)"
    echo "   ✅ Pricing tiers (Starter/Professional/Enterprise)"
    echo "   ✅ Farmer Brown scenario walkthrough"
    echo "   ✅ Contact forms and email integration"
    echo "   ✅ South African market focus"
    echo ""
    echo "📞 Support:"
    echo "   Email: hello@rozitech.com"
    echo "   Phone: +27 11 123 4567"
    echo ""
    echo "🔍 To monitor:"
    echo "   docker-compose -f docker-compose.production.yml logs -f"
    echo ""
}

# Main execution
main() {
    echo "Starting deployment process..."
    
    # Pre-deployment checks
    check_docker
    
    # Build and deploy
    build_application
    deploy_production
    run_migrations
    collect_static
    
    # Post-deployment testing
    echo "Waiting for services to fully initialize..."
    sleep 10
    
    test_deployment
    
    # Show summary
    show_summary
}

# Handle command line arguments
case "${1:-deploy}" in
    "build")
        echo "🔨 Building application only..."
        check_docker
        build_application
        ;;
    "deploy")
        main
        ;;
    "test")
        echo "🧪 Testing current deployment..."
        test_deployment
        ;;
    "logs")
        echo "📋 Showing application logs..."
        docker-compose -f docker-compose.production.yml logs -f
        ;;
    "status")
        echo "📊 Showing service status..."
        docker-compose -f docker-compose.production.yml ps
        ;;
    "stop")
        echo "🛑 Stopping services..."
        docker-compose -f docker-compose.production.yml down
        ;;
    *)
        echo "Usage: $0 {build|deploy|test|logs|status|stop}"
        echo ""
        echo "Commands:"
        echo "  build   - Build the application Docker image"
        echo "  deploy  - Full deployment (default)"
        echo "  test    - Test the current deployment"
        echo "  logs    - Show application logs"
        echo "  status  - Show service status"
        echo "  stop    - Stop all services"
        exit 1
        ;;
esac