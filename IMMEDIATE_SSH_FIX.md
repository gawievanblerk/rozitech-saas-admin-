# 🚨 IMMEDIATE SSH Key Fix

## **The Problem**
Your GitHub Actions deployment is failing with:
```
Error loading key "(stdin)": error in libcrypto
```

This means the SSH key in your GitHub secrets is corrupted or incorrectly formatted.

## **Quick Fix Options**

### **Option 1: Generate New SSH Key (Recommended - 5 minutes)**

**Run this command:**
```bash
./generate-ssh-key.sh
```

This will:
- Generate a new, properly formatted SSH key
- Show you exactly what to copy to GitHub secrets
- Provide instructions for server setup

**Then:**
1. Copy the PRIVATE KEY output to GitHub Secret `XNEELO_SSH_KEY`
2. Add the PUBLIC KEY to your server's `~/.ssh/authorized_keys`

### **Option 2: Use Alternative Deployment (Immediate)**

**Trigger the backup deployment:**
1. Go to GitHub Actions in your repository
2. Find "Deploy Website (SSH Key Fix)" 
3. Click "Run workflow"
4. Choose "Use password authentication" if you have server password
5. Click "Run workflow"

### **Option 3: Manual File Upload (Fastest)**

**If SSH continues to fail, upload manually:**
1. Download files from `quick-deploy/` folder
2. Upload to your web server via FTP/cPanel:
   - `index.html` → replaces current homepage
   - `get-started.html` → new pricing page
   - `learn-more.html` → new product page

## **Check GitHub Secrets**

**Your repository should have these secrets:**
- `XNEELO_SSH_KEY` - SSH private key (the problematic one)
- `XNEELO_SERVER_HOST` - Server hostname/IP
- `XNEELO_SERVER_USER` - SSH username  
- `XNEELO_SERVER_PASSWORD` - Server password (optional, for fallback)

**To check/update:**
1. Go to: https://github.com/gawievanblerk/rozitech-saas-admin-/settings/secrets/actions
2. Verify all secrets exist
3. Update `XNEELO_SSH_KEY` with new key from Option 1

## **SSH Key Format Requirements**

**Private key MUST look like this:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
... (many lines of base64) ...
-----END OPENSSH PRIVATE KEY-----
```

**Common issues:**
- Missing header/footer lines
- Extra spaces or characters
- Windows line endings (CRLF instead of LF)
- Encrypted key without passphrase

## **Test SSH Key Locally**

**Before updating GitHub:**
```bash
# Test the key works
ssh -i ~/.ssh/github_deploy_key your-user@your-server "echo 'Test successful'"
```

## **Immediate Actions**

**Right now, do this:**

1. **Generate new key**: `./generate-ssh-key.sh`
2. **Update GitHub secret** with the new private key
3. **Add public key to server** 
4. **Trigger deployment** (push to main or manual workflow)

**Or for immediate results:**
1. **Use manual deployment** with password authentication
2. **Upload files manually** via FTP/cPanel

## **Files Ready for Manual Upload**

If all else fails, these files in `quick-deploy/` will fix your buttons immediately:
- `index.html` - Working homepage with functional buttons
- `get-started.html` - Complete pricing page
- `learn-more.html` - Product information page

**Upload these to your web server root and your buttons will work!**

---

**⏰ Time Estimates:**
- Generate new SSH key: 5 minutes
- Manual file upload: 2 minutes  
- GitHub Actions fix: 10 minutes

**Choose the option that works best for your current situation!**