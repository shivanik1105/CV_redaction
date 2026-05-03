"""
Quick setup script to create a new role chatbot

Usage: python create_role_chatbot.py --name "Senior Python Developer"
"""

import argparse
from pathlib import Path
import sys


TEMPLATE_JD = """# Job Title: {role_name}

## About the Role
[Describe the role and its importance]

## Key Responsibilities
- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

## Required Skills
- [Skill 1]
- [Skill 2]
- [Skill 3]

## Qualifications
- [Qualification 1]
- [Qualification 2]

## What We Offer
- Competitive salary
- [Benefit 1]
- [Benefit 2]

## Location
[Location details]

## Employment Type
[Full-time/Contract/Remote]
"""

TEMPLATE_CLIENT = """# Client Information

## Company Overview
[Brief description of the client company]

## Industry
[Industry sector]

## Company Size
[Number of employees]

## Culture
[Description of company culture and values]

## Tech Stack
[Technologies used]

## Why Join?
[Compelling reasons to join this client]
"""

TEMPLATE_FAQS = """# Frequently Asked Questions

## Application Process
Q: How do I apply?
A: [Application instructions]

Q: What's the timeline?
A: [Expected timeline]

## Compensation
Q: What's the salary range?
A: [Salary information]

Q: What benefits are included?
A: [Benefits details]

## Work Arrangement
Q: Is this role remote?
A: [Remote/hybrid/onsite details]

Q: What are the working hours?
A: [Working hours information]

## Interview Process
Q: What does the interview process look like?
A: [Interview stages]

Q: How should I prepare?
A: [Preparation tips]
"""

TEMPLATE_ENV = """# API Keys
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Alternative API keys
# GOOGLE_API_KEY=your-google-api-key
# OPENAI_API_KEY=your-openai-key

# Optional: Configuration
# CHATBOT_MODEL=gemini-2.5-flash-lite
# MAX_HISTORY_MESSAGES=10
# CHUNK_SIZE=1500
# CHUNK_OVERLAP=200
# MAX_CONTEXT_CHUNKS=4
"""

TEMPLATE_ADDITIONAL = """# Additional Information

## Next Steps
[What happens after applying]

## Contact Information
Recruiter: [Name]
Email: [Email]
Phone: [Phone]

## Important Notes
[Any other important information candidates should know]
"""


def create_role_chatbot(role_name: str, base_path: Path):
    """Create a new role chatbot folder with template files."""
    
    # Create folder name (sanitize)
    folder_name = role_name.lower().replace(" ", "_").replace("-", "_")
    folder_name = "".join(c for c in folder_name if c.isalnum() or c == "_")
    
    role_folder = base_path / "roles" / folder_name
    
    if role_folder.exists():
        print(f"❌ Role folder already exists: {role_folder}")
        response = input("Overwrite? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return
    
    # Create folder
    role_folder.mkdir(parents=True, exist_ok=True)
    
    # Create template files
    files = {
        "job_description.txt": TEMPLATE_JD.format(role_name=role_name),
        "client_info.txt": TEMPLATE_CLIENT,
        "faqs.txt": TEMPLATE_FAQS,
        "additional_info.txt": TEMPLATE_ADDITIONAL,
        ".env": TEMPLATE_ENV,
    }
    
    for filename, content in files.items():
        file_path = role_folder / filename
        file_path.write_text(content, encoding="utf-8")
        print(f"✓ Created {filename}")
    
    print(f"\n✅ Role chatbot created: {role_folder}")
    print(f"\n📝 Next steps:")
    print(f"1. Edit the files in: {role_folder}")
    print(f"   - job_description.txt (add the actual JD)")
    print(f"   - client_info.txt (add client details)")
    print(f"   - faqs.txt (add common questions)")
    print(f"   - .env (add your GEMINI_API_KEY)")
    print(f"\n2. Launch the chatbot:")
    print(f"   python chatbot/role_chatbot_template.py --role {folder_name} --share")
    print(f"\n3. Share the generated link with candidates!")


def main():
    parser = argparse.ArgumentParser(description="Create a new role chatbot")
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help='Role name (e.g., "Senior Python Developer")'
    )
    
    args = parser.parse_args()
    
    # Determine base path
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    
    create_role_chatbot(args.name, base_path)


if __name__ == "__main__":
    main()
