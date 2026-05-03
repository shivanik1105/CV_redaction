# Complete Setup Instructions

Follow these steps to set up and use the chatbot systems.

## Prerequisites

1. **Python 3.8+** installed
2. **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Serper API Key** (optional) from [serper.dev](https://serper.dev) for web search

## Installation

### Step 1: Install Dependencies

```bash
pip install openai python-dotenv pypdf gradio requests
```

### Step 2: Verify Installation

```bash
python -c "import openai, dotenv, pypdf, gradio, requests; print('✅ All dependencies installed')"
```

---

## Setup Personal Site Chatbot

### Step 1: Configure Environment

Copy the example env file:
```bash
cp chatbot/.env.example chatbot/.env
```

Edit `chatbot/.env` and add your keys:
```bash
GEMINI_API_KEY=your-actual-gemini-api-key
SERPER_API_KEY=your-actual-serper-api-key  # Optional
```

### Step 2: Test the Chatbot

```bash
python chatbot/chatbot.py
```

Open the URL shown in your browser and test with questions like:
- "Tell me about your experience"
- "What does Google do?" (tests web search)

---

## Setup Role-Specific Chatbots

### Step 1: Create Your First Role

```bash
python chatbot/create_role_chatbot.py --name "Senior Python Developer"
```

This creates: `chatbot/roles/senior_python_developer/`

### Step 2: Add Content

Navigate to the role folder and edit these files:

**1. job_description.txt**
```
# Senior Python Developer

## About the Role
[Add your actual job description]

## Key Responsibilities
- [Responsibility 1]
- [Responsibility 2]

## Required Skills
- [Skill 1]
- [Skill 2]

## Salary Range
$120,000 - $160,000
```

**2. client_info.txt**
```
# Client Information

## Company Overview
[Describe the client company]

## Industry
[Industry sector]

## Culture
[Company culture and values]

## Tech Stack
[Technologies used]
```

**3. faqs.txt**
```
# Frequently Asked Questions

## Application Process
Q: How do I apply?
A: [Your answer]

Q: What's the timeline?
A: [Your answer]

## Compensation
Q: What's the salary range?
A: [Your answer]

[Add more Q&As based on common candidate questions]
```

**4. additional_info.txt**
```
# Additional Information

## Contact Information
Recruiter: [Name]
Email: [Email]
Phone: [Phone]

## Next Steps
[What happens after applying]
```

**5. .env**
```bash
GEMINI_API_KEY=your-actual-gemini-api-key
```

### Step 3: Test Your Role Chatbot

```bash
python chatbot/role_chatbot_template.py --role senior_python_developer
```

Test with questions like:
- "What are the main responsibilities?"
- "Tell me about the company"
- "What's the salary range?"
- "How do I apply?"

### Step 4: Create Shareable Link

```bash
python chatbot/role_chatbot_template.py --role senior_python_developer --share
```

This generates a public URL like: `https://abc123.gradio.live`

**Note**: Gradio share links expire after 72 hours. Regenerate as needed.

---

## Managing Multiple Roles

### List All Roles

```bash
python chatbot/list_roles.py
```

Output shows:
- ✅ Ready to launch (all files present)
- ⚠️ Missing some files
- ❌ Incomplete setup

### Create Multiple Roles

```bash
python chatbot/create_role_chatbot.py --name "Frontend Engineer"
python chatbot/create_role_chatbot.py --name "Data Scientist"
python chatbot/create_role_chatbot.py --name "DevOps Engineer"
```

### Launch Specific Role

**Windows (PowerShell):**
```powershell
.\chatbot\launch_role_chatbot.ps1 -Role "senior_python_developer" -Share
```

**Linux/Mac:**
```bash
chmod +x chatbot/launch_role_chatbot.sh
./chatbot/launch_role_chatbot.sh senior_python_developer --share
```

**Cross-platform (Python):**
```bash
python chatbot/role_chatbot_template.py --role senior_python_developer --share
```

---

## Deployment Options

### Option 1: Local Testing
Run locally for testing:
```bash
python chatbot/role_chatbot_template.py --role your_role
```

### Option 2: Temporary Public Link
Use Gradio's share feature (72-hour limit):
```bash
python chatbot/role_chatbot_template.py --role your_role --share
```

### Option 3: Hugging Face Spaces (Permanent)

1. Create account at [huggingface.co](https://huggingface.co)
2. Create new Space (Gradio SDK)
3. Upload your role folder and scripts
4. Add `GEMINI_API_KEY` to Space secrets
5. Your chatbot gets a permanent URL

### Option 4: Cloud Deployment

Deploy to cloud platforms:
- **AWS**: EC2 + Elastic IP
- **Google Cloud**: Cloud Run
- **Azure**: App Service
- **DigitalOcean**: Droplet

---

## Workflow for Each New Role

### Quick Workflow (15 minutes)

1. **Create** (1 min)
   ```bash
   python chatbot/create_role_chatbot.py --name "Role Name"
   ```

2. **Edit Content** (10 min)
   - Copy JD into `job_description.txt`
   - Add client details to `client_info.txt`
   - Fill in FAQs from past candidate questions
   - Add API key to `.env`

3. **Test** (2 min)
   ```bash
   python chatbot/role_chatbot_template.py --role role_name
   ```
   Ask 5-10 test questions

4. **Deploy** (2 min)
   ```bash
   python chatbot/role_chatbot_template.py --role role_name --share
   ```
   Copy the link

5. **Share** (immediate)
   - Add link to job posting
   - Include in candidate emails
   - Share on LinkedIn

---

## Best Practices

### Content Quality

✅ **Do:**
- Be specific and detailed
- Use real salary ranges
- Include actual tech stack
- Address common concerns
- Keep information current

❌ **Don't:**
- Leave placeholder text
- Be vague about compensation
- Oversell the role
- Include outdated information
- Use generic descriptions

### Testing

Before sharing with candidates:
1. Ask 10+ diverse questions
2. Verify all answers are accurate
3. Check response quality
4. Test edge cases
5. Get colleague feedback

### Maintenance

Regular tasks:
- Update content monthly
- Review candidate questions
- Add new FAQs as needed
- Refresh shareable links
- Monitor API usage

---

## Troubleshooting

### "API key not found"
**Solution**: Check `.env` file has `GEMINI_API_KEY=your-key`

### "Role folder not found"
**Solution**: Run `python chatbot/list_roles.py` to see available roles

### "Poor quality responses"
**Solution**: Add more detail to content files, especially FAQs

### "Slow responses"
**Solution**: Reduce `CHUNK_SIZE` and `MAX_CONTEXT_CHUNKS` in `.env`

### "Gradio link expired"
**Solution**: Regenerate with `--share` flag (links last 72 hours)

### "Import errors"
**Solution**: Reinstall dependencies:
```bash
pip install --upgrade openai python-dotenv pypdf gradio requests
```

---

## Cost Estimation

### Gemini API (Free Tier)
- 15 requests per minute
- 1,500 requests per day
- Free for moderate usage

### Gemini API (Paid)
- ~$0.001 per request
- 100 candidates × 10 questions = $1
- Very cost-effective

### Serper API (Optional)
- 2,500 free searches/month
- $50/month for 10,000 searches
- Only needed for company questions

---

## Security Checklist

✅ Never commit `.env` files to git
✅ Use separate API keys per environment
✅ Monitor API usage regularly
✅ Don't include sensitive client info
✅ Review content before sharing
✅ Keep dependencies updated

---

## Getting Help

### Documentation
- `README.md` - Overview
- `ROLE_CHATBOT_GUIDE.md` - Comprehensive guide
- `QUICK_START_ROLE_CHATBOT.md` - Quick reference
- `SYSTEM_OVERVIEW.md` - Architecture overview

### Example
- `roles/example_senior_python_dev/` - Fully populated example

### Commands
```bash
# List all roles
python chatbot/list_roles.py

# Test example role
python chatbot/role_chatbot_template.py --role example_senior_python_dev

# Create new role
python chatbot/create_role_chatbot.py --name "Your Role"
```

---

## Success Checklist

Before sharing with candidates:

- [ ] All content files filled in completely
- [ ] API key added to `.env`
- [ ] Tested with 10+ questions
- [ ] Responses are accurate and helpful
- [ ] Salary and benefits information is current
- [ ] Contact information is correct
- [ ] Shareable link generated
- [ ] Link tested in incognito browser
- [ ] Colleague has reviewed

---

## Next Steps

1. **Start with the example**
   ```bash
   python chatbot/role_chatbot_template.py --role example_senior_python_dev
   ```

2. **Create your first real role**
   ```bash
   python chatbot/create_role_chatbot.py --name "Your Role Name"
   ```

3. **Fill in the content files**

4. **Test thoroughly**

5. **Share with candidates**

6. **Gather feedback and iterate**

---

**You're all set! Start creating role-specific chatbots and transform your recruitment process.** 🚀
