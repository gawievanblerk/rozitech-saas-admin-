# GitHub Actions Pipeline Fixes

## 🔧 **What Was Broken**

The original GitHub Actions pipeline had several critical issues:

1. **Wrong Deployment Target**: Deployed to port 8080 instead of the main website
2. **Test Container Only**: Used a simple Nginx test container, not the actual website
3. **No File Replacement**: Never actually replaced the live website files
4. **No Web Root Detection**: Didn't know where to put the website files
5. **Conflicting Workflows**: Multiple pipelines running simultaneously

## ✅ **What I Fixed**

### **1. Fixed Main Deployment Pipeline (`deploy-website.yml`)**
- **Smart Web Root Detection**: Automatically finds `/var/www/html`, `public_html`, or `/usr/share/nginx/html`
- **Actual File Deployment**: Replaces the live `index.html` with our functional version
- **Complete Page Deployment**: Deploys `get-started.html` and `learn-more.html`
- **Proper Permissions**: Sets correct file ownership and permissions
- **Web Server Reload**: Automatically reloads Nginx or Apache after deployment
- **Backup Creation**: Backs up existing files before replacement
- **Comprehensive Verification**: Checks file existence, content, and HTTP responses

### **2. Added Manual Deployment Workflow (`manual-deploy.yml`)**
- **Manual Trigger**: Deploy on-demand from GitHub Actions
- **Deployment Types**: Choose between full, quick-fix, or files-only deployment
- **Backup Options**: Option to skip backup for emergency deployments
- **Real-time Testing**: Immediate verification after deployment

### **3. Added Rollback Workflow (`rollback.yml`)**
- **Emergency Recovery**: Quickly restore previous version
- **Backup Selection**: Choose specific backup or use latest
- **Automatic Verification**: Confirms rollback success

### **4. Disabled Conflicting Pipeline**
- Renamed `deploy-simple.yml` to `deploy-simple.yml.disabled`
- Prevents interference with main deployment

## 🚀 **How to Use the Fixed Pipeline**

### **Automatic Deployment (Recommended)**
1. Push changes to `main` branch
2. GitHub Actions automatically triggers deployment
3. Website updates within 2-3 minutes
4. Check GitHub Actions tab for deployment status

### **Manual Deployment (For immediate fixes)**
1. Go to GitHub Actions → "Manual Website Deployment"
2. Click "Run workflow"
3. Choose deployment type:
   - **Full**: Deploy all pages (recommended)
   - **Quick-fix**: Only update homepage
   - **Files-only**: Deploy without Docker/complex setup
4. Click "Run workflow"

### **Emergency Rollback**
1. Go to GitHub Actions → "Rollback Website Deployment"
2. Click "Run workflow"
3. Leave backup timestamp blank for latest backup
4. Click "Run workflow"

## 📊 **Pipeline Status Monitoring**

### **Check Deployment Status**
1. Go to your repository: `https://github.com/gawievanblerk/rozitech-saas-admin-/actions`
2. Look for "Deploy Rozitech Website with Functional Buttons"
3. Click on the latest run to see detailed logs

### **Verify Successful Deployment**
Run our verification script:
```bash
./verify-live-deployment.sh
```

Or check manually:
- Visit https://rozitech.com/
- Click "Get Started" → Should go to pricing page
- Click "Learn More" → Should go to product page

## 🔍 **What the Pipeline Does Now**

### **Step 1: Preparation**
- Creates deployment package with website files
- Uploads to server `/tmp/` directory

### **Step 2: Deployment**
- Finds correct web root directory automatically
- Backs up existing `index.html` with timestamp
- Extracts and deploys new website files
- Sets proper file permissions for web server

### **Step 3: Web Server Management**
- Tests web server configuration
- Reloads Nginx or Apache gracefully
- Ensures no downtime during deployment

### **Step 4: Verification**
- Checks that files exist in correct locations
- Verifies button links are properly configured
- Tests HTTP response codes
- Confirms content is updated

## 🛠️ **Troubleshooting**

### **If Deployment Fails**
1. Check GitHub Actions logs for specific error
2. Use manual deployment with different options
3. If needed, use rollback workflow to restore previous version

### **If Buttons Still Don't Work**
1. Check if deployment actually ran (GitHub Actions tab)
2. Run verification script: `./verify-live-deployment.sh`
3. Try manual deployment with "quick-fix" option
4. Check web server logs on your server

### **Common Issues & Solutions**

**"Could not find web root directory"**
- Server uses non-standard directory structure
- Manually specify in pipeline or contact hosting provider

**"Permission denied"**
- Server permissions need adjustment
- May need to run deployment with different user

**"Web server reload failed"**
- Check if Nginx/Apache is running
- Verify configuration syntax

## 📞 **Getting Help**

1. **Check Logs**: Always check GitHub Actions logs first
2. **Run Verification**: Use `./verify-live-deployment.sh`
3. **Manual Override**: Use manual deployment workflow
4. **Emergency Rollback**: Use rollback workflow if needed

## 🎯 **Expected Results**

After successful deployment:
- ✅ https://rozitech.com/ loads with modern design
- ✅ "Get Started" button goes to https://rozitech.com/get-started.html
- ✅ "Learn More" button goes to https://rozitech.com/learn-more.html
- ✅ All pages are mobile responsive
- ✅ Contact forms work with hello@rozitech.com
- ✅ Pricing shows R299, R799, R1,999 tiers
- ✅ Farmer Brown scenario visible on Learn More page

The pipeline is now **production-ready** and will properly update your live website!