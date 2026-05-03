# Role Chatbots Directory

This directory contains all your role-specific chatbots. Each folder represents one job role.

## 📁 Structure

```
roles/
├── example_senior_python_dev/    ← Example (fully populated)
├── your_role_1/                  ← Your roles
├── your_role_2/
└── your_role_3/
```

## 🚀 Quick Start

### Create a New Role

```bash
cd ../..  # Go to project root
python chatbot/create_role_chatbot.py --name "Your Role Name"
```

This creates a new folder with template files.

### Required Files per Role

Each role folder must contain:

```
role_name/
├── job_description.txt     ← Full job description
├── client_info.txt         ← Company information
├── faqs.txt                ← Common questions & answers
├── additional_info.txt     ← Extra information
└── .env                    ← API configuration
```

## 📝 File Templates

### job_description.txt
```
# Job Title

## About the Role
[Description]

## Key Responsibilities
- [Responsibility 1]
- [Responsibility 2]

## Required Skills
- [Skill 1]
- [Skill 2]

## Salary Range
[Range]
```

### client_info.txt
```
# Client Information

## Company Overview
[Description]

## Industry
[Sector]

## Culture
[Culture description]

## Tech Stack
[Technologies]
```

### faqs.txt
```
# Frequently Asked Questions

## Application Process
Q: How do I apply?
A: [Answer]

## Compensation
Q: What's the salary?
A: [Answer]

[More Q&As]
```

### additional_info.txt
```
# Additional Information

## Contact
Recruiter: [Name]
Email: [Email]

## Next Steps
[Process]
```

### .env
```bash
GEMINI_API_KEY=your-key-here
```

## 🎯 Example Role

Check out `example_senior_python_dev/` for a fully populated example with:
- Detailed job description
- Comprehensive client information
- 20+ FAQs covering all common questions
- Complete additional information
- All best practices demonstrated

## 🔧 Managing Roles

### List All Roles
```bash
python ../list_roles.py
```

### Launch a Role
```bash
python ../role_chatbot_template.py --role role_name --share
```

### Test a Role
```bash
python ../role_chatbot_template.py --role role_name
```

## ✅ Checklist for Each Role

Before launching:
- [ ] Job description is complete and accurate
- [ ] Client information is detailed
- [ ] FAQs cover common candidate questions
- [ ] Contact information is current
- [ ] API key is set in .env
- [ ] Tested with 10+ questions
- [ ] All responses are accurate

## 💡 Tips

### Content Quality
- Be specific and detailed
- Use real examples
- Address concerns proactively
- Keep information current

### Common FAQs to Include
- Application process
- Salary and benefits
- Work arrangement (remote/hybrid/onsite)
- Interview process
- Company culture
- Tech stack
- Growth opportunities
- Timeline

### Updating Roles
1. Edit the content files
2. Restart the chatbot
3. Test the changes
4. Share the new link

## 📊 Role Status

Run `python ../list_roles.py` to see:
- ✅ Ready to launch (all files present)
- ⚠️ Missing some files
- ❌ Incomplete setup

## 🔄 Workflow

### For Each New Role (15 minutes)

1. **Create** (1 min)
   ```bash
   python ../create_role_chatbot.py --name "Role Name"
   ```

2. **Edit** (10 min)
   - Fill in all .txt files
   - Add API key to .env

3. **Test** (2 min)
   ```bash
   python ../role_chatbot_template.py --role role_name
   ```

4. **Deploy** (2 min)
   ```bash
   python ../role_chatbot_template.py --role role_name --share
   ```

5. **Share** with candidates!

## 🎨 Customization

### Per-Role Configuration

Add to role's `.env`:
```bash
GEMINI_API_KEY=your-key
CHATBOT_MODEL=gemini-2.5-flash-lite
MAX_HISTORY_MESSAGES=10
CHUNK_SIZE=1500
MAX_CONTEXT_CHUNKS=4
```

### Content Tone

Adjust formality based on:
- Company culture
- Role level
- Industry norms

## 📈 Best Practices

### Successful Roles Have:
- Detailed, specific information
- Honest, transparent answers
- Clear next steps
- Current, accurate data
- Professional but friendly tone

### Avoid:
- Generic descriptions
- Vague salary ranges
- Outdated information
- Overselling the role
- Missing contact details

## 🆘 Troubleshooting

### Role Won't Launch
- Check all required files exist
- Verify .env has API key
- Run `python ../list_roles.py` to check status

### Poor Responses
- Add more detail to content files
- Expand FAQs section
- Include specific examples

### Chatbot Gives Wrong Info
- Review and update content files
- Restart the chatbot
- Test thoroughly

## 📞 Need Help?

See the main documentation:
- [SETUP_INSTRUCTIONS.md](../SETUP_INSTRUCTIONS.md)
- [ROLE_CHATBOT_GUIDE.md](../ROLE_CHATBOT_GUIDE.md)
- [QUICK_START_ROLE_CHATBOT.md](../QUICK_START_ROLE_CHATBOT.md)

---

**Start by exploring the example role, then create your own!**

```bash
# Test the example
python ../role_chatbot_template.py --role example_senior_python_dev

# Create your first role
python ../create_role_chatbot.py --name "Your Role Name"
```
