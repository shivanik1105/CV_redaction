#!/usr/bin/env python3
"""
Hybrid Resume Redaction Pipeline - All-in-One
Consolidates all modules into a single file for easy deployment.
"""

import os
import io
import re
import time
import glob
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF

# ============================================================
# CONFIGURATION
# ============================================================

# Paths
ROOT_DIR = r"c:\Users\shiva\Downloads\samplecvs"
OUTPUT_DIR = os.path.join(ROOT_DIR, "redacted_resumes")
DEBUG_DIR = os.path.join(ROOT_DIR, "debug_output")

# Layout detection thresholds
COLUMN_THRESHOLD = 0.3
HEADER_HEIGHT_RATIO = 0.15
FOOTER_HEIGHT_RATIO = 0.10
MIN_COLUMN_WIDTH = 0.2

# Redaction settings
PRESERVE_SECTIONS = [
    "SKILLS", 
    "EXPERIENCE", 
    "WORK HISTORY", 
    "PROFESSIONAL EXPERIENCE",
    "KEY CONTRIBUTIONS",
    "PROJECTS",
    "TECHNICAL SKILLS",
    "TOOLS"
]

REMOVE_SECTIONS = ["EDUCATION"]
REDACT_ZONES = ["HEADER", "RIGHT_COLUMN", "FOOTER"]

# PII patterns
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
PHONE_PATTERN = r"\b(?:\+?\d[\d\s().-]{7,}\d)\b"
URL_PATTERN = r"\bhttps?://\S+|www\.\S+"
LABEL_PATTERN = r"\b(?:Phone|Mobile|Email|E[-\s]?mail|LinkedIn|Github|GitHub|Portfolio|Website)\s*:\s*\S+"

# Section keywords for detection
SECTION_KEYWORDS = [
    "PROFILE", "SUMMARY", "OBJECTIVE",
    "SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES",
    "WORK HISTORY", "EXPERIENCE", "PROFESSIONAL EXPERIENCE", "EMPLOYMENT",
    "KEY CONTRIBUTIONS", "ACHIEVEMENTS",
    "EDUCATION", "ACADEMIC", "QUALIFICATIONS",
    "PROJECTS", "CERTIFICATIONS", "TOOLS", "OTHER"
]

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)


# ============================================================
# UTILITIES
# ============================================================

def pdf_to_image(pdf_path: str, page_num: int = 0, dpi: int = 200) -> Optional[Image.Image]:
    """Convert PDF page to PIL Image."""
    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            page_num = 0
        page = doc[page_num]
        
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img
    except Exception as e:
        print(f"Error converting PDF to image: {e}")
        return None

def calculate_iou(box1: Tuple[float, float, float, float], 
                  box2: Tuple[float, float, float, float]) -> float:
    """Calculate Intersection over Union of two bounding boxes."""
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2
    
    x_inter_min = max(x1_min, x2_min)
    y_inter_min = max(y1_min, y2_min)
    x_inter_max = min(x1_max, x2_max)
    y_inter_max = min(y1_max, y2_max)
    
    if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
        return 0.0
    
    inter_area = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)
    
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)
    union_area = box1_area + box2_area - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0

def calculate_horizontal_overlap(box1: Tuple[float, float, float, float],
                                 box2: Tuple[float, float, float, float]) -> float:
    """Calculate horizontal overlap ratio between two boxes."""
    x1_min, _, x1_max, _ = box1
    x2_min, _, x2_max, _ = box2
    
    overlap = min(x1_max, x2_max) - max(x1_min, x2_min)
    if overlap <= 0:
        return 0.0
    
    width1 = x1_max - x1_min
    width2 = x2_max - x2_min
    min_width = min(width1, width2)
    
    return overlap / min_width if min_width > 0 else 0.0

def box_contains(outer: Tuple[float, float, float, float],
                 inner: Tuple[float, float, float, float],
                 threshold: float = 0.9) -> bool:
    """Check if outer box contains inner box."""
    x1_min, y1_min, x1_max, y1_max = outer
    x2_min, y2_min, x2_max, y2_max = inner
    
    if x2_min < x1_min or x2_max > x1_max or y2_min < y1_min or y2_max > y1_max:
        return False
    
    inner_area = (x2_max - x2_min) * (y2_max - y2_min)
    contained_area = (min(x2_max, x1_max) - max(x2_min, x1_min)) * \
                     (min(y2_max, y1_max) - max(y2_min, y1_min))
    
    return (contained_area / inner_area) >= threshold if inner_area > 0 else False

