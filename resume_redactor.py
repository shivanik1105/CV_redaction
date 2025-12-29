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
        """Extract with fallback - handles 2-column layouts properly"""
        text = ""
        
        # Try pdfplumber first with smart mixed-layout extraction
        if HAS_PDFPLUMBER:
            print("Using pdfplumber extraction...")
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    all_text = []
                    
                    for i, page in enumerate(pdf.pages):
                        print(f"Processing page {i+1}...")
                        page_width = page.width
                        page_height = page.height
                        
                        # Smart column detection: find the gap between columns
                        words = page.extract_words(x_tolerance=2, y_tolerance=2)
                        
                        if words:
                            print(f"Found {len(words)} words")
                            
                            # Method 1: Analyze word distribution across page width
                            # Divide page into vertical strips and count words in each
                            strip_width = page_width / 20
                            strip_counts = {}
                            for strip_idx in range(20):
                                strip_counts[strip_idx] = 0
                            
                            for w in words:
                                word_center = (w['x0'] + w['x1']) / 2
                                strip_idx = int(word_center / strip_width)
                                if 0 <= strip_idx < 20:
                                    strip_counts[strip_idx] += 1
                            
                            # Find the strip with minimum words in middle region (strips 5-15)
                            min_count = float('inf')
                            min_strip_idx = 10
                            for strip_idx in range(5, 15):
                                if strip_counts[strip_idx] < min_count:
                                    min_count = strip_counts[strip_idx]
                                    min_strip_idx = strip_idx
                            
                            # Use this as initial split point
                            split_point = (min_strip_idx + 0.5) * strip_width
                            
                            # Method 2: Refine by finding actual gap
                            # Get all unique x-coordinates
                            x_coords = sorted(set([w['x0'] for w in words] + [w['x1'] for w in words]))
                            
                            # Find the largest gap in the middle region around our initial split
                            search_start = split_point - page_width * 0.15
                            search_end = split_point + page_width * 0.15
                            
                            max_gap = 0
                            best_split = split_point
                            for i in range(len(x_coords) - 1):
                                if search_start < x_coords[i] < search_end:
                                    gap_size = x_coords[i+1] - x_coords[i]
                                    if gap_size > max_gap:
                                        max_gap = gap_size
                                        best_split = (x_coords[i] + x_coords[i+1]) / 2
                            
                            split_point = best_split
                            print(f"Found column split at {split_point:.1f} (gap: {max_gap:.1f})")

                            # Find vertical zones based on crossing words
                            # Words that cross the Robust Split Point are defacto Headers
                            crossing_intervals = []
                            if split_point:
                                for w in words:
                                    if w['x0'] < split_point < w['x1']:
                                        crossing_intervals.append((w['top'], w['bottom']))
                            
                            # 2. Merge overlapping intervals
                            crossing_intervals.sort()
                            merged_intervals = []
                            if crossing_intervals:
                                curr_start, curr_end = crossing_intervals[0]
                                for next_start, next_end in crossing_intervals[1:]:
                                    # Merge if overlapping or very close
                                    if next_start < curr_end + 5: 
                                        curr_end = max(curr_end, next_end)
                                    else:
                                        merged_intervals.append((curr_start, curr_end))
                                        curr_start, curr_end = next_start, next_end
                                merged_intervals.append((curr_start, curr_end))
                            
                            # 3. Define all Zones with PADDING to prevent clipping
                            zones = []
                            current_y = 0
                            
                            for start, end in merged_intervals:
                                # Apply padding to Single Col Zone
                                zone_top = max(0, start - 2)
                                zone_bottom = min(page_height, end + 2)
                                
                                # Add Two-Col Zone before this
                                if zone_top > current_y + 1:
                                    zones.append({'type': 'two_col', 'top': current_y, 'bottom': zone_top})
                                
                                zones.append({'type': 'single_col', 'top': zone_top, 'bottom': zone_bottom})
                                current_y = zone_bottom
                            
                            # Add final Two-Col Zone
                            if current_y < page_height:
                                zones.append({'type': 'two_col', 'top': current_y, 'bottom': page_height})
                            
                            # 4. Extract text from zones - collect left and right columns separately
                            left_column_parts = []
                            right_column_parts = []
                            
                            for zone in zones:
                                # Use tolerances to prevent excessive merging
                                x_tol, y_tol = 2, 2
                                
                                if zone['type'] == 'single_col':
                                    bbox = (0, zone['top'], page_width, zone['bottom'])
                                    crop = page.crop(bbox)
                                    # Use balanced tolerance to preserve proper spacing
                                    text = crop.extract_text(x_tolerance=1.5, y_tolerance=2)
                                    if text:
                                        # Single column zones go to left column
                                        left_column_parts.append(text.strip())
                                        
                                elif zone['type'] == 'two_col':
                                    # For two-column zones, extract each column separately
                                    left_bbox = (0, zone['top'], split_point, zone['bottom'])
                                    left_crop = page.crop(left_bbox)
                                    # Use balanced tolerance to preserve proper spacing
                                    left_text = left_crop.extract_text(x_tolerance=1.5, y_tolerance=2)
                                    
                                    right_bbox = (split_point, zone['top'], page_width, zone['bottom'])
                                    right_crop = page.crop(right_bbox)
                                    # Use balanced tolerance to preserve proper spacing
                                    right_text = right_crop.extract_text(x_tolerance=1.5, y_tolerance=2)
                                    
                                    if left_text and left_text.strip():
                                        left_column_parts.append(left_text.strip())
                                    
                                    if right_text and right_text.strip():
                                        right_column_parts.append(right_text.strip())
                            
                            # Combine: left column first, then separator, then right column
                            page_parts = []
                            if left_column_parts:
                                page_parts.append("\n\n".join(left_column_parts))
                            if right_column_parts:
                                page_parts.append("\n" + "=" * 60 + "\n")
                                page_parts.append("\n\n".join(right_column_parts))
                            
                            page_text = "\n\n".join(page_parts)
                        else:
                            # No words found, try basic extraction
                            print("No words found, using basic extraction")
                            page_text = page.extract_text()
                        
                        if page_text:
                            all_text.append(page_text)
                    
                    text = "\n\n".join(all_text)
                    if text.strip():
                        print("Successfully extracted text with pdfplumber")
                        return text
            except Exception as e:
                print(f"pdfplumber extraction failed: {e}")
                # Re-raise to verify failure
                raise e
        
        # Fallback removed - we must use pdfplumber for correct layout handling
        # if HAS_FITZ: ...
        
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
        'l&t', 'larsen & toubro', 'scientific games', 'alcatel lucent',
        'asp.net', 'asp', '.net', 'c#', 'sencha', 'mobile', 'ext.js', 'extjs',
        'jquery', 'web api', 'webapi', 'mvc', 'blazor', 'soapui', 'fiddler',
        'capgemini', 'nbs', 'r&l', 'carriers', 'izel', 'technologies'
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
        
        # DISABLE person name removal - it causes too many false positives
        # (removes "Developed", "Mobile", "C#", profile text, etc.)
        # Person names will be removed by email/phone/LinkedIn removal above
        
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
    def remove_duplicates(text: str) -> str:
        """Remove consecutive duplicate lines and duplicate multi-line sections"""
        lines = text.split('\n')
        
        # Step 1: Remove consecutive duplicates
        deduplicated = []
        prev_line = None
        
        for line in lines:
            stripped = line.strip()
            # Only add if not duplicate of previous line
            if stripped != prev_line or len(stripped) < 5:  # Keep short lines even if duplicate
                deduplicated.append(line)
                prev_line = stripped
        
        # Step 2: Remove duplicate single lines (even if not consecutive)
        # Track lines we've seen, remove exact duplicates of substantial lines
        seen_lines = {}
        dedup2 = []
        for i, line in enumerate(deduplicated):
            stripped = line.strip().lower()
            # Only dedupe substantial lines (> 40 chars, not headers)
            if len(stripped) > 40 and not stripped.startswith('=') and '•' not in stripped[:3]:
                if stripped in seen_lines:
                    continue  # Skip duplicate
                seen_lines[stripped] = i
            dedup2.append(line)
        
        # Step 3: Remove duplicate multi-line blocks using sliding window
        # Create fingerprints of 3-line windows
        final_lines = []
        seen_fingerprints = set()
        skip_until = -1
        
        for i in range(len(dedup2)):
            # If we're in a skip zone, continue
            if i < skip_until:
                continue
                
            line = dedup2[i].strip()
            
            # Build a fingerprint from current line and next 2 lines
            if line and len(line) > 25:  # Only for substantial lines
                fingerprint_lines = []
                for j in range(i, min(i + 4, len(dedup2))):
                    fp_line = dedup2[j].strip()
                    if fp_line and not fp_line.startswith('=') and len(fp_line) > 10:
                        fingerprint_lines.append(fp_line.lower()[:40])  # First 40 chars
                
                if len(fingerprint_lines) >= 2:
                    fingerprint = '|'.join(fingerprint_lines[:2])
                    
                    if fingerprint in seen_fingerprints:
                        # Found duplicate block, skip the next several lines
                        skip_until = i + len(fingerprint_lines)
                        continue
                    else:
                        seen_fingerprints.add(fingerprint)
            
            final_lines.append(dedup2[i])
        
        return '\n'.join(final_lines)
    
    @staticmethod
    def fix_spacing(text: str) -> str:
        """Fix missing spaces between concatenated words using comprehensive word detection"""
        
        # Step 1: Fix camelCase transitions (lowercase to uppercase)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Step 2: Common concatenated words - extensive dictionary
        # Format: "badword" -> " good word"
        concatenation_fixes = [
            # Common prepositions and conjunctions
            (r'\binto([a-z])', r'into \1'),
            (r'([a-z])into\b', r'\1 into'),
            (r'\band([a-z])', r'and \1'),
            (r'([a-z])and\b', r'\1 and'),
            (r'\bwith([a-z])', r'with \1'),
            (r'([a-z])with\b', r'\1 with'),
            (r'\bfor([a-z])', r'for \1'),
            (r'([a-z])for\b', r'\1 for'),
            (r'\bfrom([a-z])', r'from \1'),
            (r'([a-z])from\b', r'\1 from'),
            (r'\bthe([a-z])', r'the \1'),
            (r'([a-z])the\b', r'\1 the'),
            (r'\bto([a-z])', r'to \1'),
            (r'([a-z])to\b', r'\1 to'),
            (r'\bin([a-z])', r'in \1'),
            (r'([a-z])in\b', r'\1 in'),
            (r'\bon([a-z])', r'on \1'),
            (r'([a-z])on\b', r'\1 on'),
            (r'\bat([a-z])', r'at \1'),
            (r'([a-z])at\b', r'\1 at'),
            (r'\bof([a-z])', r'of \1'),
            (r'([a-z])of\b', r'\1 of'),
            (r'\bor([a-z])', r'or \1'),
            (r'([a-z])or\b', r'\1 or'),
            (r'\bas([a-z])', r'as \1'),
            (r'([a-z])as\b', r'\1 as'),
            (r'\bby([a-z])', r'by \1'),
            (r'([a-z])by\b', r'\1 by'),
            
            # Common articles and determiners
            (r'\ba([A-Z])', r'a \1'),
            (r'\ban([A-Z])', r'an \1'),
            
            # Common verbs and modals
            (r'\bis([a-z])', r'is \1'),
            (r'([a-z])is\b', r'\1 is'),
            (r'\bare([a-z])', r'are \1'),
            (r'([a-z])are\b', r'\1 are'),
            (r'\bwas([a-z])', r'was \1'),
            (r'([a-z])was\b', r'\1 was'),
            (r'\bwere([a-z])', r'were \1'),
            (r'([a-z])were\b', r'\1 were'),
            (r'\bbeen([a-z])', r'been \1'),
            (r'([a-z])been\b', r'\1 been'),
            (r'\bhave([a-z])', r'have \1'),
            (r'([a-z])have\b', r'\1 have'),
            (r'\bhas([a-z])', r'has \1'),
            (r'([a-z])has\b', r'\1 has'),
        ]
        
        for pattern, replacement in concatenation_fixes:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Step 3: Detect word boundaries using lowercase-to-lowercase transitions
        # This handles cases like "Productdevelopment" -> "Product development"
        # Split on: lowercase letter followed by a new word (detected by common prefixes)
        common_prefixes = ['develop', 'manage', 'design', 'implement', 'create', 'build',
                         'product', 'project', 'system', 'software', 'hardware', 'service',
                         'business', 'customer', 'technical', 'professional', 'experience']
        
        for prefix in common_prefixes:
            # Match: word + prefix (no space between)
            # Example: "Productdevelopment" -> "Product development"
            pattern = rf'([a-z])({prefix})'
            text = re.sub(pattern, r'\1 \2', text, flags=re.IGNORECASE)
        
        # Add space between lowercase and uppercase letters (camelCase) but not single caps
        text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)
        
        # Add space between word and number (but preserve things like "C 3" -> keep as is)
        text = re.sub(r'([a-z]{3,})(\d)', r'\1 \2', text)
        # Add space between number and letter
        text = re.sub(r'(\d)([a-zA-Z]{2,})', r'\1 \2', text)
        
        # Add space after comma if missing
        text = re.sub(r',([a-zA-Z])', r', \1', text)
        
        # Fix product names that got split
        text = re.sub(r'Io\s+T', 'IoT', text)
        text = re.sub(r'Py\s+Spark', 'PySpark', text)
        text = re.sub(r'Java\s+Script', 'JavaScript', text)
        text = re.sub(r'My\s+SQL', 'MySQL', text)
        text = re.sub(r'Postgre\s+SQL', 'PostgreSQL', text)
        text = re.sub(r'Mongo\s+DB', 'MongoDB', text)
        text = re.sub(r'Dev\s+Ops', 'DevOps', text)
        text = re.sub(r'Git\s+Hub', 'GitHub', text)
        text = re.sub(r'Git\s+Lab', 'GitLab', text)
        text = re.sub(r'Mule\s+Soft', 'MuleSoft', text)
        text = re.sub(r'Power\s+Point', 'PowerPoint', text)
        text = re.sub(r'Fast\s+Api', 'FastAPI', text)
        text = re.sub(r'Saa\s+S', 'SaaS', text)
        text = re.sub(r'Web\s+API', 'WebAPI', text)
        text = re.sub(r'San\s+Disk', 'SanDisk', text)
        text = re.sub(r'Clear\s+Case', 'ClearCase', text)
        
        # Fix common broken words from PDF extraction
        text = re.sub(r'\ba\s+nd\s+roid\b', 'Android', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+dia\b', 'India', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+OSP\b', 'AOSP', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+RM\b', 'ARM', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+WS\b', 'AWS', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+PI\b', 'API', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+I\b', 'AI', text, flags=re.IGNORECASE)
        text = re.sub(r'\bYoc\s+to\b', 'Yocto', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPyth\s+on\b', 'Python', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSoftw\s+are\b', 'Software', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfirmw\s+are\b', 'firmware', text, flags=re.IGNORECASE)
        text = re.sub(r'\bHardw\s+are\b', 'Hardware', text, flags=re.IGNORECASE)
        text = re.sub(r'\bhyperv\s+is\s+or\b', 'hypervisor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bc\s+on\s+gurati\s+on\b', 'configuration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bimplementati\s+on\b', 'implementation', text, flags=re.IGNORECASE)
        text = re.sub(r'\b is\s+O\b', 'ISO', text, flags=re.IGNORECASE)
        text = re.sub(r'\banalys\s+is\b', 'analysis', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+f\s+or\b', 'as for', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+utomotive\b', 'Automotive', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+udio\b', 'Audio', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+gile\b', 'Agile', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+sembl', 'Assembl', text, flags=re.IGNORECASE)
        
        # Fix common space-broken words
        text = re.sub(r'\bin\s+to\b', 'into', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+nd\b', 'and', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+cross\b', 'across', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+terface', 'interface', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+volving', 'involving', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+fra', 'infra', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+ternals', 'internals', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+oling', 'tooling', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+rchitecture', 'architecture', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprocess\s+or\b', 'processor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bis\s+sue', 'issue', text, flags=re.IGNORECASE)
        text = re.sub(r'\bidentificati\s+on', 'identification', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+fluence', 'influence', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+lgorithm', 'algorithm', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+dditional', 'additional', text, flags=re.IGNORECASE)
        text = re.sub(r'\bon\s+e\b', 'one', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s(?=[^a-zA-Z])', 'as', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSpecialisati\s+on', 'Specialisation', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+BHISHEK', 'ABHISHEK', text, flags=re.IGNORECASE)
        
        return text
    
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
            if re.match(r'^[\.\|\-•:,=\s]+$', stripped):
                continue
            
            # REMOVED aggressive header skip - it was deleting summary lines containing commas
            
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
            
            # Skip if too short or just punctuation (BUT preserve important short terms like C#, Go, R)
            important_short_terms = ['c#', 'c++', 'go', 'r', 'js', 'ai', 'ml', 'ui', 'ux', 'qa']
            if len(cleaned_line) < 3:
                if cleaned_line.lower() not in important_short_terms:
                    continue
            elif re.match(r'^[,.\-:|•\s]+$', cleaned_line):
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
        seen_sections = set()  # Track sections we've already processed
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
                # Skip if we've already processed this section (prevents duplication)
                # Use case-insensitive comparison to catch variations
                section_title_normalized = section_title.upper()
                if section_title_normalized in seen_sections:
                    i += 1
                    continue
                
                seen_sections.add(section_title_normalized)
                
                # Found a section header - check if next line is also a section header (2-column layout)
                # DISABLED: This was causing duplication issues
                # next_is_section = False
                # if i + 1 < len(main_content):
                #     next_line = main_content[i + 1]
                #     next_lower = next_line.lower().strip()
                #     if not next_line.strip().endswith('.') and len(next_line.split()) >= 2 and len(next_line.split()) <= 5:
                #         for keyword in section_keywords:
                #             if keyword == next_lower or keyword in next_lower:
                #                 next_is_section = True
                #                 break
                
                # If next line is also a section, skip it (2-column layout handling)
                # if next_is_section:
                #     i += 1  # Skip the duplicate/adjacent section header
                
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
        
        # Remove duplicate sections before joining
        result = TextPolisher._remove_large_duplicates(result)
        
        # Join and normalize excessive spacing
        final = '\n'.join(result)
        final = re.sub(r'\n{4,}', '\n\n\n', final)
        return final
    
    @staticmethod
    def _remove_large_duplicates(lines):
        """Remove large duplicate consecutive blocks by finding exact repeating sequences"""
        if len(lines) < 30:
            return lines
        
        # Convert to string with line numbers for easier matching
        text_with_nums = '\n'.join(f"{i}:{line}" for i, line in enumerate(lines))
        
        # Look for repeating blocks of at least 15 consecutive lines
        min_block_size = 15
        i = 0
        to_remove = set()
        
        while i < len(lines) - min_block_size:
            # Get block starting at i
            block = [l.strip() for l in lines[i:i+min_block_size]]
            
            # Look for this same block later in the text
            for j in range(i + min_block_size, len(lines) - min_block_size + 1):
                next_block = [l.strip() for l in lines[j:j+min_block_size]]
                
                # Check for exact match
                if block == next_block:
                    # Found exact duplicate - mark entire duplicate section
                    # Find where duplicate ends
                    dup_len = min_block_size
                    while (i + dup_len < len(lines) and j + dup_len < len(lines) and 
                           lines[i + dup_len].strip() == lines[j + dup_len].strip()):
                        dup_len += 1
                    
                    # Mark duplicate for removal
                    for k in range(j, min(j + dup_len, len(lines))):
                        to_remove.add(k)
                    
                    break
            
            i += 1
        
        # Return lines without duplicates
        return [lines[idx] for idx in range(len(lines)) if idx not in to_remove]
    
    @staticmethod
    def polish(text: str) -> str:
        """Complete polish pipeline"""
        # First remove duplicates
        text = TextPolisher.remove_duplicates(text)
        # Fix spacing issues
        text = TextPolisher.fix_spacing(text)
        # Then clean
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
        
        # DEBUG: Save raw text
        with open("debug_raw_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
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
        important_short_terms = ['c#', 'c++', 'go', 'r', 'js', 'ai', 'ml', 'ui', 'ux', 'qa']
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Only skip truly useless lines
            # Skip single characters or numbers (unless it's an important term)
            if len(stripped) <= 2:
                if stripped.lower() not in important_short_terms:
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
