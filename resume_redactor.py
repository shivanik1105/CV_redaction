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


class ResumeClassifier:
    """Classify resume type to route to appropriate pipeline"""
    
    @staticmethod
    def classify(pdf_path: str) -> str:
        """Detect resume category: naukri, multi_column, standard, simple"""
        filename = os.path.basename(pdf_path).lower()
        
        # Check filename patterns
        if 'naukri' in filename:
            return 'naukri'
        
        # Analyze PDF structure
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    if pdf.pages:
                        page = pdf.pages[0]
                        words = page.extract_words(x_tolerance=2, y_tolerance=2)
                        
                        if not words:
                            return 'simple'
                        
                        # Detect multi-column by checking word distribution
                        page_width = page.width
                        left_words = sum(1 for w in words if w['x0'] < page_width * 0.4)
                        right_words = sum(1 for w in words if w['x0'] > page_width * 0.6)
                        
                        if left_words > 10 and right_words > 10:
                            return 'multi_column'
                        
                        return 'standard'
            except:
                pass
        
        return 'standard'


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
    
    @staticmethod
    def extract_naukri(pdf_path: str) -> str:
        """Extract Naukri resumes - typically 2-column with specific formatting"""
        return TextExtractor.extract(pdf_path)  # Use standard multi-column logic
    
    @staticmethod
    def extract_standard(pdf_path: str) -> str:
        """Extract standard single-column resumes"""
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    all_text = []
                    for page in pdf.pages:
                        text = page.extract_text(x_tolerance=1.5, y_tolerance=2)
                        if text:
                            all_text.append(text)
                    return "\n\n".join(all_text)
            except:
                pass
        return ""
    
    @staticmethod
    def extract_simple(pdf_path: str) -> str:
        """Extract simple/basic resumes with minimal formatting"""
        text = ""
        if HAS_PDFPLUMBER:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text = "\n\n".join(page.extract_text() or "" for page in pdf.pages)
            except:
                pass
        if not text and HAS_FITZ:
            try:
                doc = fitz.open(pdf_path)
                text = "\n\n".join(page.get_text() for page in doc)
                doc.close()
            except:
                pass
        return text

class WordHealer:
    """Fix fragmented text like 'a b c' -> 'abc' and common broken patterns"""
    
    @staticmethod
    def heal(text: str) -> str:
        """Rejoin fragmented single-character sequences that form valid words or patterns"""
        import re
        
        # Pattern 1: Single chars separated by spaces (e.g., 'a b h i n a v' -> 'abhinav')
        # Look for sequences of 3+ single letters with spaces
        def rejoin_fragments(match):
            fragment = match.group(0)
            # Remove spaces to get the potential word
            joined = fragment.replace(' ', '')
            # If it's 4+ chars and looks like a word (not random chars), join it
            if len(joined) >= 4 and joined.isalpha():
                # Check if it looks like a name or common word pattern
                # Names often have capital first letter when fragmented
                if fragment[0].isupper() or joined.lower() in [
                    'address', 'email', 'phone', 'linkedin', 'github',
                    'contact', 'mobile', 'abhinav', 'rohini', 'prashant'
                ]:
                    return joined
            return fragment
        
        # Match: single letter, space, single letter, space, ... (3+ times)
        text = re.sub(r'\b([a-zA-Z])\s+([a-zA-Z])\s+([a-zA-Z])(?:\s+[a-zA-Z])*\b', rejoin_fragments, text)
        
        # Pattern 2: Specific known fragmentation patterns
        fragments = {
            'a bhinav': 'Abhinav',
            'a bhishek': 'Abhishek',
            'p rashant': 'Prashant',
            'r ohini': 'Rohini',
            'p mayur': 'Mayur',
            'a mit': 'Amit',
            'rohinisp': '',  # Remove username fragments
            'pmayur': '',
            'ediwa': '',  # LinkedIn username fragments
        }
        
        for fragmented, fixed in fragments.items():
            text = text.replace(fragmented, fixed)
        
        return text


