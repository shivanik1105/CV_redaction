"""
Universal CV Redaction System
3 distinct pipelines for different resume layouts
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from collections import Counter

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except:
    HAS_PDFPLUMBER = False

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_anonymizer import AnonymizerEngine
    HAS_PRESIDIO = True
except:
    HAS_PRESIDIO = False


class WordHealer:
    """Pipeline 1: Fix fragmented text from scanned/OCR PDFs"""
    
    COMMON_WORDS = {
        'address', 'email', 'phone', 'mobile', 'linkedin', 'github',
        'experience', 'education', 'skills', 'projects', 'summary',
        'profile', 'contact', 'location', 'objective', 'certification'
    }
    
    @staticmethod
    def heal_text(text: str) -> str:
        """Rejoin fragmented single-character sequences"""
        
        # Pattern: single chars with spaces (e.g., 'a d d r e s s')
        def rejoin_callback(match):
            fragment = match.group(0)
            joined = fragment.replace(' ', '').lower()
            
            # Check if it's a common word or looks like a name
            if joined in WordHealer.COMMON_WORDS or len(joined) >= 5:
                # Preserve original capitalization pattern
                if fragment[0].isupper():
                    return fragment.replace(' ', '').capitalize()
                return fragment.replace(' ', '')
            return fragment
        
        # Match: 3+ single letters with spaces between
        pattern = r'\b([a-zA-Z])\s+([a-zA-Z])(?:\s+[a-zA-Z]){1,}\b'
        text = re.sub(pattern, rejoin_callback, text)
        
        # Fix specific known fragments
        replacements = {
            'a bhinav': 'Abhinav', 'a bhishek': 'Abhishek',
            'p rashant': 'Prashant', 'r ohini': 'Rohini',
            'for ward': 'forward', 'a daptable': 'adaptable',
            'healthc are': 'healthcare', 'litigati on': 'litigation',
            'st and-ups': 'stand-ups', 'as sisted': 'assisted',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text


class GutterAwareReconstructor:
    """Pipeline 2: Properly extract 2-column layouts"""
    
    @staticmethod
    def extract_two_column(pdf_path: str) -> str:
        """Extract left column fully, then right column (no line mixing)"""
        
        if not HAS_PDFPLUMBER:
            return ""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_text = []
                
                for page in pdf.pages:
                    page_width = page.width
                    page_height = page.height
                    
                    # Detect gutter (dead zone at 40-60% width)
                    gutter_start = page_width * 0.40
                    gutter_end = page_width * 0.60
                    
                    # Find actual column split by analyzing word positions
                    words = page.extract_words(x_tolerance=2, y_tolerance=2)
                    
                    if not words:
                        continue
                    
                    # Determine if this is actually 2-column
                    left_words = [w for w in words if w['x1'] < gutter_start]
                    right_words = [w for w in words if w['x0'] > gutter_end]
                    
                    if len(left_words) > 10 and len(right_words) > 10:
                        # TRUE 2-column layout
                        # Extract LEFT column top-to-bottom
                        left_bbox = (0, 0, gutter_start, page_height)
                        left_text = page.crop(left_bbox).extract_text()
                        
                        # Extract RIGHT column top-to-bottom
                        right_bbox = (gutter_end, 0, page_width, page_height)
                        right_text = page.crop(right_bbox).extract_text()
                        
                        # Combine: left fully, then right fully
                        if left_text:
                            all_text.append(left_text.strip())
                        if right_text:
                            all_text.append("\n" + "=" * 60 + "\n")
                            all_text.append(right_text.strip())
                    else:
                        # Single column
                        text = page.extract_text()
                        if text:
                            all_text.append(text.strip())
                
                return "\n\n".join(all_text)
        except Exception as e:
            print(f"Gutter extraction error: {e}")
            return ""


class SectionBlockProtector:
    """Pipeline 3: Deduplicate repeating sections"""
    
    SECTION_HEADERS = [
        'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EMPLOYMENT HISTORY',
        'EDUCATION', 'ACADEMIC BACKGROUND', 'QUALIFICATIONS',
        'SKILLS', 'TECHNICAL SKILLS', 'KEY SKILLS', 'CORE COMPETENCIES',
        'PROJECTS', 'KEY PROJECTS', 'MAJOR PROJECTS',
        'SUMMARY', 'PROFILE SUMMARY', 'PROFESSIONAL SUMMARY',
        'CERTIFICATIONS', 'ACHIEVEMENTS', 'AWARDS'
    ]
    
    @staticmethod
    def deduplicate_sections(text: str) -> str:
        """Remove repeating text blocks and duplicate sections"""
        
        # Split into sections
        sections = SectionBlockProtector._split_into_sections(text)
        
        # Deduplicate
        seen_content = {}
        result_sections = []
        
        for section_name, section_content in sections:
            # Create a signature for this section
            content_signature = SectionBlockProtector._get_signature(section_content)
            
            # Check if we've seen similar content
            if section_name in seen_content:
                prev_signature = seen_content[section_name]
                similarity = SectionBlockProtector._calculate_similarity(
                    content_signature, prev_signature
                )
                
                # If >85% similar, skip this duplicate
                if similarity > 0.85:
                    continue
            
            # Keep this section
            seen_content[section_name] = content_signature
            result_sections.append((section_name, section_content))
        
        # Reconstruct text
        return SectionBlockProtector._reconstruct_text(result_sections)
    
    @staticmethod
    def _split_into_sections(text: str) -> List[Tuple[str, str]]:
        """Split text into named sections"""
        sections = []
        current_section = "HEADER"
        current_content = []
        
        lines = text.split('\n')
        for line in lines:
            line_upper = line.strip().upper()
            
            # Check if this is a section header
            is_header = False
            for header in SectionBlockProtector.SECTION_HEADERS:
                if header in line_upper and len(line.strip()) < 60:
                    is_header = True
                    # Save previous section
                    if current_content:
                        sections.append((current_section, '\n'.join(current_content)))
                    # Start new section
                    current_section = header
                    current_content = [line]
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Add final section
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    @staticmethod
    def _get_signature(text: str) -> set:
        """Get word signature for similarity comparison"""
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return set(words)
    
    @staticmethod
    def _calculate_similarity(sig1: set, sig2: set) -> float:
        """Calculate Jaccard similarity"""
        if not sig1 or not sig2:
            return 0.0
        intersection = len(sig1 & sig2)
        union = len(sig1 | sig2)
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def _reconstruct_text(sections: List[Tuple[str, str]]) -> str:
        """Reconstruct text from sections"""
        result = []
        for section_name, content in sections:
            result.append(content)
            result.append("")  # Spacing
        return '\n'.join(result)


class PIIScrubber:
    """Common Core: PII redaction with technical skills protection"""
    
    TECHNICAL_SKILLS_WHITELIST = {
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
        'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl',
        # Frameworks
        'react', 'angular', 'vue', 'node', 'nodejs', 'django', 'flask', 'spring',
        'fastapi', 'express', 'nextjs', 'nuxt', 'svelte', 'blazor',
        # Cloud/DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
        'jenkins', 'gitlab', 'github', 'circleci', 'travis',
        # Databases
        'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
        'dynamodb', 'oracle', 'sqlserver', 'sqlite',
        # Tools
        'git', 'jira', 'confluence', 'slack', 'vscode', 'intellij', 'eclipse',
        # Technologies
        'linux', 'unix', 'windows', 'macos', 'android', 'ios', 'rest', 'graphql',
        'microservices', 'agile', 'scrum', 'ci/cd', 'ml', 'ai', 'nlp',
    }
    
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        
        if HAS_PRESIDIO:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
            except:
                pass
    
    def scrub_pii(self, text: str) -> str:
        """Redact PII while protecting technical terms"""
        
        # Protect technical skills by temporary replacement
        protected_terms = {}
        placeholder_prefix = "TECH_SKILL_PLACEHOLDER_"
        
        for i, skill in enumerate(self.TECHNICAL_SKILLS_WHITELIST):
            if skill in text.lower():
                placeholder = f"{placeholder_prefix}{i}"
                # Case-insensitive replacement
                pattern = re.compile(re.escape(skill), re.IGNORECASE)
                text = pattern.sub(placeholder, text)
                protected_terms[placeholder] = skill
        
        # Remove emails, phones, URLs completely (no placeholders)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'[\+]?\d{1,3}[-\.\s]?\(?\d{1,4}\)?[-\.\s]?\d{1,4}[-\.\s]?\d{4,}', '', text)
        text = re.sub(r'http[s]?://[^\s]+', '', text)
        text = re.sub(r'linkedin\.com/in/[^\s]+', '', text)
        
        # Remove contact labels
        text = re.sub(r'\b(Email|Phone|Mobile|Contact|LinkedIn)[:\s]*', '', text, flags=re.IGNORECASE)
        
        # Restore protected technical terms
        for placeholder, original in protected_terms.items():
            text = text.replace(placeholder, original)
        
        return text


class UniversalRedactor:
    """Main orchestrator that routes to correct pipeline"""
    
    def __init__(self):
        self.word_healer = WordHealer()
        self.gutter_reconstructor = GutterAwareReconstructor()
        self.section_protector = SectionBlockProtector()
        self.pii_scrubber = PIIScrubber()
    
    def detect_layout(self, pdf_path: str) -> str:
        """Detect resume layout type"""
        
        if not HAS_PDFPLUMBER:
            return 'simple'
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return 'simple'
                
                page = pdf.pages[0]
                words = page.extract_words()
                
                if not words:
                    return 'scanned'  # Likely needs OCR/healing
                
                # Check for 2-column layout
                page_width = page.width
                gutter_start = page_width * 0.40
                gutter_end = page_width * 0.60
                
                left_words = [w for w in words if w['x1'] < gutter_start]
                right_words = [w for w in words if w['x0'] > gutter_end]
                
                if len(left_words) > 15 and len(right_words) > 15:
                    return 'two_column'
                
                # Check for fragmentation (many single-letter words)
                single_char_words = [w for w in words if len(w['text'].strip()) == 1]
                if len(single_char_words) > len(words) * 0.15:  # >15% single chars
                    return 'scanned'
                
                return 'standard'
        except:
            return 'simple'
    
    def process(self, pdf_path: str) -> str:
        """Process PDF through appropriate pipeline"""
        
        layout = self.detect_layout(pdf_path)
        print(f"  > Layout detected: {layout}")
        
        # Route to appropriate pipeline
        if layout == 'scanned':
            # Pipeline 1: Word-Healer
            print("  > Using Pipeline 1: Word-Healer")
            text = self._extract_simple(pdf_path)
            text = self.word_healer.heal_text(text)
        
        elif layout == 'two_column':
            # Pipeline 2: Gutter-Aware Reconstructor
            print("  > Using Pipeline 2: Gutter-Aware Reconstructor")
            text = self.gutter_reconstructor.extract_two_column(pdf_path)
            text = self.word_healer.heal_text(text)  # Still heal any fragments
        
        else:  # standard or simple
            # Pipeline 3: Section-Block Protector
            print("  > Using Pipeline 3: Section-Block Protector")
            text = self._extract_simple(pdf_path)
            text = self.word_healer.heal_text(text)
        
        if not text or len(text) < 100:
            return ""
        
        # Common Core: Section deduplication
        print("  > Deduplicating sections...")
        text = self.section_protector.deduplicate_sections(text)
        
        # Common Core: PII Scrubbing
        print("  > Scrubbing PII (protecting technical skills)...")
        text = self.pii_scrubber.scrub_pii(text)
        
        # Remove education
        text = self._remove_education(text)
        
        # Final cleanup
        text = self._cleanup(text)
        
        return text
    
    def _extract_simple(self, pdf_path: str) -> str:
        """Simple text extraction"""
        if not HAS_PDFPLUMBER:
            return ""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return '\n\n'.join(page.extract_text() or '' for page in pdf.pages)
        except:
            return ""
    
    def _remove_education(self, text: str) -> str:
        """Remove education section"""
        lines = text.split('\n')
        result = []
        skip = False
        skip_count = 0
        
        for line in lines:
            upper = line.strip().upper()
            
            # Start skipping at education header
            if 'EDUCATION' in upper and len(upper) < 50:
                skip = True
                skip_count = 0
                continue
            
            # Skip education content
            if skip:
                skip_count += 1
                # Stop after 30 lines or at next major section
                if skip_count > 30 or any(h in upper for h in ['WORK EXPERIENCE', 'SKILLS', 'PROJECTS']):
                    skip = False
                else:
                    continue
            
            result.append(line)
        
        return '\n'.join(result)
    
    def _cleanup(self, text: str) -> str:
        """Final cleanup"""
        # Remove empty lines
        lines = [l for l in text.split('\n') if l.strip()]
        
        # Remove duplicate consecutive lines
        result = []
        prev = None
        for line in lines:
            if line.strip() != prev:
                result.append(line)
                prev = line.strip()
        
        return '\n'.join(result)


def main():
    """Process all PDFs"""
    input_dir = Path("samples")
    output_dir = input_dir / "redacted_resumes"
    output_dir.mkdir(exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found")
        return
    
    print(f"Found {len(pdf_files)} PDF files\n")
    
    redactor = UniversalRedactor()
    success = 0
    failed = 0
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        
        try:
            result = redactor.process(str(pdf_file))
            
            if result and len(result) > 100:
                output_file = output_dir / f"UNIVERSAL_{pdf_file.stem}.txt"
                output_file.write_text(result, encoding='utf-8')
                print(f"  ✓ Saved: {output_file.name} ({len(result)} chars)\n")
                success += 1
            else:
                print(f"  ✗ Output too short\n")
                failed += 1
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            failed += 1
    
    print(f"{'='*60}")
    print(f"COMPLETE: {success} successful, {failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
