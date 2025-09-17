# CLAUDE.md - Rozitech SaaS Admin Platform

This file provides guidance for working with the Rozitech SaaS Admin Platform - a comprehensive multi-tenant SaaS management system.

## Project Overview
This platform serves as the central administration hub for all Rozitech SaaS products, providing subscription management, billing, tenant isolation, service orchestration, and comprehensive analytics.

## Project Structure
```
rozitech-saas-admin/
├── config/                 # Django project configuration
├── apps/                   # Django applications
│   ├── tenants/           # Multi-tenant management
│   ├── subscriptions/     # Billing and subscription logic
│   ├── payments/          # Payment processing
│   ├── services/          # Service catalog and provisioning
│   ├── analytics/         # Usage tracking and reporting
│   └── notifications/     # Communication system
├── core/                  # Shared utilities and middleware
├── infrastructure/        # Docker, K8s, deployment configs
├── monitoring/           # Prometheus, Grafana configs
└── docs/                 # Documentation
```

## Key Technologies
- **Backend:** Django 4.2+, Python 3.11+, Django REST Framework
- **Database:** PostgreSQL 15+ with tenant partitioning
- **Multi-tenancy:** django-tenants for schema isolation
- **Cache/Queue:** Redis 7+, Celery 5+
- **Payment:** Stripe, PayPal, PayFast (SA)
- **Monitoring:** Prometheus, Grafana, ELK Stack
- **Containerization:** Docker & Kubernetes

## Core Features
### Multi-Tenant Architecture
- Schema-based tenant isolation using django-tenants
- Tenant-aware middleware for request routing
- Dynamic database routing per tenant
- Resource quotas and usage tracking

### Subscription Management
- Flexible pricing plans (flat-rate, usage-based, tiered)
- Automated billing cycles with prorated calculations
- Trial periods and promotional codes
- Dunning management for failed payments

### Payment Processing
- Multiple payment gateway support (Stripe, PayFast, etc.)
- Secure payment method storage
- Automated invoice generation
- Refund and chargeback handling

### Service Orchestration
- Service catalog with dependency management
- Automated tenant service provisioning
- Health monitoring and alerting
- Resource scaling based on usage

## Development Commands
```bash
# Setup
make setup                  # Initial project setup
make up                     # Start all services
make migrate               # Run database migrations

# Development
make shell                 # Django shell
make test                  # Run test suite
make lint                  # Code quality checks

# Database
make backup                # Backup database
make reset-db              # Reset database

# Monitoring
make up-monitoring         # Start with monitoring stack
make logs                  # View application logs
```

## Multi-Tenant Development
When working with multi-tenant features:

1. **Always use tenant-aware queries** - Use the tenant middleware to ensure proper isolation
2. **Schema migrations** - Run migrations for both public and tenant schemas
3. **Tenant context** - Use `core.middleware.tenant_context` to get current tenant
4. **Testing** - Create test tenants for proper isolation testing

## Key Models
- **Tenant** - Multi-tenant organization with resource limits
- **TenantUser** - User membership in tenants with role-based access
- **Subscription** - Billing subscription with plan and status tracking
- **PricingPlan** - Flexible pricing with feature limits
- **Transaction** - Payment transactions with provider integration
- **Service** - Available services in the platform catalog
- **TenantService** - Service instances provisioned for tenants

## API Design Patterns
- RESTful API design with Django REST Framework
- Tenant-scoped API endpoints
- Comprehensive API documentation with drf-spectacular
- JWT-based authentication
- Rate limiting and throttling

## Security Considerations
- Multi-tenant data isolation
- OAuth 2.0 / OIDC authentication
- JWT token-based API access
- Role-based access control (RBAC)
- API rate limiting
- Encrypted sensitive data storage
- Audit logging for compliance

## Payment Integration
- Stripe for international payments
- PayFast for South African market
- Webhook handling for payment events
- Secure payment method tokenization
- Automated dunning for failed payments

## Monitoring & Observability
- Application performance monitoring (APM)
- Custom metrics collection
- Centralized logging with ELK Stack
- Service health checks
- Alert management system

## Deployment
- Docker containerization for all services
- Kubernetes orchestration for production
- CI/CD pipeline with GitLab
- Blue-green deployment strategy
- Automated scaling based on metrics

## Testing Strategy
- Unit tests for models and business logic
- Integration tests for API endpoints
- Multi-tenant isolation testing
- Payment flow testing with mock providers
- Load testing for scalability

## Current Development Phase
- **Status:** Core platform foundation complete
- **Completed:** Multi-tenant architecture, subscription models, payment framework
- **Next Steps:** Service provisioning automation, analytics dashboard, monitoring setup

## Notes for Development
- Follow Django best practices and PEP 8 style guide
- Use type hints for better code maintainability
- Implement comprehensive error handling
- Add logging for audit trails
- Test multi-tenant isolation thoroughly
- Document API changes
- Consider South African compliance requirements (POPI, FICA)

## Rozitech Ecosystem Integration
This platform manages multiple SaaS products:
- **insurr-platform** - Funeral insurance system (first managed service)
- Future SaaS products will be added to the service catalog
- Shared authentication and billing across all products
- Centralized analytics and reporting

## Common Development Tasks
1. **Adding a new service** - Update Service model, create provisioning logic
2. **New payment provider** - Implement in PaymentProvider with webhook handling
3. **Tenant feature limits** - Update PricingPlan and enforcement middleware
4. **Custom metrics** - Add to ServiceMetric model and collection logic
5. **API endpoints** - Use DRF ViewSets with tenant-aware permissions