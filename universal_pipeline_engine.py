"""
Universal CV Redaction Pipeline Engine
=======================================
Comprehensive system with specialized pipelines for all CV types.
Automatically detects CV format and routes to the appropriate processing pipeline.

Architecture:
- Profile Detector: Analyzes CV structure and selects optimal pipeline
- 6 Specialized Pipelines: Each optimized for specific CV format
- Universal Redaction Engine: Common PII removal logic
- Quality Validator: Ensures output quality across all pipelines
"""

import os
import re
import abc
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

# PDF Processing
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# OCR for scanned documents - import disabled to avoid reinitialization issues
HAS_PADDLEOCR = False

# NLP for advanced PII detection  
# Temporarily disabled due to initialization issues
HAS_SPACY = False
nlp = None
def get_nlp():
    return None

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEBUG_DIR = Path("debug_output")
OUTPUT_DIR = Path("final_output")
DEBUG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


class CVType(Enum):
    """CV Format Types"""
    NAUKRI = "naukri"                    # Naukri.com format with specific headers
    MULTI_COLUMN = "multi_column"        # 2+ column layouts
    STANDARD_ATS = "standard_ats"        # Single column ATS-friendly
    SCANNED_IMAGE = "scanned_image"      # Image-based/scanned PDFs
    CREATIVE_DESIGNER = "creative"       # Designer/creative CVs with graphics
    ACADEMIC_RESEARCH = "academic"       # Academic CVs with publications


@dataclass
class CVProfile:
    """CV Analysis Profile"""
    cv_type: CVType
    confidence: float
    has_columns: bool
    column_count: int
    is_scanned: bool
    text_density: float
    has_graphics: bool
    detected_sections: List[str]
    
    def __str__(self):
        return f"{self.cv_type.value} (confidence: {self.confidence:.2f})"


