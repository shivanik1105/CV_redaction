# Oracle Cloud Deployment Guide - Complete

## 🎯 Overview

Deploy your CV Redactor application to Oracle Cloud Free Tier for **$0 forever**.

**What you'll get:**
- ✅ Free forever (no expiration)
- ✅ 1-24GB RAM (enough for all features)
- ✅ 200GB storage
- ✅ Public IP address
- ✅ Full control over server

---

## 📋 Prerequisites

### Before You Start:

1. **Virtual Credit Card** (for verification only)
   - Slice (recommended for India)
   - Or any debit/credit card
   - Oracle charges ₹100-150 for verification (refunded)

2. **Your Credentials Ready:**
   - Supabase URL
   - Supabase Keys
   - LLM API keys (optional)

3. **Time Required:**
   - Oracle account setup: 10 minutes
   - VM creation: 5 minutes
   - Deployment: 30 minutes
   - **Total: 45 minutes**

---

## 🚀 Part 1: Create Oracle Cloud Account

### Step 1: Sign Up

1. Go to https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill in details:
   - Email address
   - Country: India
   - Cloud Account Name (choose unique name)

### Step 2: Verification

1. **Email verification** - Check email and verify
2. **Phone verification** - Enter mobile number, receive SMS code
3. **Card verification** - Enter Slice virtual card details
   - Oracle will hold ₹100-150 (refunded in 2-3 days)
   - Approve transaction in Slice app

### Step 3: Wait for Approval

- Usually instant
- Sometimes takes up to 24 hours
- You'll receive email when approved

---

## 🖥️ Part 2: Create VM Instance

### Step 1: Login to Oracle Console

1. Go to https://cloud.oracle.com/
2. Login with your credentials
3. You'll see Oracle Cloud Console

### Step 2: Create Compute Instance

1. Click **"Create a VM instance"** (or go to Compute → Instances → Create Instance)

2. **Name your instance:**
   ```
   cv-redactor-app
   ```

3. **Choose Image:**
   - Click "Change Image"
   - Select: **Ubuntu 22.04** (Canonical)
   - Click "Select Image"

4. **Choose Shape:**
   
   **Option A: x86 (1GB RAM) - Good enough**
   - Shape: VM.Standard.E2.1.Micro
   - OCPU: 1
   - Memory: 1GB
   - Always Free eligible ✅

   **Option B: ARM (24GB RAM) - Best performance** ⭐
   - Click "Change Shape"
   - Select "Ampere" (ARM)
   - Shape: VM.Standard.A1.Flex
   - OCPU: 4 (max free)
   - Memory: 24GB (max free)
   - Always Free eligible ✅

5. **Networking:**
   - Leave default (creates new VCN)
   - Assign public IPv4 address: ✅ **Yes**

6. **SSH Keys:**
   
   **Option A: Generate new key pair** (Recommended)
   - Select "Generate a key pair for me"
   - Click "Save Private Key" - **IMPORTANT: Save this file!**
   - Click "Save Public Key" (optional)

   **Option B: Use existing key**
   - Select "Upload public key files"
   - Upload your public key

7. **Boot Volume:**
   - Leave default (50GB)

8. **Click "Create"**

### Step 3: Wait for Provisioning

- Takes 2-3 minutes
- Status will change from "Provisioning" to "Running"
- Note down the **Public IP address** (e.g., 123.45.67.89)

---

## 🔒 Part 3: Configure Firewall

### Step 1: Oracle Cloud Security List

1. In your instance details, click on the **VCN name** (under "Primary VNIC")
2. Click **"Security Lists"** (left menu)
3. Click **"Default Security List"**
4. Click **"Add Ingress Rules"**

5. **Add Rule for HTTP (Port 80):**
   ```
   Source CIDR: 0.0.0.0/0
   IP Protocol: TCP
   Destination Port Range: 80
   Description: HTTP access
   ```
   Click "Add Ingress Rules"

6. **Add Rule for Flask (Port 5000) - Optional for testing:**
   ```
   Source CIDR: 0.0.0.0/0
   IP Protocol: TCP
   Destination Port Range: 5000
   Description: Flask app
   ```
   Click "Add Ingress Rules"

### Step 2: Ubuntu Firewall (UFW)

We'll configure this later after connecting to the VM.

---

