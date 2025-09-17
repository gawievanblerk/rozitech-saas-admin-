# Rozitech Website Deployment Guide

## Overview
This guide covers the deployment of the new Rozitech website with functional "Get Started" and "Learn More" buttons that lead to comprehensive landing pages for the Insurr platform.

## What's Been Implemented

### ✅ **New Website Pages**
1. **Homepage** (`/`) - Modern landing page with working CTA buttons
2. **Get Started** (`/get-started/`) - Subscription page with pricing tiers
3. **Learn More** (`/learn-more/`) - Detailed product information with Farmer Brown scenario

### ✅ **Key Features**
- **Functional Routing**: Buttons now properly navigate between pages
- **Professional Design**: Modern, responsive UI with gradient backgrounds
- **Pricing Tiers**: Starter (R299), Professional (R799), Enterprise (R1,999)
- **Interactive Elements**: Email signup, demo requests, contact forms
- **South African Focus**: POPIA compliance, local banking, ZA market specifics
- **Mobile Responsive**: Works perfectly on desktop and mobile devices

### ✅ **Technical Integration**
- Django templates integrated with existing project structure
- Nginx configuration updated for proper routing
- Docker production setup maintained
- Marketing app URLs and views updated

## Quick Deployment

### Option 1: Full Automated Deployment
```bash
# Deploy everything (recommended)
./deploy-website.sh

# Or step by step:
./deploy-website.sh build    # Build application
./deploy-website.sh deploy   # Full deployment
./deploy-website.sh test     # Test the deployment
```

### Option 2: Manual Deployment Steps
```bash
# 1. Build the application
docker build -f Dockerfile.production -t rozitech-saas:latest .

# 2. Stop existing services
docker-compose -f docker-compose.production.yml down

# 3. Start new services
docker-compose -f docker-compose.production.yml up -d

# 4. Run migrations
docker-compose -f docker-compose.production.yml exec web python manage.py migrate

# 5. Collect static files
docker-compose -f docker-compose.production.yml exec web python manage.py collectstatic --noinput
```

## File Structure

```
rozitech-saas-admin/
├── templates/marketing/          # New website templates
│   ├── index.html               # Homepage
│   ├── get-started.html         # Subscription/pricing page
│   └── learn-more.html          # Product information page
├── apps/marketing/
│   ├── views.py                 # Updated with new views
│   └── urls.py                  # Updated with new routes
├── nginx/conf.d/rozitech.conf   # Updated Nginx config
├── deploy-website.sh            # Deployment automation script
└── WEBSITE_DEPLOYMENT.md        # This file
```

## User Journey

1. **Homepage** (`/`) 
   - User sees modern landing page
   - "Get Started" and "Learn More" buttons visible
   
2. **Learn More** (`/learn-more/`)
   - User learns about Insurr platform features
   - Sees Farmer Brown scenario walkthrough
   - Reviews technical specifications
   - Understands South African market focus
   
3. **Get Started** (`/get-started/`)
   - User selects pricing tier
   - Initiates signup process via email
   - Can request demo or contact sales

## Testing the Deployment

### Automated Testing
```bash
# Test all pages
./deploy-website.sh test

# Manual curl tests
curl -I http://localhost/                # Should return 200
curl -I http://localhost/get-started/    # Should return 200
curl -I http://localhost/learn-more/     # Should return 200
```

### Browser Testing
1. Visit `http://rozitech.com/`
2. Click "Get Started" → Should go to pricing page
3. Click "Learn More" → Should go to product info page
4. Test on mobile device for responsiveness

## Environment Variables

Ensure these are set in your `.env` file:
```bash
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=rozitech.com,rozitech.co.za,www.rozitech.com
SECRET_KEY=your-secret-key
DB_PASSWORD=your-db-password
```

## Monitoring

### Check Service Status
```bash
./deploy-website.sh status
# or
docker-compose -f docker-compose.production.yml ps
```

### View Logs
```bash
./deploy-website.sh logs
# or
docker-compose -f docker-compose.production.yml logs -f
```

### Health Check
```bash
curl http://localhost/health/
# Should return: healthy
```

## SSL/HTTPS Setup (Production)

After initial deployment, set up SSL:

1. **Get SSL Certificate**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d rozitech.com -d www.rozitech.com
```

2. **Update Nginx Config**
```bash
# Uncomment SSL sections in nginx/conf.d/rozitech.conf
# Restart nginx
docker-compose -f docker-compose.production.yml restart nginx
```

## Troubleshooting

### Common Issues

**1. "Page not found" errors**
- Check Django URLs are properly configured
- Verify Nginx routing
- Ensure templates exist in correct location

**2. Static files not loading**
```bash
docker-compose -f docker-compose.production.yml exec web python manage.py collectstatic --noinput
```

**3. Database connection errors**
```bash
# Check database status
docker-compose -f docker-compose.production.yml logs postgres

# Run migrations
docker-compose -f docker-compose.production.yml exec web python manage.py migrate
```

**4. Container startup issues**
```bash
# Check all services
./deploy-website.sh status

# View detailed logs
./deploy-website.sh logs
```

### Performance Optimization

**1. Enable Gzip Compression**
- Already configured in Nginx

**2. Browser Caching**
- Static files cached for 30 days
- Media files cached for 7 days

**3. Database Optimization**
- PostgreSQL with connection pooling
- Redis for caching and sessions

## Contact and Support

**Email Integration:**
- All contact forms send to `hello@rozitech.com`
- Demo requests route to sales team
- Support requests handled via email

**Phone Support:**
- +27 11 123 4567
- Business hours: Monday-Friday 8AM-6PM SAST

## Analytics and Monitoring

Consider adding:
- Google Analytics for page views
- Hotjar for user behavior tracking
- New Relic for application performance
- Sentry for error tracking

## Next Steps

1. **Deploy to Production**: Run the deployment script on your production server
2. **DNS Configuration**: Point your domain to the server IP
3. **SSL Setup**: Configure HTTPS for secure connections
4. **Analytics**: Add tracking codes for user behavior analysis
5. **SEO**: Optimize meta tags and add structured data

## Security Considerations

- Admin panel restricted to specific IP addresses
- Rate limiting on login endpoints
- HTTPS enforcement in production
- POPIA compliance for data protection
- Secure headers configured in Nginx

---

**Ready to deploy? Run: `./deploy-website.sh`**