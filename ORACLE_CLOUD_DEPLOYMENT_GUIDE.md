# Oracle Cloud Free Tier Deployment Guide

Complete step-by-step guide to deploy your CV Redactor app on Oracle Cloud's Always Free tier (4GB RAM, forever free).

---

## Why Oracle Cloud?

- **4GB RAM** (vs 512MB on Render free)
- **FREE forever** (saves $252/year vs Render paid)
- **No memory crashes**
- **Handles 30+ employees**
- **24/7 uptime**
- **Professional deployment**

---

## Prerequisites

Before starting, make sure you have:
- [ ] GitHub account with your code
- [ ] Email address
- [ ] Phone number (for verification)
- [ ] Credit card (for verification only - won't be charged)
- [ ] Supabase account with credentials

---

## Part 1: Create Oracle Cloud Account

### Step 1: Sign Up

1. Go to https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill in your details:
   - Email address
   - Country
   - Name
4. Click "Verify my email"
5. Check your email and click verification link

### Step 2: Complete Registration

1. Choose "Individual" account type
2. Enter your address
3. Add phone number (for SMS verification)
4. Add credit card (for verification - won't be charged)
5. Agree to terms
6. Click "Start my free trial"

**Note:** You get $300 credit for 30 days PLUS Always Free resources that never expire.

### Step 3: Wait for Account Activation

- Usually takes 5-10 minutes
- You'll receive email when ready
- Check spam folder if you don't see it

---

## Part 2: Create a Virtual Machine (VM)

### Step 1: Access Compute Instances

1. Log in to Oracle Cloud Console
2. Click hamburger menu (☰) top left
3. Go to **Compute** → **Instances**
4. Click **"Create Instance"**

### Step 2: Configure Instance

**Name:**
```
cv-redactor-prod
```

**Image and Shape:**
1. Click "Change Image"
2. Select **"Ubuntu 22.04"** (or latest Ubuntu)
3. Click "Select Image"

4. Click "Change Shape"
5. Select **"Ampere"** (ARM processor)
6. Choose **"VM.Standard.A1.Flex"**
7. Set:
   - **OCPUs:** 2
   - **Memory:** 12 GB (you can use up to 24GB free!)
8. Click "Select Shape"

**Networking:**
- Keep default VCN (Virtual Cloud Network)
- Keep "Assign a public IPv4 address" checked ✅

**Add SSH Keys:**
1. Select "Generate a key pair for me"
2. Click "Save Private Key" - IMPORTANT! Save this file
3. Click "Save Public Key" - Save this too

**Boot Volume:**
- Keep default (50GB is fine)

### Step 3: Create Instance

1. Click **"Create"** at the bottom
2. Wait 2-3 minutes for provisioning
3. Status will change from "PROVISIONING" to "RUNNING" (green)

### Step 4: Note Your Public IP

1. On the instance details page, find **"Public IP address"**
2. Copy this IP (example: 132.145.67.89)
3. Save it - this is your deployment link!

---

## Part 3: Configure Firewall (Open Ports)

### Step 1: Open Port 5000 in Oracle Cloud

1. On your instance page, click **"Subnet"** link
2. Click on your subnet name
3. Click **"Default Security List"**
4. Click **"Add Ingress Rules"**
5. Fill in:
   - **Source CIDR:** `0.0.0.0/0`
   - **IP Protocol:** TCP
   - **Destination Port Range:** `5000`
   - **Description:** Flask app
6. Click **"Add Ingress Rules"**

### Step 2: Open Port 80 (HTTP) and 443 (HTTPS)

Repeat above steps for:
- Port **80** (HTTP)
- Port **443** (HTTPS)

---

## Part 4: Connect to Your VM

### Step 1: Connect via SSH

**On Windows (using PowerShell):**
```powershell
# Navigate to where you saved the private key
cd Downloads

# Connect to VM (replace with your IP)
ssh -i ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
```

**On Mac/Linux:**
```bash
# Make key file secure
chmod 400 ~/Downloads/ssh-key-*.key

# Connect to VM
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
```

**First time connecting:**
- Type "yes" when asked about fingerprint
- You should see Ubuntu welcome message

---

## Part 5: Install Dependencies on VM

### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Python 3.11

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
```

### Step 3: Install Git

```bash
sudo apt install -y git
```

### Step 4: Install System Dependencies

```bash
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

---

## Part 6: Deploy Your Application

### Step 1: Clone Your Repository

```bash
cd ~
git clone https://github.com/Shivanikinagi/CV-redactor.git
cd CV-redactor
```

### Step 2: Create Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**This will take 5-10 minutes** (installing sentence-transformers, torch, etc.)

### Step 4: Create .env File

```bash
nano .env
```

Paste your environment variables:
```bash
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# LLM (Groq)
GROQ_API_KEY=your_groq_api_key

# App Configuration
UPLOAD_WORKER_COUNT=4
LLM_MAX_CONCURRENT_REQUESTS=2
FLASK_ENV=production
```

**Save and exit:**
- Press `Ctrl + X`
- Press `Y`
- Press `Enter`

### Step 5: Test the Application

```bash
python app.py
```

You should see:
```
CV Redaction Pipeline - Web Interface
Server starting...
Access the application at: http://localhost:5000
```

**Test in browser:**
- Open: `http://YOUR_PUBLIC_IP:5000`
- You should see your app!

**Stop the test:**
- Press `Ctrl + C`

---

## Part 7: Set Up Production Server (Gunicorn + Systemd)

### Step 1: Create Systemd Service File

```bash
sudo nano /etc/systemd/system/cv-redactor.service
```

Paste this configuration:
```ini
[Unit]
Description=CV Redactor Flask Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/CV-redactor
Environment="PATH=/home/ubuntu/CV-redactor/.venv/bin"
ExecStart=/home/ubuntu/CV-redactor/.venv/bin/gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save and exit:** `Ctrl + X`, `Y`, `Enter`

### Step 2: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable cv-redactor

# Start service
sudo systemctl start cv-redactor

# Check status
sudo systemctl status cv-redactor
```

You should see **"active (running)"** in green!

### Step 3: Configure Ubuntu Firewall

```bash
# Allow port 5000
sudo ufw allow 5000/tcp

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Part 8: Test Your Deployment

### Step 1: Access Your App

Open in browser:
```
http://YOUR_PUBLIC_IP:5000
```

You should see your CV Redactor interface!

### Step 2: Test Upload

1. Upload a test CV
2. Check if it processes successfully
3. Verify data appears in Supabase

### Step 3: Check Logs

```bash
# View live logs
sudo journalctl -u cv-redactor -f

# View last 100 lines
sudo journalctl -u cv-redactor -n 100
```

---

## Part 9: Set Up Auto-Deploy from GitHub (Optional)

### Step 1: Create Deploy Script

```bash
nano ~/deploy.sh
```

Paste:
```bash
#!/bin/bash
cd /home/ubuntu/CV-redactor
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cv-redactor
echo "Deployment complete!"
```

Make executable:
```bash
chmod +x ~/deploy.sh
```

### Step 2: Deploy Updates

Whenever you push to GitHub, SSH into your VM and run:
```bash
~/deploy.sh
```

### Step 3: Set Up GitHub Actions (Advanced)

Create `.github/workflows/deploy.yml` in your repo:
```yaml
name: Deploy to Oracle Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Oracle Cloud
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.ORACLE_IP }}
          username: ubuntu
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            cd /home/ubuntu/CV-redactor
            git pull origin main
            source .venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart cv-redactor
