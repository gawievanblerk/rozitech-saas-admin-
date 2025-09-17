# GitHub Actions Workflows

This directory contains the CI/CD workflows for the Rozitech SaaS Platform.

## Workflows

- `deploy-production.yml` - Production deployment to Hetzner
- `deploy-staging.yml` - Staging deployment for testing
- `tests.yml` - Run tests on pull requests
- `security-scan.yml` - Security scanning and dependency checks

## Secrets Required

The following secrets need to be configured in GitHub repository settings:

### Server Access
- `HETZNER_SERVER_HOST` - Your Hetzner server IP address
- `HETZNER_SERVER_USER` - SSH username (usually 'root')
- `HETZNER_SSH_KEY` - Private SSH key for server access

### Environment Variables
- `PRODUCTION_ENV` - Base64 encoded .env file content
- `STAGING_ENV` - Base64 encoded staging .env file content

### Docker Registry (optional)
- `DOCKER_REGISTRY_URL` - Docker registry URL
- `DOCKER_REGISTRY_USERNAME` - Registry username
- `DOCKER_REGISTRY_PASSWORD` - Registry password

### Notifications
- `SLACK_WEBHOOK_URL` - Slack webhook for deployment notifications
- `DISCORD_WEBHOOK_URL` - Discord webhook for notifications

## Branch Strategy

- `main` - Production deployments
- `staging` - Staging deployments
- `develop` - Development branch
- Feature branches for new features