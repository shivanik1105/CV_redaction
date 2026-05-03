# Role-Specific Chatbot - Quick Guide

## What This Is

A template system to create unique chatbots for each recruitment role. Share links with candidates so they can get instant answers about the job, client, and application process 24/7.

## Quick Start (5 minutes)

### 1. Create a New Role

```bash
python chatbot/create_role_chatbot.py --name "Senior Python Developer"
```

This creates a folder: `chatbot/roles/senior_python_developer/`

### 2. Edit the Content Files

Navigate to the role folder and edit these files:

- `job_description.txt` - Full job description
- `client_info.txt` - Company details and culture
- `faqs.txt` - Common candidate questions and answers
- `additional_info.txt` - Any extra information
- `.env` - Add your `GEMINI_API_KEY`

### 3. Launch the Chatbot

```bash
python chatbot/role_chatbot_template.py --role senior_python_developer --share
```

### 4. Share the Link

Copy the public URL (e.g., `https://xxxxx.gradio.live`) and share it with candidates!

## Example Questions Candidates Can Ask

- "What are the main responsibilities?"
- "Tell me about the company"
- "What's the salary range?"
- "Is this role remote?"
- "What's the interview process?"
- "What tech stack do you use?"
- "What benefits do you offer?"

## Useful Commands

### List All Roles
```bash
python chatbot/list_roles.py
```

### Launch Without Public Link (Local Only)
```bash
python chatbot/role_chatbot_template.py --role senior_python_developer
```

### Launch on Different Port
```bash
python chatbot/role_chatbot_template.py --role senior_python_developer --port 8080
```

## Tips

1. **Better Content = Better Responses**: Spend time writing detailed, clear content files
2. **Test First**: Ask 10+ questions before sharing with candidates
3. **Update Regularly**: Keep information current
4. **Use FAQs**: Add common questions to faqs.txt for best results

## Getting API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a free API key
3. Add it to your role's `.env` file:
   ```
   GEMINI_API_KEY=your-key-here
   ```

## Dependencies

```bash
pip install openai python-dotenv gradio
```

## File Structure

```
chatbot/
├── role_chatbot_template.py    # Main chatbot engine
├── create_role_chatbot.py      # Create new roles
├── list_roles.py                # List all roles
└── roles/
    ├── senior_python_developer/
    │   ├── job_description.txt
    │   ├── client_info.txt
    │   ├── faqs.txt
    │   ├── additional_info.txt
    │   └── .env
    └── frontend_engineer/
        └── ...
```

## Benefits

- **Save Time**: Candidates get instant answers 24/7
- **Consistency**: Everyone gets the same accurate information
- **Scalability**: Handle 100+ candidates without extra recruiter time
- **Better Experience**: Candidates can learn at their own pace

## Next Steps

1. Create your first role chatbot
2. Test it thoroughly
3. Share with a few candidates for feedback
4. Iterate and improve
5. Create chatbots for all your active roles

---

For more details, see:
- `README.md` - Complete overview
- `ROLE_CHATBOT_GUIDE.md` - Detailed guide
- `roles/example_senior_python_dev/` - Example role
