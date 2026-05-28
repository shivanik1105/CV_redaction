# 🚀 Quick Start - Deploy to Oracle Cloud

## What You Need (5 minutes prep)

1. **Virtual Credit Card** - Get Slice app (free, instant)
2. **Supabase Credentials** - Your database URL and keys
3. **45 minutes** - For complete deployment

---

## 📋 Quick Steps

### 1. Get Slice Virtual Card (5 min)
```
1. Download Slice app (Android/iOS)
2. Sign up with mobile number
3. Complete KYC (Aadhaar + PAN)
4. Get instant virtual card
```

### 2. Create Oracle Cloud Account (10 min)
```
1. Go to: https://www.oracle.com/cloud/free/
2. Sign up with Slice card
3. Verify email and phone
4. Wait for approval (instant to 24 hours)
```

### 3. Create VM Instance (5 min)
```
1. Login to Oracle Console
2. Create VM Instance
3. Choose: Ubuntu 22.04
4. Shape: ARM (24GB RAM) or x86 (1GB RAM)
5. Save SSH key
6. Note public IP
```

### 4. Configure Firewall (2 min)
```
1. Security List → Add Ingress Rules
2. Port 80 (HTTP)
3. Port 5000 (Flask - optional)
```

### 5. Connect & Deploy (30 min)
```bash
# Connect via SSH
ssh -i key.pem ubuntu@YOUR_IP

# Clone or upload code
git clone YOUR_REPO

# Run deployment
cd cv-redactor
bash deploy_oracle.sh

# Configure .env
nano .env

# Setup service
sudo bash setup_service.sh

# Setup Nginx
sudo bash setup_nginx.sh
```

### 6. Done! 🎉
```
Your app: http://YOUR_PUBLIC_IP
Cost: $0 forever
```

---

## 📖 Detailed Guide

See **`ORACLE_DEPLOY_GUIDE.md`** for complete step-by-step instructions.

---

## 🆘 Need Help?

**Common Issues:**

1. **Can't connect SSH** → Check Security List has port 22
2. **Can't access app** → Check service status: `sudo systemctl status cv-redactor`
3. **App crashes** → Check logs: `sudo journalctl -u cv-redactor -f`

---

## ⚡ Quick Commands

```bash
# View logs
sudo journalctl -u cv-redactor -f

# Restart app
sudo systemctl restart cv-redactor

# Check status
sudo systemctl status cv-redactor

# Update app
git pull && sudo systemctl restart cv-redactor
```

---

**Ready?** Follow **`ORACLE_DEPLOY_GUIDE.md`** for detailed instructions!
