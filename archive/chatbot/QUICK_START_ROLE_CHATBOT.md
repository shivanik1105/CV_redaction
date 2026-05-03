# Quick Start: Role Chatbot System

Create shareable chatbots for job roles in 3 simple steps.

## Step 1: Create Role Folder

```bash
python chatbot/create_role_chatbot.py --name "Senior Python Developer"
```

This creates: `chatbot/roles/senior_python_developer/`

## Step 2: Add Content

Edit these 4 files in your role folder:

1. **job_description.txt** - Full JD with responsibilities, skills, salary
2. **client_info.txt** - Company overview, culture, tech stack
3. **faqs.txt** - Common questions about process, benefits, work arrangement
4. **.env** - Add your `GEMINI_API_KEY=xxx`

## Step 3: Launch & Share

```bash
# Create shareable link
python chatbot/role_chatbot_template.py --role senior_python_developer --share
```

Copy the generated link and share with candidates!

## Example Questions Candidates Can Ask

- "What are the main responsibilities?"
- "Tell me about the company culture"
- "What's the salary range?"
- "Is this role remote?"
- "What's the interview process?"
- "What benefits do you offer?"
- "What tech stack do you use?"
- "How do I apply?"

## Tips

✅ Be specific and detailed in your content files
✅ Update FAQs based on common candidate questions
✅ Test the chatbot before sharing
✅ Keep information current

❌ Don't leave placeholder text
❌ Don't forget to add your API key
❌ Don't share outdated information

## Need Help?

See the full guide: `chatbot/ROLE_CHATBOT_GUIDE.md`

## Example

Check out the example role:
```bash
python chatbot/role_chatbot_template.py --role example_senior_python_dev --share
```

---

**That's it! You're ready to create role-specific chatbots for your recruitment needs.**