def normalize_bbox(bbox: List[float], page_width: float, page_height: float) -> Tuple[float, float, float, float]:
    """Normalize bounding box coordinates to 0-1 range."""
    if len(bbox) == 4:
        x_min, y_min, x_max, y_max = bbox
    elif len(bbox) == 8:  # Polygon format
        xs = bbox[::2]
        ys = bbox[1::2]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
    else:
        return (0, 0, 0, 0)
    
    return (
        x_min / page_width,
        y_min / page_height,
        x_max / page_width,
        y_max / page_height
    )

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple character-level similarity between two texts."""
    if not text1 or not text2:
        return 0.0
    
    t1 = ''.join(text1.split())
    t2 = ''.join(text2.split())
    
    if not t1 or not t2:
        return 0.0
    
    common = sum(1 for c in t1 if c in t2)
    return common / max(len(t1), len(t2))

def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)

def safe_filename(filename: str) -> str:
    """Create safe filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def post_process_text(text: str) -> str:
    """7️⃣ Post-Processing - Format section-wise for human readability."""
    lines = text.split('\n')
    processed = []
    prev_was_empty = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip multiple consecutive blank lines
        if not stripped:
            if not prev_was_empty:
                processed.append('')
                prev_was_empty = True
            continue
        
        prev_was_empty = False
        
        # Detect section headers (ALL CAPS, short lines, or followed by underlines)
        is_section_header = False
        if len(stripped) < 50 and stripped.isupper():
            is_section_header = True
        elif i < len(lines) - 1 and re.match(r'^[-=_]{3,}$', lines[i + 1].strip()):
            is_section_header = True
        
        # Format section headers
        if is_section_header:
            if processed and processed[-1] != '':
                processed.append('')  # Blank line before section
            processed.append(stripped)
            processed.append('=' * len(stripped))  # Underline
            continue
        
        # Skip standalone underlines (already handled with headers)
        if re.match(r'^[-=_]{3,}$', stripped):
            continue
        
        # Format bullet points
        if stripped.startswith('•'):
            processed.append('  • ' + stripped[1:].strip())
        elif stripped.startswith('-') and len(stripped) > 1 and stripped[1] == ' ':
            processed.append('  • ' + stripped[2:].strip())
        elif stripped.startswith('*') and len(stripped) > 1 and stripped[1] == ' ':
            processed.append('  • ' + stripped[2:].strip())
        # Preserve dates and ranges (e.g., "Jan 2020 - Dec 2021")
        elif re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\b', stripped, re.IGNORECASE):
            processed.append('\n' + stripped)
        # Regular content
        else:
            processed.append(stripped)
    
    # Join lines
    result = '\n'.join(processed)
    
    # Clean up excessive blank lines (max 2 consecutive)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # Ensure section headers have proper spacing
    result = re.sub(r'\n(=+)\n{3,}', r'\n\1\n\n', result)
    
    return result.strip()


# ============================================================
# LAYOUT ANALYZER
# ============================================================

@dataclass
class Block:
    """Represents a layout block with text and position."""
    text: str
    bbox: Tuple[float, float, float, float]
    block_type: str
    zone: Optional[str] = None
    
    def __repr__(self):
        return f"Block({self.zone}, {self.block_type}, bbox={self.bbox})"

@dataclass
class LayoutResult:
    """Result of layout analysis."""
    blocks: List[Block]
    page_width: float
    page_height: float
    zones: Dict[str, List[Block]]

