#!/bin/bash
# Setup Nginx reverse proxy for CV Redactor

set -e

echo "========================================="
echo "Setting up Nginx Reverse Proxy"
echo "========================================="
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)
echo "Your public IP: $PUBLIC_IP"
echo ""

# Create Nginx configuration
echo "Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/cv-redactor > /dev/null <<EOF
server {
    listen 80;
    server_name $PUBLIC_IP;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    # Static files
    location /static {
        alias $(pwd)/static;
        expires 30d;
    }
}
EOF

# Enable site
echo "Enabling site..."
sudo ln -sf /etc/nginx/sites-available/cv-redactor /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

echo ""
echo "========================================="
echo "Nginx Setup Complete!"
echo "========================================="
echo ""
echo "Your app is now accessible at:"
echo "  http://$PUBLIC_IP"
echo ""
echo "Make sure Oracle Cloud Security List allows port 80!"
echo ""
