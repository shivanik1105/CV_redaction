
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
    def extract(self, file_path: str, sort: bool = True) -> str:
        logger.info("Using UnifiedLayoutProfile (PyMuPDF Blocks)")
        all_text = []
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    # 'blocks' returns (x0, y0, x1, y1, "text", block_no, block_type)
                    # sort=True attempts to order by columns/reading order
                    blocks = page.get_text("blocks", sort=sort)
                    
                    for b in blocks:
                        # block_type 0 is text, 1 is image
                        if b[6] == 0: 
                            # Detect wide gaps (3+ spaces) and replace with newline to separate columns
                            clean_text = re.sub(r'[ \t]{3,}', '\n', b[4])
                            
                            # Normalize whitespace for each line
                            lines = [ " ".join(l.split()) for l in clean_text.split('\n') ]
                            text = "\n".join([l for l in lines if l])
                            
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
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
            except Exception as e:
                logger.warning(f"Failed to initialize Presidio: {e}")

        # Comprehensive Headers Map
        self.headers_map = {
            'EXPERIENCE': [
                r'WORK HISTORY', r'EXPERIENCE', r'EMPLOYMENT', r'PROFESSIONAL BACKGROUND', 
                r'WORK EXPERIENCE', r'PROFESSIONAL EXPERIENCE', r'CAREER HIGHLIGHTS'
            ],
            'SKILLS': [
                r'SKILLS', r'TECHNICAL SKILLS', r'TECHNOLOGIES', r'TECH STACK', r'TOOLS',
                r'CORE COMPETENCIES', r'TECHNICAL PROFICIENCY', r'COMPUTER PROFICIENCY', r'IT SKILLS',
                r'DOMAIN KNOWLEDGE'
            ],
            'PROJECTS': [r'PROJECTS', r'KEY PROJECTS', r'ACADEMIC PROJECTS', r'ACHIEVEMENTS'],
            'SUMMARY': [r'SUMMARY', r'PROFILE', r'OBJECTIVE', r'PROFESSIONAL SUMMARY', r'ABOUT', r'BIO'],
            'REFERENCES': [r'REFERENCES'],
            'EDUCATION': [
            r'EDUCATION', r'ACADEMIC', r'QUALIFICATIONS', r'QUALIFICATION', 
            r'ACADEMIC BACKGROUND', r'CERTIFICATIONS', r'PROFESSIONAL QUALIFICATION', r'PROFESSIONAL QUALIFICATIONS'
        ],
            'PERSONAL': [
                 r'PERSONAL DETAILS', r'PERSONAL PROFILE', r'PERSONAL INFORMATION', 
                 r'OTHER PERSONAL DETAILS', r'BIOGRAPHICAL DATA', r'PERSONAL ASSET'
            ],
            'DECLARATION': [r'DECLARATION']
        }

    def is_header(self, line: str) -> bool:
        """Check if a line matches a known header pattern."""
        normalized = line.strip().upper()
        token_count = len(normalized.split())
        # Heuristic: Short line, match keywords, or starts with Keyword + Colon
        if token_count < 10 or (':' in normalized[:30] and token_count < 50):
            for triggers in self.headers_map.values():
                if any(re.match(rf"^{t}([:\-\s]|$)", normalized) for t in triggers):
                    return True
        return False

    def _extract_names_from_filename(self, filename: str) -> List[str]:
        """Heuristically extract distinct Name-like parts from filename. Handles CamelCase."""
        if not filename: return []
        
        stem = Path(filename).stem
        # Remove garbage chars (keep parens/brackets out)
        clean_stem = re.sub(r'[^a-zA-Z]', ' ', stem)
        
        # Split CamelCase (e.g. AbhishekKumar -> Abhishek Kumar)
        spaced_stem = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_stem)
        
        parts = spaced_stem.split()
        valid_parts = []
        for p in parts:
            p_clean = p.strip()
            if (len(p_clean) > 2 and 
                not p_clean.isdigit() and 
                p_clean.lower() not in self.ignore_names and 
                p_clean.lower() not in self.protected_terms):
                valid_parts.append(p_clean)

        results = []
        if valid_parts:
            # Return the full name sequence
            full_name = " ".join(valid_parts)
            results.append(full_name)
            # To be safe, if we have 2+ parts, effectively a name, we might not want to return individual tokens 
            # to avoid redacting common words (e.g. "Kumar" is safe-ish, but "May" is not).
            # We stick to the Full Name for high precision.
            
        return results



    def redact_filename_names(self, text: str, filename: str) -> str:
        """Global redaction of names derived from the filename"""
        if not filename: return text
        
        file_names = self._extract_names_from_filename(filename)
        for name in file_names:
            # Allow flexible whitespace (including newlines) between name parts
            regex_pattern = re.escape(name).replace(r'\ ', r'\s+')
            # Word boundary match case-insensitive
            text = re.sub(rf"\b{regex_pattern}\b", " ", text, flags=re.IGNORECASE)
        return text

    def cleanup_garbage(self, text: str) -> str:
        """Remove lines with only punctuation or empty key-value artifacts"""
        cleaned_lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            # 1. Skip empty
            if not stripped:
                cleaned_lines.append("")
                continue
            
            # 2. Check for Punctuation Only (e.g. " , | , ")
            if re.match(r'^[\s,\|\-\.:]+$', stripped):
                continue
                
            # 3. Check for Label Artifacts (e.g. "L: | , india" -> "L: | , " after redact)
            # Regex: Single letter or small word label followed by separators only
            if re.match(r'^[A-Z]{1,2}\s*[:\-]\s*[\|\s,]*$', stripped):
                continue
                
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)

    def parse_sections(self, text: str) -> List[Tuple[str, str]]:
        """Segment text into logical sections based on headers"""
        lines = text.split('\n')
        sections = []
        current_type = 'HEADER' # Default start section
        current_lines = []
        
        for line in lines:
            normalized = line.strip().upper()
            matched_type = None
            
            # Check if line is a header
            # Heuristic: Short line, match keywords, or starts with Keyword + Colon
            token_count = len(normalized.split())
            
            # Potential Header if short OR contains a colon (Inline Header)
            if token_count < 10 or (':' in normalized[:30] and token_count < 50):
                for stype, triggers in self.headers_map.items():
                    # Strict match at start of line
                    if any(re.match(rf"^{t}([:\-\s]|$)", normalized) for t in triggers):
                        matched_type = stype
                        break
            
            if matched_type:
                # Flush previous section
                if current_lines:
                    sections.append((current_type, "\n".join(current_lines)))
                # Start new section
                current_type = matched_type
                current_lines = [line] 
            else:
                current_lines.append(line)
                
        if current_lines:
             sections.append((current_type, "\n".join(current_lines)))
             
        return sections

    def redact_regex_pii(self, text: str) -> str:
        """Apply deterministic Regex rules for Emails, Phones, Links"""
        text = self.email_pattern.sub(" ", text)
        text = self.phone_pattern.sub(" ", text)
        text = self.url_pattern.sub(" ", text)
        text = self.linkedin_pattern.sub(" ", text)
        text = self.github_pattern.sub(" ", text)
        text = self.simple_address.sub(" ", text)
        return text

    def redact_entities(self, text: str, filename: str) -> str:
        """Apply probabilistic Entity Recognition (Presidio)"""
        # Note: Filename-based redaction is now done globally in redact_filename_names
        
        # Presidio (Probabilistic)
        if HAS_PRESIDIO:
            original_results = self.analyzer.analyze(
                text=text, 
                entities=['PERSON', 'LOCATION', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'NRP'], 
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
                        "NRP": OperatorConfig("replace", {"new_value": " "}), # Nationality/Religious/Political
                        "DEFAULT": OperatorConfig("replace", {"new_value": " "})
                    }
                )
                text = anonymized_result.text
        
        return text

    def reflow(self, text: str) -> str:
        """Merge lines that seem to be part of a sentence but were split."""
        lines = text.split('\n')
        new_lines = []
        buffer = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                if buffer:
                    new_lines.append(buffer)
                    buffer = ""
                new_lines.append("") # Preserve empty line
                continue
                
            # Heuristic to merge
            should_merge = False
            if buffer:
                # Merge if buffer doesn't end in punctuation and next line isn't a bullet
                # AND neither are Headers
                if buffer[-1] not in ['.', '!', '?', ':', ';']:
                     is_bullet = bool(re.match(r'^[\u2022\u2023\u25E6\u2043\u2219o\-*]', line))
                     if not is_bullet and not self.is_header(line) and not self.is_header(buffer):
                         should_merge = True
            
            if should_merge:
                buffer += " " + line
            else:
                if buffer:
                    new_lines.append(buffer)
                buffer = line
                
        if buffer:
            new_lines.append(buffer)
            
        return "\n".join(new_lines)

    def scrub_personal_fields(self, text: str) -> str:
        """Remove specific personal data lines like DOB, Gender, etc."""
        # Case-insensitive, multiline patterns to remove the whole line or segment
        patterns = [
            r'(?i)(date of birth|dob)\s*[:\-]?\s*.*$',
            r'(?i)(father|mother|husband)\'?s?\s*name\s*[:\-]?\s*.*$',
            r'(?i)(marital|civil)\s*status\s*[:\-]?\s*.*$',
            r'(?i)gender\s*[:\-]?\s*.*$',
            r'(?i)nationality\s*[:\-]?\s*.*$',
            r'(?i)passport\s*no\s*[:\-]?\s*.*$'
        ]
        for p in patterns:
            text = re.sub(p, '', text, flags=re.MULTILINE)
        return text

    def redact(self, text: str, filename: str = "") -> str:
        # Pre-cleaning: Remove Bullet Points and Common Header Artifacts "extra words"
        text = re.sub(r'^\s*[\u2022\u2023\u25E6\u2043\u2219o]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'(?i)^\s*(resume|curriculum\s+vitae|cv|bio-?data)\s*$', '', text, flags=re.MULTILINE)
        text = text.replace('\xa0', ' ')
        
        # Scrub personal fields globally first (to clean up headers/footers/random spots)
        text = self.scrub_personal_fields(text)
        
        # Global Name Redaction
        text = self.redact_filename_names(text, filename)

        # Parse Sections
        sections = self.parse_sections(text)
        
        final_parts = []
        for sec_type, content in sections:
            # 0. Reflow content to fix fragmentation
            content = self.reflow(content)
            
            # 1. Drop Blocklisted Sections
            if sec_type in ['EDUCATION', 'PERSONAL', 'DECLARATION']:
                # Silently drop completely
                continue

            # 2. Always remove strictly formatted PII (Email, Phone) everywhere
            content = self.redact_regex_pii(content)
            
            # 3. Selective Entity Redaction
            safe_sections = ['SKILLS', 'EXPERIENCE', 'PROJECTS']
            if sec_type not in safe_sections:
                content = self.redact_entities(content, filename)
                
                # Cleanup Label Keywords only in redacted sections (mostly Header)
                keywords = ["Address", "Ph", "Mobile", "Email", "LinkedIn", "Contact", "Location", "E", "M", "L", "P"]
                for kw in keywords:
                     # For single letters, ensure strict colon matching to avoid removing words starting with E
                     if len(kw) == 1:
                         content = re.sub(rf"\b{kw}\s*[:]\s*", " ", content)
                     else:
                         content = re.sub(rf"{kw}\s*[:\-]?\s*", "", content, flags=re.IGNORECASE)
            
            final_parts.append(content)
            
        result = "\n".join(final_parts)
        return self.cleanup_garbage(result)

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
        
    def detect_complex_layout(self, text: str) -> bool:
        """Detect if layout extraction likely failed (e.g. merged columns or interleaved)"""
        lines = text.split('\n')
        
        # 1. Check for merged headers (Same Line)
        headers = ['WORK EXPERIENCE', 'KEY SKILLS', 'SKILLS', 'EDUCATION', 'PROJECTS', 'SUMMARY', 'WORK HISTORY']
        for line in lines[:50]:
             norm = line.upper()
             found = [h for h in headers if h in norm]
             if len(found) >= 2:
                 if len(norm) < 100 and " AND " not in norm:
                     logger.warning(f"Detected merged headers: {found} in line: '{line.strip()}'")
                     return True

        # 2. Check for Interleaved Headers (Proximity)
        # Using parse sections logic to find where headers start
        sections = self.redactor.parse_sections(text)
        
        # DEBUG LOGGING
        found_sections = [s[0] for s in sections]
        logger.info(f"DEBUG: Found sections: {found_sections}")
        
        # Identify indices of headers
        header_indices = []
        current_idx = 0
        for i, (stype, content) in enumerate(sections):
            if stype in ['EXPERIENCE', 'SKILLS', 'EDUCATION', 'PROJECTS']:
                content_lines = len([x for x in content.split('\n') if x.strip()])
                header_indices.append((stype, i, content_lines))
        
        # Heuristic: If we see sequential short major sections
        # Or if the FIRST of two adjacent major sections is EMPTY (l1 < 3), it implies interleaving
        for k in range(len(header_indices) - 1):
            s1, i1, l1 = header_indices[k]
            s2, i2, l2 = header_indices[k+1]
            
            # Distance check (Adjacent headers)
            if i2 == i1 + 1:
                logger.info(f"Checking Proximity: {s1}({l1}) -> {s2}({l2})")
                # If the first section is effectively empty (< 3 lines), it's likely interleaved
                if l1 < 3:
                     logger.warning(f"Detected interleaved headers (Empty Section): {s1} ({l1} lines) -> {s2}")
                     return True
                # Or both are short
                if l1 < 5 and l2 < 5:
                     logger.warning(f"Detected interleaved headers (Short Sections): {s1} ({l1}) -> {s2} ({l2})")
                     return True
                 
        return False

    def process(self, file_path: str, output_dir: str):
        filename = os.path.basename(file_path)
        logger.info(f"Processing: {filename}")
        
        # 1. Primary Extraction
        raw_text = self.layout_profile.extract(file_path)
        
        # 2. Validation & Fallback
        # A. Empty/Garbage check
        clean_check = re.sub(r'\s+', '', raw_text)
        is_garbage = len(clean_check) < 50
        
        # B. Complex Layout check
        is_complex = self.detect_complex_layout(raw_text)
        
        if is_complex:
             logger.warning(f"Complex layout detected (Merged Headers). Attempting stream-order extraction (sort=False).")
             # Try determining layout by stream order (often separates columns better)
             alt_text = self.layout_profile.extract(file_path, sort=False)
             
             # Re-evaluate
             if not self.detect_complex_layout(alt_text):
                 logger.info("Stream-order extraction succeeded. Using alternate text.")
                 raw_text = alt_text
                 is_complex = False # Resolved
             else:
                 logger.warning("Stream-order extraction also failed. Fallback to OCR required.")

        if is_garbage or is_complex:
             reason = "Garbage Text" if is_garbage else "Complex Layout (Merged Columns)"
             logger.warning(f"Fallback to OCR due to: {reason}")
             ocr_text = self.ocr_profile.extract(file_path)
             # Basic sanity check on OCR result (ensure it's not 'OCR Unavailable' or empty)
             if len(re.sub(r'\s+', '', ocr_text)) > 50 and "OCR" not in ocr_text[:30]:
                 raw_text = ocr_text

        self.layout_profile.save_debug(raw_text, "01_raw", filename)
        
        # 3. Redaction Pipeline
        # Combined Parsing & Selective Redaction (Handles Education Removal internally)
        redacted_text = self.redactor.redact(raw_text, filename=filename)
        
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