class LayoutAnalyzer:
    def __init__(self, use_paddleocr: bool = False):
        self.use_paddleocr = use_paddleocr
        self.ocr_engine = None
        
        if use_paddleocr:
            try:
                from paddleocr import PPStructure
                self.ocr_engine = PPStructure(show_log=False, use_gpu=False)
            except ImportError:
                print("Warning: PaddleOCR not available, using PyMuPDF only")
    
    def analyze_layout(self, pdf_path: str, page_num: int = 0) -> LayoutResult:
        """Analyze layout of a PDF page."""
        if self.use_paddleocr and self.ocr_engine:
            return self._analyze_with_paddleocr(pdf_path, page_num)
        else:
            return self._analyze_with_pymupdf(pdf_path, page_num)
    
    def _analyze_with_pymupdf(self, pdf_path: str, page_num: int = 0) -> LayoutResult:
        """Analyze layout using PyMuPDF."""
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            page_num = 0
        
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        
        blocks = []
        
        text_blocks = page.get_text("dict")["blocks"]
        
        for block in text_blocks:
            if "lines" not in block:
                continue
            
            text_parts = []
            for line in block["lines"]:
                for span in line["spans"]:
                    text_parts.append(span["text"])
            
            text = " ".join(text_parts).strip()
            if not text:
                continue
            
            bbox_raw = block["bbox"]
            bbox = normalize_bbox(list(bbox_raw), page_width, page_height)
            
            avg_size = 0
            if block["lines"]:
                sizes = [span["size"] for line in block["lines"] for span in line["spans"]]
                avg_size = sum(sizes) / len(sizes) if sizes else 0
            
            block_type = "title" if avg_size > 12 else "text"
            
            blocks.append(Block(text, bbox, block_type))
        
        doc.close()
        
        zones = self.classify_zones(blocks, page_width, page_height)
        
        return LayoutResult(blocks, page_width, page_height, zones)
    
    def _analyze_with_paddleocr(self, pdf_path: str, page_num: int = 0) -> LayoutResult:
        """Analyze layout using PaddleOCR PP-Structure."""
        img = pdf_to_image(pdf_path, page_num)
        if img is None:
            return self._analyze_with_pymupdf(pdf_path, page_num)
        
        page_width, page_height = img.size
        
        import numpy as np
        img_array = np.array(img)
        result = self.ocr_engine(img_array)
        
        blocks = []
        for item in result:
            if 'type' not in item or 'bbox' not in item:
                continue
            
            bbox_raw = item['bbox']
            bbox = normalize_bbox(bbox_raw, page_width, page_height)
            
            text = item.get('text', '') or item.get('res', {}).get('text', '')
            block_type = item['type']
            
            if text:
                blocks.append(Block(text, bbox, block_type))
        
        zones = self.classify_zones(blocks, page_width, page_height)
        
        return LayoutResult(blocks, page_width, page_height, zones)
    
    def classify_zones(self, blocks: List[Block], page_width: float, page_height: float) -> Dict[str, List[Block]]:
        """3️⃣ Block Filtering - Classify blocks and filter based on layout rules."""
        zones = {
            'HEADER': [],
            'FOOTER': [],
            'LEFT_COLUMN': [],
            'RIGHT_COLUMN': [],
            'MAIN_BODY': [],
            'FILTERED': []  # Blocks to keep
        }
        
        for block in blocks:
            x_min, y_min, x_max, y_max = block.bbox
            
            # Classify zone
            if y_min < HEADER_HEIGHT_RATIO:
                block.zone = 'HEADER'
                zones['HEADER'].append(block)
            elif y_max > (1 - FOOTER_HEIGHT_RATIO):
                block.zone = 'FOOTER'
                zones['FOOTER'].append(block)
            else:
                block_width = x_max - x_min
                block_center_x = (x_min + x_max) / 2
                
                if block_center_x < 0.4 and block_width < 0.5:
                    block.zone = 'LEFT_COLUMN'
                    zones['LEFT_COLUMN'].append(block)
                elif block_center_x > 0.6 and block_width < 0.5:
                    block.zone = 'RIGHT_COLUMN'
                    zones['RIGHT_COLUMN'].append(block)
                else:
                    block.zone = 'MAIN_BODY'
                    zones['MAIN_BODY'].append(block)
            
            # ✅ Keep blocks that contain experience/skills/projects
            # ❌ Remove headers/footers and right column (contact info)
            if block.zone in ['MAIN_BODY', 'LEFT_COLUMN']:
                zones['FILTERED'].append(block)
        
        return zones
    
    def visualize_layout(self, pdf_path: str, layout: LayoutResult, output_path: Optional[str] = None) -> str:
        """Visualize layout with colored zones."""
        img = pdf_to_image(pdf_path, page_num=0, dpi=150)
        if img is None:
            return ""
        
        draw = ImageDraw.Draw(img, 'RGBA')
        
        colors = {
            'HEADER': (255, 0, 0, 60),
            'FOOTER': (0, 0, 255, 60),
            'LEFT_COLUMN': (0, 255, 0, 60),
            'RIGHT_COLUMN': (255, 165, 0, 60),
            'MAIN_BODY': (128, 0, 128, 60)
        }
        
        for block in layout.blocks:
            x_min, y_min, x_max, y_max = block.bbox
            
            x_min_px = int(x_min * img.width)
            y_min_px = int(y_min * img.height)
            x_max_px = int(x_max * img.width)
            y_max_px = int(y_max * img.height)
            
            color = colors.get(block.zone, (128, 128, 128, 60))
            draw.rectangle([x_min_px, y_min_px, x_max_px, y_max_px], 
                          fill=color, outline=color[:3] + (255,), width=2)
        
        if output_path is None:
            ensure_dir(DEBUG_DIR)
            basename = os.path.basename(pdf_path).replace('.pdf', '_layout.png')
            output_path = os.path.join(DEBUG_DIR, basename)
        
        img.save(output_path)
        return output_path