## 🔌 Part 4: Connect to Your VM

### From Windows (PowerShell):

1. **Open PowerShell**

2. **Navigate to where you saved the SSH key:**
   ```powershell
   cd C:\Users\YourName\Downloads
   ```

3. **Set correct permissions on key:**
   ```powershell
   icacls "ssh-key-*.key" /inheritance:r /grant:r "%username%:R"
   ```

4. **Connect to VM:**
   ```powershell
   ssh -i "ssh-key-*.key" ubuntu@YOUR_PUBLIC_IP
   ```
   Replace `YOUR_PUBLIC_IP` with your actual IP (e.g., 123.45.67.89)

5. **First time connecting:**
   - Type `yes` when asked about fingerprint
   - You're now connected to your Oracle Cloud VM! 🎉

---

## 📦 Part 5: Upload Your Application

### Option A: Using Git (Recommended)

**On your Windows machine:**

1. **Push code to GitHub** (if not already):
   ```powershell
   cd C:\Users\shiva\Downloads\samplecvs
   git init
   git add .
   git commit -m "Deploy to Oracle Cloud"
   git remote add origin https://github.com/YOUR_USERNAME/cv-redactor.git
   git push -u origin main
   ```

**On your Oracle VM:**

2. **Clone repository:**
   ```bash
   cd ~
   git clone https://github.com/YOUR_USERNAME/cv-redactor.git
   cd cv-redactor
   ```

### Option B: Using SCP (Direct Upload)

**On your Windows machine:**

```powershell
cd C:\Users\shiva\Downloads\samplecvs

# Upload all files
scp -i "ssh-key-*.key" -r * ubuntu@YOUR_PUBLIC_IP:~/cv-redactor/
```

This will take 5-10 minutes depending on your internet speed.

---

## ⚙️ Part 6: Deploy Application

### On your Oracle VM (connected via SSH):

1. **Navigate to app directory:**
   ```bash
   cd ~/cv-redactor
   ```

2. **Make deployment script executable:**
   ```bash
   chmod +x deploy_oracle.sh setup_service.sh setup_nginx.sh
   ```

3. **Run deployment script:**
   ```bash
   bash deploy_oracle.sh
   ```

   This will:
   - Update system packages
   - Install Python 3.11
   - Install dependencies (~10-15 minutes)
   - Create necessary directories

4. **Configure environment variables:**
   ```bash
   nano .env
   ```

   **Add your credentials:**
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   FLASK_SECRET_KEY=your_random_secret_key
   REDIS_URL=redis://localhost:6379
   ```

   **Save:** Ctrl+X, then Y, then Enter

5. **Test the application:**
   ```bash
   source venv/bin/activate
   python app.py
   ```

   You should see:
   ```
   * Running on http://0.0.0.0:5000
   ```

6. **Test in browser:**
   - Open: `http://YOUR_PUBLIC_IP:5000`
   - You should see your CV Redactor app! 🎉

7. **Stop the test** (Ctrl+C)

---

## 🔧 Part 7: Setup as System Service

### Make App Run Forever:

1. **Setup systemd service:**
   ```bash
   sudo bash setup_service.sh
   ```

   This will:
   - Create systemd service
   - Enable auto-start on boot
   - Start the service

2. **Check service status:**
   ```bash
   sudo systemctl status cv-redactor
   ```

   Should show: **Active: active (running)** ✅

3. **View logs:**
   ```bash
   sudo journalctl -u cv-redactor -f
   ```

   Press Ctrl+C to exit

---

## 🌐 Part 8: Setup Nginx (Production)

### Add Reverse Proxy:

1. **Run Nginx setup:**
   ```bash
   sudo bash setup_nginx.sh
   ```

   This will:
   - Install and configure Nginx
   - Setup reverse proxy
   - Enable your app on port 80

2. **Your app is now live at:**
   ```
   http://YOUR_PUBLIC_IP
   ```

   (No need for :5000 port anymore!)

---

## ✅ Part 9: Verification

### Test All Features:

1. **Open browser:** `http://YOUR_PUBLIC_IP`

2. **Test Upload:**
   - Upload a CV
   - Enter your LLM API key
   - Should process successfully ✅

3. **Test Search:**
   - Search for candidates
   - Should show results ✅

