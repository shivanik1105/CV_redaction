# Role-Specific Information Chatbots

Create unique chatbots for each recruitment role that candidates can interact with to get detailed information about the position, client, and application process.

## Quick Start

```bash
# 1. Create a new role chatbot
python chatbot/create_role_chatbot.py --name "Senior Python Developer"

# 2. Edit the generated files in chatbot/roles/senior_python_developer/
#    - job_description.txt
#    - client_info.txt
#    - faqs.txt
#    - .env (add GEMINI_API_KEY)

# 3. Launch and share
python chatbot/role_chatbot_template.py --role senior_python_developer --share
```

## What It Does

- Creates unique chatbots for each recruitment role
- Candidates can ask about JD, client, process, benefits, etc.
- Automatically selects relevant information to answer questions
- Generates shareable links for easy distribution

## Use Cases

- Share with candidates to answer common questions 24/7
- Reduce recruiter time on repetitive inquiries
- Provide consistent information to all candidates
- Pre-qualify candidates with detailed role information

## Files Structure

```
chatbot/roles/
├── senior_python_developer/
│   ├── job_description.txt    # Full JD
│   ├── client_info.txt        # Company details
│   ├── faqs.txt               # Common questions
│   ├── additional_info.txt    # Extra information
│   └── .env                   # API keys
└── frontend_engineer/
    └── ...
```

## Documentation

- **Quick Start**: `QUICK_START_ROLE_CHATBOT.md`
- **Full Guide**: `ROLE_CHATBOT_GUIDE.md`
- **Example Role**: `roles/example_senior_python_dev/`

## Example Questions Candidates Can Ask

- "What are the main responsibilities?"
- "Tell me about the company culture"
- "What's the salary range?"
- "Is this role remote?"
- "What's the interview process?"
- "What benefits do you offer?"
- "What tech stack do you use?"

## Dependencies

```bash
pip install openai python-dotenv gradio
```
