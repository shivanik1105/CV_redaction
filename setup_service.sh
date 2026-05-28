#!/bin/bash
# Setup systemd service for CV Redactor on Oracle Cloud

set -e

echo "========================================="
echo "Setting up CV Redactor as System Service"
echo "========================================="
echo ""

# Get current directory
APP_DIR=$(pwd)
USER=$(whoami)

# Create systemd service file
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/cv-redactor.service > /dev/null <<EOF
[Unit]
Description=CV Redactor Flask Application
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 2 --threads 2 --timeout 120 --bind 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service..."
sudo systemctl enable cv-redactor

# Start service
echo "Starting service..."
sudo systemctl start cv-redactor

# Check status
echo ""
echo "Service status:"
sudo systemctl status cv-redactor --no-pager

echo ""
echo "========================================="
echo "Service Setup Complete!"
echo "========================================="
echo ""
echo "Useful commands:"
echo "  View logs:    sudo journalctl -u cv-redactor -f"
echo "  Restart:      sudo systemctl restart cv-redactor"
echo "  Stop:         sudo systemctl stop cv-redactor"
echo "  Status:       sudo systemctl status cv-redactor"
echo ""