# ============================================================
# TEXT EXTRACTOR
# ============================================================

@dataclass
class OrderedText:
    """Text extracted in proper reading order."""
    full_text: str
    by_zone: dict
    blocks_ordered: List[Block]

class TextExtractor:
    def __init__(self):
        pass
    
    def extract_ordered_text(self, layout: LayoutResult) -> OrderedText:
        """4️⃣ Text Extraction - Extract only from filtered blocks in reading order."""
        ordered_blocks = self._sort_blocks_reading_order(layout.blocks)
        
        by_zone = {}
        for zone_name, zone_blocks in layout.zones.items():
            if zone_blocks:
                sorted_zone_blocks = self._sort_blocks_in_zone(zone_blocks)
                zone_text = self._merge_blocks_text(sorted_zone_blocks)
                by_zone[zone_name] = zone_text
        
        # Use only FILTERED blocks (excludes headers/footers/right column)
        if 'FILTERED' in layout.zones and layout.zones['FILTERED']:
            filtered_blocks = self._sort_blocks_in_zone(layout.zones['FILTERED'])
            full_text = self._merge_blocks_text(filtered_blocks)
        else:
            # Fallback to main body
            full_text_parts = []
            zone_order = ['MAIN_BODY', 'LEFT_COLUMN']
            
            for zone in zone_order:
                if zone in by_zone and by_zone[zone].strip():
                    full_text_parts.append(by_zone[zone])
            
            full_text = '\n\n'.join(full_text_parts)
        
        return OrderedText(full_text, by_zone, ordered_blocks)
    
    def _sort_blocks_reading_order(self, blocks: List[Block]) -> List[Block]:
        """Sort blocks in natural reading order."""
        zone_priority = {
            'HEADER': 0,
            'MAIN_BODY': 1,
            'LEFT_COLUMN': 2,
            'RIGHT_COLUMN': 3,
            'FOOTER': 4
        }
        
        def sort_key(block: Block):
            zone_pri = zone_priority.get(block.zone, 5)
            y_pos = block.bbox[1]
            x_pos = block.bbox[0]
            return (zone_pri, y_pos, x_pos)
        
        return sorted(blocks, key=sort_key)
    
    def _sort_blocks_in_zone(self, blocks: List[Block]) -> List[Block]:
        """Sort blocks within a zone."""
        def sort_key(block: Block):
            y_pos = block.bbox[1]
            x_pos = block.bbox[0]
            return (y_pos, x_pos)
        
        return sorted(blocks, key=sort_key)
    
    def _merge_blocks_text(self, blocks: List[Block]) -> str:
        """Merge text from multiple blocks with proper formatting."""
        if not blocks:
            return ""
        
        result = []
        prev_block_y = None
        
        for block in blocks:
            text = block.text.strip()
            if not text:
                continue
            
            # Add spacing between blocks that are far apart vertically
            if prev_block_y is not None:
                y_diff = abs(block.bbox[1] - prev_block_y)
                if y_diff > 0.05:  # Significant vertical gap
                    result.append('')  # Add blank line for spacing
            
            result.append(text)
            prev_block_y = block.bbox[3]  # Bottom of current block
        
        return '\n'.join(result)
    
    def validate_completeness(self, original_text: str, extracted_text: str) -> dict:
        """Validate that extracted text is complete."""
        orig_chars = ''.join(original_text.split())
        extr_chars = ''.join(extracted_text.split())
        
        orig_len = len(orig_chars)
        extr_len = len(extr_chars)
        
        common = sum(1 for c in orig_chars if c in extr_chars)
        similarity = common / orig_len if orig_len > 0 else 0.0
        
        missing = orig_len - extr_len
        missing_pct = (missing / orig_len * 100) if orig_len > 0 else 0.0
        
        return {
            'original_chars': orig_len,
            'extracted_chars': extr_len,
            'missing_chars': missing,
            'missing_percent': missing_pct,
            'similarity': similarity,
            'complete': missing_pct < 1.0
        }