class DeDuplicator:
    """Remove duplicate or near-duplicate text blocks"""
    
    @staticmethod
    def remove_duplicates(text: str, similarity_threshold: float = 0.85) -> str:
        """Remove duplicate blocks of text that appear consecutively"""
        lines = text.split('\n')
        
        # Group lines into blocks (paragraphs)
        blocks = []
        current_block = []
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                current_block.append(line)
            elif current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
        if current_block:
            blocks.append('\n'.join(current_block))
        
        # Remove near-duplicate consecutive blocks
        result_blocks = []
        for i, block in enumerate(blocks):
            if i == 0:
                result_blocks.append(block)
                continue
            
            # Compare with previous block
            prev_block = result_blocks[-1]
            similarity = DeDuplicator._calculate_similarity(block, prev_block)
            
            if similarity < similarity_threshold:
                result_blocks.append(block)
            # else: skip duplicate
        
        return '\n\n'.join(result_blocks)
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """Calculate text similarity (simple word overlap)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


class LayoutAwareRedactor:
    """Redact content based on physical location in PDF (sidebars, headers)"""
    
    @staticmethod
    def extract_with_zones(pdf_path: str) -> tuple:
        """Extract text with zone information (main content vs sidebars)"""
        if not HAS_PDFPLUMBER:
            return "", []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                main_content = []
                redacted_zones = []
                
                for page in pdf.pages:
                    page_width = page.width
                    words = page.extract_words(x_tolerance=2, y_tolerance=2)
                    
                    if not words:
                        continue
                    
                    # Classify words into zones
                    for word in words:
                        x_center = (word['x0'] + word['x1']) / 2
                        x_percent = x_center / page_width
                        
                        # Contact sidebar: left 30% or right 30%
                        if x_percent < 0.30 or x_percent > 0.70:
                            # This is sidebar content - likely contact info
                            word_text = word['text'].strip()
                            if word_text and len(word_text) > 2:
                                # Check if it looks like PII (usernames, handles)
                                if any(c.isdigit() for c in word_text) or '@' in word_text or word_text.islower():
                                    redacted_zones.append(word_text)
                        else:
                            # Main content area
                            main_content.append(word['text'])
                
                return ' '.join(main_content), redacted_zones
        except:
            return "", []
    
    @staticmethod
    def redact_zones(text: str, redacted_items: list) -> str:
        """Remove redacted zone content from text"""
        for item in redacted_items:
            text = text.replace(item, '')
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
    
    def redact(self, text: str, debug_dir=None) -> str:
        """Remove ONLY safe PII: email, phone, URLs, DOB. Keep everything else."""
        # DEBUG: Save checkpoint 1 - before redaction
        if debug_dir:
            Path(debug_dir).mkdir(exist_ok=True)
            Path(debug_dir, '01_before_redaction.txt').write_text(text, encoding='utf-8')
        
        # Email - REMOVE completely, no placeholder
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        self.stats['pii_redacted'] += len(emails)
        
        # Phone numbers - REMOVE completely, no placeholder
        text = re.sub(r'[\+]?[\d]{1,3}[-\.\s]?[\(]?[\d]{1,4}[\)]?[-\.\s]?[\d]{1,4}[-\.\s]?[\d]{5,9}', '', text)
        text = re.sub(r'\b\d{10,}\b', '', text)
        
        # URLs - REMOVE completely, no placeholder
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # LinkedIn - REMOVE completely
        text = re.sub(r'LinkedIn[:\s]+[a-zA-Z0-9-_/]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'linkedin\.com/in/[a-zA-Z0-9-]+', '', text)
        text = re.sub(r'\[LINKED\s*in\]', '', text, flags=re.IGNORECASE)
        
        # Contact labels - remove label only, keep rest of line
        text = re.sub(r'\bContact No[:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMOB[\s]*[-:]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMobile[:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bTel[:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPhone[:\s]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bEmail[\s]*id[:\s]*[-–]', '', text, flags=re.IGNORECASE)
        
        # DOB patterns - multiple formats
        text = re.sub(r'\bDate of Birth[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDOB[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bBorn[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d{1,2}[-/]\w{3}[-/]\d{4}\b', '', text)  # 23-JAN-1994 format
        text = re.sub(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b', '', text)  # 23/01/1994 format
        
        # Marital status and gender
        text = re.sub(r'\bMarital Status[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(MARRIED|Unmarried|Single)\b', '', text)
        text = re.sub(r'\bGender[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(Male|Female)\b', '', text)
        
        # Nationality
        text = re.sub(r'\bNationality[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPassport[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(INDIAN|in DIAN)\b', '', text)  # Handle broken spacing
        
        # Family details
        text = re.sub(r"\bFather['\u2019]?s? Name[:\s]+[^\n]+", '', text, flags=re.IGNORECASE)
        text = re.sub(r"\bMother['\u2019]?s? Name[:\s]+[^\n]+", '', text, flags=re.IGNORECASE)
        
        # Government IDs
        text = re.sub(r'\bPAN[:\s]+[A-Z0-9]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(Aadhar|Aadhaar)[:\s]+[\d\s]+', '', text, flags=re.IGNORECASE)
        
        # Addresses - comprehensive patterns
        text = re.sub(r'\b(Address|Permanent|Current)[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bResidence[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        
        # Indian locations - states, cities
        locations = ['Maharashtra', 'Karnataka', 'Gujarat', 'Delhi', 'Tamil Nadu', 'Kerala', 
                    'Pune', 'Mumbai', 'Bangalore', 'Chennai', 'Hyderabad', 'Kolkata', 
                    'Mahalunge', 'Balewadi', 'a manora Park', 'to wn']
        for loc in locations:
            text = re.sub(r'\b' + re.escape(loc) + r'\b', '', text, flags=re.IGNORECASE)
        
        # Country names
        text = re.sub(r',\s*India\b', '', text)
        text = re.sub(r'\bIndia\b', '', text)
        
        # ZIP/PIN codes (6 digits)
        text = re.sub(r'\b\d{6}\b', '', text)
        
        # Declaration sections
        text = re.sub(r'I here ?by declare.*?$', '', text, flags=re.MULTILINE|re.DOTALL)
        text = re.sub(r'\bPlace[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDate[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSignature[:\s]+[^\n]+', '', text, flags=re.IGNORECASE)
        
        # Titles
        text = re.sub(r'\b(Mrs?|Mr|Ms|Dr)\.?\s+', '', text)
        
        # Remove "PERSONAL INFORMATION" section headers
        text = re.sub(r'\bPERSONAL INFORMATION\b', '', text, flags=re.IGNORECASE)
        
        # Remove OBJECTIVE sections (contains personal statements)
        text = re.sub(r'OBJECTIVE[:\s]+.*?(?=\n[A-Z\s]{5,}|\Z)', '', text, flags=re.DOTALL|re.IGNORECASE)
        text = re.sub(r'DECLARATION[:\s]+.*?(?=\n[A-Z\s]{5,}|\Z)', '', text, flags=re.DOTALL|re.IGNORECASE)
        
        # DEBUG: Save checkpoint 2 - after safe PII removal
        if debug_dir:
            Path(debug_dir, '02_after_safe_pii.txt').write_text(text, encoding='utf-8')
        
        # Remove ALL person names from header section (before WORK EXPERIENCE)
        text = self._remove_all_header_names(text)
        
        # DEBUG: Save checkpoint 3 - after header name removal
        if debug_dir:
            Path(debug_dir, '03_after_header_redaction.txt').write_text(text, encoding='utf-8')
        
        return text
    
    def _remove_all_header_names(self, text: str) -> str:
        """Remove ALL person names from header area (everything before WORK EXPERIENCE/PROFESSIONAL EXPERIENCE)"""
        lines = text.split('\n')
        result = []
        in_header = True
        
        # Common title prefixes that indicate names
        title_prefixes = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.']
        
        # Section markers that indicate end of header
        work_section_markers = [
            'work experience', 'professional experience', 'employment history',
            'work history', 'career history', 'experience'
        ]
        
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if we've reached work experience section - end of header
            if in_header:
                for marker in work_section_markers:
                    if marker in stripped.lower() and len(stripped) < 60:
                        in_header = False
                        break
            
            # If we're past header, keep everything
            if not in_header:
                result.append(line)
                continue
            
            # Skip empty lines
            if not stripped:
                result.append(line)
                continue
            
            # Remove entire lines that start with titles in header
            skip_line = False
            for prefix in title_prefixes:
                if stripped.startswith(prefix):
                    skip_line = True
                    break
            if skip_line:
                continue
            
            # MORE AGGRESSIVE: Remove ANY line with 2-4 capitalized words in header
            # This catches names even when mixed with other content
            words = stripped.split()
            if len(words) >= 2 and len(words) <= 4:
                # Count capitalized words (potential name parts)
                cap_words = [w for w in words if w and len(w) > 1 and w[0].isupper() and w.replace('-', '').replace("'", '').isalpha()]
                
                # If 2+ capitalized words, likely a name
                if len(cap_words) >= 2:
                    # Exceptions: Keep if it contains protected terms or technical keywords
                    lower_line = stripped.lower()
                    is_protected = any(protected in lower_line for protected in [
                        'key skills', 'profile', 'summary', 'objective', 'developer', 
                        'engineer', 'lead', 'senior', 'architect', 'consultant', 'analyst',
                        'manager', 'director', 'specialist', 'technologist', 'activities',
                        'interest', 'skills', 'product'
                    ] + self.PROTECTED_NAMES)
                    
                    if not is_protected:
                        # This is likely a person name - skip it
                        continue
            
            # Also remove lines that are JUST a single capitalized word (first/last name alone)
            if len(words) == 1 and len(stripped) > 2 and stripped[0].isupper() and stripped.isalpha():
                # Exception: Keep if it's a known section header or keyword
                if stripped.upper() not in ['PROFILE', 'SUMMARY', 'SKILLS', 'OBJECTIVE', 'KEY', 'ACTIVITIES', 'INTEREST', 'SOCIAL']:
                    continue
            
            # Keep everything else in header
            result.append(line)
        
        return '\n'.join(result)
    
    def _remove_header_names(self, text: str) -> str:
        """Remove person names and locations from header section (first 30 lines)"""
        lines = text.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Only process first 35 lines (header area - extended to catch more names)
            if i >= 35:
                result.append(line)
                continue
            
            # Skip if empty
            if not stripped:
                result.append(line)
                continue
            
            # Skip if it's a section header (preserve these)
            if any(keyword in stripped.lower() for keyword in ['summary', 'skills', 'experience', 'profile', 'objective', 'key skills', 'work experience', 'technical skills', 'profile summary']):
                result.append(line)
                continue
            
            # FIRST: Remove location patterns from ALL lines (City, Country anywhere in the text)
            # Match patterns like "Bangalore, India" or "New York, USA" 
            # But NOT programming languages like "Python, Java"
            # Location names typically: Bangalore, Mumbai, Delhi, Chennai, Hyderabad, Pune, Kolkata
            #                           India, USA, UK, Canada, Singapore
            location_cities = ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata', 'Noida', 'Gurgaon', 'Ahmedabad']
            location_countries = ['India', 'USA', 'UK', 'Canada', 'Singapore', 'Australia', 'Germany', 'France']
            
            for city in location_cities:
                line = re.sub(rf'\b{city}\b,?\s*', '', line, flags=re.IGNORECASE)
            for country in location_countries:
                line = re.sub(rf'\b{country}\b,?\s*', '', line, flags=re.IGNORECASE)
            
            stripped = line.strip()
            
            # If line became empty or too short after location removal, skip it
            if not stripped or len(stripped) < 3:
                continue
            
            # Skip if it contains protected company/tech names
            lower_line = stripped.lower()
            if any(protected in lower_line for protected in self.PROTECTED_NAMES):
                result.append(line)
                continue
            
            # Skip if line contains technical content, dates, or job titles
            if any(x in lower_line for x in ['c++', 'python', 'java', 'linux', 'android', 'years', '20', 'exp:', 'specialisation', 'product :', 'programming :']):
                result.append(line)
                continue
            
            # Remove lines that look like names (1-4 capitalized words, no numbers)
            words = stripped.split()
            if 1 <= len(words) <= 4:
                # Check if all words are capitalized and alphanumeric (names)
                # BUT not job titles like "Lead Engineer" or "Software Developer"
                if all(w and w[0].isupper() and re.match(r"^[A-Za-z\-']+$", w) for w in words):
                    # Skip this line - it's likely a person name
                    continue
            
            # Keep the line (possibly modified with location removed)
            result.append(line)
        
        return '\n'.join(result)


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
        """Remove ONLY consecutive duplicate lines (not global dedup)"""
        lines = text.split('\n')
        if not lines:
            return text
        
        result = [lines[0]]  # Always keep first line
        
        for i in range(1, len(lines)):
            current = lines[i].strip()
            previous = lines[i-1].strip()
            
            # Only skip if EXACT consecutive duplicate
            if current == previous and current:  # Don't skip empty lines
                continue
            
            result.append(lines[i])
        
        return '\n'.join(result)
    
    @staticmethod
    def fix_spacing(text: str) -> str:
        """Fix missing spaces between concatenated words using comprehensive word detection"""
        
        # CRITICAL: Fix common OCR broken words FIRST (before any other processing)
        # Fix common OCR errors with simple string replacement
        text = text.replace('for ward', 'forward').replace('a daptable', 'adaptable')
        text = text.replace('healthc are', 'healthcare').replace('Evolvew are in c', 'Evolveware Inc')
        text = text.replace('a hmedabad', 'Ahmedabad').replace(' or M', ' ORM').replace(' or M:', ' ORM:')
        text = text.replace('a dm in', 'admin').replace('in voices', 'invoices').replace('litigati on', 'litigation')
        text = text.replace('Whats a pp', 'WhatsApp').replace('web for ms', 'web forms')
        text = text.replace('is o8582', 'ISO8582').replace('is O8583', 'ISO8583')
        text = text.replace(' a nt', ' ant').replace('a uthorizati on', 'authorization')
        text = text.replace('a cquiring', 'acquiring').replace('st and-ups', 'stand-ups')
        text = text.replace('problemsolving', 'problem solving').replace('Software&prod', 'Software & prod')
        text = text.replace('a RM9', 'ARM9').replace('c on gurati on', 'configuration')
        text = text.replace('EDUCATI on', 'EDUCATION').replace('Bachel or', 'Bachelor')
        text = text.replace('a bhinav', 'Abhinav').replace('as sisted', 'assisted')
        text = text.replace('linked in.com', 'linkedin.com').replace('ia a end', 'is an end')
        text = text.replace('also having', 'Also having')
        
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
        
        # Additional fixes for common broken words seen in outputs
        text = re.sub(r'\ba\s+ny\s*[Pp]oint', 'AnyPoint', text)
        text = re.sub(r'\bin\s+tegrati\s*on', 'Integration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDesignati\s*on', 'Designation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDurati\s*on', 'Duration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDescripti\s*on', 'Description', text, flags=re.IGNORECASE)
        text = re.sub(r'\bRegistrati\s*on', 'Registration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bGenerati\s*on', 'Generation', text, flags=re.IGNORECASE)
        
        # COMPREHENSIVE fixes for all broken spacing issues found in output files
        text = re.sub(r'\ba\s+nalys\s*is\b', 'analysis', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+nalytical\b', 'analytical', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+formati\s*on\b', 'information', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+bove\b', 'above', text, flags=re.IGNORECASE)
        text = re.sub(r'\bor\s+ganizati\s*on\b', 'organization', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+morrow\b', 'tomorrow', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+dexing\b', 'indexing', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+loha\b', 'Aloha', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+manora\b', 'Amanora', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pplicati\s*on\b', 'application', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pplocati\s*on\b', 'application', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pproach\b', 'approach', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+bility\b', 'ability', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ctivities\b', 'activities', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ctions\b', 'actions', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+gents\b', 'agents', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ppreciati\s*on\b', 'appreciation', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+uth\s*or\b', 'author', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+uthenticati\s*on\b', 'authentication', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+utomated\b', 'automated', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+utomatically\b', 'automatically', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+vanced\b', 'advanced', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+dvance\b', 'advance', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+JAX\b', 'AJAX', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+llows?\b', 'allows', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+merican\b', 'American', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+marlal\b', 'Amarlal', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+PAC\b', 'APAC', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+BAP\b', 'ABAP', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+CCA\b', 'ACCA', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+CHIEVEMENTS\b', 'ACHIEVEMENTS', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ssist\b', 'assist', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ssociati\s*on\b', 'association', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+t\b(?!\s+the)', 'at', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ustria\b', 'Austria', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+warded\b', 'awarded', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ward\b', 'award', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+rticles\b', 'articles', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+bstracti\s*on\b', 'abstraction', text, flags=re.IGNORECASE)
        text = re.sub(r'\bCategorizati\s*on\b', 'Categorization', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcha\s+in\b', 'chain', text, flags=re.IGNORECASE)
        text = re.sub(r'\bCommunicati\s*on\b', 'Communication', text, flags=re.IGNORECASE)
        text = re.sub(r'\bCollaborati\s*on\b', 'Collaboration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bContributi\s*on\b', 'Contribution', text, flags=re.IGNORECASE)
        text = re.sub(r'\bco\s*-\s*or\s+dinated\b', 'coordinated', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdecisi\s*on\b', 'decision', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfor\s+ecasting\b', 'forecasting', text, flags=re.IGNORECASE)
        text = re.sub(r'\bgre\s+a\s+t\b', 'great', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+sights\b', 'insights', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+tegrat\s*or\b', 'Integrator', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+teractions\b', 'interactions', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+tuitive\b', 'intuitive', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+volved\b', 'involved', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmaj\s+or\b', 'major', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMainta\s+in\b', 'Maintain', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMonitoring\b(?=\s+SI)', 'Monitoring', text, flags=re.IGNORECASE)
        text = re.sub(r'\bof\s+fering\b', 'offering', text, flags=re.IGNORECASE)
        text = re.sub(r'\bof\s+fers\b', 'offers', text, flags=re.IGNORECASE)
        text = re.sub(r'\bof\s+fice\b', 'office', text, flags=re.IGNORECASE)
        text = re.sub(r'\bParticipate\b(?!\s+in)', 'Participate', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprep\s+are\b', 'prepare', text, flags=re.IGNORECASE)
        text = re.sub(r'\bproactive\b(?!\s+approach)', 'proactive', text, flags=re.IGNORECASE)
        text = re.sub(r'\bproducti\s*on\b', 'production', text, flags=re.IGNORECASE)
        text = re.sub(r'\breducti\s*on\b', 'reduction', text, flags=re.IGNORECASE)
        text = re.sub(r'\brecogniti\s*on\b', 'recognition', text, flags=re.IGNORECASE)
        text = re.sub(r'\bregi\s*on\b', 'region', text, flags=re.IGNORECASE)
        text = re.sub(r'\bResponsive\b(?!\s+UI)', 'Responsive', text, flags=re.IGNORECASE)
        text = re.sub(r'\bsatisfacti\s*on\b', 'satisfaction', text, flags=re.IGNORECASE)
        text = re.sub(r'\bsections?\b(?!\s+from)', 'sections', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSeni\s*or\b', 'Senior', text, flags=re.IGNORECASE)
        text = re.sub(r'\bspecificati\s*ons\b', 'specifications', text, flags=re.IGNORECASE)
        text = re.sub(r'\bstatistic\b', 'statistics', text, flags=re.IGNORECASE)
        text = re.sub(r'\bsubscripti\s*ons?\b', 'subscriptions', text, flags=re.IGNORECASE)
        text = re.sub(r'\btransmissi\s*on\b', 'transmission', text, flags=re.IGNORECASE)
        text = re.sub(r'\bTransiti\s*on\b', 'Transition', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+wards\b', 'towards', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+wn\b', 'town', text, flags=re.IGNORECASE)
        text = re.sub(r'\bvalidati\s*on\b', 'validation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bvisualizati\s*on\b', 'visualization', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwill\b(?!\s+in)', 'well', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+tal\b', 'total', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pril\b', 'April', text, flags=re.IGNORECASE)
        text = re.sub(r'\bVersi\s*on', 'Version', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pplications?\b', 'application', text, flags=re.IGNORECASE)
        text = re.sub(r'\bEnvironment', 'Environment', text)
        text = re.sub(r'\bor\s+iented', 'oriented', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+FORMATI\s+on', 'INFORMATION', text)
        text = re.sub(r'\ba\s+MIT', 'AMIT', text)
        
        # More broken word patterns found in outputs
        text = re.sub(r'\ba\s+nalyze\b', 'analyze', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+cidents\b', 'incidents', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfuncti\s*on\b', 'function', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+maz\s*on\b', 'Amazon', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+zure\b', 'Azure', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ugust\b', 'August', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ims\b', 'aims', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+bstracts\b', 'abstracts', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+chieving\b', 'achieving', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+re\b(?!\s+you)', 'are', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+sist\b', 'assist', text, flags=re.IGNORECASE)
        text = re.sub(r'\bE\s+at\s+on\b', 'Eaton', text, flags=re.IGNORECASE)
        text = re.sub(r'\bgre\s+a\s+t\b', 'great', text, flags=re.IGNORECASE)
        text = re.sub(r'\bQuali\s*ficati\s*on\b', 'Qualification', text, flags=re.IGNORECASE)
        text = re.sub(r'\bexperti\s+se\b', 'expertise', text, flags=re.IGNORECASE)
        text = re.sub(r'\bchiev\s*ing\b', 'achieving', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfoster\s*ing\b', 'fostering', text, flags=re.IGNORECASE)
        text = re.sub(r'\bextracti\s*on\b', 'extraction', text, flags=re.IGNORECASE)
        
        # Additional broken patterns from latest check
        text = re.sub(r'\ba\s+dvanced\b', 'advanced', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+dex\b', 'index', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+tegrating\b', 'integrating', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprecisi\s*on\b', 'precision', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+nalytics\b', 'analytics', text, flags=re.IGNORECASE)
        text = re.sub(r'\bor\s+ganizational\b', 'organizational', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpreparati\s*on\b', 'preparation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpresentati\s*on\b', 'presentation', text, flags=re.IGNORECASE)
        text = re.sub(r'\btransacti\s*on\b', 'transaction', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdoma\s+in\b', 'domain', text, flags=re.IGNORECASE)
        text = re.sub(r'\bflow\s+\.', 'flow.', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ccounting\b', 'accounting', text, flags=re.IGNORECASE)
        
        # Final fixes for remaining broken words
        text = re.sub(r'\bin\s+tercompany\b', 'intercompany', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+greement\b', 'agreement', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcreati\s*on\b', 'creation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+itiatives\b', 'initiatives', text, flags=re.IGNORECASE)
        text = re.sub(r'\bobta\s+in\b', 'obtain', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpositi\s*on\b', 'position', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ngular\b', 'Angular', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+utomati\s*on\b', 'automation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bCalculati\s*on\b', 'Calculation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+ce\b', 'once', text, flags=re.IGNORECASE)
        text = re.sub(r'\bide\s+as\b', 'ideas', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+nnum\b', 'annum', text, flags=re.IGNORECASE)
        text = re.sub(r'\bth\s+at\b', 'that', text, flags=re.IGNORECASE)
        text = re.sub(r'\bthe\s+me\b', 'theme', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+p\b', 'top', text, flags=re.IGNORECASE)
        
        # MORE patterns from verification (critical fixes)
        text = re.sub(r'EFFICIENT\s+SOLUTIONS\.\s*-SOLVING\s+SKILLS', 'EFFICIENT SOLUTIONS. PROBLEM-SOLVING SKILLS', text)
        text = re.sub(r'\bpers\s+on\b', 'person', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pply\b', 'apply', text, flags=re.IGNORECASE)
        text = re.sub(r'\bst\s+and-ups\b', 'stand-ups', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+dustry\b', 'industry', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+teractivity\b', 'interactivity', text, flags=re.IGNORECASE)
        text = re.sub(r'\bconfigurati\s*on\b', 'configuration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bBlaz\s+or\b', 'Blazor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bCertificati\s*on\b', 'Certification', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+dopt\b', 'adopt', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+dividual\b', 'individual', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+fotech\b', 'infotech', text, flags=re.IGNORECASE)
        text = re.sub(r'\bor\s+der\b', 'order', text, flags=re.IGNORECASE)
        text = re.sub(r'\bSoft-?\s*w\s+are\b', 'Software', text, flags=re.IGNORECASE)
        text = re.sub(r'\bc\s+on-?\s*trol\b', 'control', text, flags=re.IGNORECASE)
        text = re.sub(r'\bthe\s+mes\b', 'themes', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pr\b', 'Apr', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdistracti\s*on\b', 'distraction', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+rchitect\b', 'architect', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+udi\b', 'Audi', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+utomo-?\s*tive\b', 'automotive', text, flags=re.IGNORECASE)
        text = re.sub(r'\bKotl\s+in\b', 'Kotlin', text, flags=re.IGNORECASE)
        text = re.sub(r'\bper\s+for-?\s*mance\b', 'performance', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ctivity\b', 'activity', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ltran\b', 'Altran', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpa\s+in\b', 'pain', text, flags=re.IGNORECASE)
        text = re.sub(r'\bEdit\s+or\b', 'Editor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwith\s+in\b', 'within', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+dhering\b', 'adhering', text, flags=re.IGNORECASE)
        text = re.sub(r'\bas\s+sisted\b', 'assisted', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwith\s+out\b', 'without', text, flags=re.IGNORECASE)
        
        # Remove weird symbol patterns
        text = re.sub(r'●●\s+[a-z]\s+[a-z]+\s*', '', text)
        text = re.sub(r'\(cid:\d+\)', '', text)  # Remove (cid:123) patterns
        text = re.sub(r'\(cid\s*\)', '', text)
        text = re.sub(r'\(cid\s+', '', text)
        text = re.sub(r'○\s+', '• ', text)  # Convert hollow bullets to solid
        
        # Clean up incomplete URLs and orphaned text
        text = re.sub(r'\bwww\.\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\bwww\.\s*\n', '\n', text, flags=re.MULTILINE)
        text = re.sub(r'\bhttp[s]?://\s*$', '', text, flags=re.MULTILINE)
        
        # ALL remaining broken word patterns - comprehensive fix
        text = re.sub(r'\ba\s+bout\b', 'about', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+fter\b', 'after', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ll\b', 'all', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+lso\b', 'also', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+n\s+', 'an ', text)
        text = re.sub(r'\ba\s+nd\b', 'and', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ny\b', 'any', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+', 'as ', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+t\b', 'at', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+uth\s*or\b', 'author', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+uthenticati\s*on\b', 'authentication', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+utomated\b', 'automated', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+vailable\b', 'available', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ware\b', 'aware', text, flags=re.IGNORECASE)
        text = re.sub(r'\bco\s+or\s+dinati\s*on\b', 'coordination', text, flags=re.IGNORECASE)
        text = re.sub(r'\bf\s+or\b', 'for', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfor\s+ecasting\b', 'forecasting', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+clude\b', 'include', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+come\b', 'income', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+dependently\b', 'independently', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+fosys\b', 'Infosys', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+formati\s*on\b', 'information', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+itiatives\b', 'initiatives', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+tel\b', 'Intel', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+tercompany\b', 'intercompany', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+to\b', 'into', text, flags=re.IGNORECASE)
        text = re.sub(r'\bm\s+onitoring\b', 'monitoring', text, flags=re.IGNORECASE)
        text = re.sub(r'\bon\s+ce\b', 'once', text, flags=re.IGNORECASE)
        text = re.sub(r'\bover\s+view\b', 'overview', text, flags=re.IGNORECASE)
        text = re.sub(r'\bP\s+apis\b', 'APIs', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+P\s+is\b', 'APIs', text, flags=re.IGNORECASE)
        text = re.sub(r'\bper\s+form\b', 'perform', text, flags=re.IGNORECASE)
        text = re.sub(r'\bper\s+formed\b', 'performed', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpre\s+pared\b', 'prepared', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpre\s+pare\b', 'prepare', text, flags=re.IGNORECASE)
        text = re.sub(r'\breconciliati\s*on\b', 'reconciliation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bs\s+ame\b', 'same', text, flags=re.IGNORECASE)
        text = re.sub(r'\bsoluti\s*on\b', 'solution', text, flags=re.IGNORECASE)
        text = re.sub(r'\bt\s+o\b', 'to', text, flags=re.IGNORECASE)
        text = re.sub(r'\bthe\s+ir\b', 'their', text, flags=re.IGNORECASE)
        text = re.sub(r'\bthe\s+re\b', 'there', text, flags=re.IGNORECASE)
        text = re.sub(r'\bth\s+is\b', 'this', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+ols?\b', 'tool', text, flags=re.IGNORECASE)
        text = re.sub(r'\bW\s+as\b', 'Was', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwell\s+be\b', 'will be', text, flags=re.IGNORECASE)
        text = re.sub(r'\bw\s+ork\b', 'work', text, flags=re.IGNORECASE)
        
        # Fix specific broken patterns
        text = re.sub(r'\ba\s+s\s+sociate\b', 'Associate', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+sociati\s*on\b', 'association', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+signed\b', 'assigned', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+sist\b', 'assist', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+sisted\b', 'assisted', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+u\s+dit\b', 'audit', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+UG\b', 'AUG', text, flags=re.IGNORECASE)
        text = re.sub(r'\bas\s+P\.NET\b', 'ASP.NET', text, flags=re.IGNORECASE)
        text = re.sub(r'\bat\s+OS\b', 'TCS', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcomponent\s*s\b', 'components', text, flags=re.IGNORECASE)
        text = re.sub(r'\bDECLARATI\s*on\b', 'DECLARATION', text, flags=re.IGNORECASE)
        text = re.sub(r'\bF\s+is\b', 'FIS', text, flags=re.IGNORECASE)
        text = re.sub(r'\bide\s+as\b', 'ideas', text, flags=re.IGNORECASE)
        text = re.sub(r'\bide\s+a\b', 'idea', text, flags=re.IGNORECASE)
        text = re.sub(r'\bimplemeted\b', 'implemented', text, flags=re.IGNORECASE)
        text = re.sub(r'\bJ\s+S\s+on\b', 'JSON', text, flags=re.IGNORECASE)
        text = re.sub(r'\bJalga\s+on\b', 'Jalgaon', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmigrati\s*on\b', 'migration', text, flags=re.IGNORECASE)
        text = re.sub(r'\bstretegies\b', 'strategies', text, flags=re.IGNORECASE)
        text = re.sub(r'\bV\s+at\b', 'VAT', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+cross\b', 'across', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+terface', 'interface', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+volving', 'involving', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+fra', 'infra', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+ternals', 'internals', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+oling', 'tooling', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+rchitecture', 'architecture', text, flags=re.IGNORECASE)
        text = re.sub(r'\bprocess\s+or\b', 'processor', text, flags=re.IGNORECASE)
        
        # Remove garbled/nonsense text patterns
        text = re.sub(r'\b[A-Z][a-z]{2,}[a-z]{2,}[a-z]{2,}\s+[a-z]{3,}[a-z]{3,}\s+[a-z]{3,}[a-z]{3,}\b', '', text)
        # Remove specific garbled patterns
        text = re.sub(r'●●\s*H[A-Z][a-z]+\s+[a-z]+\s+[a-z]+\s+[a-z]+.*?\.', '●', text)
        text = re.sub(r'[A-Z][a-z]{8,}\s+[a-z]{8,}\s+[a-z]{8,}.*?\.', '', text)
        
        # Clean up standalone single letters and fragments
        text = re.sub(r'\bC\s+O\s*\n', '\n', text)  # "C O" on its own line
        text = re.sub(r'\bP\s+Q\s*\n', '\n', text)  # "P Q" on its own line
        text = re.sub(r'\bD\s+IFRS\b', 'DIPLOMA IFRS', text)
        text = re.sub(r'\bC\s+A\b', 'CA', text)
        text = re.sub(r'\bD\s+eveloper', 'Developer', text, flags=re.IGNORECASE)
        text = re.sub(r'\bE\s+SB\b', 'ESB', text)
        text = re.sub(r'\bR\s+EST\b', 'REST', text)
        text = re.sub(r'\bS\s+OAP\b', 'SOAP', text)
        text = re.sub(r'\bW\s+in\b', 'Win', text)
        
        # Fix common typos and misspellings
        text = re.sub(r'\bFilers\b', 'Filters', text)
        text = re.sub(r'\bMunit\b', 'MUnit', text)
        text = re.sub(r'\bcomponants\b', 'components', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcompletication\b', 'completion', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcompleti\s*on\b', 'completion', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwell\s+be\s+providing\b', 'will be providing', text, flags=re.IGNORECASE)
        text = re.sub(r'\bwell\s+be\s+Provides\b', 'will be Provides', text, flags=re.IGNORECASE)
        text = re.sub(r'\bresourcerequests\b', 'resource requests', text, flags=re.IGNORECASE)
        
        # Final cleanup for remaining broken words - COMPREHENSIVE
        text = re.sub(r'\ba\s+ccept\b', 'accept', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ccuracy\b', 'accuracy', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+chieve\b', 'achieve', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+dapt\b', 'adapt', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+dherence\b', 'adherence', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+DO\.NET\b', 'ADO.NET', text)
        text = re.sub(r'\ba\s+iming\b', 'aiming', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+lcatel\b', 'Alcatel', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+lign\b', 'align', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+LM\b', 'ALM', text)
        text = re.sub(r'\ba\s+nalyst\b', 'analyst', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+nalyzing\b', 'analyzing', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+nti-Executable\b', 'Anti-Executable', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+ntivirus\b', 'Antivirus', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pache\b', 'Apache', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+pplicants\b', 'applicants', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+rchitects\b', 'architects', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+s\s+sessments\b', 'assessments', text, flags=re.IGNORECASE)
        text = re.sub(r'\ba\s+utomates\b', 'automates', text, flags=re.IGNORECASE)
        text = re.sub(r'\bas\s+sociati\s*on\b', 'association', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdept\b', 'adept', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdirecti\s*on\b', 'direction', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdocumentati\s*on\b', 'documentation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bErr\s+or\b', 'Error', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfor\s+m\b', 'form', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfor\s+matting\b', 'formatting', text, flags=re.IGNORECASE)
        text = re.sub(r'\bgre\s+at\b', 'great', text, flags=re.IGNORECASE)
        text = re.sub(r'\bh\s+as\b', 'has', text, flags=re.IGNORECASE)
        text = re.sub(r'\bhas\s+sle-free\b', 'hassle-free', text, flags=re.IGNORECASE)
        text = re.sub(r'\bimplemet\b', 'implement', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+cluding\b', 'including', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+tern\b', 'Intern', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+novative\b', 'innovative', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+put\b', 'input', text, flags=re.IGNORECASE)
        text = re.sub(r'\bin\s+tegrated\b', 'integrated', text, flags=re.IGNORECASE)
        text = re.sub(r'\bj\s+Query\b', 'jQuery', text, flags=re.IGNORECASE)
        text = re.sub(r'\bJS\s+on\b', 'JSON', text)
        text = re.sub(r'\blog\s+in\b', 'login', text, flags=re.IGNORECASE)
        text = re.sub(r'\bMeditati\s*on\b', 'Meditation', text, flags=re.IGNORECASE)
        text = re.sub(r'\bor\s+dinati\s*on\b', 'ordination', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpersonalizati\s*on\b', 'personalization', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPredicti\s*on\b', 'Prediction', text, flags=re.IGNORECASE)
        text = re.sub(r'\bRequirment\b', 'Requirement', text, flags=re.IGNORECASE)
        text = re.sub(r'\bto\s+mc\s+at\b', 'Tomcat', text, flags=re.IGNORECASE)
        
        # Remove complete garbled nonsense lines
        text = re.sub(r'●●\s*[A-Z][a-z]+[a-z]+[a-z]+\s+[a-z]+[a-z]+\s+.*?\.', '', text)
        text = re.sub(r'Daneds\s+i\s+a\s+gnneyd.*?\.', '', text)
        text = re.sub(r'IHmapnldesm-oenn.*?\.', '', text)
        text = re.sub(r'IAmnpalleymzeedn.*?\.', '', text)
        text = re.sub(r'DAenpalloyyzemde.*?\.', '', text)
        text = re.sub(r'i\s+Pmarptliecmipeatteedd.*?\.', '', text)
        
        # Clean up "id. –" and similar fragments
        text = re.sub(r'\bid\.\s*[-–—]\s*\n', '\n', text)
        text = re.sub(r'\bNo\.\s*:\(\s*\n', '\n', text)
        
        # Remove "www." on its own line or at end of line
        text = re.sub(r'^www\.\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\nwww\.\s*\n', '\n', text)
        text = re.sub(r'Consultant\s*\nwww\.', 'Consultant', text)
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
                
                # TASK 4: Structural Integrity - Clear section boundaries
                # Ensure proper spacing before section headers
                if result and result[-1].strip():
                    result.append("")
                    result.append("")
                
                # Add section header with clear visual separation
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
    """Main orchestrator with category-based routing"""
    
    def __init__(self):
        self.extractor = TextExtractor()
        self.redactor = PIIRedactor()
        self.classifier = ResumeClassifier()
        self.stats = {
            'extracted_chars': 0,
            'pii_redacted': 0,
            'output_chars': 0,
            'category': ''
        }
    
    def process(self, pdf_path: str) -> str:
        """Process PDF through complete pipeline with category detection"""
        print(f"\nProcessing: {os.path.basename(pdf_path)}")
        
        # Classify resume type
        category = self.classifier.classify(pdf_path)
        self.stats['category'] = category
        print(f"  > Category: {category}")
        
        # Extract using appropriate method
        print("  > Extracting text...")
        if category == 'naukri':
            text = self.extractor.extract_naukri(pdf_path)
        elif category == 'multi_column':
            text = self.extractor.extract(pdf_path)
        elif category == 'simple':
            text = self.extractor.extract_simple(pdf_path)
        else:  # standard
            text = self.extractor.extract_standard(pdf_path)
        
        # DEBUG: Save raw text
        with open("debug_raw_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        if not text:
            print("  X Failed to extract text")
            return ""
        
        self.stats['extracted_chars'] = len(text)
        print(f"  OK Extracted: {len(text)} characters")
        
        # TASK 1: Word-Healer - Fix fragmented words
        print("  > Healing fragmented text...")
        text = WordHealer.heal(text)
        
        # FIX OCR ERRORS IMMEDIATELY after extraction
        text = TextPolisher.fix_spacing(text)
        
        # TASK 2: De-Duplicator - Remove duplicate blocks
        print("  > Removing duplicates...")
        text = DeDuplicator.remove_duplicates(text)
        
        # Remove education section first
        print("  > Removing education...")
        text = self._remove_education(text)
        
        # TASK 3: Layout-Aware Redaction - Remove sidebar contact info
        print("  > Applying layout-aware redaction...")
        _, redacted_zones = LayoutAwareRedactor.extract_with_zones(pdf_path)
        if redacted_zones:
            text = LayoutAwareRedactor.redact_zones(text, redacted_zones)
            print(f"  OK Redacted {len(redacted_zones)} sidebar items")
        
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
        
        # Polish (but skip fix_spacing since we already did it)
        result = TextPolisher.remove_duplicates(result)
        result = TextPolisher.clean(result)
        result = TextPolisher.normalize_bullets(result)
        result = TextPolisher.add_spacing(result)
        
        self.stats['output_chars'] = len(result)
        print(f"  OK Output: {len(result)} characters")
        print(f"  OK PII removed: {self.redactor.stats['pii_redacted']} items")
        print(f"  OK Pipeline: {self.stats['category']}")
        
        return result
    
    def _remove_education(self, text: str) -> str:
        """Remove education section COMPLETELY with enhanced detection"""
        lines = text.split('\n')
        result = []
        in_education = False
        skip_count = 0
        
        for i, line in enumerate(lines):
            line_upper = line.strip().upper()
            line_lower = line.strip().lower()
            
            # Detect education section start
            if 'EDUCATION' in line_upper and len(line_upper) < 40:
                in_education = True
                skip_count = 0
                continue
            
            # Also detect lines with degree keywords
            if any(x in line_lower for x in ['b.tech', 'b.e.', 'm.tech', 'm.e.', 'bachelor', 'master',
                                              'diploma', 'ph.d', 'phd', 'university', 'college', 'institute']):
                in_education = True
                skip_count = 0
                continue
            
            # Also detect CGPA/GPA/percentage lines (education details)
            if any(x in line_lower for x in ['cgpa:', 'gpa:', 'percentage:', 'marks:', 'score:']):
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
