# Xneelo Cloud Server Setup for Rozitech SaaS Platform

## 🇿🇦 Xneelo Cloud Console Guide

Xneelo is perfect for the South African market! Let me guide you through setting up your server.

## 💰 Recommended Xneelo Configuration

### **Virtual Server (Recommended)**
- **Package:** Business Cloud Server
- **CPU:** 4 vCPU 
- **RAM:** 8 GB
- **SSD Storage:** 100 GB
- **Bandwidth:** Unlimited (local SA traffic)
- **Cost:** ~R800-1200/month ($45-70)
- **Perfect for:** 100-500 tenants

### **Budget Option**
- **Package:** Startup Cloud Server  
- **CPU:** 2 vCPU
- **RAM:** 4 GB
- **SSD Storage:** 50 GB
- **Cost:** ~R400-600/month ($25-35)
- **Perfect for:** 50-100 tenants initially

## 🚀 Step-by-Step Xneelo Server Creation

### Step 1: Navigate to Cloud Servers

1. **Log into Xneelo Console:** https://console.xneelo.co.za/
2. **Go to:** Cloud Servers → Virtual Servers
3. **Click:** "Order New Server"

### Step 2: Choose Server Configuration

1. **Server Type:** Ubuntu Server
2. **Version:** Ubuntu 22.04 LTS (most stable)
3. **Data Center:** 
   - **Johannesburg** (best for SA customers)
   - **Cape Town** (alternative)
4. **Server Size:** Business Cloud Server (8GB RAM recommended)

### Step 3: Configure Server Details

1. **Server Name:** `rozitech-saas-prod-01`
2. **Root Password:** Create a strong password (save it securely!)
3. **SSH Key:** We'll add this after creation
4. **Backup:** Enable daily backups (+R50/month)

### Step 4: Additional Services

1. **Load Balancer:** Skip for now (can add later)
2. **Firewall:** Use default (we'll configure UFW)
3. **Monitoring:** Basic monitoring included
4. **SSL Certificates:** We'll use Let's Encrypt (free)

### Step 5: Complete Order

1. **Review configuration**
2. **Accept terms**
3. **Submit order**
4. **Wait for server provisioning** (usually 5-15 minutes)

## 🔧 Initial Server Access

Once your server is ready:

### Option 1: SSH Access (Recommended)

1. **Get server IP** from Xneelo console
2. **Generate SSH key** on your local machine:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/rozitech-xneelo -C "admin@rozitech.com"
   ```
3. **Connect to server:**
   ```bash
   ssh root@YOUR_SERVER_IP
   ```
4. **Add your SSH key** to the server:
   ```bash
   mkdir -p ~/.ssh
   echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

### Option 2: Xneelo Console Access

Use the web console in your Xneelo dashboard if SSH isn't working initially.

## 🚀 Run the Xneelo Setup Script

Once logged into your server:

```bash
# Download and run the Xneelo-optimized setup script
curl -fsSL https://raw.githubusercontent.com/your-username/rozitech-saas-admin/main/infrastructure/xneelo-server-setup/XNEELO-PROVISIONING.md | bash
```

Or manually copy the script and run it.

## 🌐 DNS Configuration for Xneelo

### If DNS is managed by Xneelo:

1. **Go to:** Domain Management → DNS Management
2. **Add these A records:**

| Record Type | Name | Value | TTL |
|-------------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 300 |
| A | www | YOUR_SERVER_IP | 300 |
| A | app | YOUR_SERVER_IP | 300 |
| A | admin | YOUR_SERVER_IP | 300 |
| A | * | YOUR_SERVER_IP | 300 |

### For rozitech.co.za (repeat the same pattern):

| Record Type | Name | Value | TTL |
|-------------|------|-------|-----|
| A | @ | YOUR_SERVER_IP | 300 |
| A | www | YOUR_SERVER_IP | 300 |
| A | * | YOUR_SERVER_IP | 300 |

### Mail Server (if hosting email on same server):

| Record Type | Name | Value | TTL |
|-------------|------|-------|-----|
| A | mail | YOUR_SERVER_IP | 300 |
| MX | @ | mail.rozitech.com | 300 |

## 🇿🇦 South African Advantages with Xneelo

### **Legal Compliance:**
- ✅ **POPI Act compliance** - SA data stays in SA
- ✅ **Local support** - SA business hours
- ✅ **SARS compliance** - local invoicing in ZAR

### **Performance Benefits:**
- ✅ **Low latency** for SA customers
- ✅ **Free local bandwidth** - no international charges
- ✅ **Local CDN** integration available

### **Business Benefits:**
- ✅ **ZAR pricing** - no forex exposure
- ✅ **Local payment methods** - EFT, debit orders
- ✅ **B-BBEE** compliance if applicable

## 💰 Estimated Monthly Costs (ZAR)

| Service | Cost (ZAR) | Cost (USD) |
|---------|------------|------------|
| Business Cloud Server | R1000 | $55 |
| Daily Backups | R50 | $3 |
| Domain renewals | R400/year | $22/year |
| **Total Monthly** | **R1050** | **$58** |

## 🔧 Xneelo-Specific Optimizations

The setup script includes:

### **South African Optimizations:**
- 🇿🇦 Johannesburg timezone
- 🏦 Banking integration tools (PayFast, Yoco ready)
- 📊 Local monitoring and logging
- 🌐 Network optimized for SA internet conditions

### **Performance Optimizations:**
- 💾 4GB swap file (good for 8GB RAM)
- 🔧 System limits increased for SaaS workload
- 📈 BBR congestion control for better network performance
- 🚀 Docker optimized for Ubuntu 22.04

### **Security Hardening:**
- 🔒 UFW firewall configured
- 🛡️ Fail2ban with SA-specific settings
- 🔐 SSH key authentication
- 📝 Comprehensive logging

## 🎯 What's Next?

After server setup is complete:

1. **✅ Note your server IP address**
2. **✅ Verify DNS propagation** (can take up to 24 hours)
3. **✅ Test SSH access**
4. **✅ Continue with GitHub CI/CD setup**

## 📞 Xneelo Support

If you encounter issues:
- **Support:** support@xneelo.co.za
- **Phone:** 087 805 0000
- **Live Chat:** Available in console
- **Knowledge Base:** https://help.xneelo.co.za

## 🚨 Common Xneelo Issues & Solutions

### **SSH Connection Issues:**
```bash
# If SSH is refused, try:
ssh -v root@YOUR_SERVER_IP

# Check if server is fully booted
ping YOUR_SERVER_IP
```

### **DNS Not Propagating:**
```bash
# Check DNS from SA perspective
dig @8.8.8.8 rozitech.com
nslookup rozitech.com 8.8.8.8
```

### **Firewall Blocking Access:**
```bash
# Temporarily disable UFW if needed
sudo ufw disable

# Re-enable with proper rules
sudo ufw enable
```

---

## 📋 Checklist Before Continuing

- [ ] Xneelo server created and running
- [ ] SSH access working
- [ ] Setup script completed successfully
- [ ] DNS records configured
- [ ] Server IP address noted
- [ ] Firewall and security configured

**Once complete, provide me with your server IP and we'll continue with the CI/CD setup!**