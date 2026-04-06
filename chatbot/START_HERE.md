# 👋 Welcome to the Chatbot System!

You now have a complete recruitment chatbot infrastructure. Here's how to get started.

## 🎯 What You Have

Two powerful chatbot systems:

1. **Personal Site Chatbot** - For Amit's website (with company search)
2. **Role-Specific Chatbots** - Create unique chatbots for each job role

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies (2 minutes)

```bash
pip install openai python-dotenv pypdf gradio requests
```

### Step 2: Get API Key (2 minutes)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a free API key
3. Copy it

### Step 3: Try the Example (1 minute)

Create a `.env` file in the example role:
```bash
# Copy the example
cp roles/example_senior_python_dev/.env.example roles/example_senior_python_dev/.env

# Edit it and add your API key
# GEMINI_API_KEY=your-actual-key-here
```

Launch the example:
```bash
python role_chatbot_template.py --role example_senior_python_dev
```

Open the URL in your browser and ask:
- "What are the main responsibilities?"
- "What's the salary range?"
- "Tell me about the company"

## 🎉 That's It!

You just launched your first recruitment chatbot!

---

## 📚 What to Read Next

### If you want to...

**Create your first real role chatbot**
→ Read [QUICK_START_ROLE_CHATBOT.md](QUICK_START_ROLE_CHATBOT.md) (5 min read)

**Understand the complete system**
→ Read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) (10 min read)

**Set up everything properly**
→ Read [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) (15 min read)

**Learn all features and best practices**
→ Read [ROLE_CHATBOT_GUIDE.md](ROLE_CHATBOT_GUIDE.md) (30 min read)

**Quick command reference**
→ Read [CHEAT_SHEET.md](CHEAT_SHEET.md) (2 min read)

**Navigate all documentation**
→ Read [INDEX.md](INDEX.md) (3 min read)

---

## 🎓 Quick Tutorial

### Create Your First Role (15 minutes)

**1. Create the role**
```bash
python create_role_chatbot.py --name "Senior Python Developer"
```

**2. Edit the files**

Navigate to `roles/senior_python_developer/` and edit:
- `job_description.txt` - Add your actual JD
- `client_info.txt` - Add company details
- `faqs.txt` - Add common Q&As
- `.env` - Add your API key

**3. Test it**
```bash
python role_chatbot_template.py --role senior_python_developer
```

Ask some questions to verify responses are good.

**4. Share it**
```bash
python role_chatbot_template.py --role senior_python_developer --share
```

Copy the generated link and share with candidates!

---

## 💡 Pro Tips

### Content is King
The better your content files, the better the chatbot responses. Spend time on:
- Detailed job descriptions
- Comprehensive FAQs
- Specific company information

### Test Before Sharing
Always test with 10+ questions before sharing with candidates.

### Keep It Updated
Review and update content monthly to keep information current.

### Monitor Usage
Pay attention to which questions candidates ask most and add them to FAQs.

---

## 🗺️ Documentation Map

```
START_HERE.md (you are here)
    ↓
QUICK_START_ROLE_CHATBOT.md (5 min)
    ↓
SETUP_INSTRUCTIONS.md (15 min)
    ↓
ROLE_CHATBOT_GUIDE.md (30 min)
    ↓
SYSTEM_OVERVIEW.md (deep dive)
    ↓
ARCHITECTURE.md (technical details)
```

**Reference:**
- [INDEX.md](INDEX.md) - Documentation hub
- [CHEAT_SHEET.md](CHEAT_SHEET.md) - Quick commands
- [README.md](README.md) - Main overview

---

## 🎯 Common Use Cases

### Use Case 1: High-Volume Role
You have 100+ applicants for a popular position.

**Solution:** Create a chatbot to answer common questions 24/7.
- Saves 10+ hours of recruiter time
- Provides instant answers to candidates
- Ensures consistent information

### Use Case 2: Confidential Client
Client name can't be disclosed yet.

**Solution:** Create a chatbot with general company info.
- Share industry and culture details
- Explain why anonymity is needed
- Provide enough info for candidates to decide

### Use Case 3: International Role
Role requires visa sponsorship and relocation.

**Solution:** Create a chatbot with detailed visa/relocation info.
- Explain visa sponsorship process
- Provide relocation support details
- Address timezone and remote work questions

---

## 📊 What You'll Achieve

### Week 1
- ✅ Set up the system
- ✅ Create 1-2 role chatbots
- ✅ Test with colleagues
- ✅ Share with first candidates

### Week 2
- ✅ Create 3-5 more roles
- ✅ Gather candidate feedback
- ✅ Iterate on content
- ✅ Track time savings

### Month 1
- ✅ Chatbots for all active roles
- ✅ 10+ hours saved per week
- ✅ Better candidate experience
- ✅ Faster time-to-hire

---

## 🚦 Your Next Action

Choose one:

### Option A: Quick Test (5 minutes)
```bash
# Test the example role
python role_chatbot_template.py --role example_senior_python_dev
```

### Option B: Create First Role (15 minutes)
```bash
# Create your first real role
python create_role_chatbot.py --name "Your Role Name"
# Then edit the files and launch
```

### Option C: Learn More (10 minutes)
Read [QUICK_START_ROLE_CHATBOT.md](QUICK_START_ROLE_CHATBOT.md)

---

## 🆘 Need Help?

### Quick Fixes

**"Command not found"**
→ Make sure you're in the chatbot/ directory

**"API key not found"**
→ Check your .env file has GEMINI_API_KEY=your-key

**"Module not found"**
→ Run: `pip install openai python-dotenv pypdf gradio requests`

### Documentation

All questions answered in:
- [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - Setup help
- [ROLE_CHATBOT_GUIDE.md](ROLE_CHATBOT_GUIDE.md) - Complete guide
- [CHEAT_SHEET.md](CHEAT_SHEET.md) - Quick reference

---

## 🎉 Ready to Transform Your Recruitment?

You have everything you need:
- ✅ Working code
- ✅ Complete documentation
- ✅ Example role
- ✅ Easy deployment

**Start with the example, then create your first real role!**

```bash
# Test example
python role_chatbot_template.py --role example_senior_python_dev

# Create your own
python create_role_chatbot.py --name "Your Role Name"
```

---

**Questions?** Check [INDEX.md](INDEX.md) for documentation navigation.

**Ready?** Go to [QUICK_START_ROLE_CHATBOT.md](QUICK_START_ROLE_CHATBOT.md) →
