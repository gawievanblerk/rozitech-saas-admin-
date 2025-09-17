# Fix SSH Key Issue in GitHub Actions

## 🔍 **The Problem**
```
Error loading key "(stdin)": error in libcrypto
```

This error means the SSH key in your GitHub secrets is corrupted, has wrong format, or encoding issues.

## 🛠️ **Solution Options**

### **Option 1: Check Current SSH Key Format (Quick Fix)**

**Step 1: Check your current SSH key**
```bash
# Check if key exists and format
cat ~/.ssh/id_rsa
# or
cat ~/.ssh/id_ed25519
```

**Expected format should be:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn
... (base64 content) ...
-----END OPENSSH PRIVATE KEY-----
```

**Step 2: Update GitHub Secret**
1. Go to your repository: https://github.com/gawievanblerk/rozitech-saas-admin-
2. Settings → Secrets and variables → Actions
3. Find `XNEELO_SSH_KEY` secret
4. Update with the correctly formatted key (entire content including headers)

### **Option 2: Generate New SSH Key (Recommended)**

**Step 1: Generate new SSH key**
```bash
# Generate new ED25519 key (more secure)
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy_key -N ""

# Or RSA if ED25519 not supported
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_deploy_key -N ""
```

**Step 2: Copy the private key**
```bash
# Copy private key content (including headers/footers)
cat ~/.ssh/github_deploy_key

# Copy public key for server
cat ~/.ssh/github_deploy_key.pub
```

**Step 3: Add to your server**
```bash
# SSH to your server
ssh your-user@your-server

# Add public key to authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGbr..." >> ~/.ssh/authorized_keys
# (replace with your actual public key)

# Set proper permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

**Step 4: Update GitHub Secrets**
1. Repository → Settings → Secrets and variables → Actions
2. Update `XNEELO_SSH_KEY` with the **private key** content (from `cat ~/.ssh/github_deploy_key`)
3. Make sure to include the entire key:
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   ... entire key content ...
   -----END OPENSSH PRIVATE KEY-----
   ```

### **Option 3: Fix Line Ending Issues**

If your SSH key has Windows line endings:

```bash
# Fix line endings (if on Mac/Linux)
tr -d '\r' < your_ssh_key > fixed_ssh_key

# Or use dos2unix if available
dos2unix your_ssh_key
```

### **Option 4: Test SSH Key Locally First**

Before updating GitHub secrets, test locally:

```bash
# Test SSH connection
ssh -i ~/.ssh/github_deploy_key -o ConnectTimeout=10 your-user@your-server "echo 'SSH test successful'"
```

## 🔧 **Quick Debug Steps**

### **Check Current Secret Format**
The SSH key should:
- Start with `-----BEGIN OPENSSH PRIVATE KEY-----` or `-----BEGIN RSA PRIVATE KEY-----`
- End with `-----END OPENSSH PRIVATE KEY-----` or `-----END RSA PRIVATE KEY-----`
- Have no extra spaces or characters
- Use Unix line endings (LF, not CRLF)

### **Common Issues & Fixes**

**Issue: "Invalid key format"**
- Solution: Regenerate key with correct algorithm

**Issue: "Permission denied"**
- Solution: Ensure public key is in server's `~/.ssh/authorized_keys`

**Issue: "Connection timeout"**
- Solution: Check server host/port in GitHub secrets

## 🚀 **Alternative: Use Username/Password (Temporary)**

If SSH continues to fail, temporarily use password authentication:

**Update workflow to use password:**
```yaml
- name: Deploy via Password
  uses: appleboy/ssh-action@v0.1.5
  with:
    host: ${{ secrets.XNEELO_SERVER_HOST }}
    username: ${{ secrets.XNEELO_SERVER_USER }}
    password: ${{ secrets.XNEELO_SERVER_PASSWORD }}
    script: |
      echo "SSH connection successful"
      # deployment commands here
```

**Add password secret:**
1. Repository → Settings → Secrets → Actions
2. Add `XNEELO_SERVER_PASSWORD` with your server password

## 📋 **GitHub Secrets Checklist**

Ensure these secrets exist and are correct:
- `XNEELO_SSH_KEY` - Private SSH key (entire content with headers)
- `XNEELO_SERVER_HOST` - Server hostname or IP
- `XNEELO_SERVER_USER` - SSH username

## 🧪 **Test the Fix**

After updating the SSH key:

1. **Trigger deployment**: Push to main branch or use manual workflow
2. **Check logs**: GitHub Actions should show successful SSH connection
3. **Verify deployment**: Run `./verify-live-deployment.sh`

## 📞 **Need Help?**

**If you're still having issues:**
1. Share the first few lines of your SSH key (not the full key!)
2. Check your server's SSH configuration
3. Verify the server allows key-based authentication
4. Consider using the password-based alternative temporarily

## 🔒 **Security Notes**

- Never share your private SSH key
- Use strong, unique keys for deployment
- Consider using deploy keys instead of personal SSH keys
- Regularly rotate deployment keys