4. **Test Download:**
   - Download masked PDF
   - Should have black boxes ✅
   - Download original CV
   - Should work ✅

---

## 🎛️ Management Commands

### Service Management:

```bash
# View logs (real-time)
sudo journalctl -u cv-redactor -f

# Restart service
sudo systemctl restart cv-redactor

# Stop service
sudo systemctl stop cv-redactor

# Start service
sudo systemctl start cv-redactor

# Check status
sudo systemctl status cv-redactor
```

### Update Application:

```bash
# If using Git
cd ~/cv-redactor
git pull
sudo systemctl restart cv-redactor

# If using SCP
# Upload new files from Windows, then:
sudo systemctl restart cv-redactor
```

### Check Resource Usage:

```bash
# Memory usage
free -h

# Disk usage
df -h

# CPU usage
top
```

---

## 🛡️ Security Best Practices

### 1. Setup Firewall:

```bash
# Enable UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw enable
```

### 2. Keep System Updated:

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Monitor Logs:

```bash
# Check for errors
sudo journalctl -u cv-redactor --since today
```

---

## 💰 Cost Monitoring

### Stay in Free Tier:

1. **Go to:** Oracle Console → Billing → Cost Analysis
2. **Check:** You're using "Always Free" resources
3. **Set alerts:** Billing → Budgets → Create Budget
   - Set budget: $0
   - Alert threshold: 100%

### Always Free Resources:

- ✅ 2x VM.Standard.E2.1.Micro (1GB RAM each)
- ✅ OR 4x OCPU + 24GB RAM (ARM)
- ✅ 200GB Block Storage
- ✅ 10TB Outbound Data Transfer/month

**You're using:** 1 VM (well within limits) ✅

---

## 🆘 Troubleshooting

### Issue: Can't connect via SSH

**Fix:**
```bash
# Check Security List has port 22 open
# Check you're using correct key file
# Check IP address is correct
```

### Issue: Can't access app in browser

**Fix:**
```bash
# Check service is running
sudo systemctl status cv-redactor

# Check Nginx is running
sudo systemctl status nginx

# Check firewall
sudo ufw status

# Check Oracle Security List has port 80 open
```

### Issue: App crashes

**Fix:**
```bash
# Check logs
sudo journalctl -u cv-redactor -n 100

# Check .env file
cat .env

# Restart service
sudo systemctl restart cv-redactor
```

### Issue: Out of memory (1GB VM)

**Fix:**
```bash
# Reduce workers in service file
sudo nano /etc/systemd/system/cv-redactor.service

# Change to:
ExecStart=.../gunicorn --workers 1 --threads 1 ...

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart cv-redactor
```

**Or:** Recreate VM with ARM shape (24GB RAM)

---

## 🎉 Success Checklist

- [x] Oracle Cloud account created
- [x] VM instance created and running
- [x] Firewall configured (ports 22, 80)
- [x] Connected via SSH
- [x] Application uploaded
- [x] Dependencies installed
- [x] Environment variables configured
- [x] Service running
- [x] Nginx configured
- [x] App accessible at http://YOUR_PUBLIC_IP
- [x] All features tested and working

---

## 📚 Quick Reference

### Your App Details:

```
Public URL: http://YOUR_PUBLIC_IP
SSH Access: ssh -i key.pem ubuntu@YOUR_PUBLIC_IP
App Directory: ~/cv-redactor
Service Name: cv-redactor
Logs: sudo journalctl -u cv-redactor -f
```

### Important Files:

```
Application: ~/cv-redactor/app.py
Environment: ~/cv-redactor/.env
Service: /etc/systemd/system/cv-redactor.service
Nginx: /etc/nginx/sites-available/cv-redactor
```

---

## 🎯 Next Steps

1. **Share your app URL** with users
2. **Monitor logs** regularly
3. **Keep system updated**
4. **Backup your .env file**
5. **Consider adding SSL** (Let's Encrypt) for HTTPS

---

## 🌟 Congratulations!

Your CV Redactor app is now live on Oracle Cloud for **$0 forever**! 🎉

**Your app URL:** `http://YOUR_PUBLIC_IP`

**Need help?** Check the troubleshooting section or review the logs.

---

**Deployment Time:** ~45 minutes  
**Monthly Cost:** $0 forever  
**Features:** 100% complete  
**Status:** Production ready ✅
