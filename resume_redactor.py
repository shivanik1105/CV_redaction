"""
Resume Redaction Pipeline - Single File Solution
Removes personal information while preserving professional content
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional

# Optional imports with fallback
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except:
    HAS_PDFPLUMBER = False

try:
    import spacy
    HAS_SPACY = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        nlp = None
except:
    HAS_SPACY = False
    nlp = None


class TextExtractor:
    """Extract text from PDFs"""
    
    @staticmethod
    def extract(pdf_path: str) -> str:
        """Extract with fallback"""
        text = ""
        
        # Try PyMuPDF first
        if HAS_FITZ:
            try:
                doc = fitz.open(pdf_path)
                text = "\n".join([page.get_text() for page in doc])
                doc.close()
                if text.strip():
                    return text
            except:
                pass
        
        # Fallback to pdfplumber
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                if text.strip():
                    return text
            except:
                pass
        
        return text


class PIIRedactor:
    """Remove only personal contact info - preserve professional content"""
    
    # Protected terms - never redact these
    PROTECTED_NAMES = [
        'google', 'microsoft', 'amazon', 'apple', 'samsung', 'intel', 'qualcomm',
        'netflix', 'cisco', 'oracle', 'sap', 'ibm', 'adobe', 'tesla', 'nvidia',
        'harman', 'technicolor', 'infosys', 'wipro', 'tcs', 'bosch', 'siemens',
        'linkedin', 'facebook', 'twitter', 'github', 'gitlab', 'jira', 'aws',
        'azure', 'docker', 'kubernetes', 'jenkins', 'android', 'ios', 'linux',
        'windows', 'java', 'python', 'javascript', 'react', 'angular', 'node',
        'mulesoft', 'salesforce', 'workday', 'servicenow', 'slack', 'zoom',
        'vmware', 'dell', 'hp', 'lenovo', 'asus', 'acer', 'sony', 'lg',
        'philips', 'jindal', 'tata', 'reliance', 'mahindra', 'birla',
        'collabera', 'kyocera', 'alcatel', 'lucent', 'linaro', 'hughes',
        'red hat', 'infobeans', 'openstack', 'openshift', 'sandisk',
        'django', 'flask', 'pandas', 'numpy', 'seaborn', 'boto3', 'tempest',
        'hashicorp', 'vault', 'cassandra', 'mongodb', 'mysql', 'postgresql',
        'redis', 'elasticsearch', 'kafka', 'spark', 'hadoop', 'terraform',
        'ansible', 'tensorflow', 'pytorch', 'scikit-learn', 'matplotlib',
        'directors', 'director', 'manager', 'managers', 'engineer', 'engineers',
        'l&t', 'larsen & toubro', 'scientific games', 'alcatel lucent'
    ]
    
    def __init__(self):
        self.stats = {'pii_redacted': 0}
    
    def redact(self, text: str) -> str:
        """Remove only contact info - keep company/product names"""
        # Email
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        self.stats['pii_redacted'] += len(emails)
        
        # Phone numbers (but preserve 4-digit years like 2023, 2021)
        text = re.sub(r'[\+]?[\d]{1,3}[-\.\s]?[\(]?[\d]{1,4}[\)]?[-\.\s]?[\d]{1,4}[-\.\s]?[\d]{5,9}', '', text)
        text = re.sub(r'\b\d{10,}\b', '', text)
        
        # URLs (but keep domain names in text)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # LinkedIn profile URLs only
        text = re.sub(r'linkedin\.com/in/[a-zA-Z0-9-]+', '', text)
        
        # Person names - but ONLY if not a protected company/tech term
        if nlp:
            try:
                doc = nlp(text)
                for ent in reversed(doc.ents):
                    if ent.label_ == "PERSON":
                        name_lower = ent.text.lower()
                        # Skip if it's a protected term
                        if any(protected in name_lower for protected in self.PROTECTED_NAMES):
                            continue
                        # Skip if it's all caps (likely a company/acronym)
                        if ent.text.isupper() and len(ent.text) > 2:
                            continue
                        # Remove only actual person names
                        text = text[:ent.start_char] + text[ent.end_char:]
                        self.stats['pii_redacted'] += 1
            except:
                pass
        
        return text


class ContentProtector:
    """Protect important content from removal"""
    
    TECH_KEYWORDS = [
        'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'html', 'css',
        'react', 'angular', 'node', 'django', 'flask', 'spring', 'aws',
        'azure', 'docker', 'kubernetes', 'git', 'agile', 'scrum', 'devops',
        'api', 'rest', 'graphql', 'mongodb', 'postgresql', 'mysql',
        'machine learning', 'ai', 'data science', 'tensorflow', 'pytorch',
        'android', 'ios', 'mobile', 'web', 'backend', 'frontend', 'fullstack',
        'mulesoft', 'salesforce', 'sap', 'oracle', 'microsoft', 'linux'
    ]
    
    SECTION_HEADERS = [
        'summary', 'experience', 'skills', 'projects', 'work', 'employment',
        'technical', 'professional', 'certification', 'achievements',
        'responsibilities', 'profile', 'objective', 'qualifications',
        'competencies', 'expertise', 'background', 'roles', 'duties',
        'accomplishments', 'highlights', 'capabilities', 'history'
    ]
    
    @classmethod
    def should_preserve(cls, text: str) -> bool:
        """Check if content should be preserved"""
        text_lower = text.lower()
        
        # Preserve tech keywords
        if any(keyword in text_lower for keyword in cls.TECH_KEYWORDS):
            return True
        
        # Preserve dates and durations
        if re.search(r'\b(19|20)\d{2}\b', text):
            return True
        if re.search(r'\b\d+\s*(years?|months?|yrs?)\b', text_lower):
            return True
        
        # Preserve bullets and lists
        if text.strip().startswith(('•', '-', '*', '→', '◦', '▪')):
            return True
        
        # Preserve meaningful content (not just labels)
        if len(text.split()) > 5:
            return True
        
        return False
    
    @classmethod
    def is_section_header(cls, text: str) -> bool:
        """Check if line is a section header"""
        text_clean = text.strip().lower()
        text_clean = re.sub(r'[^\w\s]', '', text_clean)
        
        if len(text_clean) < 4 or len(text_clean) > 50:
            return False
        
        return any(header in text_clean for header in cls.SECTION_HEADERS)


class TextPolisher:
    """Clean and format output"""
    
    @staticmethod
    def clean(text: str) -> str:
        """Remove empty lines, contact labels, and fix orphaned commas"""
        lines = text.split('\n')
        cleaned = []
        skip_next = False
        
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
                
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Skip contact label lines
            if re.match(r'^(E-mail|Email|Phone|Mobile|Address|LinkedIn|Link|Contact|Location|E:|M:|L:)\s*:?\s*$', stripped, re.IGNORECASE):
                continue
            
            # Skip lines that are ONLY contact markers
            if re.match(r'^[\(\)\+\d\s\-]+$', stripped) and len(stripped) < 20:
                continue
            
            # Skip lines with just punctuation/separators
            if re.match(r'^[\|\-•:,\s=]+$', stripped):
                continue
            
            # Skip header lines with just name and fragments
            if i < 3 and ',' in stripped and len(stripped) < 100:
                # This is likely "NAME , fragment, fragment" - skip it
                continue
            
            # Remove contact label prefixes
            cleaned_line = re.sub(r'^(E-mail|Email|Phone|Mobile|E:|M:|L:)\s*:?\s*', '', stripped, flags=re.IGNORECASE)
            
            # Remove orphaned phone prefixes
            cleaned_line = re.sub(r'\(\+\d{1,3}\)\s*$', '', cleaned_line)
            
            # Fix orphaned commas: ", , ," or " , "
            cleaned_line = re.sub(r'[,\s]*,\s*,\s*,?', ', ', cleaned_line)
            cleaned_line = re.sub(r'\s*,\s*,\s*', ', ', cleaned_line)
            
            # Remove leading/trailing commas and pipes
            cleaned_line = re.sub(r'^[,|:\s]+', '', cleaned_line)
            cleaned_line = re.sub(r'[,|:\s]+$', '', cleaned_line)
            
            # Fix patterns like "word , , word"
            cleaned_line = re.sub(r'(\w)\s*,\s*,\s*(\w)', r'\1, \2', cleaned_line)
            
            # Remove orphaned brackets
            cleaned_line = re.sub(r'\[\s*,?\s*\]', '', cleaned_line)
            cleaned_line = re.sub(r'\(\s*,?\s*\)', '', cleaned_line)
            
            # Clean multiple spaces
            cleaned_line = re.sub(r'\s{2,}', ' ', cleaned_line)
            cleaned_line = cleaned_line.strip()
            
            # Skip if too short or just punctuation
            if len(cleaned_line) < 3 or re.match(r'^[,.\-:|•\s]+$', cleaned_line):
                continue
            
            # Skip lines that are just location fragments like "| , india"
            if re.match(r'^\|\s*,\s*\w+\s*$', cleaned_line):
                continue
            
            cleaned.append(cleaned_line)
        
        return '\n'.join(cleaned)
    
    @staticmethod
    def normalize_bullets(text: str) -> str:
        """Normalize bullet points"""
        text = re.sub(r'^[\s]*[•◦▪→\-\*]\s+', '• ', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def add_spacing(text: str) -> str:
        """Add proper spacing and detect section headers"""
        lines = text.split('\n')
        result = []
        header_lines = []
        main_content = []
        
        # Strict section header keywords
        section_keywords = [
            'summary', 'profile', 'objective', 'experience', 'work experience', 
            'professional experience', 'employment history', 'work history', 'skills', 'technical skills',
            'key skills', 'expertise', 'projects', 'certifications', 'certification', 'achievements', 
            'career', 'activities', 'interests', 'personal details', 'languages'
        ]
        
        # First pass - separate header from main content, but detect early section headers
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if this line is a major section header even in first 20 lines
            is_major_section = False
            line_lower = stripped.lower()
            major_sections = ['work history', 'work experience', 'professional experience', 
                            'employment history', 'projects', 'certifications']
            if not stripped.endswith('.') and len(stripped.split()) >= 2 and len(stripped.split()) <= 5:
                for section in major_sections:
                    if section == line_lower:
                        is_major_section = True
                        break
            
            # If we hit a major section, everything from here goes to main_content
            if is_major_section and i < 20:
                # Everything before this goes to header
                main_content.append(stripped)
                for j in range(i + 1, len(lines)):
                    s = lines[j].strip()
                    if s:
                        main_content.append(s)
                break
            elif not is_major_section and i < 12:
                header_lines.append(stripped)
            else:
                main_content.append(stripped)
        
        # Add formatted header section
        if header_lines:
            result.append("SUMMARY & KEY SKILLS")
            result.append("=" * 60)
            result.append("")
            for line in header_lines:
                result.append(line)
            result.append("")
            result.append("")
        
        # Process main content - detect sections and organize
        i = 0
        while i < len(main_content):
            line = main_content[i]
            line_lower = line.lower().strip()
            
            # Skip standalone separator lines
            if line.startswith('=') and len(set(line)) == 1:
                i += 1
                continue
            
            # Detect section headers - STRICT RULES
            is_section = False
            section_title = None
            
            # Must be short (2-5 words) and NOT end with period
            if not line.strip().endswith('.') and len(line.split()) >= 2 and len(line.split()) <= 5:
                # Check for section keywords
                for keyword in section_keywords:
                    if keyword == line_lower or keyword in line_lower:
                        is_section = True
                        section_title = line.upper()
                        break
            
            if is_section and section_title:
                # Found a section header - check if next line is also a section header (2-column layout)
                next_is_section = False
                if i + 1 < len(main_content):
                    next_line = main_content[i + 1]
                    next_lower = next_line.lower().strip()
                    if not next_line.strip().endswith('.') and len(next_line.split()) >= 2 and len(next_line.split()) <= 5:
                        for keyword in section_keywords:
                            if keyword == next_lower or keyword in next_lower:
                                next_is_section = True
                                break
                
                # If next line is also a section, skip it (2-column layout handling)
                if next_is_section:
                    i += 1  # Skip the duplicate/adjacent section header
                
                # Output current section header
                if result and result[-1].strip():
                    result.append("")
                    result.append("")
                result.append(section_title)
                result.append("=" * 60)
                result.append("")
                
                # Collect content for this section
                i += 1
                section_content = []
                work_exp_indicators = ['engineer', 'developer', 'manager', 'lead', 'architect', 
                                      'analyst', 'consultant', 'specialist', 'technologist', 
                                      'intern', 'associate', 'director']
                switched_to_work_exp = False
                
                while i < len(main_content):
                    next_line = main_content[i]
                    next_lower = next_line.lower().strip()
                    
                    # Check if this is a new section header
                    is_next_section = False
                    next_section_title = None
                    if not next_line.strip().endswith('.') and len(next_line.split()) >= 2 and len(next_line.split()) <= 5:
                        for keyword in section_keywords:
                            if keyword == next_lower or keyword in next_lower:
                                is_next_section = True
                                next_section_title = keyword
                                break
                    
                    # Smart detection: if in KEY SKILLS section and we hit a job title, switch to WORK EXPERIENCE
                    if 'SKILL' in section_title and not switched_to_work_exp:
                        is_job_title = any(indicator in next_lower for indicator in work_exp_indicators)
                        if is_job_title and len(next_line.split()) <= 10 and len(next_line.split()) >= 2:
                            # Output skills section
                            result.extend(section_content)
                            result.append("")
                            result.append("")
                            result.append("WORK EXPERIENCE")
                            result.append("=" * 60)
                            result.append("")
                            # Now we're collecting work experience
                            section_content = []
                            section_title = "WORK EXPERIENCE"
                            switched_to_work_exp = True
                    
                    # If we hit ACTIVITIES while in WORK EXPERIENCE, handle specially
                    if is_next_section and next_section_title and 'activit' in next_section_title and 'WORK' in section_title:
                        # Output current work experience
                        result.extend(section_content)
                        section_content = []  # Clear it!
                        result.append("")
                        result.append("")
                        
                        # Collect activity items
                        result.append("ACTIVITIES AND INTEREST")
                        result.append("=" * 60)
                        result.append("")
                        i += 1
                        while i < len(main_content):
                            act_line = main_content[i]
                            act_lower = act_line.lower().strip()
                            # Activity items are short and non-technical
                            if len(act_line.split()) <= 4 and not any(tech in act_lower for tech in ['tech:', 'c++', 'python', 'pvt', 'ltd', 'engineer', 'technologist']):
                                result.append(act_line)
                                i += 1
                            else:
                                # Hit work experience again - start continued section
                                if any(indicator in act_lower for indicator in work_exp_indicators):
                                    result.append("")
                                    result.append("")
                                    result.append("WORK EXPERIENCE (CONTINUED)")
                                    result.append("=" * 60)
                                    result.append("")
                                    # Continue with rest of work experience - don't break
                                    section_title = "WORK EXPERIENCE (CONTINUED)"
                                    break
                                else:
                                    # End of activities
                                    break
                        continue
                    
                    # If we hit another section, output and break
                    if is_next_section:
                        result.extend(section_content)
                        break
                    
                    # Add content with spacing logic
                    if next_line.startswith('[') and ']' in next_line:
                        if section_content and section_content[-1].strip():
                            section_content.append("")
                    
                    has_date = re.search(r'20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present', next_line)
                    if has_date and len(next_line) < 120:
                        if section_content and section_content[-1].strip() and len(section_content[-1]) > 30:
                            section_content.append("")
                    
                    section_content.append(next_line)
                    i += 1
                
                # Output any remaining content
                if section_content:
                    result.extend(section_content)
            else:
                # Not a section header, just add the line
                if line.startswith('[') and ']' in line:
                    if result and result[-1].strip():
                        result.append("")
                
                has_date = re.search(r'20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present', line)
                if has_date and len(line) < 120:
                    if result and result[-1].strip() and len(result[-1]) > 30:
                        result.append("")
                
                result.append(line)
                i += 1
        
        # Join and normalize excessive spacing
        final = '\n'.join(result)
        final = re.sub(r'\n{4,}', '\n\n\n', final)
        return final
    
    @staticmethod
    def polish(text: str) -> str:
        """Complete polish pipeline"""
        text = TextPolisher.clean(text)
        text = TextPolisher.normalize_bullets(text)
        text = TextPolisher.add_spacing(text)
        return text


class ResumePipeline:
    """Main orchestrator"""
    
    def __init__(self):
        self.extractor = TextExtractor()
        self.redactor = PIIRedactor()
        self.stats = {
            'extracted_chars': 0,
            'pii_redacted': 0,
            'output_chars': 0
        }
    
    def process(self, pdf_path: str) -> str:
        """Process PDF through complete pipeline"""
        print(f"\nProcessing: {os.path.basename(pdf_path)}")
        
        # Extract
        print("  > Extracting text...")
        text = self.extractor.extract(pdf_path)
        if not text:
            print("  X Failed to extract text")
            return ""
        
        self.stats['extracted_chars'] = len(text)
        print(f"  OK Extracted: {len(text)} characters")
        
        # Remove education section first
        print("  > Removing education...")
        text = self._remove_education(text)
        
        # Redact PII
        print("  > Redacting PII...")
        text = self.redactor.redact(text)
        
        # Filter lines - keep meaningful content (minimal filtering)
        print("  > Filtering content...")
        lines = text.split('\n')
        kept_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Only skip truly useless lines
            # Skip single characters or numbers
            if len(stripped) <= 2:
                continue
            # Skip lines that are just punctuation
            if all(not c.isalnum() for c in stripped):
                continue
            
            # Keep everything else
            kept_lines.append(line)
        
        result = '\n'.join(kept_lines)
        
        # Polish
        result = TextPolisher.polish(result)
        
        self.stats['output_chars'] = len(result)
        print(f"  OK Output: {len(result)} characters")
        print(f"  OK PII removed: {self.redactor.stats['pii_redacted']} items")
        
        return result
    
    def _remove_education(self, text: str) -> str:
        """Remove education section from text"""
        lines = text.split('\n')
        result = []
        in_education = False
        skip_count = 0
        
        for i, line in enumerate(lines):
            line_upper = line.strip().upper()
            
            # Detect education section start
            if 'EDUCATION' in line_upper and len(line_upper) < 40:
                in_education = True
                skip_count = 0
                continue
            
            # Stay in education section for next 30 lines or until clear new section
            if in_education:
                skip_count += 1
                # Exit if we see clear non-education content
                if skip_count > 30:
                    in_education = False
                elif any(keyword in line_upper for keyword in ['WORK EXPERIENCE', 'PROFESSIONAL', 'EMPLOYMENT', 'PROJECTS', 'SKILLS', 'CERTIFICATION']):
                    in_education = False
                else:
                    continue
            
            result.append(line)
        
        return '\n'.join(result)


def main():
    """Process all PDFs"""
    # Setup
    input_dir = Path("samples")
    output_dir = input_dir / "redacted_resumes"
    output_dir.mkdir(exist_ok=True)
    
    # Find PDFs
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in samples/")
        return
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Process
    pipeline = ResumePipeline()
    success_count = 0
    fail_count = 0
    
    for pdf_file in pdf_files:
        try:
            result = pipeline.process(str(pdf_file))
            
            if result and len(result) > 100:
                # Save
                output_file = output_dir / f"REDACTED_{pdf_file.stem}.txt"
                output_file.write_text(result, encoding='utf-8')
                print(f"  OK Saved: {output_file.name}")
                success_count += 1
            else:
                print(f"  X Output too short or empty")
                fail_count += 1
        
        except Exception as e:
            print(f"  X Error: {e}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: {success_count} successful, {fail_count} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
