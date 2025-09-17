# Rozitech SaaS Admin - Development Commands

.PHONY: help setup build up down migrate test lint clean logs shell createsuperuser

# Default target
help:
	@echo "Available commands:"
	@echo "  setup           - Initial project setup"
	@echo "  build           - Build Docker containers"
	@echo "  up              - Start all services"
	@echo "  down            - Stop all services"
	@echo "  migrate         - Run database migrations"
	@echo "  test            - Run test suite"
	@echo "  lint            - Run code quality checks"
	@echo "  clean           - Clean up containers and volumes"
	@echo "  logs            - View application logs"
	@echo "  shell           - Open Django shell"
	@echo "  createsuperuser - Create Django superuser"
	@echo "  backup          - Backup database"
	@echo "  restore         - Restore database from backup"

# Initial setup
setup:
	@echo "Setting up Rozitech SaaS Admin..."
	cp .env.example .env
	docker-compose up -d postgres redis
	sleep 10
	docker-compose run --rm web python manage.py migrate
	docker-compose run --rm web python manage.py migrate --tenant
	@echo "Setup complete! Run 'make up' to start all services."

# Build containers
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Start with monitoring
up-monitoring:
	docker-compose --profile monitoring up -d

# Start with logging
up-logging:
	docker-compose --profile logging up -d

# Start with all profiles
up-all:
	docker-compose --profile monitoring --profile logging --profile development up -d

# Stop services
down:
	docker-compose down

# Stop and remove volumes
down-volumes:
	docker-compose down -v

# Database migrations
migrate:
	docker-compose run --rm web python manage.py migrate
	docker-compose run --rm web python manage.py migrate --tenant

# Create new migration
makemigrations:
	docker-compose run --rm web python manage.py makemigrations

# Run tests
test:
	docker-compose run --rm web python manage.py test

# Run tests with coverage
test-coverage:
	docker-compose run --rm web coverage run --source='.' manage.py test
	docker-compose run --rm web coverage report
	docker-compose run --rm web coverage html

# Code quality checks
lint:
	docker-compose run --rm web flake8 .
	docker-compose run --rm web black --check .
	docker-compose run --rm web isort --check-only .

# Auto-fix code formatting
format:
	docker-compose run --rm web black .
	docker-compose run --rm web isort .

# Security checks
security-check:
	docker-compose run --rm web safety check
	docker-compose run --rm web bandit -r . -f json

# Clean up
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

# View logs
logs:
	docker-compose logs -f web

# View all logs
logs-all:
	docker-compose logs -f

# Django shell
shell:
	docker-compose run --rm web python manage.py shell

# Django shell plus
shell-plus:
	docker-compose run --rm web python manage.py shell_plus

# Create superuser
createsuperuser:
	docker-compose run --rm web python manage.py createsuperuser

# Collect static files
collectstatic:
	docker-compose run --rm web python manage.py collectstatic --noinput

# Database backup
backup:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U postgres rozitech_saas_admin > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Database restore
restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file name: " backup_file; \
	docker-compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS rozitech_saas_admin;"; \
	docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE rozitech_saas_admin;"; \
	docker-compose exec -T postgres psql -U postgres rozitech_saas_admin < $$backup_file

# Load demo data
load-demo:
	docker-compose run --rm web python manage.py loaddata fixtures/demo_data.json

# Reset database
reset-db:
	docker-compose down
	docker-compose up -d postgres redis
	sleep 5
	docker-compose run --rm web python manage.py reset_db --noinput
	docker-compose run --rm web python manage.py migrate
	docker-compose run --rm web python manage.py migrate --tenant

# Monitor services
monitor:
	@echo "Service Status:"
	docker-compose ps
	@echo "\nResource Usage:"
	docker stats --no-stream

# Update dependencies
update-deps:
	docker-compose run --rm web pip-compile requirements.in
	docker-compose run --rm web pip-compile requirements-dev.in
	docker-compose build

# Generate API documentation
docs:
	docker-compose run --rm web python manage.py spectacular --file schema.yml
	@echo "API schema generated: schema.yml"

# Deploy to staging
deploy-staging:
	@echo "Deploying to staging..."
	# Add your staging deployment commands here

# Deploy to production
deploy-production:
	@echo "Deploying to production..."
	# Add your production deployment commands here