# ============================================================
# SECTION PARSER
# ============================================================

class Section:
    def __init__(self, name: str, start_line: int, end_line: int, content: List[str]):
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.content = content
    
    def __repr__(self):
        return f"Section({self.name}, lines {self.start_line}-{self.end_line})"

def detect_sections(lines: List[str]) -> Dict[str, Section]:
    """Detect section headers and their content in resume text."""
    sections = {}
    current_section = None
    current_start = 0
    current_content = []
    
    underline_pattern = re.compile(r'^[-=_]{3,}$')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        is_header = False
        header_name = None
        
        if i < len(lines) - 1:
            next_line = lines[i + 1].strip()
            if stripped.isupper() and len(stripped) > 2 and underline_pattern.match(next_line):
                for keyword in SECTION_KEYWORDS:
                    if keyword in stripped:
                        is_header = True
                        header_name = keyword
                        break
        
        if not is_header:
            for keyword in SECTION_KEYWORDS:
                pattern = rf'\b{re.escape(keyword)}\b'
                if re.search(pattern, stripped, re.IGNORECASE):
                    if len(stripped) < 50 and (stripped.isupper() or stripped.istitle()):
                        is_header = True
                        header_name = keyword
                        break
        
        if is_header and header_name:
            if current_section:
                sections[current_section] = Section(
                    current_section, 
                    current_start, 
                    i - 1, 
                    current_content
                )
            
            current_section = header_name
            current_start = i
            current_content = [line]
        elif current_section:
            current_content.append(line)
        else:
            if 'HEADER' not in sections:
                sections['HEADER'] = Section('HEADER', 0, i, [line])
            else:
                sections['HEADER'].content.append(line)
                sections['HEADER'].end_line = i
    
    if current_section:
        sections[current_section] = Section(
            current_section,
            current_start,
            len(lines) - 1,
            current_content
        )
    
    return sections

def extract_section_content(lines: List[str], section_name: str) -> List[str]:
    """Extract content of a specific section."""
    sections = detect_sections(lines)
    
    for name, section in sections.items():
        if section_name.upper() in name.upper():
            return section.content
    
    return []

def is_preserve_section(section_name: str) -> bool:
    """Check if section should be preserved without redaction."""
    section_upper = section_name.upper()
    return any(preserve in section_upper for preserve in PRESERVE_SECTIONS)

def is_remove_section(section_name: str) -> bool:
    """Check if section should be completely removed."""
    section_upper = section_name.upper()
    return any(remove in section_upper for remove in REMOVE_SECTIONS)

def remove_education_section(lines: List[str]) -> Tuple[List[str], List[str]]:
    """Remove education section and return (remaining_lines, removed_education_content)."""
    sections = detect_sections(lines)
    
    remaining = []
    removed = []
    
    education_lines = set()
    for name, section in sections.items():
        if is_remove_section(name):
            for i in range(section.start_line, section.end_line + 1):
                education_lines.add(i)
            removed.extend(section.content)
    
    for i, line in enumerate(lines):
        if i not in education_lines:
            remaining.append(line)
    
    return remaining, removed

def get_section_type(section_name: str) -> str:
    """Classify section into type: PRESERVE, REMOVE, or REDACT."""
    if is_preserve_section(section_name):
        return "PRESERVE"
    elif is_remove_section(section_name):
        return "REMOVE"
    else:
        return "REDACT"


# ============================================================
# PII REDACTOR
# ============================================================

@dataclass
class RedactionLog:
    """Log entry for a redacted item."""
    category: str
    original_value: str
    line_number: Optional[int] = None
    zone: Optional[str] = None

