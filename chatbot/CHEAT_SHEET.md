# Chatbot System - Cheat Sheet

Quick reference for common commands and workflows.

## 🚀 Quick Commands

### Create New Role
```bash
python chatbot/create_role_chatbot.py --name "Role Name"
```

### List All Roles
```bash
python chatbot/list_roles.py
```

### Launch Role Chatbot (Local)
```bash
python chatbot/role_chatbot_template.py --role role_name
```

### Launch Role Chatbot (Shareable)
```bash
python chatbot/role_chatbot_template.py --role role_name --share
```

### Launch Personal Chatbot
```bash
python chatbot/chatbot.py
```

---

## 📁 File Locations

### Role Content Files
```
chatbot/roles/YOUR_ROLE_NAME/
├── job_description.txt    ← Full JD
├── client_info.txt        ← Company details
├── faqs.txt               ← Q&A
├── additional_info.txt    ← Extra info
└── .env                   ← API key
```

### Configuration
```
chatbot/.env               ← Personal chatbot config
chatbot/roles/ROLE/.env    ← Role-specific config
```

---

## ⚙️ Environment Variables

### Required
```bash
GEMINI_API_KEY=your-key
```

### Optional
```bash
SERPER_API_KEY=your-key           # Web search
CHATBOT_MODEL=gemini-2.5-flash-lite
MAX_HISTORY_MESSAGES=10
CHUNK_SIZE=1500
CHUNK_OVERLAP=200
MAX_CONTEXT_CHUNKS=4
```

---

## 🔄 Common Workflows

### Workflow 1: Create New Role (15 min)
```bash
# 1. Create (1 min)
python chatbot/create_role_chatbot.py --name "Senior Python Dev"

# 2. Edit files (10 min)
# Edit: roles/senior_python_dev/*.txt
# Add: GEMINI_API_KEY to roles/senior_python_dev/.env

# 3. Test (2 min)
python chatbot/role_chatbot_template.py --role senior_python_dev

# 4. Deploy (2 min)
python chatbot/role_chatbot_template.py --role senior_python_dev --share
```

### Workflow 2: Update Existing Role
```bash
# 1. Edit content files
# Edit: roles/role_name/*.txt

# 2. Relaunch
python chatbot/role_chatbot_template.py --role role_name --share
```

### Workflow 3: Check All Roles
```bash
# List all roles with status
python chatbot/list_roles.py
```

---

## 💬 Example Questions

### For Role Chatbots
- "What are the main responsibilities?"
- "Tell me about the company"
- "What's the salary range?"
- "Is this role remote?"
- "What's the interview process?"
- "What benefits do you offer?"
- "What tech stack do you use?"
- "How do I apply?"

### For Personal Chatbot
- "Tell me about your experience"
- "What projects have you worked on?"
- "What does [Company Name] do?"
- "Tell me about your skills"

---

## 🐛 Troubleshooting

### Error: "API key not found"
```bash
# Check .env file exists and has key
cat chatbot/roles/YOUR_ROLE/.env
# Should show: GEMINI_API_KEY=xxx
```

### Error: "Role folder not found"
```bash
# List available roles
python chatbot/list_roles.py
```

### Poor Response Quality
```bash
# Add more detail to content files
# Especially: faqs.txt
```

### Slow Responses
```bash
# In .env, reduce:
CHUNK_SIZE=1000
MAX_CONTEXT_CHUNKS=2
```

---

## 📊 Status Indicators

```
✅ = Ready to launch (100% complete)
⚠️ = Missing some files (75%+ complete)
❌ = Incomplete setup (<75% complete)
```

---

## 🔗 Quick Links

### Get API Keys
- Gemini: https://makersuite.google.com/app/apikey
- Serper: https://serper.dev

### Documentation
- Setup: [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
- Quick Start: [QUICK_START_ROLE_CHATBOT.md](QUICK_START_ROLE_CHATBOT.md)
- Full Guide: [ROLE_CHATBOT_GUIDE.md](ROLE_CHATBOT_GUIDE.md)
- Index: [INDEX.md](INDEX.md)

---

## 📦 Installation

```bash
# Install dependencies
pip install openai python-dotenv pypdf gradio requests

# Verify installation
python -c "import openai, dotenv, pypdf, gradio, requests; print('✅ Ready')"
```

---

## 🎯 Best Practices

### Content
- ✅ Be specific and detailed
- ✅ Use real examples
- ✅ Keep information current
- ❌ Don't leave placeholders

### Testing
- ✅ Test before sharing
- ✅ Ask 10+ questions
- ✅ Verify accuracy
- ❌ Don't skip testing

### Deployment
- ✅ Use --share for candidates
- ✅ Regenerate links weekly
- ✅ Monitor usage
- ❌ Don't share untested bots

---

## 💰 Cost Estimates

### Per Role
- Setup: 15 minutes
- API cost: $1-5/month
- Candidates: Unlimited
- Questions: Unlimited

### ROI
- Traditional: $625 per role
- With chatbot: $15 per role
- Savings: 97%

---

## 🎨 Customization

### Change Model
```bash
# In .env
CHATBOT_MODEL=gemini-2.0-flash-exp
```

### Adjust Context
```bash
# In .env
MAX_CONTEXT_CHUNKS=6    # More context
CHUNK_SIZE=2000         # Larger chunks
```

### Limit History
```bash
# In .env
MAX_HISTORY_MESSAGES=5  # Shorter memory
```

---

## 📱 Sharing with Candidates

### Email Template
```
Hi [Name],

I've set up an AI chatbot to answer your questions about 
the [Role] position 24/7:

🤖 [Link]

Ask anything about the role, company, process, or benefits!

Best,
[Your Name]
```

### Job Posting
```
💬 Have questions? Chat with our AI assistant: [Link]
```

### LinkedIn
```
Interested in this role? Get instant answers from our 
chatbot: [Link]
```

---

## 🔄 Update Checklist

Before sharing with candidates:
- [ ] All content files filled in
- [ ] API key added to .env
- [ ] Tested with 10+ questions
- [ ] Responses are accurate
- [ ] Contact info is current
- [ ] Shareable link generated
- [ ] Link tested in incognito

---

## 🆘 Emergency Fixes

### Chatbot Down
```bash
# Regenerate link
python chatbot/role_chatbot_template.py --role ROLE --share
```

### Wrong Information
```bash
# 1. Edit content file
# 2. Restart chatbot
# 3. Test the fix
```

### API Limit Hit
```bash
# Check usage at:
# https://console.cloud.google.com/apis/dashboard
```

---

## 📈 Success Metrics

Track:
- Conversations per day
- Questions per conversation
- Application rate
- Time saved
- Candidate satisfaction

---

**Keep this cheat sheet handy for quick reference!**

For detailed information, see [INDEX.md](INDEX.md)
