#!/bin/bash

# Script to properly format and set GitHub secrets
# Handles line ending issues and ensures proper formatting

echo "GitHub Secrets Setup Script"
echo "==========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to clean and validate SSH key
clean_ssh_key() {
    local key_file=$1
    local key_name=$2
    
    echo -e "${YELLOW}Processing $key_name...${NC}"
    
    if [ ! -f "$key_file" ]; then
        echo -e "${RED}Error: $key_file not found${NC}"
        return 1
    fi
    
    # Create a cleaned version
    local cleaned_file="${key_file}.cleaned"
    
    # Remove any carriage returns and ensure proper Unix line endings
    tr -d '\r' < "$key_file" > "$cleaned_file"
    
    # Ensure the file ends with a newline
    sed -i '' -e '$a\' "$cleaned_file" 2>/dev/null || sed -i -e '$a\' "$cleaned_file"
    
    # Validate SSH key format
    if grep -q "BEGIN.*PRIVATE KEY" "$cleaned_file"; then
        echo -e "${GREEN}✓ Valid private key format detected${NC}"
    elif grep -q "ssh-rsa\|ssh-ed25519\|ecdsa-sha2" "$cleaned_file"; then
        echo -e "${GREEN}✓ Valid public key format detected${NC}"
    else
        echo -e "${RED}Warning: Key format might be invalid${NC}"
    fi
    
    # Show the first and last lines for verification (without exposing the key)
    echo "First line: $(head -n1 "$cleaned_file" | cut -c1-30)..."
    echo "Last line: ...$(tail -n1 "$cleaned_file" | rev | cut -c1-30 | rev)"
    echo ""
    
    # Copy cleaned content to clipboard (macOS)
    cat "$cleaned_file" | pbcopy
    echo -e "${GREEN}✓ Cleaned $key_name copied to clipboard${NC}"
    echo -e "${YELLOW}→ Now paste this into GitHub Secrets as $key_name${NC}"
    echo ""
    
    # Store cleaned version
    mv "$cleaned_file" "$key_file"
    
    return 0
}

# Function to clean and validate known hosts
clean_known_hosts() {
    local hosts_file=$1
    
    echo -e "${YELLOW}Processing SSH_KNOWN_HOSTS...${NC}"
    
    if [ ! -f "$hosts_file" ]; then
        echo -e "${RED}Error: $hosts_file not found${NC}"
        return 1
    fi
    
    # Create a cleaned version
    local cleaned_file="${hosts_file}.cleaned"
    
    # Remove any carriage returns and ensure proper Unix line endings
    tr -d '\r' < "$hosts_file" > "$cleaned_file"
    
    # Remove empty lines and comments
    grep -v '^#' "$cleaned_file" | grep -v '^$' > "${cleaned_file}.tmp"
    mv "${cleaned_file}.tmp" "$cleaned_file"
    
    # Validate format (should contain host keys)
    if grep -q "ssh-rsa\|ssh-ed25519\|ecdsa-sha2" "$cleaned_file"; then
        echo -e "${GREEN}✓ Valid known_hosts format detected${NC}"
        echo "Number of host entries: $(wc -l < "$cleaned_file")"
    else
        echo -e "${RED}Warning: known_hosts format might be invalid${NC}"
    fi
    
    # Copy cleaned content to clipboard
    cat "$cleaned_file" | pbcopy
    echo -e "${GREEN}✓ Cleaned known_hosts copied to clipboard${NC}"
    echo -e "${YELLOW}→ Now paste this into GitHub Secrets as SSH_KNOWN_HOSTS${NC}"
    echo ""
    
    # Store cleaned version
    mv "$cleaned_file" "$hosts_file"
    
    return 0
}

# Function to generate known_hosts if needed
generate_known_hosts() {
    local host=$1
    local port=${2:-22}
    local output_file="known_hosts_generated"
    
    echo -e "${YELLOW}Generating known_hosts for $host:$port...${NC}"
    
    # Remove old entry if exists
    ssh-keygen -R "[$host]:$port" 2>/dev/null
    
    # Scan and add the host key
    ssh-keyscan -p $port -H $host 2>/dev/null > "$output_file"
    
    if [ -s "$output_file" ]; then
        echo -e "${GREEN}✓ Successfully generated known_hosts entry${NC}"
        cat "$output_file" | pbcopy
        echo -e "${GREEN}✓ Copied to clipboard${NC}"
        echo -e "${YELLOW}→ Now paste this into GitHub Secrets as SSH_KNOWN_HOSTS${NC}"
    else
        echo -e "${RED}Failed to generate known_hosts entry${NC}"
        echo "Make sure the host $host is accessible on port $port"
    fi
}

