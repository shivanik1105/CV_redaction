# Chatbot System - Documentation Index

Quick navigation to all documentation and resources.

## 🚀 Getting Started

**New to the system?** Start here:
1. [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - Complete setup guide
2. [QUICK_START_ROLE_CHATBOT.md](QUICK_START_ROLE_CHATBOT.md) - 3-step quick start

## 📚 Documentation

### Overview
- [README.md](README.md) - Main overview of both chatbot systems
- [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - Architecture and technical details

### Guides
- [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - Step-by-step setup
- [ROLE_CHATBOT_GUIDE.md](ROLE_CHATBOT_GUIDE.md) - Comprehensive role chatbot guide
- [QUICK_START_ROLE_CHATBOT.md](QUICK_START_ROLE_CHATBOT.md) - Quick reference

## 🛠️ Scripts & Tools

### Main Scripts
- `chatbot.py` - Personal site chatbot (Amit Babel)
- `role_chatbot_template.py` - Role chatbot engine
- `create_role_chatbot.py` - Create new role chatbots
- `list_roles.py` - List all available roles

### Launcher Scripts
- `launch_role_chatbot.ps1` - Windows PowerShell launcher
- `launch_role_chatbot.sh` - Linux/Mac bash launcher

## 📁 Examples

### Example Role
- `roles/example_senior_python_dev/` - Fully populated example
  - `job_description.txt` - Sample JD
  - `client_info.txt` - Sample client info
  - `faqs.txt` - Sample FAQs
  - `additional_info.txt` - Sample additional info
  - `.env.example` - Configuration template

## 🎯 Common Tasks

### Create a New Role Chatbot
```bash
python chatbot/create_role_chatbot.py --name "Your Role Name"
```

### List All Roles
```bash
python chatbot/list_roles.py
```

### Launch a Role Chatbot
```bash
python chatbot/role_chatbot_template.py --role your_role --share
```

### Test Personal Site Chatbot
```bash
python chatbot/chatbot.py
```

## 📖 Documentation by Use Case

### I want to...

**...understand what this system does**
→ Read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)

**...set up the chatbots for the first time**
→ Follow [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)

**...quickly create a role chatbot**
→ Use [QUICK_START_ROLE_CHATBOT.md](QUICK_START_ROLE_CHATBOT.md)

**...learn all features and best practices**
→ Read [ROLE_CHATBOT_GUIDE.md](ROLE_CHATBOT_GUIDE.md)

**...see a working example**
→ Check `roles/example_senior_python_dev/`

**...troubleshoot issues**
→ See troubleshooting sections in [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)

## 🔗 Quick Links

### External Resources
- [Google AI Studio](https://makersuite.google.com/app/apikey) - Get Gemini API key
- [Serper.dev](https://serper.dev) - Get web search API key (optional)
- [Gradio Documentation](https://gradio.app/docs/) - Gradio framework docs
- [Hugging Face Spaces](https://huggingface.co/spaces) - Deploy chatbots permanently

### Dependencies
```bash
pip install openai python-dotenv pypdf gradio requests
```

## 📊 File Structure

```
chatbot/
├── Documentation
│   ├── INDEX.md (this file)
│   ├── README.md
│   ├── SETUP_INSTRUCTIONS.md
│   ├── QUICK_START_ROLE_CHATBOT.md
│   ├── ROLE_CHATBOT_GUIDE.md
│   └── SYSTEM_OVERVIEW.md
│
├── Scripts
│   ├── chatbot.py
│   ├── role_chatbot_template.py
│   ├── create_role_chatbot.py
│   ├── list_roles.py
│   ├── launch_role_chatbot.ps1
│   └── launch_role_chatbot.sh
│
├── Configuration
│   ├── .env
│   └── .env.example
│
├── Personal Chatbot Data
│   ├── summary.txt
│   └── Amit_Li_Profile.pdf
│
└── Role Chatbots
    └── roles/
        └── example_senior_python_dev/
            ├── job_description.txt
            ├── client_info.txt
            ├── faqs.txt
            ├── additional_info.txt
            └── .env.example
```

## 💡 Tips

- Start with the example role to understand the structure
- Test thoroughly before sharing with candidates
- Keep content updated regularly
- Monitor which questions are asked most
- Iterate based on candidate feedback

## 🆘 Need Help?

1. Check the relevant documentation above
2. Review the example role
3. Run `python chatbot/list_roles.py` to verify setup
4. Check error messages carefully
5. Verify API keys are set correctly

---

**Ready to get started?** → [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
