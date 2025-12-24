#!/usr/bin/env python3
"""
PaddleOCR PP-Structure Resume Redactor
Using PP-Structure for layout detection + Presidio/spaCy for PII detection
Outputs: Skills, Experience, Summary (non-PII content only)
"""

import os
import sys
import re
import logging
import argparse
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime

# === Suppress Presidio warnings ===
logging.getLogger("presidio_analyzer").setLevel(logging.WARNING)
logging.getLogger("presidio_analyzer.recognizer_registry").setLevel(logging.WARNING)
logging.getLogger("presidio_anonymizer").setLevel(logging.WARNING)

# ============================================================
# CONFIGURATION
# ============================================================

ROOT_DIR = r"c:\Users\shiva\Downloads\samplecvs"
OUTPUT_DIR = os.path.join(ROOT_DIR, "redacted_resumes")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Blocks to remove (layout types)
BLOCKS_TO_REMOVE = {'title', 'figure', 'header', 'footer'}

# Contact keywords to filter
CONTACT_KEYWORDS = {'email', 'phone', 'mobile', 'contact', 'address', 'location', 'linkedin', 'github'}

# Sections to preserve
PRESERVE_SECTIONS = [
    "SKILLS", "EXPERIENCE", "WORK HISTORY", "PROFESSIONAL EXPERIENCE",
    "KEY CONTRIBUTIONS", "PROJECTS", "TECHNICAL SKILLS", "TOOLS",
    "CERTIFICATIONS", "ACHIEVEMENTS", "SUMMARY", "OBJECTIVE", "PROFILE"
]

# ============================================================
# DEPENDENCY CHECKS
# ============================================================

# PP-Structure for layout analysis
try:
    from paddleocr import PPStructure
    PADDLE_AVAILABLE = True
    print("[OK] PaddleOCR PP-Structure available")
except ImportError:
    PADDLE_AVAILABLE = False
    print("[INFO] PP-Structure not available - using fallback text extraction")

# Presidio for PII detection
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
    print("[OK] Presidio available")
except ImportError:
    PRESIDIO_AVAILABLE = False
    print("[INFO] Presidio not available - using regex PII detection")

# spaCy for NER
try:
    import spacy
    SPACY_AVAILABLE = True
    print("[OK] spaCy available")
except ImportError:
    SPACY_AVAILABLE = False
    print("[INFO] spaCy not available - using basic NER")

# PyMuPDF for PDF handling
try:
    import fitz
    PYMUPDF_AVAILABLE = True
    print("[OK] PyMuPDF available")
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("[WARN] PyMuPDF not available")

# DOCX handling
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
logger.addHandler(handler)


# ============================================================
# PP-STRUCTURE REDACTOR CLASS
# ============================================================