# Main menu
echo "What would you like to setup?"
echo "1) Clean and setup SSH_PRIVATE_KEY"
echo "2) Clean and setup SSH_KNOWN_HOSTS"
echo "3) Generate new SSH_KNOWN_HOSTS from host"
echo "4) Setup all secrets interactively"
echo "5) Validate GitHub secret format (paste from clipboard)"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        read -p "Enter path to SSH private key file: " key_file
        clean_ssh_key "$key_file" "SSH_PRIVATE_KEY"
        ;;
    2)
        read -p "Enter path to known_hosts file: " hosts_file
        clean_known_hosts "$hosts_file"
        ;;
    3)
        read -p "Enter hostname or IP: " hostname
        read -p "Enter SSH port (default 22): " port
        port=${port:-22}
        generate_known_hosts "$hostname" "$port"
        ;;
    4)
        echo -e "${YELLOW}Interactive Setup Mode${NC}"
        echo "This will help you set up all required secrets"
        echo ""
        
        # SSH Private Key
        echo "Step 1: SSH_PRIVATE_KEY"
        read -p "Enter path to your SSH private key: " ssh_key
        if clean_ssh_key "$ssh_key" "SSH_PRIVATE_KEY"; then
            read -p "Press Enter after adding to GitHub Secrets..."
        fi
        
        # Known Hosts
        echo "Step 2: SSH_KNOWN_HOSTS"
        echo "Do you have an existing known_hosts file? (y/n)"
        read -p "> " has_known_hosts
        
        if [[ $has_known_hosts == "y" ]]; then
            read -p "Enter path to known_hosts file: " hosts_file
            if clean_known_hosts "$hosts_file"; then
                read -p "Press Enter after adding to GitHub Secrets..."
            fi
        else
            read -p "Enter your server hostname or IP: " hostname
            read -p "Enter SSH port (default 22): " port
            port=${port:-22}
            generate_known_hosts "$hostname" "$port"
            read -p "Press Enter after adding to GitHub Secrets..."
        fi
        
        # Other secrets
        echo "Step 3: Other Required Secrets"
        echo -e "${YELLOW}Add these secrets manually in GitHub:${NC}"
        echo "  - SSH_HOST: Your server hostname or IP"
        echo "  - SSH_USERNAME: Your SSH username"
        echo "  - SSH_PORT: Your SSH port (usually 22)"
        echo ""
        echo -e "${GREEN}Setup complete!${NC}"
        ;;
    5)
        echo -e "${YELLOW}Paste the content from clipboard (Ctrl+D when done):${NC}"
        content=$(pbpaste)
        
        # Check for common issues
        if echo "$content" | grep -q $'\r'; then
            echo -e "${RED}✗ Carriage returns detected (Windows line endings)${NC}"
        else
            echo -e "${GREEN}✓ No carriage returns found${NC}"
        fi
        
        if echo "$content" | grep -q "BEGIN.*PRIVATE KEY"; then
            echo -e "${GREEN}✓ Valid private key header found${NC}"
            if echo "$content" | grep -q "END.*PRIVATE KEY"; then
                echo -e "${GREEN}✓ Valid private key footer found${NC}"
            else
                echo -e "${RED}✗ Missing private key footer${NC}"
            fi
        elif echo "$content" | grep -q "ssh-rsa\|ssh-ed25519\|ecdsa-sha2"; then
            echo -e "${GREEN}✓ Valid SSH public key or known_hosts format${NC}"
        else
            echo -e "${YELLOW}⚠ Could not determine key format${NC}"
        fi
        
        # Check for trailing spaces
        if echo "$content" | grep -q ' $'; then
            echo -e "${YELLOW}⚠ Trailing spaces detected${NC}"
        fi
        
        # Clean and copy back
        echo "$content" | tr -d '\r' | sed 's/[[:space:]]*$//' | pbcopy
        echo -e "${GREEN}✓ Cleaned version copied back to clipboard${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${YELLOW}Important GitHub Secrets Setup Tips:${NC}"
echo "1. Go to: Settings → Secrets and variables → Actions"
echo "2. Click 'New repository secret'"
echo "3. Use EXACT secret names: SSH_PRIVATE_KEY, SSH_KNOWN_HOSTS, SSH_HOST, SSH_USERNAME, SSH_PORT"
echo "4. Paste the clipboard content directly (no quotes or modifications)"
echo "5. Make sure there are no extra spaces or lines"
echo ""
echo -e "${GREEN}After setting up secrets, trigger the deployment workflow to test.${NC}"