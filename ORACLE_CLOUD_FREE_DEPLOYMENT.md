# Deploy to Oracle Cloud Free Tier (Always Free)

## Why Oracle Cloud?

✅ **Always Free** - No credit card charges, truly free forever  
✅ **Generous Resources** - 1-4 GB RAM (enough for all dependencies)  
✅ **Keep ALL Requirements** - sentence-transformers, spaCy, everything  
✅ **200GB Storage** - More than enough for CVs  
✅ **No Time Limit** - Unlike AWS/GCP free tiers that expire after 12 months  

---

## What You Get (Always Free)

- **2 AMD Compute VMs** - 1GB RAM each, or
- **4 ARM Compute VMs** - 24GB RAM total (!)
- **200GB Block Storage**
- **10TB Outbound Data Transfer/month**
- **No credit card required** (for free tier)

---

## Step-by-Step Deployment

### Phase 1: Create Oracle Cloud Account

1. **Go to**: https://www.oracle.com/cloud/free/
2. **Click**: "Start for free"
3. **Fill in details**:
   - Email address
   - Country
   - Cloud Account Name (choose unique name)
4. **Verify email**
5. **Complete registration**
   - May ask for credit card for verification (won't charge)
   - Or use without credit card (limited features but enough for us)

---

### Phase 2: Create a VM Instance

1. **Login to Oracle Cloud Console**
2. **Go to**: Compute → Instances
3. **Click**: "Create Instance"

4. **Configure Instance**:
   ```
   Name: cv-redactor-app
   
   Image: Ubuntu 22.04 (Canonical)
   
   Shape: 
   - VM.Standard.E2.1.Micro (1GB RAM, Always Free)
   - OR VM.Standard.A1.Flex (ARM, up to 24GB RAM free!)
   
   Network: 
   - Create new VCN (default settings)
   - Assign public IP: Yes
   
   SSH Keys:
   - Generate SSH key pair (download private key!)
   - OR paste your existing public key
   ```

5. **Click**: "Create"

6. **Wait 2-3 minutes** for instance to provision

7. **Note down**:
   - Public IP address (e.g., 123.45.67.89)
   - Username: `ubuntu`

---

### Phase 3: Configure Firewall

1. **In Oracle Console**:
   - Go to: Networking → Virtual Cloud Networks
   - Click your VCN
   - Click "Security Lists"
   - Click "Default Security List"

2. **Add Ingress Rule**:
   ```
   Source CIDR: 0.0.0.0/0
   IP Protocol: TCP
   Destination Port: 5000
   Description: Flask app
   ```

3. **Click**: "Add Ingress Rules"

---

### Phase 4: Connect to VM

**On Windows (using PowerShell)**:

```powershell
# Navigate to where you saved the SSH key
cd C:\Users\YourName\Downloads

# Set correct permissions (if needed)
icacls "ssh-key-*.key" /inheritance:r /grant:r "%username%:R"

# Connect to VM
ssh -i "ssh-key-*.key" ubuntu@YOUR_PUBLIC_IP
```

**First time connecting**:
- Type `yes` when asked about fingerprint

---

### Phase 5: Setup Server

Once connected to VM, run these commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install system dependencies
sudo apt install -y build-essential libpq-dev git

# Create app directory
mkdir -p ~/cv-redactor
cd ~/cv-redactor
```

---

### Phase 6: Upload Your Application

**Option A: Using Git (Recommended)**

```bash
# On VM
cd ~/cv-redactor
git clone YOUR_GITHUB_REPO_URL .

# Or if you don't have a repo, use SCP from your Windows machine:
```

**Option B: Using SCP from Windows**

```powershell
# On your Windows machine
cd C:\Users\shiva\Downloads\samplecvs

# Upload files (replace YOUR_PUBLIC_IP)
scp -i "ssh-key-*.key" -r * ubuntu@YOUR_PUBLIC_IP:~/cv-redactor/
```

---

### Phase 7: Install Dependencies

```bash
# On VM
cd ~/cv-redactor

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# This will take 5-10 minutes for all dependencies
```

---

### Phase 8: Configure Environment

```bash
# Create .env file
nano .env
```

**Paste your environment variables**:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key
FLASK_SECRET_KEY=your_secret_key
REDIS_URL=redis://localhost:6379
```

**Save**: Ctrl+X, then Y, then Enter

---

### Phase 9: Install Redis (Optional, for caching)

```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

---

### Phase 10: Test the Application

```bash
# On VM
cd ~/cv-redactor
source venv/bin/activate

# Run Flask app
python app.py
```

**Expected output**:
```
* Running on http://0.0.0.0:5000
```

**Test from your browser**:
```
http://YOUR_PUBLIC_IP:5000
```

---

### Phase 11: Setup as System Service (Run Forever)

Create systemd service:

```bash
sudo nano /etc/systemd/system/cv-redactor.service
```

**Paste this**:
```ini
[Unit]
Description=CV Redactor Flask App
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cv-redactor
Environment="PATH=/home/ubuntu/cv-redactor/venv/bin"
ExecStart=/home/ubuntu/cv-redactor/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Save**: Ctrl+X, then Y, then Enter

**Enable and start service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cv-redactor
sudo systemctl start cv-redactor
sudo systemctl status cv-redactor
```

---

### Phase 12: Setup Nginx (Optional, for production)

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx config
sudo nano /etc/nginx/sites-available/cv-redactor
```

**Paste this**:
```nginx
server {
    listen 80;
    server_name YOUR_PUBLIC_IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable site**:
```bash
sudo ln -s /etc/nginx/sites-available/cv-redactor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Update firewall rule** in Oracle Console:
- Change port from 5000 to 80

---

## Maintenance Commands

```bash
# View logs
sudo journalctl -u cv-redactor -f

# Restart service
sudo systemctl restart cv-redactor

# Stop service
sudo systemctl stop cv-redactor

# Update application
cd ~/cv-redactor
git pull
sudo systemctl restart cv-redactor
```

---

## Troubleshooting

### Issue: Can't connect via SSH

**Fix**: Check Oracle Cloud firewall rules (Security List)
- Add ingress rule for port 22 (SSH)

### Issue: Can't access app in browser

**Fix 1**: Check Ubuntu firewall
```bash
sudo ufw allow 5000
sudo ufw allow 80
```

**Fix 2**: Check Oracle Cloud Security List has port 5000/80 open

### Issue: Out of memory

**Fix**: Use ARM instance (VM.Standard.A1.Flex) with 24GB RAM
- Stop current instance
- Create new ARM instance
- Migrate data

### Issue: App crashes

**Fix**: Check logs
```bash
sudo journalctl -u cv-redactor -n 100
```

---

## Cost Monitoring

Even though it's free, monitor usage:

1. **Go to**: Billing → Cost Analysis
2. **Check**: You're within Always Free limits
3. **Set alerts**: If usage approaches limits

---

## Advantages Over Render/Railway

| Feature | Oracle Free | Render Free | Railway |
|---------|-------------|-------------|---------|
| RAM | 1-24GB | 512MB | 8GB |
| Cost | $0 forever | $0 (limited) | $5/month |
| Timeout | None | 15min idle | None |
| Storage | 200GB | 1GB | 5GB |
| Dependencies | All | Limited | All |

---

## Next Steps

1. **Create Oracle Cloud account** (10 minutes)
2. **Create VM instance** (5 minutes)
3. **Upload your app** (10 minutes)
4. **Install dependencies** (10 minutes)
5. **Test and deploy** (5 minutes)

**Total time**: ~40 minutes for full deployment

---

## Need Help?

If you get stuck:
1. Share the error message
2. Share which phase you're on
3. I'll help you troubleshoot

---

**Ready to deploy?** Start with Phase 1 and let me know when you need help!