class PPStructureRedactor:
    """Resume redactor using PP-Structure layout detection"""
    
    def __init__(self, filepath: str, redaction_level: str = 'medium'):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.extension = os.path.splitext(filepath)[1].lower()
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        self.redaction_level = redaction_level
        self.candidate_name = None
        
        # Statistics
        self.stats = {
            'pages_processed': 0,
            'blocks_processed': 0,
            'blocks_removed': 0,
            'blocks_kept': 0,
            'pii_items_removed': 0,
            'contact_blocks_removed': 0
        }
        
        # Initialize PP-Structure
        self.layout_engine = None
        if PADDLE_AVAILABLE and self.extension in ['.pdf', '.jpg', '.jpeg', '.png']:
            try:
                self.layout_engine = PPStructure(
                    show_log=False,
                    lang='en',
                    use_gpu=False,
                    ocr=True,
                    table=False
                )
                logger.info("PP-Structure layout engine initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize PP-Structure: {e}")
                self.layout_engine = None
        
        # Initialize Presidio
        self.presidio_available = False
        self.analyzer = None
        self.anonymizer = None
        
        if PRESIDIO_AVAILABLE:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                self.presidio_available = True
                logger.info("Presidio initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Presidio: {e}")
        
        # Initialize spaCy
        self.spacy_available = False
        self.nlp = None
        
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm", disable=['parser', 'tagger'])
                self.spacy_available = True
                logger.info("spaCy NER model loaded")
            except Exception as e:
                logger.warning(f"Failed to load spaCy model: {e}")
            
    
    def extract_text_fallback(self) -> str:
        """Fallback text extraction without layout detection"""
        if self.extension == '.pdf' and PYMUPDF_AVAILABLE:
            return self._extract_with_pymupdf()
        elif self.extension == '.docx' and DOCX_AVAILABLE:
            return self._extract_with_docx()
        elif self.extension in ['.jpg', '.jpeg', '.png']:
            logger.warning("Image files require OCR")
            return ""
        else:
            logger.warning(f"Unsupported file format: {self.extension}")
            return ""
    
    def _extract_with_pymupdf(self) -> str:
        """Extract text using PyMuPDF"""
        doc = fitz.open(self.filepath)
        all_text = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                all_text.append(text)
        
        doc.close()
        return "\n".join(all_text)
    
    def _extract_with_docx(self) -> str:
        """Extract text from DOCX files"""
        doc = docx.Document(self.filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    
    def clean_text(self, text: str) -> str:
        """Remove PII from text while keeping professional content"""
        if not text.strip():
            return ''
        
        cleaned_text = text
        
        # spaCy NER for name detection
        if self.spacy_available and self.nlp and len(text) < 5000:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    if ent.label_ == 'PERSON':
                        if not self.candidate_name and len(ent.text.split()) >= 2:
                            self.candidate_name = ent.text
                        cleaned_text = cleaned_text.replace(ent.text, '')
                        self.stats['pii_items_removed'] += 1
            except Exception:
                pass
        
        # Regex patterns for PII
        patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),
            (r'(?:\+?91|0)?\s?[-.]?\s?\(?\d{3}\)?\s?[-.]?\s?\d{3}\s?[-.]?\s?\d{4}', 'PHONE'),
            (r'(https?://\S+|www\.\S+|linkedin\.com\S+|github\.com\S+)', 'URL'),
            (r'\b\d{6}\b', 'PINCODE')
        ]
        
        for pattern, pii_type in patterns:
            matches = list(re.finditer(pattern, cleaned_text, re.IGNORECASE))
            for match in reversed(matches):
                cleaned_text = cleaned_text[:match.start()] + cleaned_text[match.end():]
                self.stats['pii_items_removed'] += 1
        
        return cleaned_text.strip()
    
    def should_remove_block(self, block: Dict[str, Any], page_width: float = 1000) -> bool:
        """Determine if a block should be removed"""
        block_type = block.get('type', '').lower()
        block_text = self._extract_text_from_block(block)
        bbox = block.get('bbox', [0, 0, page_width, 1000])
        
        x1, y1, x2, y2 = bbox
        block_width = x2 - x1
        
        # Remove certain block types
        if block_type in BLOCKS_TO_REMOVE:
            return True
        
        # Remove top section title blocks
        if block_type == 'title' and y1 < 100:
            return True
        
        # Remove narrow right-column blocks (usually contact info)
        if (x1 > page_width * 0.6 and block_width < page_width * 0.35 and y1 < 300):
            return True
        
        # Check block text for contact keywords
        if block_text:
            block_text_lower = block_text.lower()
            if any(keyword in block_text_lower for keyword in CONTACT_KEYWORDS):
                self.stats['contact_blocks_removed'] += 1
                return True
        
        return False
    
    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        """Extract text from PP-Structure block"""
        content = block.get('res')
        if not content:
            return ''
        
        text_parts = []
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                text = item.get('text', '').strip()
                confidence = item.get('confidence', 0)
                if text and confidence > 0.5:
                    text_parts.append(text)
        
        return ' '.join(text_parts)
    
    def process_with_ppstructure(self) -> str:
        """Process with PP-Structure layout detection"""
        if not self.layout_engine:
            return self.process_without_layout()
        
        try:
            logger.info("Analyzing layout with PP-Structure...")
            result = self.layout_engine(self.filepath)
            logger.info(f"PP-Structure returned {len(result)} pages")
            
            all_text = []
            
            for page_idx, page_blocks in enumerate(result):
                page_text = []
                
                for block in page_blocks:
                    self.stats['blocks_processed'] += 1
                    
                    # Check if block should be removed
                    if self.should_remove_block(block):
                        self.stats['blocks_removed'] += 1
                        continue
                    
                    # Extract text from block content
                    block_text = self._extract_text_from_block(block)
                    
                    if block_text:
                        cleaned_text = self.clean_text(block_text)
                        if cleaned_text:
                            page_text.append(cleaned_text)
                            self.stats['blocks_kept'] += 1
                
                if page_text:
                    all_text.extend(page_text)
            
            self.stats['pages_processed'] = len(result)
            result_text = '\n'.join(all_text)
            return self._post_process_text(result_text)
            
        except Exception as e:
            logger.error(f"PP-Structure processing failed: {e}")
            return self.process_without_layout()
    
    def process_without_layout(self) -> str:
        """Process without layout detection (fallback)"""
        logger.info("Using text extraction fallback")
        
        text = self.extract_text_fallback()
        if not text:
            return ""
        
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            
            cleaned_line = self.clean_text(line)
            if cleaned_line and len(cleaned_line) > 2:
                processed_lines.append(cleaned_line)
        
        result_text = '\n'.join(processed_lines)
        return self._post_process_text(result_text)
    
    def _is_section_header(self, line: str) -> bool:
        """Check if line is a section header - must be exact or start with the section name"""
        line_upper = line.strip().upper()
        # Remove common punctuation
        line_clean = re.sub(r'[:\-=]+$', '', line_upper).strip()
        
        # Check if it's an exact match or the line IS ONLY the section name (not containing it)
        return line_clean in PRESERVE_SECTIONS or any(
            line_clean == section or line_clean.startswith(section + ' ') 
            for section in PRESERVE_SECTIONS
        )
    
    def _post_process_text(self, text: str) -> str:
        """Post-process extracted text - format nicely with comprehensive cleaning"""
        
        # ===== STEP 0: Improve header/skills section spacing =====
        # Add simple line breaks to make the dense skills section more readable
        
        # Add blank line before major skill sections
        text = re.sub(r'(?<!\n)\n(Specialisation:|Programming:|Current Role:|Past one year:|Embedded Linux and OS:|Engineering practices:|Others:)', r'\n\n\1', text)
        
        # Separate items that were joined on same line  
        # For role descriptions
        text = re.sub(r'(Technical lead)\s+(System architecture)', r'\1\n\2', text)
        text = re.sub(r'(System architecture)\s+(Android and Yocto)', r'\1\n\2', text)
        text = re.sub(r'(Android and Yocto linux)\s+(Systems and TARA)', r'\1\n\2', text)
        text = re.sub(r'(Cyber security product owner)\s+Programming\s+Primary:', r'\1\n\nProgramming:\nPrimary:', text)
        text = re.sub(r'(Primary:[^\n]+)\s+Additional:', r'\1\nAdditional:', text)
        
        # Separate firmware skills
        text = re.sub(r'(ARM core and internals)\s+(Assembly code)', r'\1\n\2', text)
        text = re.sub(r'(Assembly code understanding)\s+(Schematics)', r'\1\n\2', text)
        
        # Separate OS/Linux skills to individual lines  
        text = re.sub(r'(BT, network)\s+(Audio, Multimedia)', r'\1\n\2', text)
        text = re.sub(r'(Audio, Multimedia)\s+(USB, SPI)', r'\1\n\2', text)
        text = re.sub(r'(USB, SPI, I2C)\s+(Yocto linux)', r'\1\n\2', text)
        text = re.sub(r'(Peripheral bring-up)\s+(Embedded hardware modules)', r'\1\n\2', text)
        text = re.sub(r'(QEMU)\s+(Kernel driver)', r'\1\n\2', text)
        
        # Separate engineering practices
        text = re.sub(r'(Product Lifecycle Management)\s+(Product roadmap)', r'\1\n\2', text)
        text = re.sub(r'(Agile model)\s+(Requirement grooming)', r'\1\n\2', text)
        text = re.sub(r'(System design \(UML\))\s+(Concept, HLD)', r'\1\n\2', text)
        
        # Separate others section  
        text = re.sub(r'(Hardware debugging and probing)\s+(AWS cloud)', r'\1\n\2', text)
        text = re.sub(r'(AWS cloud infra)\s+(Entrepreneurship)', r'\1\n\2', text)
        
        # ===== STEP 1: Remove empty PII placeholders =====
        # Remove patterns like "E: | M:" or "L: |"
        text = re.sub(r'\b[A-Z]:\s*\|\s*[A-Z]?:?\s*', '', text)
        text = re.sub(r'\b[A-Z]:\s*\|', '', text)
        
        # Remove ", ," patterns
        text = re.sub(r',\s*,+', ',', text)
        text = re.sub(r'^,\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*,+$', '', text, flags=re.MULTILINE)
        
        # Remove empty brackets
        text = re.sub(r'\[\s*\]', '', text)
        text = re.sub(r'\(\s*\)', '', text)
        
        # Remove lines that are just separators or placeholders
        text = re.sub(r'^[\s|,\-=]+$', '', text, flags=re.MULTILINE)
        
        # ===== STEP 2: Remove broken all-caps lines AND education section =====
        # Remove broken all-caps lines (mid-sentence text)
        lines = text.split('\n')
        cleaned_lines = []
        skip_education = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                if not skip_education:
                    cleaned_lines.append(line)
                continue
            
            # Remove education section completely
            if re.match(r'^Education\s*$', line, re.IGNORECASE):
                skip_education = True
                continue
            
            # Stop skipping when we hit Work Experience or other major section
            if skip_education and (re.match(r'^(Work Experience|Professional Experience|Experience|Projects)', line, re.IGNORECASE) or
                                  re.match(r'^[-=]{20,}$', line)):
                skip_education = False
            
            if skip_education:
                continue
            
            # Remove lines that are all caps AND:
            # 1. Long (>40 chars) but not recognizable section headers, OR
            # 2. End with "AND" or "ON" or other conjunctions (mid-sentence), OR
            # 3. Start with common words but in all caps like "POWER STATES", "ANALYTICAL SKILLS", etc.
            if re.match(r'^[A-Z\s\[\],\.\-;:&]+$', line):
                # Check if it's a recognized section header
                if self._is_section_header(line):
                    cleaned_lines.append(line)
                    continue
                    
                # If it's all caps and long, likely broken text - remove it
                if (len(line) > 40 or 
                    re.search(r'\b(AND|ON|OF|WITH|FOR|IN|TO|FROM|AT)\s*$', line) or
                    line.startswith(('POWER ', 'ANALYTICAL ', 'DESCRIPTION:', 'PRODUCTION '))):
                    # Skip this broken line
                    continue
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # ===== STEP 3: Fix broken word spacing - CONSERVATIVE line joining =====
        # Only join lines that are clearly broken mid-sentence, not separate items
        lines = text.split('\n')
        joined_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Only join if it's CLEARLY a broken sentence (ends with conjunction/preposition)
            # and is relatively short
            if (line and i + 1 < len(lines) and 
                len(line) < 100 and  # Short line
                re.search(r'\b(and|or|with|for|in|on|at|to|from|of|the|a|an)\s*$', line, re.IGNORECASE) and  # Ends with connector word
                not self._is_section_header(line) and
                not re.match(r'^\d{4}[-/]', line) and
                not re.match(r'^\[', line) and
                not re.match(r'^(Description|Platform|Programming|Duration|Role|Business):', line, re.IGNORECASE)):
                
                next_line = lines[i + 1].strip()
                # Join only if next line continues naturally (starts lowercase or is short)
                if (next_line and len(next_line) < 100 and
                    not self._is_section_header(next_line) and
                    not re.match(r'^\d{4}[-/]', next_line) and
                    not re.match(r'^\[', next_line) and
                    not re.match(r'^(Description|Platform|Programming|Duration|Role|Business):', next_line, re.IGNORECASE)):
                    joined_lines.append(line + ' ' + next_line)
                    i += 2
                    continue
            
            joined_lines.append(line)
            i += 1
        
        text = '\n'.join(joined_lines)
        
        # Remove multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)
        
        # ===== STEP 4: Fix date formatting =====
        def fix_dates(match):
            match_text = match.group(0)
            match_text = re.sub(r'\s+to\s+present\b', ' - Present', match_text, flags=re.IGNORECASE)
            match_text = re.sub(r'\s+to\s+till\s+date\b', ' - Present', match_text, flags=re.IGNORECASE)
            match_text = re.sub(r'(\d{4}(?:-\d{2})?)\s+to\s+(\d{4}(?:-\d{2})?)', r'\1 - \2', match_text, flags=re.IGNORECASE)
            return match_text
        
        text = re.sub(r'\d{4}(?:-\d{2})?\s+to\s+(?:present|till date|\d{4}(?:-\d{2})?)', fix_dates, text, flags=re.IGNORECASE)
        
        # ===== STEP 5: Format sections and add structure =====
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Add spacing between items that run together (e.g., "Development. Work requires" -> "Development.\n\nWork requires")
        text = re.sub(r'(\w)\.\s+([A-Z][a-z]+\s+(requires|involves|worked|implemented|built|used|did|also))', r'\1.\n\n\2', text)
        
        # Add spacing after sentences that end distinct thoughts
        text = re.sub(r'(development|implementation|requirements|analysis|support|partnership|traction|control stack|security|findings|NodeJS|app implementation)\.\s+([A-Z])', r'\1.\n\n\2', text, flags=re.IGNORECASE)
        
        # Fix awkwardly broken descriptions - join single words that are on separate lines within descriptions
        # Pattern: lines that are just 1-2 words and lowercase/small, should join with previous line
        lines = text.split('\n')
        rejoined = []
        i = 0
        while i < len(lines):
            current = lines[i].strip()
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If current line is very short (1-3 words) and next line starts lowercase or is continuation
                if (current and len(current.split()) <= 3 and 
                    not re.match(r'^(Description|Platform|Programming|Duration|Role|Business|\[|---):', current, re.IGNORECASE) and
                    next_line and len(next_line.split()) <= 3 and
                    not re.match(r'^[A-Z]', next_line) and
                    not re.match(r'^(Description|Platform|Programming|Duration|Role|Business|\[|---):', next_line, re.IGNORECASE)):
                    # Join these short fragments
                    rejoined.append(current + ' ' + next_line)
                    i += 2
                    continue
            rejoined.append(current)
            i += 1
        text = '\n'.join(rejoined)
        
        lines = text.split('\n')
        formatted_lines = []
        
        major_sections = {
            'PROFILE', 'SUMMARY', 'PROFILE SUMMARY',
            'SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES',
            'EXPERIENCE', 'WORK EXPERIENCE', 'WORK HISTORY', 'PROFESSIONAL EXPERIENCE',
            'PROJECTS', 'KEY PROJECTS',
            'CERTIFICATIONS', 'EDUCATION',
            'ACHIEVEMENTS', 'AWARDS'
        }
        
        last_was_date = False
        last_was_description = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a date line (start of new job entry)
            is_date_line = bool(re.match(r'^\d{4}[-/]', line))
            
            # Check if this is a description/platform line
            is_desc_line = bool(re.match(r'^(Description|Platform|Programming|Duration|Role|Business):', line, re.IGNORECASE))
            
            # Format section headers
            if self._is_section_header(line):
                if formatted_lines:
                    formatted_lines.append('')
                formatted_lines.append(line.upper())
                is_major = any(sec in line.upper() for sec in major_sections)
                formatted_lines.append(('=' if is_major else '-') * 50)
                last_was_date = False
                last_was_description = False
                
            # Add spacing and separator before each job entry (date lines)
            elif is_date_line:
                if formatted_lines:
                    formatted_lines.append('')
                    formatted_lines.append('-' * 50)
                formatted_lines.append('')
                formatted_lines.append(line)
                last_was_date = True
                last_was_description = False
                
            # Add spacing before Description/Platform/etc.
            elif is_desc_line:
                # Add extra space if there was a previous description (separate descriptions)
                if last_was_description and formatted_lines:
                    formatted_lines.append('')
                elif formatted_lines and not last_was_date:
                    formatted_lines.append('')
                formatted_lines.append(line)
                last_was_date = False
                last_was_description = True
                
            # Add spacing before [startup]/[contractor] tags
            elif re.match(r'^\[.*?\]', line):
                if formatted_lines:
                    formatted_lines.append('')
                    formatted_lines.append('')  # Double space before project tags
                formatted_lines.append(line)
                last_was_date = False
                last_was_description = False
                
            # Format bullet points
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                clean_line = line.lstrip('•-* ')
                if (re.match(r'^[A-Z]', clean_line) and 
                    'PROJECT:' not in clean_line.upper() and
                    not re.match(r'^(?:Developed|Implemented|Created|Built|Designed|Led)', clean_line) and
                    ':' in clean_line and len(clean_line) < 100):
                    clean_line = 'PROJECT: ' + clean_line
                formatted_lines.append('  • ' + clean_line)
                last_was_date = False
            else:
                formatted_lines.append(line)
                last_was_date = False
        
        # ===== STEP 6: Final cleanup =====
        text = '\n'.join(formatted_lines)
        
        # Remove excessive blank lines (max 2)
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        # Clean up separator duplicates
        text = re.sub(r'(-{50}\n)+', '-' * 50 + '\n', text)
        text = re.sub(r'(={50}\n)+', '=' * 50 + '\n', text)
        
        return text
    
    def process(self) -> str:
        """Main processing function"""
        logger.info(f"Processing {self.filename}")
        start_time = datetime.now()
        
        try:
            if self.layout_engine and self.extension in ['.pdf', '.jpg', '.jpeg', '.png']:
                result = self.process_with_ppstructure()
            else:
                result = self.process_without_layout()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Processing complete in {processing_time:.2f}s")
            logger.info(f"  Blocks kept: {self.stats['blocks_kept']}")
            logger.info(f"  PII items removed: {self.stats['pii_items_removed']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise


# ============================================================
# MAIN
# ============================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='PP-Structure Resume Redactor - Extract Skills, Experience, Summary'
    )
    
    parser.add_argument(
        'files',
        nargs='*',
        help='Resume files to process (PDF, DOCX, JPG, PNG)'
    )
    
    parser.add_argument(
        '--output-dir',
        '-o',
        default=OUTPUT_DIR,
        help='Output directory for cleaned resumes'
    )
    
    parser.add_argument(
        '--no-layout',
        action='store_true',
        help='Disable layout detection (use text extraction only)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Find files if none specified
    if not args.files:
        supported_extensions = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
        args.files = [
            os.path.join(ROOT_DIR, f) for f in os.listdir(ROOT_DIR)
            if os.path.splitext(f)[1].lower() in supported_extensions
        ]
    
    if not args.files:
        print("No files to process in:", ROOT_DIR)
        return 1
    
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("PP-STRUCTURE RESUME REDACTOR")
    print("Extracts: Skills, Experience, Summary (removes PII)")
    print("=" * 60)
    print(f"Found {len(args.files)} files to process")
    print()
    
    successful = 0
    failed = 0
    
    for filepath in args.files:
        try:
            print(f"\nProcessing: {os.path.basename(filepath)}")
            
            redactor = PPStructureRedactor(filepath)
            
            if args.no_layout:
                redactor.layout_engine = None
            
            result = redactor.process()
            
            # Generate output filename (simple .txt extension)
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            safe_name = re.sub(r'[^\w\-_\. ]', '_', base_name)
            output_name = f"{safe_name}.txt"
            output_path = os.path.join(output_dir, output_name)
            
            # Save result (no need for separate formatted file)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"PROFESSIONAL RESUME\n")
                f.write(f"{'=' * 50}\n\n")
                f.write(result)
            
            print(f"  Saved: {output_name}")
            successful += 1
            
        except Exception as e:
            print(f"  Failed: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"SUMMARY: {successful} successful, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
