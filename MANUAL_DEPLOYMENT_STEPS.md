# Manual Deployment Steps - Rozitech Website

## Quick Fix: Update Live Website Buttons

Since the GitHub Actions deployment completed but the live website hasn't updated, here are manual steps to get your buttons working immediately.

### Option 1: Direct Server Access (Recommended)

**Step 1: Connect to your server**
```bash
ssh your-username@your-server-ip
# Replace with your actual server credentials
```

**Step 2: Navigate to your website directory**
```bash
cd /opt/rozitech-saas
# or wherever your website files are located
```

**Step 3: Update the website files**
```bash
# Pull latest changes from GitHub
git pull origin main

# Or if you need to clone fresh:
# git clone https://github.com/gawievanblerk/rozitech-saas-admin-.git

# Copy our new templates to the active directory
cp templates/marketing/*.html /var/www/html/ 2>/dev/null || echo "Template copy skipped"
```

**Step 4: Restart web services**
```bash
# Restart nginx
sudo systemctl restart nginx

# If using Apache
sudo systemctl restart apache2

# If using Docker
docker-compose restart
```

### Option 2: Quick JavaScript Fix (Immediate)

If you can't access the server right now, you can make a quick fix by updating the existing JavaScript on your live site.

**Current buttons (on live site):**
```html
<button class="btn-primary" onclick="scrollToSection('pricing')">Get Started</button>
<button class="btn-secondary" onclick="scrollToSection('products')">Learn More</button>
```

**Quick fix: Update the JavaScript function**

Replace the current `scrollToSection` function with:
```javascript
function scrollToSection(section) {
    if (section === 'pricing') {
        window.location.href = '/get-started.html';
    } else if (section === 'products') {
        window.location.href = '/learn-more.html';
    }
}
```

Then upload our landing pages:
- Upload `website_pages/get-started.html` to your web server as `/get-started.html`
- Upload `website_pages/learn-more.html` to your web server as `/learn-more.html`

### Option 3: Direct File Upload via FTP/cPanel

**Files to upload:**
1. `website_pages/index-example.html` → `/index.html` (replace current homepage)
2. `website_pages/get-started.html` → `/get-started.html`
3. `website_pages/learn-more.html` → `/learn-more.html`

**Directory structure after upload:**
```
/var/www/html/
├── index.html          (updated homepage with working buttons)
├── get-started.html    (pricing page)
└── learn-more.html     (product info page)
```

### Testing After Update

Run our verification script:
```bash
./verify-live-deployment.sh
```

Or manually test:
1. Visit https://rozitech.com/
2. Click "Get Started" → Should go to https://rozitech.com/get-started.html
3. Click "Learn More" → Should go to https://rozitech.com/learn-more.html

### Common Server Locations

**Nginx:**
- Config: `/etc/nginx/sites-available/default`
- Web root: `/var/www/html/`

**Apache:**
- Config: `/etc/apache2/sites-available/000-default.conf`
- Web root: `/var/www/html/`

**cPanel/Shared Hosting:**
- Web root: `public_html/`

### Files Ready for Upload

I've prepared these files in your project:
- `website_pages/index-example.html` - Updated homepage
- `website_pages/get-started.html` - Pricing/signup page
- `website_pages/learn-more.html` - Product information page

All files are standalone HTML with embedded CSS and JavaScript - no external dependencies needed!

### Next Steps

1. Choose the option that works best for your setup
2. Test the buttons after implementation
3. Let me know if you need help with any specific step

**Need help with server access?** 
- Check your hosting provider's documentation
- Look for SSH access or File Manager in your control panel
- If using shared hosting, use the File Manager or FTP