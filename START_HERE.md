# 🚀 START HERE - CV Intelligence System

Welcome! This document will guide you to the right place based on what you want to do.

---

## 👤 I'm a User (I want to use the application)

**Read**: `USER_GUIDE.md`

**Quick Start**:
1. Open http://127.0.0.1:5000 in your browser
2. Go to "Upload and Process Single CV" tab
3. Get API key from https://console.groq.com/keys
4. Upload a CV with your API key
5. Search for candidates in "Search & Filter CVs" tab

**Learn**:
- How to upload CVs
- How to search candidates
- How to download results
- Tips for best results

---

## 👨‍💻 I'm a Developer (I want to run/modify the code)

**Read**: `SETUP_GUIDE.md`

**Quick Start**:
```bash
# 1. Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
# Create .env file with API keys

# 3. Run
python app.py
```

**Learn**:
- How to install dependencies
- How to configure environment
- How to run locally
- How to troubleshoot issues
- Project structure

---

## 🚀 I Want to Deploy to Production

**Read**: `RENDER_DEPLOYMENT_GUIDE.md`

**Quick Start**:
```bash
# 1. Push to GitHub
git push origin main

# 2. Create Render service
# Go to https://render.com
# Connect GitHub repo

# 3. Add environment variables
# SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY
```

**Learn**:
- How to deploy to Render
- Environment variables needed
- Production configuration
- File storage considerations

---

## 📖 I Want Complete Documentation

**Read**: `README.md`

**Covers**:
- Project overview
- Features
- Installation
- Configuration
- Usage
- Troubleshooting
- System requirements

---

## 🎯 Quick Reference

### For Users:
```
1. Get API key: https://console.groq.com/keys
2. Open app: http://127.0.0.1:5000
3. Upload CV with API key
4. Search candidates
5. Download results
```

### For Developers:
```
1. Clone repo
2. Install: pip install -r requirements.txt
3. Configure: Create .env file
4. Run: python app.py
5. Test: http://127.0.0.1:5000
```

### For Deployment:
```
1. Push to GitHub
2. Create Render service
3. Add environment variables
4. Deploy automatically
```

---

## 📚 All Documentation Files

| File | Purpose | For |
|------|---------|-----|
| `START_HERE.md` | This file - navigation | Everyone |
| `README.md` | Complete documentation | Everyone |
| `USER_GUIDE.md` | How to use the app | Users |
| `SETUP_GUIDE.md` | How to run locally | Developers |
| `RENDER_DEPLOYMENT_GUIDE.md` | How to deploy | DevOps |
| `VISUAL_MASKING_FIX.md` | Visual PDF masking details | Developers |
| `UPLOAD_FIX_SUMMARY.md` | Upload feature fixes | Developers |
| `CURRENT_STATUS.md` | Project status | Everyone |

---

## ❓ Common Questions

### Q: How do I start using the application?
**A**: Read `USER_GUIDE.md` → Get API key → Upload CVs → Search

### Q: How do I run the application locally?
**A**: Read `SETUP_GUIDE.md` → Install dependencies → Configure → Run

### Q: How do I deploy to production?
**A**: Read `RENDER_DEPLOYMENT_GUIDE.md` → Push to GitHub → Deploy on Render

### Q: Where do I get API keys?
**A**: 
- Supabase: https://supabase.com
- Groq (Free): https://console.groq.com/keys
- OpenAI: https://platform.openai.com/api-keys

### Q: What does this application do?
**A**: 
1. Uploads CVs and removes personal information
2. Extracts skills, experience, and intelligence
3. Searches candidates using AI matching
4. Downloads anonymized CVs with visual black boxes

---

## 🆘 Need Help?

1. **Check the relevant guide** (see table above)
2. **Check troubleshooting sections** in each guide
3. **Check application logs** in the terminal
4. **Restart the application** - fixes many issues
5. **Contact support** if nothing works

---

## 🎉 Quick Start for Everyone

### Absolute Beginner:
1. Read `USER_GUIDE.md`
2. Get API key from Groq
3. Use the application

### Developer:
1. Read `SETUP_GUIDE.md`
2. Install and configure
3. Run locally

### DevOps:
1. Read `RENDER_DEPLOYMENT_GUIDE.md`
2. Deploy to Render
3. Monitor and maintain

---

**Choose your path above and get started!** 🚀