class PIIRedactor:
    """5️⃣ PII Detection (Local Only) - Remove personal identifiers, preserve skills/experience"""
    def __init__(self, use_presidio: bool = False, use_spacy: bool = False):
        self.use_presidio = use_presidio
        self.use_spacy = use_spacy
        self.redaction_logs: List[RedactionLog] = []
        
        self.presidio_analyzer = None
        self.nlp = None
        
        if use_presidio:
            try:
                from presidio_analyzer import AnalyzerEngine
                self.presidio_analyzer = AnalyzerEngine()
            except ImportError:
                print("Warning: Presidio not available, using regex only")
        
        if use_spacy:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_sm")
            except (ImportError, OSError):
                print("Warning: spaCy not available, using regex only")
    
    def redact_email(self, text: str, track: bool = True) -> str:
        """Redact email addresses."""
        emails = re.findall(EMAIL_PATTERN, text)
        for email in emails:
            text = text.replace(email, "")
            if track:
                self.redaction_logs.append(RedactionLog("EMAIL", email))
        return text
    
    def redact_phone(self, text: str, track: bool = True) -> str:
        """Redact phone numbers."""
        phones = re.findall(PHONE_PATTERN, text)
        for phone in phones:
            digits = re.sub(r'\D', '', phone)
            if len(digits) >= 8:
                text = text.replace(phone, "")
                if track:
                    self.redaction_logs.append(RedactionLog("PHONE", phone))
        return text
    
    def redact_url(self, text: str, track: bool = True) -> str:
        """Redact URLs."""
        urls = re.findall(URL_PATTERN, text)
        for url in urls:
            text = text.replace(url, "")
            if track:
                self.redaction_logs.append(RedactionLog("URL", url))
        return text
    
    def redact_labels(self, text: str, track: bool = True) -> str:
        """Redact label-value pairs like 'Email: xxx' or 'Phone: xxx'."""
        labels = re.findall(LABEL_PATTERN, text, re.IGNORECASE)
        for label in labels:
            text = text.replace(label, "")
            if track:
                self.redaction_logs.append(RedactionLog("LABEL", label))
        return text
    
    def redact_person_names(self, text: str, track: bool = True) -> str:
        """Redact person names using spaCy if available."""
        if not self.nlp:
            return text
        
        doc = self.nlp(text)
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        
        for name in names:
            if len(name.split()) >= 2:
                text = text.replace(name, "")
                if track:
                    self.redaction_logs.append(RedactionLog("PERSON_NAME", name))
        
        return text
    
    def redact_by_zone(self, text: str, zone: str, section_name: Optional[str] = None) -> str:
        """Apply zone-specific redaction rules."""
        if section_name and is_preserve_section(section_name):
            return text
        
        if zone == "HEADER":
            text = self.redact_person_names(text)
            text = self.redact_email(text)
            text = self.redact_phone(text)
            text = self.redact_url(text)
            text = self.redact_labels(text)
        elif zone == "RIGHT_COLUMN":
            text = self.redact_email(text)
            text = self.redact_phone(text)
            text = self.redact_url(text)
            text = self.redact_labels(text)
        elif zone == "FOOTER":
            text = self.redact_email(text)
            text = self.redact_phone(text)
            text = self.redact_url(text)
        else:
            text = self.redact_email(text)
            text = self.redact_phone(text)
            text = self.redact_url(text)
            text = self.redact_labels(text)
        
        return text
    
    def redact_lines(self, lines: List[str], zone: str = "MAIN_BODY", 
                     section_name: Optional[str] = None) -> List[str]:
        """Redact a list of lines with zone awareness."""
        redacted = []
        for line in lines:
            redacted_line = self.redact_by_zone(line, zone, section_name)
            redacted.append(redacted_line)
        return redacted
    
    def get_redaction_summary(self) -> Dict[str, List[str]]:
        """Get summary of all redactions grouped by category."""
        summary = {}
        for log in self.redaction_logs:
            if log.category not in summary:
                summary[log.category] = []
            summary[log.category].append(log.original_value)
        return summary
    
    def clear_logs(self):
        """Clear redaction logs."""
        self.redaction_logs = []


# ============================================================
# OUTPUT FORMATTER
# ============================================================

