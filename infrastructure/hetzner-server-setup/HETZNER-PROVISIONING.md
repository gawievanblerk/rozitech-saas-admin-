# Hetzner Server Provisioning for Rozitech SaaS Platform

## 🎯 Objective
Set up a cost-effective Hetzner Cloud server optimized for the Rozitech SaaS platform.

## 💰 Recommended Server Configuration

For starting out with good performance and room to grow:

### **CCX22 (Recommended)**
- **CPU:** 4 vCPU AMD EPYC
- **RAM:** 8 GB
- **SSD:** 80 GB NVMe
- **Traffic:** 20 TB
- **Cost:** €20.46/month
- **Perfect for:** 100-500 tenants

### **CCX12 (Budget Option)**
- **CPU:** 2 vCPU AMD EPYC  
- **RAM:** 4 GB
- **SSD:** 40 GB NVMe
- **Traffic:** 20 TB
- **Cost:** €10.23/month
- **Perfect for:** 50-100 tenants initially

## 🚀 Step-by-Step Server Creation

### Step 1: Access Hetzner Cloud Console

1. **Log in to Hetzner Cloud Console:**
   - Go to: https://console.hetzner.cloud/
   - Sign in with your Hetzner account

2. **Create a New Project:**
   - Click "New Project"
   - Name: `rozitech-saas-production`
   - Click "Create Project"

### Step 2: Create the Server

1. **Click "Add Server"**

2. **Choose Location:**
   - **Recommended:** Nuremberg (Germany) - EU data protection
   - **Alternative:** Ashburn (USA) - if targeting US market
   - **Note:** Nuremberg offers best price/performance

3. **Choose Image:**
   - **Operating System:** Ubuntu
   - **Version:** Ubuntu 22.04 LTS (most stable)

4. **Choose Server Type:**
   - **Category:** Dedicated vCPU
   - **Type:** CCX22 (recommended) or CCX12 (budget)

5. **Add SSH Key (Important!):**
   - Click "Add SSH key"
   - **Name:** `rozitech-admin-key`
   - **Public Key:** You'll need to generate this first

### Step 3: Generate SSH Key for Server Access

**On your local machine, run:**

```bash
# Generate SSH key for server management
ssh-keygen -t ed25519 -f ~/.ssh/rozitech-hetzner -C "admin@rozitech.com"

# Display the public key
cat ~/.ssh/rozitech-hetzner.pub
```

**Copy the output and paste it in Hetzner's SSH key field.**

### Step 4: Complete Server Configuration

1. **Volumes (Optional):**
   - Skip for now (can add later if needed)

2. **Networks:**
   - Leave default (can configure later)

3. **Load Balancers:**
   - Skip (not needed initially)

4. **Backup:**
   - **Enable automatic backups** (€2/month) - Recommended!

5. **Placement Groups:**
   - Skip (not needed for single server)

6. **Labels:**
   - Add labels for organization:
     - `project: rozitech-saas`
     - `environment: production`
     - `role: web-app`

7. **Cloud-init (User Data):**
   ```bash
   #cloud-config
   package_update: true
   package_upgrade: true
   
   packages:
     - curl
     - wget
     - git
     - htop
     - ufw
     - fail2ban
   
   runcmd:
     - ufw default deny incoming
     - ufw default allow outgoing
     - ufw allow ssh
     - ufw allow 80
     - ufw allow 443
     - ufw --force enable
     - systemctl enable fail2ban
     - systemctl start fail2ban
   
   final_message: "Rozitech SaaS server setup complete!"
   ```

8. **Server Name:**
   - Name: `rozitech-saas-prod-01`

9. **Click "Create & Buy Now"**

### Step 5: Initial Server Access

1. **Wait for server to be ready** (usually 1-2 minutes)

2. **Note the server IP address** from the Hetzner console

3. **Test SSH access:**
   ```bash
   ssh -i ~/.ssh/rozitech-hetzner root@YOUR_SERVER_IP
   ```

