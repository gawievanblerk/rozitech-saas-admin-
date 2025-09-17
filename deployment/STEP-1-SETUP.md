# Step 1: GitHub Repository and Secrets Setup

## 🎯 Objective
Set up your GitHub repository with proper structure and configure all necessary secrets for secure CI/CD deployment.

## 📋 Prerequisites
- GitHub repository for your Rozitech SaaS project
- Access to your Hetzner server
- Basic terminal/command line knowledge

## 🚀 Instructions

### 1.1 Create GitHub Repository (if not already done)

1. Go to GitHub and create a new repository named `rozitech-saas-admin`
2. Make it **private** (recommended for production SaaS)
3. Initialize with README if starting fresh

### 1.2 Set Up Local Repository Structure

```bash
# Clone your repository (if not already done)
git clone https://github.com/your-username/rozitech-saas-admin.git
cd rozitech-saas-admin

# Copy your current project files into the repository
# (if you haven't already done this)
```

### 1.3 Run the Secrets Setup Script

```bash
# Make the script executable
chmod +x deployment/setup-secrets.sh

# Run the setup script
./deployment/setup-secrets.sh
```

The script will:
- Generate an SSH key pair for deployment
- Create environment file templates
- Generate secure passwords and secret keys
- Create a GitHub secrets configuration guide

### 1.4 Add SSH Key to Your Hetzner Server

1. **Copy the public key** (displayed by the script)
2. **SSH into your Hetzner server:**
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
3. **Add the public key to authorized_keys:**
   ```bash
   echo 'PASTE_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

### 1.5 Create Environment Files

```bash
# Run the helper script to create environment files
./deployment/create-env-files.sh

# Edit the production environment file
nano deployment/secrets/.env.production

# Edit the staging environment file  
nano deployment/secrets/.env.staging
```

**Important:** Fill in all the `REPLACE_WITH_*` placeholders with your actual values:
- Email server credentials
- Payment gateway keys (Stripe, PayFast, Yoco)
- Hetzner Object Storage credentials
- Sentry DSN
- Google Analytics ID

### 1.6 Configure GitHub Repository Secrets

1. **Go to your GitHub repository**
2. **Navigate to:** Settings → Secrets and variables → Actions
3. **Click "New repository secret"**
4. **Add these secrets one by one:**

#### Required Secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `HETZNER_SERVER_HOST` | Your server IP | Hetzner server IP address |
| `HETZNER_SERVER_USER` | `root` | SSH username |
| `HETZNER_SSH_KEY` | Content of `secrets/github-deploy-key` | Private SSH key (entire file content) |
| `PRODUCTION_ENV` | Base64 of `.env.production` | Production environment variables |
| `STAGING_ENV` | Base64 of `.env.staging` | Staging environment variables |

#### To get Base64 encoded environment files:

```bash
# For production
base64 -i deployment/secrets/.env.production

# For staging  
base64 -i deployment/secrets/.env.staging
```

Copy the base64 output and paste it as the secret value.

#### Optional Secrets (for notifications):

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `SLACK_WEBHOOK_URL` | Your Slack webhook | Deployment notifications |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook | Alternative notifications |

### 1.7 Test SSH Connection

**Test the GitHub Actions SSH access:**

```bash
# From your local machine, test SSH with the generated key
ssh -i deployment/secrets/github-deploy-key root@YOUR_SERVER_IP

# If successful, you should be able to log in without password
```

### 1.8 Commit Initial Setup (without secrets)

```bash
# Add files to git (secrets directory is already in .gitignore)
git add .
git commit -m "Initial CI/CD setup and repository structure"
git push origin main
```

## ✅ Verification Checklist

Before proceeding to Step 2, verify:

- [ ] GitHub repository is created and accessible
- [ ] SSH key is generated and added to Hetzner server
- [ ] Environment files are created and filled with real values
- [ ] All GitHub secrets are configured correctly
- [ ] SSH connection test is successful
- [ ] Repository structure is pushed to GitHub
- [ ] No sensitive files are committed to git

## 🔧 Troubleshooting

### SSH Connection Issues
```bash
# Check SSH key permissions
chmod 600 deployment/secrets/github-deploy-key
chmod 644 deployment/secrets/github-deploy-key.pub

# Test SSH with verbose output
ssh -v -i deployment/secrets/github-deploy-key root@YOUR_SERVER_IP
```

### Base64 Encoding Issues
```bash
# On macOS/Linux
base64 -i deployment/secrets/.env.production

# On some Linux systems
base64 deployment/secrets/.env.production

# Manual check - decode to verify
echo "BASE64_STRING" | base64 -d
```

### GitHub Secrets Not Working
- Ensure secret names are exactly as specified (case-sensitive)
- Verify base64 encoding doesn't have extra newlines
- Check that SSH key includes both header and footer lines

## 📝 Security Notes

- **Never commit** the `deployment/secrets/` directory
- **Rotate secrets** regularly (every 90 days recommended)
- **Use strong passwords** for all services
- **Monitor** GitHub Actions logs for any credential exposure
- **Backup** your environment files securely

## 🎯 What's Next?

Once Step 1 is complete, you'll be ready for:
- **Step 2:** Create Docker build configuration
- **Step 3:** Configure GitHub Actions workflow
- **Step 4:** Set up deployment scripts on server

---

## 📞 Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are met
3. Ensure your Hetzner server is accessible
4. Double-check GitHub secrets configuration

**Confirm Step 1 is complete before proceeding to Step 2!**