class OutputFormatter:
    def __init__(self):
        self.underline = "-" * 40
    
    def format_redacted_resume(self, 
                               filename: str,
                               redacted_text: str,
                               removed_education: List[str],
                               redaction_summary: Dict[str, List[str]],
                               completeness_report: dict = None) -> str:
        """Format complete output with redacted resume and logs."""
        
        output = []
        
        output.append(f"{'=' * 60}")
        output.append(f"START: {filename}")
        output.append(f"{'=' * 60}")
        output.append("")
        
        output.append(redacted_text)
        output.append("")
        output.append("")
        
        output.append("REMOVED EDUCATION")
        output.append(self.underline)
        if removed_education:
            output.extend(removed_education)
        else:
            output.append("None")
        output.append("")
        output.append("")
        
        output.append("REDACTED DETAILS")
        output.append(self.underline)
        if redaction_summary:
            for category, values in sorted(redaction_summary.items()):
                for value in values:
                    output.append(f"{category}: {value}")
        else:
            output.append("None")
        output.append("")
        output.append("")
        
        if completeness_report:
            output.append("COMPLETENESS REPORT")
            output.append(self.underline)
            output.append(f"Original characters: {completeness_report.get('original_chars', 0)}")
            output.append(f"Output characters: {completeness_report.get('extracted_chars', 0)}")
            output.append(f"Missing: {completeness_report.get('missing_chars', 0)} ({completeness_report.get('missing_percent', 0):.2f}%)")
            status = "✓ COMPLETE" if completeness_report.get('complete', False) else "⚠ INCOMPLETE"
            output.append(f"Status: {status}")
            output.append("")
            output.append("")
        
        output.append(f"{'=' * 60}")
        output.append(f"END: {filename}")
        output.append(f"{'=' * 60}")
        output.append("")
        output.append("")
        
        return '\n'.join(output)
    
    def format_summary_report(self, total_files: int, total_redactions: int, 
                             processing_time: float) -> str:
        """Format summary report for batch processing."""
        output = []
        output.append("=" * 60)
        output.append("PROCESSING SUMMARY")
        output.append("=" * 60)
        output.append(f"Total files processed: {total_files}")
        output.append(f"Total redactions: {total_redactions}")
        output.append(f"Processing time: {processing_time:.2f} seconds")
        output.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)
        return '\n'.join(output)


# ============================================================
# HYBRID RESUME PIPELINE
# ============================================================