```

Add secrets in GitHub:
- `ORACLE_IP`: Your public IP
- `ORACLE_SSH_KEY`: Contents of your private key file

---

## Part 10: Set Up Custom Domain (Optional)

### Step 1: Buy a Domain

Options:
- Namecheap: $10-15/year
- GoDaddy: $12-20/year
- Cloudflare: $10/year

### Step 2: Configure DNS

In your domain registrar:
1. Add **A Record**:
   - Name: `@` (or `cv-redactor`)
   - Value: Your Oracle public IP
   - TTL: 3600

2. Wait 5-60 minutes for DNS propagation

### Step 3: Install Nginx (Reverse Proxy)

```bash
sudo apt install -y nginx
```

Create Nginx config:
```bash
sudo nano /etc/nginx/sites-available/cv-redactor
```

Paste:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/cv-redactor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4: Install SSL Certificate (HTTPS)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts, choose redirect HTTP to HTTPS
```

Now access your app at: `https://yourdomain.com`

---

## Part 11: Monitoring & Maintenance

### Check App Status

```bash
# Service status
sudo systemctl status cv-redactor

# Live logs
sudo journalctl -u cv-redactor -f

# Disk usage
df -h

# Memory usage
free -h

# CPU usage
top
```

### Restart App

```bash
sudo systemctl restart cv-redactor
```

