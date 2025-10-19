#!/bin/bash
#
# HPLink PBX Cloud - Installation Script for Ubuntu 22.04
# This script automates the installation process
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=========================================="
echo "  HPLink PBX Cloud Installation Script"
echo "=========================================="
echo -e "${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should NOT be run as root${NC}"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Check Ubuntu version
if ! grep -q "22.04" /etc/os-release; then
    echo -e "${YELLOW}Warning: This script is designed for Ubuntu 22.04${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Prompt for configuration
echo ""
echo "Please provide configuration details:"
read -p "Database password for 'hplink' user: " DB_PASSWORD
read -p "Domain for API (e.g., api.hplinkpbx.com): " API_DOMAIN
read -p "Install directory [/opt/hplink-pbx]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-/opt/hplink-pbx}

echo ""
echo -e "${GREEN}Starting installation...${NC}"

# 1. Update system
echo -e "\n${GREEN}[1/10] Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# 2. Install dependencies
echo -e "\n${GREEN}[2/10] Installing system dependencies...${NC}"
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    python3.11 \
    python3.11-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    pkg-config \
    libssl-dev \
    libasound2-dev

# 3. Install Node.js
echo -e "\n${GREEN}[3/10] Installing Node.js 18...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
fi

# 4. Create application user
echo -e "\n${GREEN}[4/10] Creating application user...${NC}"
if ! id "hplink" &>/dev/null; then
    sudo useradd -r -m -d $INSTALL_DIR -s /bin/bash hplink
fi

# 5. Setup PostgreSQL
echo -e "\n${GREEN}[5/10] Configuring PostgreSQL...${NC}"
sudo -u postgres psql << EOF
-- Create database if not exists
SELECT 'CREATE DATABASE hplink_pbx' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'hplink_pbx')\gexec
-- Create user if not exists
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'hplink') THEN
    CREATE USER hplink WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
  END IF;
END
\$\$;
GRANT ALL PRIVILEGES ON DATABASE hplink_pbx TO hplink;
\c hplink_pbx
GRANT ALL ON SCHEMA public TO hplink;
EOF

# 6. Clone or use existing repository
echo -e "\n${GREEN}[6/10] Setting up application files...${NC}"
if [ ! -d "$INSTALL_DIR" ]; then
    sudo mkdir -p $INSTALL_DIR
    sudo chown hplink:hplink $INSTALL_DIR
fi

cd $INSTALL_DIR

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        sudo -u hplink cp .env.example .env
        
        # Update .env with database password
        sudo -u hplink sed -i "s|postgresql://hplink:hplink@localhost|postgresql://hplink:$DB_PASSWORD@localhost|g" .env
        
        echo -e "${YELLOW}Please edit $INSTALL_DIR/.env and update all secrets!${NC}"
    fi
fi

# 7. Create Python virtual environment
echo -e "\n${GREEN}[7/10] Creating Python virtual environment...${NC}"
if [ ! -d "$INSTALL_DIR/venv" ]; then
    sudo -u hplink python3.11 -m venv $INSTALL_DIR/venv
fi

# Install Python dependencies
echo "Installing API server dependencies..."
sudo -u hplink $INSTALL_DIR/venv/bin/pip install --upgrade pip
sudo -u hplink $INSTALL_DIR/venv/bin/pip install -r $INSTALL_DIR/api-server/requirements.txt

echo "Installing PBX core dependencies..."
sudo -u hplink $INSTALL_DIR/venv/bin/pip install -r $INSTALL_DIR/core-engine/requirements.txt

# 8. Create directories
echo -e "\n${GREEN}[8/10] Creating application directories...${NC}"
sudo -u hplink mkdir -p /var/lib/hplink-pbx/{media,recordings,storage}
sudo -u hplink mkdir -p /var/lib/hplink-pbx/media/voicemail

# 9. Install systemd services
echo -e "\n${GREEN}[9/10] Installing systemd services...${NC}"
sudo cp $INSTALL_DIR/api-server/systemd/hplink-api.service /etc/systemd/system/
sudo cp $INSTALL_DIR/core-engine/systemd/hplink-core.service /etc/systemd/system/

# Update service files with correct paths
sudo sed -i "s|/opt/hplink-pbx|$INSTALL_DIR|g" /etc/systemd/system/hplink-api.service
sudo sed -i "s|/opt/hplink-pbx|$INSTALL_DIR|g" /etc/systemd/system/hplink-core.service

sudo systemctl daemon-reload

# 10. Run database migrations
echo -e "\n${GREEN}[10/10] Running database migrations...${NC}"
cd $INSTALL_DIR/api-server
sudo -u hplink $INSTALL_DIR/venv/bin/alembic upgrade head

echo ""
echo -e "${GREEN}=========================================="
echo "  Installation Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/.env and update all secrets"
echo "2. Seed initial data: sudo -u hplink $INSTALL_DIR/venv/bin/python $INSTALL_DIR/scripts/seed_data.py"
echo "3. Start services: sudo systemctl start hplink-api hplink-core"
echo "4. Enable services: sudo systemctl enable hplink-api hplink-core"
echo "5. Configure NGINX: sudo cp $INSTALL_DIR/reverse-proxy/nginx/hplink-pbx.conf /etc/nginx/sites-available/"
echo "6. Obtain SSL certificate: sudo certbot --nginx -d $API_DOMAIN"
echo ""
echo "Check service status:"
echo "  sudo systemctl status hplink-api"
echo "  sudo systemctl status hplink-core"
echo ""
echo "View logs:"
echo "  sudo journalctl -u hplink-api -f"
echo "  sudo journalctl -u hplink-core -f"
echo ""
