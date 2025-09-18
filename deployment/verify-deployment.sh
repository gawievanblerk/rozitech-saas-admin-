#!/bin/bash

# Script to verify deployment setup and GitHub secrets
# Tests SSH connection and deployment configuration

echo "Deployment Verification Script"
echo "=============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in GitHub Actions
if [ -n "$GITHUB_ACTIONS" ]; then
    echo "Running in GitHub Actions environment"
    IS_GITHUB_ACTIONS=true
else
    echo "Running locally"
    IS_GITHUB_ACTIONS=false
fi

# Function to test SSH connection
test_ssh_connection() {
    local host=$1
    local user=$2
    local port=${3:-22}
    local key_file=$4
    
    echo -e "${YELLOW}Testing SSH connection to $user@$host:$port...${NC}"
    
    if [ -n "$key_file" ] && [ -f "$key_file" ]; then
        ssh_cmd="ssh -i $key_file -p $port -o StrictHostKeyChecking=no -o ConnectTimeout=10"
    else
        ssh_cmd="ssh -p $port -o StrictHostKeyChecking=no -o ConnectTimeout=10"
    fi
    
    if $ssh_cmd $user@$host "echo 'SSH connection successful'" 2>/dev/null; then
        echo -e "${GREEN}✓ SSH connection successful${NC}"
        return 0
    else
        echo -e "${RED}✗ SSH connection failed${NC}"
        return 1
    fi
}

# Function to verify GitHub secrets format
verify_github_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo -e "${YELLOW}Verifying $secret_name...${NC}"
    
    if [ -z "$secret_value" ]; then
        echo -e "${RED}✗ $secret_name is not set${NC}"
        return 1
    fi
    
    # Check for common issues
    if echo "$secret_value" | grep -q $'\r'; then
        echo -e "${RED}✗ $secret_name contains carriage returns${NC}"
        return 1
    fi
    
    case $secret_name in
        SSH_PRIVATE_KEY|XNEELO_SSH_KEY)
            if echo "$secret_value" | grep -q "BEGIN.*PRIVATE KEY"; then
                echo -e "${GREEN}✓ $secret_name has valid private key header${NC}"
                if echo "$secret_value" | grep -q "END.*PRIVATE KEY"; then
                    echo -e "${GREEN}✓ $secret_name has valid private key footer${NC}"
                else
                    echo -e "${RED}✗ $secret_name missing private key footer${NC}"
                    return 1
                fi
            else
                echo -e "${RED}✗ $secret_name doesn't appear to be a valid private key${NC}"
                return 1
            fi
            ;;
        SSH_KNOWN_HOSTS)
            if echo "$secret_value" | grep -q "ssh-rsa\|ssh-ed25519\|ecdsa-sha2"; then
                echo -e "${GREEN}✓ $secret_name has valid host key format${NC}"
            else
                echo -e "${RED}✗ $secret_name doesn't appear to be valid known_hosts${NC}"
                return 1
            fi
            ;;
        SSH_HOST|XNEELO_SERVER_HOST)
            echo -e "${GREEN}✓ $secret_name is set${NC}"
            ;;
        SSH_USERNAME|XNEELO_SERVER_USER)
            echo -e "${GREEN}✓ $secret_name is set${NC}"
            ;;
        SSH_PORT)
            if [[ "$secret_value" =~ ^[0-9]+$ ]]; then
                echo -e "${GREEN}✓ $secret_name is a valid port number${NC}"
            else
                echo -e "${RED}✗ $secret_name is not a valid port number${NC}"
                return 1
            fi
            ;;
    esac
    
    return 0
}

# Main verification
echo "Starting deployment verification..."
echo ""

if [ "$IS_GITHUB_ACTIONS" = true ]; then
    # Verify GitHub secrets
    echo "Verifying GitHub Secrets..."
    echo "=========================="
    
    # Check for old secret names (XNEELO_*)
    if [ -n "$XNEELO_SERVER_HOST" ] || [ -n "$XNEELO_SERVER_USER" ] || [ -n "$XNEELO_SSH_KEY" ]; then
        echo -e "${YELLOW}⚠ Found old XNEELO_* secrets. Consider migrating to new names:${NC}"
        echo "  XNEELO_SERVER_HOST → SSH_HOST"
        echo "  XNEELO_SERVER_USER → SSH_USERNAME"
        echo "  XNEELO_SSH_KEY → SSH_PRIVATE_KEY"
        echo ""
    fi
    
    # Verify secrets (try both old and new names)
    HOST="${SSH_HOST:-$XNEELO_SERVER_HOST}"
    USERNAME="${SSH_USERNAME:-$XNEELO_SERVER_USER}"
    PRIVATE_KEY="${SSH_PRIVATE_KEY:-$XNEELO_SSH_KEY}"
    PORT="${SSH_PORT:-22}"
    
    verify_github_secret "SSH_HOST" "$HOST"
    verify_github_secret "SSH_USERNAME" "$USERNAME"
    verify_github_secret "SSH_PRIVATE_KEY" "$PRIVATE_KEY"
    verify_github_secret "SSH_PORT" "$PORT"
    
    if [ -n "$SSH_KNOWN_HOSTS" ]; then
        verify_github_secret "SSH_KNOWN_HOSTS" "$SSH_KNOWN_HOSTS"
    else
        echo -e "${YELLOW}⚠ SSH_KNOWN_HOSTS not set (optional but recommended)${NC}"
    fi
    
    echo ""
    echo "Testing SSH Connection..."
    echo "========================"
    
    # Create temp key file
    TEMP_KEY="/tmp/deploy_key_$$"
    echo "$PRIVATE_KEY" > "$TEMP_KEY"
    chmod 600 "$TEMP_KEY"
    
    # Test connection
    if test_ssh_connection "$HOST" "$USERNAME" "$PORT" "$TEMP_KEY"; then
        echo -e "${GREEN}✓ Deployment configuration is valid${NC}"
        rm -f "$TEMP_KEY"
        exit 0
    else
        echo -e "${RED}✗ Deployment configuration has issues${NC}"
        rm -f "$TEMP_KEY"
        exit 1
    fi
else
    # Local verification
    echo "Local Verification Mode"
    echo "======================="
    echo ""
    
    echo "Enter deployment details to test:"
    read -p "SSH Host/IP: " host
    read -p "SSH Username: " username
    read -p "SSH Port (default 22): " port
    port=${port:-22}
    read -p "SSH Key file path (leave empty for default): " key_file
    
    if test_ssh_connection "$host" "$username" "$port" "$key_file"; then
        echo ""
        echo -e "${GREEN}✓ Connection test successful!${NC}"
        echo ""
        echo "To set up GitHub secrets, use these values:"
        echo "  SSH_HOST=$host"
        echo "  SSH_USERNAME=$username"
        echo "  SSH_PORT=$port"
        echo ""
        echo "For SSH_PRIVATE_KEY, run:"
        echo "  ./deployment/setup-secrets.sh"
    else
        echo ""
        echo -e "${RED}✗ Connection test failed${NC}"
        echo ""
        echo "Please verify:"
        echo "1. Host is accessible"
        echo "2. Username is correct"
        echo "3. SSH key has proper permissions (chmod 600)"
        echo "4. SSH key is authorized on the server"
    fi
fi