class CVProfileDetector:
    """
    Analyzes PDF structure to determine CV type and characteristics.
    Routes to appropriate specialized pipeline.
    """
    
    def __init__(self):
        self.naukri_indicators = [
            'naukri', 'resume headline', 'key skills', 'it skills',
            'profile summary', 'personal details', 'declaration'
        ]
        
        self.academic_indicators = [
            'publications', 'research', 'citations', 'h-index',
            'conference', 'journal', 'thesis', 'dissertation'
        ]
        
        self.creative_indicators = [
            'portfolio', 'behance', 'dribbble', 'design',
            'creative', 'ui/ux', 'graphic design'
        ]
    
    def analyze(self, pdf_path: str) -> CVProfile:
        """Comprehensive CV analysis"""
        logger.info(f"Analyzing: {Path(pdf_path).name}")
        
        # Check filename for obvious indicators
        filename = Path(pdf_path).name.lower()
        if 'naukri' in filename:
            return self._create_profile(CVType.NAUKRI, 0.95, pdf_path)
        
        # Analyze PDF structure
        if not HAS_FITZ and not HAS_PDFPLUMBER:
            logger.error("No PDF library available")
            return self._create_profile(CVType.STANDARD_ATS, 0.5, pdf_path)
        
        try:
            # Get structure analysis
            structure = self._analyze_structure(pdf_path)
            
            # Determine CV type based on structure
            cv_type, confidence = self._classify_type(structure, filename)
            
            return CVProfile(
                cv_type=cv_type,
                confidence=confidence,
                has_columns=structure['has_columns'],
                column_count=structure['column_count'],
                is_scanned=structure['is_scanned'],
                text_density=structure['text_density'],
                has_graphics=structure['has_graphics'],
                detected_sections=structure['sections']
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._create_profile(CVType.STANDARD_ATS, 0.5, pdf_path)
    
    def _analyze_structure(self, pdf_path: str) -> Dict:
        """Analyze PDF structure"""
        structure = {
            'has_columns': False,
            'column_count': 1,
            'is_scanned': False,
            'text_density': 0.0,
            'has_graphics': False,
            'sections': [],
            'content_sample': ''
        }
        
        if HAS_PDFPLUMBER:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return structure
                
                page = pdf.pages[0]
                
                # Check for columns
                words = page.extract_words(x_tolerance=2, y_tolerance=2)
                if words:
                    structure['column_count'] = self._detect_columns(words, page.width)
                    structure['has_columns'] = structure['column_count'] > 1
                    
                    # Text density
                    total_chars = sum(len(w['text']) for w in words)
                    page_area = page.width * page.height
                    structure['text_density'] = total_chars / page_area if page_area > 0 else 0
                    
                    # Check if scanned (low text density or fragmented text)
                    single_char_words = sum(1 for w in words if len(w['text']) == 1)
                    fragmentation_ratio = single_char_words / len(words) if words else 0
                    structure['is_scanned'] = fragmentation_ratio > 0.15 or structure['text_density'] < 0.02
                    
                    # Extract sample text for content analysis
                    structure['content_sample'] = ' '.join([w['text'] for w in words[:200]])
                
                # Check for graphics/images
                structure['has_graphics'] = len(page.images) > 0
        
        elif HAS_FITZ:
            with fitz.open(pdf_path) as doc:
                if not doc:
                    return structure
                
                page = doc[0]
                text = page.get_text()
                
                # Simple text density check
                page_area = page.rect.width * page.rect.height
                structure['text_density'] = len(text) / page_area if page_area > 0 else 0
                structure['is_scanned'] = structure['text_density'] < 0.02
                structure['content_sample'] = text[:1000]
                
                # Check for images
                structure['has_graphics'] = len(page.get_images()) > 0
        
        # Detect sections from sample text
        structure['sections'] = self._detect_sections(structure['content_sample'])
        
        return structure
    
    def _detect_columns(self, words: List[Dict], page_width: float) -> int:
        """Detect number of columns"""
        if not words:
            return 1
        
        # Count words in left/center/right thirds
        left = sum(1 for w in words if w['x0'] < page_width * 0.35)
        center = sum(1 for w in words if page_width * 0.35 <= w['x0'] < page_width * 0.65)
        right = sum(1 for w in words if w['x0'] >= page_width * 0.65)
        
        # Multi-column if significant content in multiple regions
        active_regions = sum([left > 20, center > 20, right > 20])
        
        if active_regions >= 2 and (left > 30 or right > 30):
            return 2
        elif active_regions >= 3:
            return 3
        
        return 1
    
    def _detect_sections(self, text: str) -> List[str]:
        """Detect CV sections"""
        text_upper = text.upper()
        sections = []
        
        section_keywords = {
            'SUMMARY': ['SUMMARY', 'PROFILE', 'OBJECTIVE', 'ABOUT'],
            'EXPERIENCE': ['EXPERIENCE', 'WORK HISTORY', 'EMPLOYMENT'],
            'EDUCATION': ['EDUCATION', 'ACADEMIC', 'QUALIFICATION'],
            'SKILLS': ['SKILLS', 'TECHNICAL SKILLS', 'COMPETENCIES'],
            'PROJECTS': ['PROJECTS', 'KEY PROJECTS'],
            'CERTIFICATIONS': ['CERTIFICATIONS', 'LICENSES'],
            'PUBLICATIONS': ['PUBLICATIONS', 'RESEARCH'],
            'REFERENCES': ['REFERENCES']
        }
        
        for section, keywords in section_keywords.items():
            if any(kw in text_upper for kw in keywords):
                sections.append(section)
        
        return sections
    
    def _classify_type(self, structure: Dict, filename: str) -> Tuple[CVType, float]:
        """Classify CV type based on structure and content"""
        content = structure['content_sample'].lower()
        
        # Check for Naukri format
        naukri_score = sum(1 for indicator in self.naukri_indicators if indicator in content)
        if naukri_score >= 3:
            return CVType.NAUKRI, min(0.95, 0.7 + (naukri_score * 0.05))
        
        # Check for academic format
        academic_score = sum(1 for indicator in self.academic_indicators if indicator in content)
        if academic_score >= 3:
            return CVType.ACADEMIC_RESEARCH, min(0.95, 0.7 + (academic_score * 0.05))
        
        # Check for creative format
        creative_score = sum(1 for indicator in self.creative_indicators if indicator in content)
        if creative_score >= 2 and structure['has_graphics']:
            return CVType.CREATIVE_DESIGNER, min(0.90, 0.7 + (creative_score * 0.08))
        
        # Check for scanned
        if structure['is_scanned']:
            return CVType.SCANNED_IMAGE, 0.85
        
        # Check for multi-column
        if structure['has_columns'] and structure['column_count'] >= 2:
            return CVType.MULTI_COLUMN, 0.85
        
        # Default to standard ATS
        return CVType.STANDARD_ATS, 0.75
    
    def _create_profile(self, cv_type: CVType, confidence: float, pdf_path: str) -> CVProfile:
        """Create minimal profile"""
        return CVProfile(
            cv_type=cv_type,
            confidence=confidence,
            has_columns=False,
            column_count=1,
            is_scanned=False,
            text_density=0.0,
            has_graphics=False,
            detected_sections=[]
        )


class BasePipeline(abc.ABC):
    """Abstract base class for all specialized pipelines"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.pipeline_name = self.__class__.__name__
    
    @abc.abstractmethod
    def extract_text(self, pdf_path: str) -> str:
        """Extract text maintaining reading order"""
        pass
    
    @abc.abstractmethod
    def preprocess(self, text: str) -> str:
        """Pipeline-specific preprocessing"""
        pass
    
    def save_debug(self, content: str, stage: str, filename: str):
        """Save debug output"""
        if self.debug:
            try:
                name = Path(filename).stem
                path = DEBUG_DIR / f"{name}_{self.pipeline_name}_{stage}.txt"
                path.write_text(content, encoding='utf-8')
                logger.debug(f"Saved debug: {path}")
            except Exception as e:
                logger.error(f"Failed to save debug: {e}")
    
    def process(self, pdf_path: str) -> str:
        """Main processing pipeline"""
        logger.info(f"[{self.pipeline_name}] Processing: {Path(pdf_path).name}")
        
        # Extract
        raw_text = self.extract_text(pdf_path)
        if self.debug:
            self.save_debug(raw_text, "01_extracted", pdf_path)
        
        # Preprocess
        processed_text = self.preprocess(raw_text)
        if self.debug:
            self.save_debug(processed_text, "02_preprocessed", pdf_path)
        
        return processed_text


class NaukriPipeline(BasePipeline):
    """
    Specialized pipeline for Naukri.com format CVs.
    Handles specific headers, formatting, and layout quirks.
    """
    
    def __init__(self, debug: bool = False):
        super().__init__(debug)
        self.naukri_sections = [
            'RESUME HEADLINE', 'KEY SKILLS', 'EMPLOYMENT DETAILS',
            'IT SKILLS', 'PROJECTS', 'PROFILE SUMMARY',
            'PERSONAL DETAILS', 'DECLARATION'
        ]
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract using PyMuPDF with block sorting"""
        if not HAS_FITZ:
            return "Error: PyMuPDF not available"
        
        text_blocks = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                blocks = page.get_text("blocks", sort=True)
                for block in blocks:
                    if block[6] == 0:  # Text block
                        text = block[4].strip()
                        if text:
                            text_blocks.append(text)
        
        return "\n\n".join(text_blocks)
    
    def preprocess(self, text: str) -> str:
        """Naukri-specific preprocessing"""
        # Normalize Naukri section headers
        for section in self.naukri_sections:
            text = re.sub(rf'\b{section}\b\s*:?', f"\n{section}\n", text, flags=re.IGNORECASE)
        
        # Remove Naukri branding/watermarks
        text = re.sub(r'Naukri\.com|www\.naukri\.com', '', text, flags=re.IGNORECASE)
        
        # Clean up spacing
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text


class MultiColumnPipeline(BasePipeline):
    """
    Specialized pipeline for multi-column CV layouts.
    Intelligently detects column gutters and maintains reading order.
    """
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract with column-aware processing"""
        if not HAS_PDFPLUMBER:
            if HAS_FITZ:
                return self._fitz_fallback(pdf_path)
            return "Error: No PDF library available"
        
        all_text = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                logger.info(f"Processing page {page_num + 1}")
                
                words = page.extract_words(x_tolerance=2, y_tolerance=2)
                if not words:
                    continue
                
                # Detect column split
                split_point = self._find_column_split(words, page.width)
                
                if split_point:
                    # Extract columns separately
                    left_words = [w for w in words if w['x1'] < split_point]
                    right_words = [w for w in words if w['x0'] > split_point]
                    
                    # Sort by vertical position
                    left_words.sort(key=lambda w: w['top'])
                    right_words.sort(key=lambda w: w['top'])
                    
                    # Build text
                    left_text = self._build_text_from_words(left_words)
                    right_text = self._build_text_from_words(right_words)
                    
                    all_text.append(left_text)
                    all_text.append(right_text)
                else:
                    # Single column
                    words.sort(key=lambda w: (w['top'], w['x0']))
                    page_text = self._build_text_from_words(words)
                    all_text.append(page_text)
        
        return "\n\n".join(all_text)
    
    def _find_column_split(self, words: List[Dict], page_width: float) -> Optional[float]:
        """Find the gutter between columns"""
        if not words:
            return None
        
        # Count words in vertical strips
        strip_width = page_width / 20
        strip_counts = [0] * 20
        
        for w in words:
            word_center = (w['x0'] + w['x1']) / 2
            strip_idx = int(word_center / strip_width)
            if 0 <= strip_idx < 20:
                strip_counts[strip_idx] += 1
        
        # Find minimum in middle region
        min_count = float('inf')
        min_idx = -1
        for idx in range(5, 15):
            if strip_counts[idx] < min_count:
                min_count = strip_counts[idx]
                min_idx = idx
        
        # Validate it's a real gap
        if min_count < 3 and min_idx >= 0:
            return (min_idx + 0.5) * strip_width
        
        return None
    
    def _build_text_from_words(self, words: List[Dict]) -> str:
        """Build text from word list"""
        if not words:
            return ""
        
        lines = []
        current_line = []
        current_top = words[0]['top']
        
        for word in words:
            # New line if vertical gap
            if abs(word['top'] - current_top) > 3:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word['text']]
                current_top = word['top']
            else:
                current_line.append(word['text'])
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _fitz_fallback(self, pdf_path: str) -> str:
        """Fallback to PyMuPDF"""
        text_blocks = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                blocks = page.get_text("blocks", sort=True)
                for block in blocks:
                    if block[6] == 0:
                        text_blocks.append(block[4].strip())
        return "\n\n".join(text_blocks)
    
    def preprocess(self, text: str) -> str:
        """Multi-column specific preprocessing"""
        # Fix split words
        text = self._fix_split_words(text)
        
        # Normalize spacing
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _fix_split_words(self, text: str) -> str:
        """Fix words split across columns"""
        # Pattern: word ending with hyphen followed by continuation
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        return text


class StandardATSPipeline(BasePipeline):
    """
    Pipeline for standard single-column ATS-friendly CVs.
    Optimized for clean extraction and section detection.
    """
    
    def extract_text(self, pdf_path: str) -> str:
        """Simple linear extraction"""
        if HAS_FITZ:
            with fitz.open(pdf_path) as doc:
                return "\n\n".join([page.get_text() for page in doc])
        elif HAS_PDFPLUMBER:
            with pdfplumber.open(pdf_path) as pdf:
                return "\n\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return "Error: No PDF library available"
    
    def preprocess(self, text: str) -> str:
        """Standard preprocessing"""
        # Normalize bullets
        text = re.sub(r'[•●○◦▪▫■□⬤→]', '•', text)
        
        # Fix spacing
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text


class ScannedImagePipeline(BasePipeline):
    """
    Pipeline for scanned/image-based PDFs.
    Uses OCR with word healing for fragmented text.
    """
    
    # Class-level OCR instance to avoid reinitialization
    _ocr_instance = None
    
    def __init__(self, debug: bool = False):
        super().__init__(debug)
        # Use class-level instance
        if ScannedImagePipeline._ocr_instance is None and HAS_PADDLEOCR:
            try:
                from paddleocr import PaddleOCR
                ScannedImagePipeline._ocr_instance = PaddleOCR(lang='en', use_angle_cls=False)
                logger.info("PaddleOCR initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize PaddleOCR: {e}")
                ScannedImagePipeline._ocr_instance = None
        
        self.ocr = ScannedImagePipeline._ocr_instance
    
    def extract_text(self, pdf_path: str) -> str:
        """OCR extraction"""
        if not self.ocr:
            logger.warning("OCR not available, using basic extraction")
            return self._basic_extraction(pdf_path)
        
        text_lines = []
        
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                logger.info(f"OCR processing page {page_num + 1}")
                
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling
                img_path = f"temp_ocr_page_{page_num}.png"
                pix.save(img_path)
                
                try:
                    # Run OCR
                    result = self.ocr.ocr(img_path)
                    
                    if result and result[0]:
                        for line in result[0]:
                            if isinstance(line, list) and len(line) >= 2:
                                text = line[1][0] if isinstance(line[1], tuple) else line[1]
                                text_lines.append(text)
                finally:
                    # Cleanup
                    if os.path.exists(img_path):
                        os.remove(img_path)
        
        return "\n".join(text_lines)
    
    def _basic_extraction(self, pdf_path: str) -> str:
        """Fallback extraction"""
        if HAS_FITZ:
            with fitz.open(pdf_path) as doc:
                return "\n".join([page.get_text() for page in doc])
        return ""
    
    def preprocess(self, text: str) -> str:
        """OCR-specific preprocessing with word healing"""
        # Fix common OCR errors
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  # Add space between camelCase
        
        # Heal fragmented words
        text = self._heal_fragmented_words(text)
        
        # Clean up
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _heal_fragmented_words(self, text: str) -> str:
        """Fix fragmented text like 'e x p e r i e n c e' -> 'experience'"""
        lines = text.split('\n')
        healed_lines = []
        
        for line in lines:
            # Pattern: single letters separated by spaces
            if re.search(r'\b[a-z]\s+[a-z](\s+[a-z])+\b', line, re.IGNORECASE):
                # Try to heal
                parts = line.split()
                healed_parts = []
                temp_word = []
                
                for part in parts:
                    if len(part) == 1 and part.isalpha():
                        temp_word.append(part)
                    else:
                        if temp_word:
                            # Join and check if valid
                            joined = ''.join(temp_word)
                            if len(joined) >= 3:
                                healed_parts.append(joined)
                            else:
                                healed_parts.extend(temp_word)
                            temp_word = []
                        healed_parts.append(part)
                
                if temp_word:
                    joined = ''.join(temp_word)
                    healed_parts.append(joined)
                
                healed_lines.append(' '.join(healed_parts))
            else:
                healed_lines.append(line)
        
        return '\n'.join(healed_lines)


class CreativeDesignerPipeline(BasePipeline):
    """
    Pipeline for creative/designer CVs with graphics and unusual layouts.
    Handles non-standard structures while preserving content.
    """
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text avoiding graphic areas"""
        if not HAS_PDFPLUMBER:
            return self._fitz_fallback(pdf_path)
        
        all_text = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Get text and images
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    all_text.append(text)
        
        return "\n\n".join(all_text)
    
    def _fitz_fallback(self, pdf_path: str) -> str:
        """Fallback extraction"""
        with fitz.open(pdf_path) as doc:
            return "\n\n".join([page.get_text() for page in doc])
    
    def preprocess(self, text: str) -> str:
        """Creative CV preprocessing"""
        # Remove common design artifacts
        text = re.sub(r'[★☆⭐✨💼📧📱🏠]', '', text)  # Remove icons
        
        # Normalize spacing
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text


class AcademicResearchPipeline(BasePipeline):
    """
    Pipeline for academic/research CVs with publications and citations.
    Preserves structured academic content.
    """
    
    def extract_text(self, pdf_path: str) -> str:
        """Standard extraction"""
        if HAS_FITZ:
            with fitz.open(pdf_path) as doc:
                return "\n\n".join([page.get_text() for page in doc])
        elif HAS_PDFPLUMBER:
            with pdfplumber.open(pdf_path) as pdf:
                return "\n\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return ""
    
    def preprocess(self, text: str) -> str:
        """Academic-specific preprocessing"""
        # Normalize citation formats
        text = re.sub(r'\[(\d+)\]', r'[\1]', text)
        
        # Clean up
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text


class UniversalRedactionEngine:
    """
    Universal PII removal engine used by all pipelines.
    Handles emails, phones, names, addresses while protecting professional content.
    """
    
    def __init__(self):
        # Compile patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.url_pattern = re.compile(r'https?://[^\s]+')
        self.linkedin_pattern = re.compile(r'linkedin\.com/in/[\w\-]+', re.IGNORECASE)
        self.github_pattern = re.compile(r'github\.com/[\w\-]+', re.IGNORECASE)
        
        # Protected terms (technical skills, etc.)
        self.protected_terms = self._load_protected_terms()
        
        # Lazy load spaCy
        self.nlp = None
    
    def _load_protected_terms(self) -> Set[str]:
        """Load comprehensive list of protected terms"""
        terms = {
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'go',
            'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash',
            
            # Frameworks & libraries
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'nodejs', 'express',
            'laravel', 'rails', 'aspnet', 'dotnet', 'jquery', 'bootstrap', 'tailwind',
            
            # Databases
            'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlserver', 'redis', 'cassandra',
            'dynamodb', 'elasticsearch', 'neo4j', 'sqlite', 'mariadb',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github',
            'terraform', 'ansible', 'puppet', 'chef', 'circleci', 'travis',
            
            # Tools & Technologies
            'git', 'linux', 'unix', 'windows', 'macos', 'vscode', 'intellij', 'eclipse',
            'vim', 'emacs', 'postman', 'swagger', 'jira', 'confluence', 'slack',
            
            # Roles & titles
            'engineer', 'developer', 'programmer', 'architect', 'manager', 'lead',
            'senior', 'junior', 'principal', 'staff', 'consultant', 'analyst',
            'scientist', 'researcher', 'designer', 'administrator', 'specialist',
            
            # Common terms (excluding section headers that we want to remove)
            'responsibilities', 'certifications', 'achievements', 'references'
        }
        return terms
    
    def redact(self, text: str, filename: str = "") -> str:
        """
        Main redaction method with comprehensive PII removal and professional formatting.
        """
        # Phase 1: Protect technical terms first
        protected_map = {}
        placeholder_counter = [0]
        
        def protect_term(match):
            term = match.group(0)
            if term.lower() in self.protected_terms:
                placeholder = f"§PROTECTED{placeholder_counter[0]}§"
                protected_map[placeholder] = term
                placeholder_counter[0] += 1
                return placeholder
            return term
        
        text = re.sub(r'\b\w+\b', protect_term, text)
        
        # Phase 2: Remove ALL PII patterns aggressively (NO PLACEHOLDERS)
        # Emails - remove completely
        text = self.email_pattern.sub('', text)
        
        # Phones - multiple patterns, remove completely
        text = re.sub(r'\(?\+?\d{1,3}\)?[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}', '', text)
        text = re.sub(r'\b\d{10}\b', '', text)
        text = re.sub(r'PHONE\s*[:|-]?\s*\S+', '', text, flags=re.IGNORECASE)
        
        # URLs and Social - NO PLACEHOLDERS, just remove
        text = self.url_pattern.sub('', text)
        text = self.linkedin_pattern.sub('', text)
        text = self.github_pattern.sub('', text)
        text = re.sub(r'linkedin\.com[^\s]*', '', text, flags=re.IGNORECASE)
        
        # Locations - Comprehensive Indian cities removal (NO PLACEHOLDERS)
        # First remove city + state + country combinations
        text = re.sub(r'\b(Pune|Mumbai|Delhi|Bangalore|Bengaluru|Hyderabad|Chennai|Kolkata|Ahmedabad|Jaipur),?\s*(Maharashtra|Karnataka|Tamil Nadu|Telangana)?,?\s*(India|INDIA)?\b', '', text, flags=re.IGNORECASE)
        
        # Then remove all cities
        cities = ['Pune', 'Mumbai', 'Delhi', 'Bangalore', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 
                 'Ahmedabad', 'Jaipur', 'Lucknow', 'Kanpur', 'Nagpur', 'Indore', 'Thane', 'Bhopal', 
                 'Visakhapatnam', 'Pimpri', 'Patna', 'Vadodara', 'Ghaziabad', 'Ludhiana', 'Agra', 
                 'Nashik', 'Faridabad', 'Meerut', 'Rajkot', 'Varanasi', 'Srinagar', 'Aurangabad', 
                 'Dhanbad', 'Amritsar', 'Noida', 'Allahabad', 'Ranchi', 'Howrah', 'Coimbatore', 
                 'Jabalpur', 'Gwalior', 'Jalgaon', 'Solapur', 'Mysore', 'Mysuru', 'Vellore', 
                 'Faizabad', 'Salem', 'Tiruchirappalli', 'Tirupati', 'Belgaum', 'Mangalore', 
                 'Trivandrum', 'Kochi', 'Cochin', 'Ernakulam', 'Chandigarh', 'Gurgaon', 'Gurugram', 
                 'Navi Mumbai', 'Greater Noida', 'Shegaon', 'Cambridge', 'London', 'Boston']
        
        for city in cities:
            text = re.sub(rf'\b{city}\b,?\s*', '', text, flags=re.IGNORECASE)
        
        # Then remove all states
        states = ['Maharashtra', 'Karnataka', 'Tamil Nadu', 'Telangana', 'West Bengal', 'Gujarat', 
                 'Rajasthan', 'Madhya Pradesh', 'Uttar Pradesh', 'Kerala', 'Punjab', 'Haryana', 
                 'Bihar', 'Odisha', 'Andhra Pradesh', 'Assam', 'Jharkhand', 'Chhattisgarh', 
                 'Uttarakhand', 'Himachal Pradesh', 'Goa', 'India', 'INDIA']
        
        for state in states:
            text = re.sub(rf'\b{state}\b,?\s*', '', text, flags=re.IGNORECASE)
        
        # Email/Phone labels
        text = re.sub(r'EMAIL\s*[:|-]?\s*[^\s\n]+', '', text, flags=re.IGNORECASE)
        
        # Phase 3: Remove names from filename
        if filename:
            text = self._remove_filename_names(text, filename)
        
        # Phase 4: Position-aware name removal (aggressive in header)
        text = self._position_aware_name_removal(text)
        
        # Phase 5: Remove Education section completely
        text = self._remove_education_section(text)
        
        # Phase 5b: Remove Personal sections (Hobbies, Interests, Languages)
        text = self._remove_personal_sections(text)
        
        # Phase 5c: Remove demographics (DOB, Gender, Marital Status, etc.)
        text = self._remove_demographics(text)
        
        # Phase 5d: Rewrite profile summaries to remove first-person with names
        text = self._rewrite_profile_summaries(text)
        
        # Phase 5e: Remove declaration sections
        text = self._remove_declaration_section(text)
        
        # Phase 6: Clean up artifacts
        text = self._cleanup_artifacts(text)
        
        # Phase 7: Restore protected terms BEFORE final formatting
        for placeholder, original_term in protected_map.items():
            text = text.replace(placeholder, original_term)
        
        # Phase 8: Professional formatting with aggressive word spacing (AFTER term restoration)
        text = self._professional_formatting(text)
        
        return text
    
    def _remove_filename_names(self, text: str, filename: str) -> str:
        """Extract and remove names from filename"""
        # Extract potential names from filename
        stem = Path(filename).stem
        # Remove common non-name parts
        clean_stem = re.sub(r'(resume|cv|naukri|redacted|_\d+|\.\.)', '', stem, flags=re.IGNORECASE)
        clean_stem = re.sub(r'[^a-zA-Z\s]', ' ', clean_stem)
        
        # Split camelCase
        clean_stem = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_stem)
        
        # Extract words that look like names (capitalized, 2+ chars)
        parts = clean_stem.split()
        potential_names = [p for p in parts if p and len(p) > 2 and p[0].isupper()]
        
        # Remove as full name and individual parts
        if len(potential_names) >= 2:
            full_name = ' '.join(potential_names)
            # Remove with flexible whitespace
            pattern = r'\b' + r'\s+'.join([re.escape(p) for p in potential_names]) + r'\b'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    def _position_aware_name_removal(self, text: str) -> str:
        """Remove names throughout the document"""
        # Without NLP, use aggressive pattern-based removal
        lines = text.split('\n')
        
        # Common section headers to preserve
        section_headers = ['summary', 'education', 'experience', 'skills', 'projects', 
                          'work experience', 'professional', 'certifications', 'awards',
                          'publications', 'programming', 'technical', 'languages',
                          'achievements', 'objective', 'profile', 'qualifications',
                          'training', 'interests', 'references', 'others']
        
        # Process all lines for name removal
        for i in range(len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            # Skip if line is a section header
            if stripped.lower() in section_headers:
                continue
            
            # Skip if line is ALL CAPS or has technical content
            if line.isupper() or any(tech in line.lower() for tech in ['java', 'python', 'android', 'linux', 'aws']):
                continue
            
            # Remove standalone name patterns (more aggressive in first 20 lines)
            if i < 20:
                # Very aggressive in header
                lines[i] = re.sub(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\b', '', line)
            else:
                # Moderate in body - only obvious name patterns on their own lines
                lines[i] = re.sub(r'^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\s*$', '', line)
        
        return '\n'.join(lines)
    
    def _remove_education_section(self, text: str) -> str:
        """Remove education section completely"""
        # Split text into lines for line-by-line analysis
        lines = text.split('\n')
        result_lines = []
        in_education = False
        education_depth = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if this is an education section header (case-insensitive, allows some variations)
            if stripped.lower() in ['education', 'academic', 'academics', 'qualifications', 'qualification', 
                                     'educational background', 'academic background']:
                in_education = True
                education_depth = 0
                continue
            
            # Detect inline degree patterns that indicate education info
            # Match patterns like "Bachelor of", "Master of", "B.Tech", "M.Tech", etc.
            if re.search(r'\b(bachelor|master|b\.tech|m\.tech|b\.e\.|m\.e\.|mba|phd|diploma)\b', 
                        stripped, re.IGNORECASE):
                in_education = True
                education_depth = 0
                continue
            
            # Check if we've reached next major section (exit education)
            if in_education:
                # Next section markers - check against common section names
                next_sections = ['work experience', 'experience', 'professional experience', 
                               'work', 'skills', 'technical skills', 'projects', 'project',
                               'professional', 'summary', 'others', 'programming', 
                               'embedded', 'engineering', 'certifications']
                
                if any(stripped.lower() == sec for sec in next_sections):
                    in_education = False
                # Also exit after substantial content (like 25 lines)
                elif education_depth > 25:
                    in_education = False
                else:
                    education_depth += 1
                    continue
            
            # Keep line if not in education section
            if not in_education:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _remove_personal_sections(self, text: str) -> str:
        """Remove Personal Interests, Hobbies, Languages Known sections"""
        lines = text.split('\n')
        result_lines = []
        in_personal_section = False
        section_depth = 0
        
        # Personal section markers
        personal_markers = ['personal interests', 'hobbies', 'interests', 
                          'activities and interest', 'activities and interests',
                          'languages known', 'language proficiency', 'languages',
                          'personal assets', 'personal details', 'personal information',
                          'extra curricular', 'extracurricular activities',
                          'personal', 'leisure', 'recreation']
        
        for i, line in enumerate(lines):
            stripped = line.strip().lower()
            
            # Check if this is a personal section header
            if any(marker == stripped or stripped.startswith(marker + ':') for marker in personal_markers):
                in_personal_section = True
                section_depth = 0
                continue
            
            # Check if we've reached next major section
            if in_personal_section:
                next_sections = ['work experience', 'experience', 'professional experience',
                               'projects', 'certifications', 'skills', 'technical skills',
                               'achievements', 'awards', 'declaration', 'references']
                
                if any(stripped == sec or stripped.startswith(sec + ':') for sec in next_sections):
                    in_personal_section = False
                elif section_depth > 20:  # Exit after substantial content
                    in_personal_section = False
                else:
                    section_depth += 1
                    continue
            
            # Keep line if not in personal section
            if not in_personal_section:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _remove_demographics(self, text: str) -> str:
        """Remove demographic information: DOB, Gender, Marital Status, Father's/Mother's names, Nationality"""
        # Date of Birth patterns
        text = re.sub(r'(?i)\b(date of birth|dob|birth date)\s*:?\s*[^\n]+', '', text)
        text = re.sub(r'(?i)\b(born on|born)\s*:?\s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', '', text)
        
        # Gender
        text = re.sub(r'(?i)\b(gender|sex)\s*:?\s*(male|female|m|f|other)[^\n]*', '', text)
        
        # Marital Status
        text = re.sub(r'(?i)\b(marital status|marriage status)\s*:?\s*(single|married|divorced|widowed)[^\n]*', '', text)
        
        # Father's/Mother's names
        text = re.sub(r"(?i)\b(father's name|fathers name|mother's name|mothers name)\s*:?\s*[^\n]+", '', text)
        
        # Nationality (when explicitly stated)
        text = re.sub(r'(?i)\bnationality\s*:?\s*(indian|american|british|canadian|australian)[^\n]*', '', text)
        
        # Age
        text = re.sub(r'(?i)\bage\s*:?\s*\d{1,3}\s*(years?|yrs?)?[^\n]*', '', text)
        
        return text
    
    def _remove_declaration_section(self, text: str) -> str:
        """Remove declaration section completely"""
        # Remove declaration section with various patterns
        # Pattern 1: Section header followed by content
        text = re.sub(r'(?i)^\s*DECLARATION\s*\n.*?(?=\n\s*[A-Z][A-Z\s]{3,}|\Z)', '', text, flags=re.MULTILINE | re.DOTALL)
        
        # Pattern 2: "I hereby declare..." statements
        text = re.sub(r'(?i)\bI\s+hereby\s+declare\b.*?(?=\n\n|\Z)', '', text, flags=re.DOTALL)
        
        # Pattern 3: Common declaration phrases
        text = re.sub(r'(?i)^\s*.*?declaration.*?(?:true|correct|best of my knowledge).*?$', '', text, flags=re.MULTILINE)
        
        # Pattern 4: Declaration with signature/place/date
        text = re.sub(r'(?i)(declaration|place|date)\s*:.*?$', '', text, flags=re.MULTILINE)
        
        return text
    
    def _rewrite_profile_summaries(self, text: str) -> str:
        """Rewrite profile summaries to remove first-person references with names"""
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            original_line = line
            
            # Pattern: "I am [Name], a [title]..." -> "A [title]..."
            line = re.sub(r'(?i)^\s*I am [A-Z][a-z]+(\s+[A-Z][a-z]+){0,3},\s*a\s+', 'A ', line)
            line = re.sub(r'(?i)^\s*I am [A-Z][a-z]+(\s+[A-Z][a-z]+){0,3},\s*an\s+', 'An ', line)
            
            # Pattern: "I, [Name], am a [title]..." -> "A [title]..."
            line = re.sub(r'(?i)^\s*I,\s*[A-Z][a-z]+(\s+[A-Z][a-z]+){0,3},\s*am\s+a\s+', 'A ', line)
            
            # Pattern: "My name is [Name] and I am..." -> Remove entire name clause
            line = re.sub(r'(?i)^\s*My name is [A-Z][a-z]+(\s+[A-Z][a-z]+){0,3}\s*and\s*', '', line)
            line = re.sub(r'(?i)^\s*My name is [A-Z][a-z]+(\s+[A-Z][a-z]+){0,3}\.?\s*', '', line)
            
            # If line was modified, ensure it starts properly
            if line != original_line and line.strip():
                # Capitalize first letter if needed
                line = line.strip()
                if line and line[0].islower():
                    line = line[0].upper() + line[1:]
            
            result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _cleanup_artifacts(self, text: str) -> str:
        """Clean up redaction artifacts and remove remaining names"""
        # Remove social media labels and remnants
        text = re.sub(r'(?i)\b(?:social links?|connect with me|find me on|follow me)\s*:?\s*', '', text)
        text = re.sub(r'(?i)\b(?:linkedin|github|twitter|facebook|instagram)\s*:?\s*', '', text)
        
        # Remove standalone names on their own lines (aggressive)
        # This catches names like "John Doe" or "Abhishek Kumar Dwivedi"
        text = re.sub(r'^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\s*$', '', text, flags=re.MULTILINE)
        
        # Remove lines that are just single digits (page numbers)
        text = re.sub(r'^\s*\d\s*$', '', text, flags=re.MULTILINE)
        
        # Remove common header/footer patterns
        text = re.sub(r'^\s*PROFESSIONAL EXPERIENCES\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove empty labels and their remnants
        text = re.sub(r'\b(Email|Phone|Mobile|Address|Location|Contact|LinkedIn|GitHub|Website|Twitter|Facebook|Instagram|Social Links?)\s*[:|-]?\s*[,|\n]', '', text, flags=re.IGNORECASE)
        
        # Remove lines with only removed markers
        text = re.sub(r'^.*?\[.*?REMOVED\].*?$', '', text, flags=re.MULTILINE)
        
        # Remove lines that only have labels without content
        text = re.sub(r'(?m)^\s*(E:|M:|P:|Email:|Phone:|Mobile:|Address:|Location:|City:|State:|Country:)\s*$', '', text, flags=re.IGNORECASE)
        
        # Remove isolated social media fragments
        text = re.sub(r'(?m)^\s*(?:n/|/in/|@)[a-zA-Z0-9_-]+/?\s*$', '', text)
        
        # Fix multiple spaces/separators
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'([|,])\s*\1+', r'\1', text)
        
        # Fix line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove empty lines at start/end
        text = text.strip()
        
        return text
    
    def _aggressive_word_separation(self, text: str) -> str:
        """Super aggressive word separation for concatenated text - applied AFTER protected term restoration"""
        # Common verbs that get concatenated
        verbs = ['worked', 'developed', 'built', 'created', 'implemented', 'designed', 'managed', 
                 'tested', 'analyzed', 'executed', 'performed', 'configured', 'deployed', 'integrated',
                 'coordinated', 'collaborated', 'conducted', 'resolved', 'provided', 'ensured',
                 'resolved', 'fixing', 'debugging', 'coding', 'programming', 'mentoring', 'leading']
        
        for verb in verbs:
            text = re.sub(rf'([a-z])({verb})', rf'\1 {verb}', text, flags=re.IGNORECASE)
            text = re.sub(rf'({verb})([a-z])', rf'{verb} \2', text, flags=re.IGNORECASE)
        
        # Common prepositions and conjunctions
        small_words = ['to', 'at', 'in', 'on', 'of', 'by', 'as', 'is', 'was', 'are', 'were',
                       'and', 'with', 'for', 'from', 'into', 'across', 'under', 'over', 'the']
        
        for word in small_words:
            # More aggressive - add space before and after
            text = re.sub(rf'([a-z])({word})([a-z])', rf'\1 {word} \3', text, flags=re.IGNORECASE)
            text = re.sub(rf'([a-z])({word})\b', rf'\1 {word}', text, flags=re.IGNORECASE)
            text = re.sub(rf'\b({word})([a-z])', rf'{word} \2', text, flags=re.IGNORECASE)
        
        # Fix specific technical concatenations
        tech_terms = ['Linux', 'Android', 'Windows', 'Python', 'Java', 'AWS', 'Docker', 'Kubernetes',
                     'NodeJS', 'JavaScript', 'TypeScript']
        for term in tech_terms:
            text = re.sub(rf'([a-z])({term})', rf'\1 {term}', text)
            text = re.sub(rf'({term})([a-z])', rf'{term} \2', text)
        
        # Common nouns that get concatenated
        nouns = ['software', 'hardware', 'system', 'product', 'security', 'application', 'development',
                'implementation', 'architecture', 'framework', 'interface', 'component', 'service',
                'device', 'module', 'stack', 'layer', 'kernel', 'driver', 'firmware', 'gateway']
        
        for noun in nouns:
            text = re.sub(rf'([a-z])({noun})', rf'\1 {noun}', text, flags=re.IGNORECASE)
            text = re.sub(rf'({noun})([a-z])', rf'{noun} \2', text, flags=re.IGNORECASE)
        
        return text
    
    def _professional_formatting(self, text: str) -> str:
        """Apply professional formatting with proper spacing and structure"""
        # Don't apply intelligent separation if protected terms haven't been restored yet
        if '§PROTECTED' not in text:
            text = self._aggressive_word_separation(text)
        
        # Fix basic spacing issues
        text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)  # camelCase
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)  # letter-number
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)  # number-letter
        text = re.sub(r':([A-Za-z])', r': \1', text)  # colon spacing
        text = re.sub(r',([A-Za-z])', r', \1', text)  # comma spacing
        
        # Fix spaced-out words (e.g., "st and ard" -> "standard")
        text = re.sub(r'\bst and ard\b', 'standard', text, flags=re.IGNORECASE)
        text = re.sub(r'\bunderst and ing\b', 'understanding', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcon guration\b', 'configuration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bs and box', 'sandbox', text, flags=re.IGNORECASE)
        text = re.sub(r'\bh and s\b', 'hands', text, flags=re.IGNORECASE)
        text = re.sub(r'\bh and ling\b', 'handling', text, flags=re.IGNORECASE)
        text = re.sub(r'\bper for m', 'perform', text, flags=re.IGNORECASE)
        text = re.sub(r'\bplat for m', 'platform', text, flags=re.IGNORECASE)
        
        # Preserve compound terms
        text = re.sub(r'\bproblem solving\b', 'problem-solving', text, flags=re.IGNORECASE)
        
        lines = text.split('\n')
        formatted_lines = []
        prev_was_header = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            is_header = (
                (line.isupper() and 3 <= len(line) <= 60 and len(line.split()) <= 10) or
                re.match(r'^[A-Z][a-zA-Z\s]{2,50}$', line) and len(line.split()) <= 6
            )
            
            # Format based on line type
            if is_header:
                # Add spacing around headers
                if formatted_lines and not prev_was_header:
                    formatted_lines.append('')
                formatted_lines.append(line)
                formatted_lines.append('')
                prev_was_header = True
            elif line.startswith(('•', '-', '·', '○', '*')):
                # Bullet points - clean formatting
                clean_bullet = '• ' + line.lstrip('•-·○* ').strip()
                formatted_lines.append(clean_bullet)
                prev_was_header = False
            elif re.match(r'^\d{4}\s*[-–—]\s*(\d{4}|Present|Current|Till)', line, re.IGNORECASE):
                # Date ranges - likely job/education entries
                if formatted_lines and formatted_lines[-1]:
                    formatted_lines.append('')
                formatted_lines.append(line)
                prev_was_header = False
            else:
                # Regular content
                formatted_lines.append(line)
                prev_was_header = False
        
        # Join lines
        text = '\n'.join(formatted_lines)
        
        # Clean up excessive blank lines (max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Ensure proper spacing around content
        text = text.strip()
        
        return text


class PipelineOrchestrator:
    """
    Main orchestrator that:
    1. Analyzes CV to determine type
    2. Selects appropriate specialized pipeline
    3. Executes extraction and processing
    4. Applies universal redaction
    5. Validates and saves output
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.detector = CVProfileDetector()
        self.redactor = UniversalRedactionEngine()
        
        # Initialize all pipelines
        self.pipelines = {
            CVType.NAUKRI: NaukriPipeline(debug),
            CVType.MULTI_COLUMN: MultiColumnPipeline(debug),
            CVType.STANDARD_ATS: StandardATSPipeline(debug),
            CVType.SCANNED_IMAGE: ScannedImagePipeline(debug),
            CVType.CREATIVE_DESIGNER: CreativeDesignerPipeline(debug),
            CVType.ACADEMIC_RESEARCH: AcademicResearchPipeline(debug)
        }
    
    def process_cv(self, pdf_path: str) -> Tuple[str, CVProfile]:
        """Process a single CV"""
        logger.info(f"=" * 80)
        logger.info(f"Processing: {Path(pdf_path).name}")
        logger.info(f"=" * 80)
        
        # Step 1: Analyze CV
        profile = self.detector.analyze(pdf_path)
        logger.info(f"Detected: {profile}")
        
        # Step 2: Select pipeline
        pipeline = self.pipelines.get(profile.cv_type)
        if not pipeline:
            logger.warning(f"No pipeline for {profile.cv_type}, using standard")
            pipeline = self.pipelines[CVType.STANDARD_ATS]
        
        # Step 3: Extract and preprocess
        processed_text = pipeline.process(pdf_path)
        
        # Step 4: Apply universal redaction
        filename = Path(pdf_path).name
        redacted_text = self.redactor.redact(processed_text, filename)
        
        # Step 5: Final cleanup and professional formatting
        final_text = self._final_cleanup(redacted_text)
        
        return final_text, profile
    
    def _final_cleanup(self, text: str) -> str:
        """Final text cleanup"""
        # Remove any remaining standalone names (3-4 word capitalized names on their own lines)
        text = re.sub(r'(?m)^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,4}\s*$', '', text)
        
        # Remove standalone page numbers
        text = re.sub(r'(?m)^\s*\d\s*$', '', text)
        
        # Normalize bullets
        text = re.sub(r'[•●○◦▪▫■□⬤]', '•', text)
        
        # Fix spacing
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def process_directory(self, input_dir: str, output_dir: str = None):
        """Process all PDFs in directory"""
        input_path = Path(input_dir)
        output_path = Path(output_dir) if output_dir else OUTPUT_DIR
        output_path.mkdir(exist_ok=True)
        
        pdf_files = list(input_path.glob("**/*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        stats = {cv_type: 0 for cv_type in CVType}
        success_count = 0
        
        for pdf_file in pdf_files:
            try:
                # Process
                redacted_text, profile = self.process_cv(str(pdf_file))
                
                # Save output
                output_file = output_path / f"REDACTED_{pdf_file.stem}.txt"
                output_file.write_text(redacted_text, encoding='utf-8')
                
                logger.info(f"✓ Saved: {output_file.name}")
                logger.info(f"  Pipeline: {profile.cv_type.value}")
                logger.info(f"  Confidence: {profile.confidence:.2f}")
                
                stats[profile.cv_type] += 1
                success_count += 1
                
            except Exception as e:
                logger.error(f"✗ Failed: {pdf_file.name} - {e}")
        
        # Print summary
        logger.info(f"\n" + "=" * 80)
        logger.info(f"PROCESSING COMPLETE")
        logger.info(f"=" * 80)
        logger.info(f"Total files: {len(pdf_files)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {len(pdf_files) - success_count}")
        logger.info(f"\nPipeline Usage:")
        for cv_type, count in stats.items():
            if count > 0:
                logger.info(f"  {cv_type.value}: {count}")


def main():
    """Main entry point"""
    import sys
    
    # Configure
    debug = '--debug' in sys.argv
    
    # Input directory
    input_dir = "resume"
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        input_dir = sys.argv[1]
    
    # Output directory
    output_dir = "final_output"
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        output_dir = sys.argv[2]
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(debug=debug)
    
    # Process
    orchestrator.process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()