### Update App

```bash
cd ~/CV-redactor
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart cv-redactor
```

### Backup Data

```bash
# Backup uploads and outputs
tar -czf backup-$(date +%Y%m%d).tar.gz uploads/ redacted_output/ llm_analysis/

# Download to your computer
scp -i ssh-key-*.key ubuntu@YOUR_IP:~/backup-*.tar.gz ~/Downloads/
```

---

## Troubleshooting

### App Won't Start

```bash
# Check logs
sudo journalctl -u cv-redactor -n 100

# Check if port is in use
sudo lsof -i :5000

# Restart service
sudo systemctl restart cv-redactor
```

### Can't Access from Browser

1. Check firewall:
```bash
sudo ufw status
```

2. Check Oracle Cloud security list (Part 3)

3. Check if app is running:
```bash
sudo systemctl status cv-redactor
```

### Out of Memory

```bash
# Check memory
free -h

# Reduce workers in systemd service
sudo nano /etc/systemd/system/cv-redactor.service
# Change --workers 2 to --workers 1

sudo systemctl daemon-reload
sudo systemctl restart cv-redactor
```

### Supabase Connection Issues

```bash
# Test connection
cd ~/CV-redactor
source .venv/bin/activate
python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')); print('Connected!')"
```

---

## Performance Optimization

### Enable Swap (Extra Memory)

```bash
# Create 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Optimize Gunicorn

Edit service file:
```bash
sudo nano /etc/systemd/system/cv-redactor.service
```

Adjust workers based on usage:
- Light usage (1-5 users): `--workers 2`
- Medium usage (5-15 users): `--workers 4`
- Heavy usage (15-30 users): `--workers 6`

---

## Cost Breakdown

| Resource | Oracle Free | Render Paid | Savings |
|----------|-------------|-------------|---------|
| Compute (4GB RAM) | $0 | $21/month | $252/year |
| Storage (50GB) | $0 | Included | - |
| Bandwidth (10TB) | $0 | Included | - |
| **Total** | **$0** | **$252/year** | **$252/year** |

**Additional costs (optional):**
- Domain name: $10-15/year
- SSL certificate: FREE (Let's Encrypt)

---

## Next Steps

1. ✅ Deploy on Oracle Cloud
2. ✅ Test with real users
3. ✅ Set up custom domain (optional)
4. ✅ Configure auto-deploy from GitHub
5. ✅ Monitor performance
6. ✅ Scale up if needed (Oracle allows up to 24GB RAM free!)

---

## Support

If you encounter issues:
1. Check logs: `sudo journalctl -u cv-redactor -f`
2. Check Oracle Cloud documentation
3. Check GitHub issues
4. Contact Oracle Cloud support (free tier includes support)

---

## Summary

You now have:
- ✅ Production-ready deployment
- ✅ 4GB RAM (no memory crashes)
- ✅ FREE forever
- ✅ 24/7 uptime
- ✅ Public deployment link
- ✅ Handles 30+ employees
- ✅ Auto-restart on crashes
- ✅ Easy updates from GitHub

**Your deployment link:** `http://YOUR_PUBLIC_IP:5000`

Enjoy your free, powerful deployment! 🚀