class HybridResumePipeline:
    """
    🔁 Complete Resume Processing Flow:
    1️⃣ Input - Local PDF/DOCX (no cloud, no LLM)
    2️⃣ Layout Understanding - Detect blocks, columns, headings
    3️⃣ Block Filtering - Remove contact info, keep experience/skills
    4️⃣ Text Extraction - Ordered, preserve bullets/dates
    5️⃣ PII Detection - Local spaCy/Presidio (email, phone, name, address)
    6️⃣ Skill Preservation - Never delete skills/experience
    7️⃣ Post-Processing - Clean spacing, fix bullets
    8️⃣ Output - Clean TXT for blind hiring/ATS
    """
    
    def __init__(self, use_paddleocr: bool = False, use_presidio: bool = False, 
                 use_spacy: bool = False, debug: bool = False):
        self.layout_analyzer = LayoutAnalyzer(use_paddleocr=use_paddleocr)
        self.text_extractor = TextExtractor()
        self.pii_redactor = PIIRedactor(use_presidio=use_presidio, use_spacy=use_spacy)
        self.output_formatter = OutputFormatter()
        self.debug = debug
    
    def process_pdf(self, pdf_path: str, save_individual: bool = True) -> Tuple[str, dict]:
        """
        🔁 Complete Processing Flow:
        1️⃣ Input → 2️⃣ Layout → 3️⃣ Filter → 4️⃣ Extract → 5️⃣ Redact → 6️⃣ Preserve → 7️⃣ Clean → 8️⃣ Output
        """
        print(f"1️⃣ Input: {os.path.basename(pdf_path)}")
        
        # 2️⃣ Layout Understanding
        print("  2️⃣ Layout Understanding...")
        layout = self.layout_analyzer.analyze_layout(pdf_path, page_num=0)
        
        if self.debug:
            self.layout_analyzer.visualize_layout(pdf_path, layout)
        
        # 3️⃣ Block Filtering (already done in classify_zones)
        # 4️⃣ Text Extraction
        print("  4️⃣ Text Extraction...")
        ordered_text = self.text_extractor.extract_ordered_text(layout)
        
        original_text = self._extract_raw_text(pdf_path)
        
        # 5️⃣ PII Detection + 6️⃣ Skill Preservation
        print("  5️⃣ PII Detection (preserving skills/experience)...")
        redacted_output = self._redact_with_zones(ordered_text, layout)
        
        lines = redacted_output.split('\n')
        remaining_lines, removed_education = remove_education_section(lines)
        redacted_text = '\n'.join(remaining_lines)
        
        # 7️⃣ Post-Processing
        print("  7️⃣ Post-Processing (formatting sections)...")
        redacted_text = post_process_text(redacted_text)
        
        # Add professional header
        final_output = f"REDACTED RESUME\n{'=' * 50}\n\n{redacted_text}"
        
        redaction_summary = self.pii_redactor.get_redaction_summary()
        
        # 8️⃣ Output
        if save_individual:
            filename = os.path.basename(pdf_path).replace('.pdf', '_redacted.txt')
            output_path = os.path.join(OUTPUT_DIR, filename)
            ensure_dir(OUTPUT_DIR)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_output)
            print(f"  8️⃣ Output saved: {filename}")
        
        completeness = self.text_extractor.validate_completeness(original_text, ordered_text.full_text)
        
        filename = os.path.basename(pdf_path)
        formatted_output = self.output_formatter.format_redacted_resume(
            filename=filename,
            redacted_text=final_output,
            removed_education=removed_education,
            redaction_summary=redaction_summary,
            completeness_report=completeness
        )
        
        self.pii_redactor.clear_logs()
        
        metadata = {
            'filename': filename,
            'num_blocks': len(layout.blocks),
            'num_redactions': sum(len(v) for v in redaction_summary.values()),
            'completeness': completeness
        }
        
        return formatted_output, metadata
    
    def _extract_raw_text(self, pdf_path: str) -> str:
        """Extract raw text for completeness comparison."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Warning: Could not extract raw text: {e}")
            return ""
    
    def _redact_with_zones(self, ordered_text: OrderedText, layout: LayoutResult) -> str:
        """Apply zone-aware and section-aware redaction."""
        lines = ordered_text.full_text.split('\n')
        sections = detect_sections(lines)
        
        line_to_section = {}
        for section_name, section in sections.items():
            for i in range(section.start_line, section.end_line + 1):
                if i < len(lines):
                    line_to_section[i] = section_name
        
        redacted_lines = []
        for i, line in enumerate(lines):
            section_name = line_to_section.get(i, None)
            zone = "MAIN_BODY"
            
            if section_name and is_preserve_section(section_name):
                redacted_lines.append(line)
            else:
                redacted_line = self.pii_redactor.redact_by_zone(line, zone, section_name)
                redacted_lines.append(redacted_line)
        
        return '\n'.join(redacted_lines)
    
    def process_batch(self, pdf_paths: List[str], output_file: str = None) -> str:
        """Process multiple PDFs and combine into single output."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(OUTPUT_DIR, f"HYBRID_REDACTED_{timestamp}.txt")
        
        ensure_dir(os.path.dirname(output_file))
        
        start_time = time.time()
        all_outputs = []
        total_redactions = 0
        
        for pdf_path in pdf_paths:
            try:
                output, metadata = self.process_pdf(pdf_path, save_individual=True)
                all_outputs.append(output)
                total_redactions += metadata['num_redactions']
            except Exception as e:
                print(f"Error processing {pdf_path}: {e}")
                continue
        
        processing_time = time.time() - start_time
        
        summary = self.output_formatter.format_summary_report(
            total_files=len(pdf_paths),
            total_redactions=total_redactions,
            processing_time=processing_time
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
            f.write('\n\n')
            f.write('\n'.join(all_outputs))
        
        print(f"\n✓ Complete! Output written to: {output_file}")
        print(f"  Processed {len(pdf_paths)} files in {processing_time:.2f}s")
        print(f"  Total redactions: {total_redactions}")
        
        return output_file


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """🔁 Resume Redaction Pipeline - Local, Privacy-Focused Processing"""
    import sys
    
    use_paddleocr = '--paddleocr' in sys.argv
    use_presidio = '--presidio' in sys.argv
    use_spacy = '--spacy' in sys.argv
    debug = '--debug' in sys.argv
    
    pdf_pattern = os.path.join(ROOT_DIR, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    
    if not pdf_files:
        print("No PDF files found in:", ROOT_DIR)
        return
    
    print("="*60)
    print("🔁 RESUME REDACTION PIPELINE")
    print("="*60)
    print(f"📁 Found {len(pdf_files)} PDF files")
    print(f"🔒 Local Processing (no cloud, no LLM, no data sharing)")
    print(f"\nConfiguration:")
    print(f"  - Layout Detection (PaddleOCR): {use_paddleocr}")
    print(f"  - Advanced PII (Presidio): {use_presidio}")
    print(f"  - Name Detection (spaCy): {use_spacy}")
    print(f"  - Debug Visualization: {debug}")
    print("="*60)
    print()
    
    pipeline = HybridResumePipeline(
        use_paddleocr=use_paddleocr,
        use_presidio=use_presidio,
        use_spacy=use_spacy,
        debug=debug
    )
    
    pipeline.process_batch(pdf_files)

if __name__ == "__main__":
    main()
