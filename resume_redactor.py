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

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    HAS_PRESIDIO = True
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
except:
    HAS_PRESIDIO = False


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
    """Remove all PII completely - no placeholders"""
    
    def __init__(self):
        self.stats = {'pii_redacted': 0}
    
    def redact(self, text: str) -> str:
        """Remove PII completely"""
        # Email
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        self.stats['pii_redacted'] += len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        
        # Phone numbers - multiple patterns
        text = re.sub(r'[\+]?[\d]{1,3}[-.\s]?[\(]?[\d]{1,4}[\)]?[-.\s]?[\d]{1,4}[-.\s]?[\d]{1,9}', '', text)
        text = re.sub(r'\b\d{10,}\b', '', text)
        
        # URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
        
        # LinkedIn
        text = re.sub(r'linkedin\.com/in/[a-zA-Z0-9-]+', '', text)
        
        # Person names with spaCy
        if nlp:
            try:
                doc = nlp(text)
                for ent in reversed(doc.ents):
                    if ent.label_ == "PERSON":
                        text = text[:ent.start_char] + text[ent.end_char:]
                        self.stats['pii_redacted'] += 1
            except:
                pass
        
        # Presidio fallback
        if HAS_PRESIDIO:
            try:
                results = analyzer.analyze(text=text, language='en', entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"])
                for result in sorted(results, key=lambda x: x.start, reverse=True):
                    text = text[:result.start] + text[result.end:]
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
        """Remove empty lines and contact labels"""
        lines = text.split('\n')
        cleaned = []
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Skip contact label lines
            if re.match(r'^(E-mail|Email|Phone|Mobile|Address|LinkedIn|Link|Contact|Location|E:|M:|L:)\s*:?\s*$', stripped, re.IGNORECASE):
                continue
            
            # Skip lines that are ONLY contact markers like "(+91)" or "E:" without content
            if re.match(r'^[\(\)\+\d\s\-]+$', stripped) and len(stripped) < 20:
                continue
            
            # Skip lines with just punctuation/separators
            if re.match(r'^[\|\-•:,\s=]+$', stripped):
                continue
            
            # Remove contact label prefixes from lines
            cleaned_line = re.sub(r'^(E-mail|Email|Phone|Mobile|E:|M:|L:)\s*:?\s*', '', stripped, flags=re.IGNORECASE)
            
            # Remove orphaned phone prefixes
            cleaned_line = re.sub(r'\(\+\d{1,3}\)\s*$', '', cleaned_line)
            
            # Clean punctuation
            cleaned_line = re.sub(r'\s*\|\s*', ' ', cleaned_line)
            cleaned_line = re.sub(r'^\s*[,|•\-]\s*', '', cleaned_line)
            cleaned_line = re.sub(r'\s*[,|]\s*$', '', cleaned_line)
            cleaned_line = re.sub(r'\s{2,}', ' ', cleaned_line)
            cleaned_line = cleaned_line.strip()
            
            if cleaned_line and len(cleaned_line) > 2:
                cleaned.append(cleaned_line)
        
        return '\n'.join(cleaned)
    
    @staticmethod
    def normalize_bullets(text: str) -> str:
        """Normalize bullet points"""
        text = re.sub(r'^[\s]*[•◦▪→\-\*]\s+', '• ', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def add_spacing(text: str) -> str:
        """Add proper spacing - only keep separators that follow section headers"""
        lines = text.split('\n')
        result = []
        last_was_separator = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if this is a separator line
            is_separator = stripped.startswith('=') and len(set(stripped)) == 1
            
            # Skip separators that don't follow section headers
            if is_separator:
                if result and ContentProtector.is_section_header(result[-1]):
                    result.append(stripped)
                    last_was_separator = True
                continue
            
            # Add the line
            result.append(stripped)
            last_was_separator = False
        
        # Normalize excessive line breaks
        final = '\n'.join(result)
        final = re.sub(r'\n{3,}', '\n\n', final)
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
        
        # Parse sections
        print("  > Parsing sections...")
        sections = self._parse_sections(text)
        print(f"  OK Found: {len(sections)} sections")
        
        # Process each section
        print("  > Redacting PII...")
        processed = []
        for section_name, section_content in sections:
            # Redact PII first
            redacted = self.redactor.redact(section_content)
            
            # Filter lines - keep only protected content
            lines = redacted.split('\n')
            kept_lines = [
                line for line in lines 
                if ContentProtector.should_preserve(line)
            ]
            
            if kept_lines:
                processed.append((section_name, '\n'.join(kept_lines)))
        
        # Combine
        result = self._combine(processed)
        
        # Polish
        result = TextPolisher.polish(result)
        
        self.stats['output_chars'] = len(result)
        print(f"  OK Output: {len(result)} characters")
        print(f"  OK PII removed: {self.redactor.stats['pii_redacted']} items")
        
        return result
    
    def _parse_sections(self, text: str) -> List[Tuple[str, str]]:
        """Parse into sections"""
        sections = []
        lines = text.split('\n')
        current_section = "HEADER"
        current_content = []
        
        for line in lines:
            # Check if this is a section header
            line_upper = line.strip().upper()
            
            # Look for education section to skip it
            if 'EDUCATION' in line_upper and len(line_upper) < 30:
                # Save current section
                if current_content:
                    sections.append((current_section, '\n'.join(current_content)))
                current_section = "EDUCATION_SKIP"
                current_content = []
                continue
            
            # Skip content if we're in education section
            if current_section == "EDUCATION_SKIP":
                # Check if we hit a new section
                if ContentProtector.is_section_header(line):
                    current_section = line.strip()
                    current_content = []
                continue
            
            # Regular section detection
            if ContentProtector.is_section_header(line):
                if current_content:
                    sections.append((current_section, '\n'.join(current_content)))
                current_section = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section (unless it's education)
        if current_content and current_section != "EDUCATION_SKIP":
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    def _combine(self, sections: List[Tuple[str, str]]) -> str:
        """Combine sections without adding separators in content"""
        output = []
        
        for section_name, content in sections:
            content = content.strip()
            
            # Skip header if mostly empty or just contact info
            if section_name == "HEADER":
                lines = [l for l in content.split('\n') if len(l.strip()) > 5]
                if len(lines) < 3:
                    continue
            
            if content and len(content) > 20:
                # Add section header
                if output:  # Add spacing before new section
                    output.append('')
                output.append('')
                output.append(section_name.upper())
                output.append('=' * 60)
                output.append('')
                # Add content as-is (no processing here)
                output.append(content)
        
        return '\n'.join(output)


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