### Step 6: Basic Server Hardening

Once logged in to your server:

```bash
# Update system
apt update && apt upgrade -y

# Create a non-root user (optional but recommended)
adduser rozitech
usermod -aG sudo rozitech

# Copy SSH key to new user (optional)
mkdir -p /home/rozitech/.ssh
cp ~/.ssh/authorized_keys /home/rozitech/.ssh/
chown -R rozitech:rozitech /home/rozitech/.ssh
chmod 700 /home/rozitech/.ssh
chmod 600 /home/rozitech/.ssh/authorized_keys

# Configure SSH (more secure)
nano /etc/ssh/sshd_config
```

**SSH Configuration changes:**
```
PermitRootLogin yes  # Keep as yes for now (we'll need it for CI/CD)
PasswordAuthentication no
PubkeyAuthentication yes
```

```bash
# Restart SSH
systemctl restart sshd

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

## 🌐 Domain Configuration

### Step 7: Configure DNS for Your Domains

In your Hetzner DNS console or domain registrar:

#### **A Records:**
```
rozitech.com              → YOUR_SERVER_IP
www.rozitech.com          → YOUR_SERVER_IP
app.rozitech.com          → YOUR_SERVER_IP
admin.rozitech.com        → YOUR_SERVER_IP
rozitech.co.za            → YOUR_SERVER_IP
www.rozitech.co.za        → YOUR_SERVER_IP
```

#### **Wildcard for Tenants:**
```
*.rozitech.com            → YOUR_SERVER_IP
*.rozitech.co.za          → YOUR_SERVER_IP
```

#### **Mail Records (if using Hetzner for email):**
```
mail.rozitech.com         → YOUR_SERVER_IP
```

#### **MX Records:**
```
rozitech.com              → mail.rozitech.com (Priority: 10)
rozitech.co.za            → mail.rozitech.com (Priority: 10)
```

## 💾 Optional: Add Object Storage

For media files and backups:

1. **In Hetzner console, go to "Object Storage"**
2. **Click "Create Bucket"**
3. **Configuration:**
   - Name: `rozitech-saas-media`
   - Location: Same as your server
4. **Create API credentials:**
   - Go to "Access Keys"
   - Create new key pair
   - **Save these credentials** - you'll need them later!

## 🔧 Server Specifications Summary

After setup, your server will have:

- ✅ **Ubuntu 22.04 LTS** - Stable and secure
- ✅ **Docker & Docker Compose** - For containerized apps
- ✅ **Firewall configured** - Only necessary ports open
- ✅ **Fail2ban** - Protection against brute force
- ✅ **SSH key authentication** - Secure access
- ✅ **Automatic backups** - Daily snapshots
- ✅ **20TB traffic** - More than enough for growth

## 💰 Monthly Costs Breakdown

| Service | Cost | Purpose |
|---------|------|---------|
| CCX22 Server | €20.46 | Main application |
| Automatic Backups | €2.00 | Daily snapshots |
| Object Storage (100GB) | €4.00 | Media files |
| **Total** | **€26.46** | **~$29/month** |

## 🎯 What's Next?

Once your server is ready:

1. **Get the server IP address**
2. **Add the GitHub Actions SSH key** (from our previous step)
3. **Continue with the CI/CD setup**

---

## 📞 Need Help?

**Common Issues:**

### SSH Connection Refused
```bash
# Check if SSH service is running
ssh -v root@YOUR_SERVER_IP

# If port 22 is filtered, check firewall
ufw status
```

### Can't Access After Creation
- Wait 2-3 minutes for server to fully boot
- Check server status in Hetzner console
- Verify SSH key was added correctly

### Domain Not Resolving
- DNS changes can take up to 24 hours
- Test with: `dig rozitech.com`
- Verify A records are correct

---

**Let me know when you've created the server and I'll continue with the CI/CD setup!**