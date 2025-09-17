#!/bin/bash

# Generate SSH Key for GitHub Actions Deployment
# This script creates a properly formatted SSH key for your deployment pipeline

echo "🔑 SSH Key Generator for GitHub Actions"
echo "======================================"

# Check if ssh-keygen is available
if ! command -v ssh-keygen &> /dev/null; then
    echo "❌ ssh-keygen not found. Please install OpenSSH client."
    exit 1
fi

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Key file path
KEY_FILE="$HOME/.ssh/github_deploy_key"

# Remove existing key if it exists
if [ -f "$KEY_FILE" ]; then
    echo "⚠️  Existing key found. Creating backup..."
    mv "$KEY_FILE" "${KEY_FILE}.backup.$(date +%Y%m%d-%H%M%S)"
    mv "${KEY_FILE}.pub" "${KEY_FILE}.pub.backup.$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
fi

echo ""
echo "🔧 Generating new SSH key..."

# Generate ED25519 key (modern and secure)
ssh-keygen -t ed25519 -f "$KEY_FILE" -N "" -C "github-actions-deploy-$(date +%Y%m%d)"

if [ $? -eq 0 ]; then
    echo "✅ SSH key generated successfully!"
else
    echo "❌ Failed to generate SSH key"
    exit 1
fi

echo ""
echo "📋 Your SSH Keys:"
echo "=================="

echo ""
echo "🔒 PRIVATE KEY (for GitHub Secret XNEELO_SSH_KEY):"
echo "---------------------------------------------------"
echo "Copy this ENTIRE content to your GitHub secret:"
echo ""
cat "$KEY_FILE"
echo ""

echo "🔓 PUBLIC KEY (for your server ~/.ssh/authorized_keys):"
echo "------------------------------------------------------"
echo "Add this line to your server's ~/.ssh/authorized_keys file:"
echo ""
cat "${KEY_FILE}.pub"
echo ""

# Create instructions file
INSTRUCTIONS_FILE="$HOME/.ssh/github_deploy_instructions.txt"
cat > "$INSTRUCTIONS_FILE" << EOF
SSH Key Setup Instructions
==========================

Generated: $(date)

STEP 1: Add Private Key to GitHub Secrets
------------------------------------------
1. Go to: https://github.com/gawievanblerk/rozitech-saas-admin-/settings/secrets/actions
2. Find or create secret: XNEELO_SSH_KEY
3. Copy the ENTIRE private key content (including headers):

$(cat "$KEY_FILE")

STEP 2: Add Public Key to Your Server
--------------------------------------
1. SSH to your server: ssh your-user@your-server
2. Add this line to ~/.ssh/authorized_keys:

$(cat "${KEY_FILE}.pub")

3. Set proper permissions:
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh

STEP 3: Test the Connection
---------------------------
Test locally first:
ssh -i $KEY_FILE your-user@your-server "echo 'SSH test successful'"

STEP 4: Trigger GitHub Actions
-------------------------------
After updating the secret, push to main branch or use manual workflow.

Security Notes:
- Never share the private key
- Keep the private key secure
- The public key can be shared safely
- Consider rotating keys regularly
EOF

echo "📄 Instructions saved to: $INSTRUCTIONS_FILE"
echo ""

echo "🚀 Next Steps:"
echo "=============="
echo "1. Copy the PRIVATE KEY above to GitHub Secret: XNEELO_SSH_KEY"
echo "2. Add the PUBLIC KEY to your server's ~/.ssh/authorized_keys"
echo "3. Test deployment with GitHub Actions"
echo ""

echo "🧪 Test SSH Connection:"
echo "======================="
echo "Run this command to test the key works:"
echo "ssh -i $KEY_FILE your-user@your-server \"echo 'SSH test successful'\""
echo ""

echo "📞 If you need help:"
echo "===================="
echo "- Check the generated instructions file: $INSTRUCTIONS_FILE"
echo "- Verify your server allows key-based authentication"
echo "- Ensure proper file permissions on server"
echo ""

echo "✅ SSH key generation completed!"