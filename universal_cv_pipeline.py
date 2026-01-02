
"""
Universal CV Redaction System
Strict pipeline architecture:
Profile Selection -> Extraction -> Reading Order -> Redaction -> Cleanup -> Output
"""

import os
import re
import sys
import abc
import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Presidio Imports
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    HAS_PRESIDIO = True
except ImportError:
    HAS_PRESIDIO = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress PaddleOCR verbose logging
logging.getLogger("ppocr").setLevel(logging.ERROR)

# Constants
DEBUG_DIR = Path("debug_output")
DEBUG_DIR.mkdir(exist_ok=True)

class ExtractionProfile(abc.ABC):
    """Abstract base class for all extraction profiles"""
    
    @abc.abstractmethod
    def extract(self, file_path: str) -> str:
        """Extract text maintaining reading order"""
        pass

    def save_debug(self, content: str, stage: str, filename: str):
        """Save intermediate output"""
        try:
            name = Path(filename).stem
            path = DEBUG_DIR / f"{name}_{stage}.txt"
            path.write_text(content, encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save debug for {stage}: {e}")

class UnifiedLayoutProfile(ExtractionProfile):
    """
    Uses PyMuPDF's smart block sorting to handle both single and multi-column layouts
    without explicit mode switching. Returns text in reading order.
    """
    def extract(self, file_path: str) -> str:
        logger.info("Using UnifiedLayoutProfile (PyMuPDF Blocks)")
        all_text = []
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    # 'blocks' returns (x0, y0, x1, y1, "text", block_no, block_type)
                    # sort=True attempts to order by columns/reading order
                    blocks = page.get_text("blocks", sort=True)
                    
                    for b in blocks:
                        # block_type 0 is text, 1 is image
                        if b[6] == 0: 
                            text = b[4].strip()
                            if text:
                                # Remove common footer artifacts like "Page 1 of 2"
                                if re.match(r'^Page\s+\d+(\s+of\s+\d+)?$', text, re.IGNORECASE):
                                    continue
                                # Remove solitary page numbers (e.g. "1", "2")
                                if re.match(r'^\d{1,2}$', text):
                                    continue
                                
                                all_text.append(text)
            
            # Join with double newlines to preserve section spacing
            return "\n\n".join(all_text)
            
        except Exception as e:
            logger.error(f"Unified extraction failed: {e}")
            return ""

class OCRProfile(ExtractionProfile):
    """Profile 4: For image-based resumes using PaddleOCR"""
    
    def __init__(self):
        print("Initializing OCRProfile...")
        try:
            from paddleocr import PaddleOCR
            # Minimal init - DISABLE use_angle_cls to avoid TypeError
            self.ocr = PaddleOCR(lang='en', use_angle_cls=False, show_log=False) 
            print("PaddleOCR initialized successfully.")
        except ImportError as ie:
            self.ocr = None
            print(f"PaddleOCR ImportError: {ie}")
            logger.warning(f"PaddleOCR not installed or failed to load: {ie}")
        except Exception as e:
             self.ocr = None
             print(f"PaddleOCR Init Exception: {e}")
             logger.warning(f"PaddleOCR failed to init: {e}")

    def extract(self, file_path: str) -> str:
        logger.info("Using OCRProfile")
        if not self.ocr:
            print(f"OCR attempted but engine is None for {file_path}")
            return "OCR Engine Unavailable"
            
        try:
            text_result = []
            print(f"Starting OCR for {file_path}")
            
            if file_path.lower().endswith('.pdf'):
                doc = fitz.open(file_path)
                for page in doc:
                    pix = page.get_pixmap()
                    img_path = f"temp_ocr_{page.number}.png"
                    pix.save(img_path)
                    
                    try:
                        # Scan without cls argument
                        result = self.ocr.ocr(img_path)
                    except TypeError:
                        result = self.ocr.ocr(img_path) # Fallback uses basic call
                    except Exception as e:
                        print(f"OCR Internal Error on {img_path}: {e}")
                        result = None

                    if result:
                        try:
                            # PaddleOCR returns [None] if no text found on page
                            page_result = result[0]
                            if not page_result:
                                continue

                            lines = page_result if isinstance(page_result, list) else [page_result]
                            if lines:
                                parsed = []
                                for line in lines:
                                    if isinstance(line, list) and len(line) >= 2:
                                        if isinstance(line[1], tuple):
                                            parsed.append((line[0], line[1][0])) # box, text
                                
                                if parsed:
                                    parsed.sort(key=lambda x: x[0][0][1]) # Sort by Y
                                    for txt in [p[1] for p in parsed]:
                                        # Deduplicate headers in OCR
                                        if re.match(r'^Page\s+\d+(\s+of\s+\d+)?$', txt, re.IGNORECASE):
                                            continue
                                        text_result.append(txt)
                        except Exception as parse_err:
                            logger.error(f"Failed to parse OCR result: {parse_err}")
                            
                    if os.path.exists(img_path):
                        os.remove(img_path)
            
            return "\n".join(text_result)
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

class RedactionCore:
    """Common PII Removal Logic with Presidio + Regex + Filename Heuristics"""
    
    def __init__(self):
        # Compiled patterns for speed
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?\d{1,3}[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.linkedin_pattern = re.compile(r'(linkedin\.com/in/[a-zA-Z0-9%\-_]+)', re.IGNORECASE)
        self.github_pattern = re.compile(r'(github\.com/[a-zA-Z0-9%\-_]+)', re.IGNORECASE)
        # Regex for likely address "City, State, Zip"
        self.simple_address = re.compile(r'\b[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+,\s*\d{5,6}\b')
        
        # Protected terms to NEVER redact (Tech stack, etc)
        self.protected_terms = {
            'python', 'java', 'c++', 'sql', 'aws', 'docker', 'manager', 'engineer', 'developer',
            'git', 'linux', 'azure', 'cloud', 'salesforce', 'sap', 'oracle', 'data', 'analyst',
            'science', 'consultant', 'lead', 'senior', 'junior', 'associate', 'architect',
            'admin', 'administrator', 'executive', 'specialist', 'go', 'react', 'net', 'web'
        }
        
        # Terms to ignore when extracting names from filenames
        self.ignore_names = {
            'resume', 'cv', 'naukri', 'profile', 'biodata', 'curriculum', 'vitae', 
            'pdf', 'docx', 'doc', 'txt', 'copy', 'converted', 'page', 'scan'
        }
        
        if HAS_PRESIDIO:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
        else:
            logger.warning("Presidio not found. Falling back to regex only.")

    def _extract_names_from_filename(self, filename: str) -> List[str]:
        """Heuristically extract distinct Name-like parts from filename"""
        if not filename: return []
        
        # Clean extension
        stem = Path(filename).stem
        # Split by non-alphanumeric
        parts = re.split(r'[_\-\s\(\)\[\]\.,]+', stem)
        
        extracted = []
        for p in parts:
            p_clean = p.strip()
            # Filter unlikely names (digits, short words, common resume terms, tech stack)
            if (len(p_clean) > 2 and 
                not p_clean.isdigit() and
                p_clean.lower() not in self.ignore_names and
                p_clean.lower() not in self.protected_terms):
                extracted.append(p_clean)
        return extracted

    def redact(self, text: str, filename: str = "") -> str:
        # Pre-cleaning: Remove Bullet Points and Common Header Artifacts "extra words"
        text = re.sub(r'^\s*[\u2022\u2023\u25E6\u2043\u2219o]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)^\s*(resume|curriculum\s+vitae|cv|bio-?data)\s*$', '', text, flags=re.MULTILINE)
        # Normalize non-breaking spaces
        text = text.replace('\xa0', ' ')

        # 1. Regex Redaction (Deterministics)
        text = self.email_pattern.sub(" ", text)
        text = self.phone_pattern.sub(" ", text)
        text = self.url_pattern.sub(" ", text)
        text = self.linkedin_pattern.sub(" ", text)
        text = self.github_pattern.sub(" ", text)
        text = self.simple_address.sub(" ", text)
        
        # 2. Filename-based Redaction (Heuristc Failsafe)
        if filename:
            file_names = self._extract_names_from_filename(filename)
            for name in file_names:
                regex_name = re.escape(name)
                # Word boundary match case-insensitive
                text = re.sub(rf"\b{regex_name}\b", " ", text, flags=re.IGNORECASE)

        # 3. Presidio (Probabilistic)
        if HAS_PRESIDIO:
            original_results = self.analyzer.analyze(
                text=text, 
                entities=['PERSON', 'LOCATION', 'EMAIL_ADDRESS', 'PHONE_NUMBER'], 
                language='en'
            )
            
            filtered_results = []
            for res in original_results:
                entity_text = text[res.start:res.end].lower()
                # Skip if protected
                if any(term in entity_text for term in self.protected_terms):
                    continue
                filtered_results.append(res)
                
            if filtered_results:
                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=filtered_results,
                    operators={
                        "PERSON": OperatorConfig("replace", {"new_value": " "}),
                        "LOCATION": OperatorConfig("replace", {"new_value": " "}),
                        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": " "}),
                        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": " "}),
                        "DEFAULT": OperatorConfig("replace", {"new_value": " "})
                    }
                )
                text = anonymized_result.text

        # 4. Cleanup Label Keywords
        keywords = ["Address", "Ph", "Mobile", "Email", "LinkedIn", "Contact", "Location"]
        for kw in keywords:
             text = re.sub(rf"{kw}\s*[:\-]?\s*", "", text, flags=re.IGNORECASE)

        return text

    def remove_education(self, text: str) -> str:
        """Heuristic to remove Education section"""
        # Headers marking start of Education
        edu_headers = [
            r"EDUCATION", r"ACADEMIC QUALIFICATIONS", r"ACADEMIC BACKGROUND", 
            r"SCHOLASTIC PROFILE", r"ACADEMICS"
        ]
        # Headers marking start of OTHER sections (terminating Education)
        other_headers = [
            r".*SKILLS", r"TECHNICAL SKILLS", r".*EXPERIENCE", r".*PROJECTS", 
            r"PROFESSIONAL DETAILS", r"CERTIFICATIONS", r"ACHIEVEMENTS",
            r"DECLARATION", r"PERSONAL DETAILS", r"SUMMARY", r"PROFILE", 
            r"OBJECTIVE", r"LANGUAGES", r"REFERENCES"
        ]
        
        lines = text.split('\n')
        new_lines = []
        in_education = False
        
        for line in lines:
            normalized = line.strip().upper()
            
            # Check for Education Start
            if any(re.match(rf"^{h}([:\-\s]|$)", normalized) for h in edu_headers):
                # Safeguard: Header should be short-ish
                if len(normalized.split()) < 6:
                    in_education = True
                    continue 
                
            # Check for Other Section Start (Exit Education)
            if in_education:
                if any(re.match(rf"^{h}([:\-\s]|$)", normalized) for h in other_headers):
                     # If we hit another header, check line length to be sure it's a header
                     if len(normalized.split()) < 6:
                        in_education = False
                        # Do NOT continue; this line is the new header, keep it
                     else:
                        continue # Still inside education text body that looks like header
                else:
                    continue # Skip line (Education content)
            
            new_lines.append(line)
            
        return "\n".join(new_lines)


class PipelineOrchestrator:
    """Orchestrates the flow"""
    
    def __init__(self):
        self.layout_profile = UnifiedLayoutProfile()
        self.ocr_profile = OCRProfile()
        self.redactor = RedactionCore()
        
    def process(self, file_path: str, output_dir: str):
        filename = os.path.basename(file_path)
        logger.info(f"Processing: {filename}")
        
        # 1. Primary Extraction
        raw_text = self.layout_profile.extract(file_path)
        
        # 2. Fallback to OCR if text is garbage/empty
        clean_check = re.sub(r'\s+', '', raw_text)
        if len(clean_check) < 50:
             logger.warning(f"Text extraction insufficient ({len(clean_check)} chars). Fallback to OCR for {filename}")
             raw_text = self.ocr_profile.extract(file_path)

        self.layout_profile.save_debug(raw_text, "01_raw", filename)
        
        # 3. Redaction Pipeline
        # A: Remove Education Structure
        text_struct = self.redactor.remove_education(raw_text)
        
        # B: Redact PII (passing filename for heuristic name removal)
        redacted_text = self.redactor.redact(text_struct, filename=filename)
        
        self.layout_profile.save_debug(redacted_text, "02_redacted", filename)
        
        # 4. Final Polish
        # Normalize spacing
        final_text = re.sub(r'\n{3,}', '\n\n', redacted_text)
        final_text = "\n".join([line.rstrip() for line in final_text.splitlines()])
        final_text = final_text.strip()
        
        # 5. Output
        out_path = Path(output_dir) / f"REDACTED_{filename}.txt"
        out_path.write_text(final_text, encoding='utf-8')
        logger.info(f"Saved to {out_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python universal_cv_pipeline.py <pdf_file_or_directory>")
        return

    target = sys.argv[1]
    out_dir = "final_output"
    Path(out_dir).mkdir(exist_ok=True)
    
    orchestrator = PipelineOrchestrator()
    
    if os.path.isfile(target):
        orchestrator.process(target, out_dir)
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            for file in files:
                if file.lower().endswith('.pdf'):
                    orchestrator.process(os.path.join(root, file), out_dir)
                    
    print("\n--- Processing Complete ---")

if __name__ == "__main__":
    main()
