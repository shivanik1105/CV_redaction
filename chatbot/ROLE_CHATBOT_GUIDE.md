# Role-Specific Information Chatbot System

A template-based system to quickly create shareable chatbots for specific job roles. Each chatbot is fed with the job description, client info, and FAQs to answer candidate questions.

## 🎯 Purpose

Create unique chatbots for each recruitment role that candidates can interact with to:
- Learn about the role and responsibilities
- Understand client culture and tech stack
- Get answers to common questions
- Understand the application process
- Make informed decisions about applying

## 🚀 Quick Start

### 1. Create a New Role Chatbot

```bash
python chatbot/create_role_chatbot.py --name "Senior Python Developer"
```

This creates a folder structure:
```
chatbot/roles/senior_python_developer/
├── job_description.txt
├── client_info.txt
├── faqs.txt
├── additional_info.txt
└── .env
```

### 2. Fill in the Content

Edit the generated files with actual information:

**job_description.txt** - The complete job description
```
# Job Title: Senior Python Developer

## About the Role
We're seeking an experienced Python developer to lead backend development...

## Key Responsibilities
- Design and implement scalable APIs
- Mentor junior developers
- Optimize database performance

## Required Skills
- 5+ years Python experience
- Django/FastAPI expertise
- PostgreSQL proficiency
...
```

**client_info.txt** - Information about the client
```
# Client Information

## Company Overview
A fast-growing fintech startup revolutionizing payments...

## Industry
Financial Technology

## Company Size
150 employees, Series B funded

## Culture
Collaborative, innovation-focused, work-life balance...

## Tech Stack
Python, Django, PostgreSQL, Redis, AWS, Docker
...
```

**faqs.txt** - Common candidate questions
```
# Frequently Asked Questions

## Compensation
Q: What's the salary range?
A: $120,000 - $160,000 based on experience

Q: What benefits are included?
A: Health insurance, 401k matching, unlimited PTO...

## Work Arrangement
Q: Is this role remote?
A: Hybrid - 2 days in office, 3 days remote
...
```

**additional_info.txt** - Any other relevant information
```
# Additional Information

## Next Steps
1. Submit your application
2. Phone screening (30 min)
3. Technical interview (90 min)
4. Team fit interview (60 min)
5. Offer

## Contact Information
Recruiter: Sarah Johnson
Email: sarah@recruitment.com
Phone: +1-555-0123
```

**.env** - API configuration
```
GEMINI_API_KEY=your-actual-api-key-here
```

### 3. Launch the Chatbot

```bash
# Local testing
python chatbot/role_chatbot_template.py --role senior_python_developer

# Create shareable link
python chatbot/role_chatbot_template.py --role senior_python_developer --share

# Custom port
python chatbot/role_chatbot_template.py --role senior_python_developer --share --port 8080
```

### 4. Share with Candidates

The `--share` flag creates a public Gradio link (valid for 72 hours):
```
Running on public URL: https://abc123.gradio.live
```

Share this link with candidates via:
- Email
- Job postings
- LinkedIn messages
- Application confirmation emails

## 📁 File Structure

```
chatbot/
├── role_chatbot_template.py      # Main chatbot engine
├── create_role_chatbot.py        # Setup script
├── ROLE_CHATBOT_GUIDE.md         # This guide
└── roles/                        # All role chatbots
    ├── senior_python_developer/
    │   ├── job_description.txt
    │   ├── client_info.txt
    │   ├── faqs.txt
    │   ├── additional_info.txt
    │   └── .env
    ├── frontend_engineer/
    │   └── ...
    └── data_scientist/
        └── ...
```

## 🎨 Customization

### Environment Variables

Add these to your role's `.env` file:

```bash
# Required
GEMINI_API_KEY=your-key

# Optional tuning
CHATBOT_MODEL=gemini-2.5-flash-lite    # Model to use
MAX_HISTORY_MESSAGES=10                # Chat history length
CHUNK_SIZE=1500                        # Content chunk size
CHUNK_OVERLAP=200                      # Chunk overlap
MAX_CONTEXT_CHUNKS=4                   # Chunks per response
```

### Content Tips

**Job Description:**
- Be specific about responsibilities
- List required vs. nice-to-have skills
- Include growth opportunities
- Mention team structure

**Client Info:**
- Highlight unique selling points
- Describe company culture authentically
- List technologies and tools
- Mention recent achievements

**FAQs:**
- Cover salary and benefits
- Explain work arrangements
- Describe interview process
- Address common concerns
- Include timeline expectations

**Additional Info:**
- Provide recruiter contact details
- Explain next steps clearly
- Add any legal/visa information
- Include application tips

## 💡 Best Practices

1. **Keep Content Updated**
   - Review and update regularly
   - Adjust based on candidate feedback
   - Update salary ranges as needed

2. **Be Transparent**
   - Provide honest information
   - Don't oversell the role
   - Address potential concerns upfront

3. **Test Before Sharing**
   - Ask common questions
   - Verify all information is accurate
   - Check response quality

4. **Monitor Usage**
   - Track which questions are asked most
   - Update FAQs based on patterns
   - Improve content based on feedback

5. **Personalize**
   - Tailor tone to company culture
   - Adjust formality level appropriately
   - Include company-specific terminology

## 🔧 Troubleshooting

**Chatbot won't start:**
- Check GEMINI_API_KEY is set in .env
- Verify role folder exists
- Ensure all required files are present

**Poor responses:**
- Add more detail to content files
- Check for typos in source files
- Increase MAX_CONTEXT_CHUNKS

**Slow responses:**
- Reduce CHUNK_SIZE
- Decrease MAX_CONTEXT_CHUNKS
- Use a faster model

## 📊 Example Use Cases

### Use Case 1: High-Volume Roles
Create a chatbot for roles with many applicants to:
- Pre-qualify candidates
- Answer repetitive questions
- Provide 24/7 information access

### Use Case 2: Confidential Clients
For roles where client name is confidential:
- Share general industry info
- Describe company culture
- Explain why anonymity is needed

### Use Case 3: International Roles
For roles with visa/relocation:
- Explain visa sponsorship
- Provide relocation support details
- Address timezone concerns

### Use Case 4: Technical Roles
For specialized technical positions:
- Detail tech stack thoroughly
- Explain technical challenges
- Describe development practices

## 🚀 Advanced Features

### Multiple Languages
Create separate content files for different languages:
```
roles/senior_python_developer/
├── job_description_en.txt
├── job_description_es.txt
├── client_info_en.txt
└── client_info_es.txt
```

### Analytics Integration
Track chatbot usage by adding logging:
```python
# In role_chatbot_template.py
import logging
logging.info(f"Question asked: {user_message}")
```

### Custom Branding
Modify the Gradio theme in `build_interface()`:
```python
theme=gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="gray",
)
```

## 📝 Dependencies

Install required packages:
```bash
pip install openai python-dotenv gradio
```

## 🔐 Security Notes

- Never commit .env files with real API keys
- Use separate API keys per role if needed
- Monitor API usage to prevent abuse
- Consider rate limiting for public links

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review error messages carefully
3. Test with minimal content
4. Verify API key is valid

## 🎉 Success Metrics

Track these to measure effectiveness:
- Number of candidates using chatbot
- Common questions asked
- Application rate after chatbot use
- Candidate feedback on helpfulness
- Time saved on recruiter calls

---

**Ready to create your first role chatbot?**

```bash
python chatbot/create_role_chatbot.py --name "Your Role Name"
```
