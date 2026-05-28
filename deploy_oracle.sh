#!/bin/bash
# Oracle Cloud Deployment Script
# Run this script on your Oracle Cloud VM after uploading the code

set -e  # Exit on error

echo "========================================="
echo "CV Redactor - Oracle Cloud Deployment"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Update system
echo -e "${GREEN}[1/8] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install Python 3.11
echo -e "${GREEN}[2/8] Installing Python 3.11...${NC}"
sudo apt install -y python3.11 python3.11-venv python3-pip

# Step 3: Install system dependencies
echo -e "${GREEN}[3/8] Installing system dependencies...${NC}"
sudo apt install -y build-essential libpq-dev git redis-server nginx

# Step 4: Create virtual environment
echo -e "${GREEN}[4/8] Creating virtual environment...${NC}"
python3.11 -m venv venv
source venv/bin/activate

# Step 5: Upgrade pip
echo -e "${GREEN}[5/8] Upgrading pip...${NC}"
pip install --upgrade pip

# Step 6: Install Python dependencies
echo -e "${GREEN}[6/8] Installing Python dependencies (this will take 10-15 minutes)...${NC}"
pip install -r requirements.txt

# Step 7: Create necessary directories
echo -e "${GREEN}[7/8] Creating directories...${NC}"
mkdir -p uploads redacted_output final_output llm_analysis debug_output

# Step 8: Setup environment
echo -e "${GREEN}[8/8] Setting up environment...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Please create it with your credentials.${NC}"
    echo "Copy .env.example to .env and fill in your values:"
    echo "  cp .env.example .env"
    echo "  nano .env"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure .env file with your credentials"
echo "2. Start Redis: sudo systemctl start redis-server"
echo "3. Test the app: python app.py"
echo "4. Setup systemd service: sudo bash setup_service.sh"
echo ""
