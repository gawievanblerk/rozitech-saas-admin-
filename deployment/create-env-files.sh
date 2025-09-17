#!/bin/bash

# Helper script to create environment files from templates

echo "Creating production environment file..."
cp secrets/.env.production.template secrets/.env.production

echo "Creating staging environment file..."
cp secrets/.env.staging.template secrets/.env.staging

echo ""
echo "📝 Next steps:"
echo "1. Edit secrets/.env.production with your actual production values"
echo "2. Edit secrets/.env.staging with your actual staging values"
echo "3. Encode the files for GitHub secrets:"
echo ""
echo "   # Production environment (base64)"
echo "   base64 -i secrets/.env.production"
echo ""
echo "   # Staging environment (base64)"
echo "   base64 -i secrets/.env.staging"
echo ""
echo "4. Add the base64 output to GitHub secrets as:"
echo "   - PRODUCTION_ENV"
echo "   - STAGING_ENV"
