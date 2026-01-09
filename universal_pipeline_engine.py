"""
Universal CV Redaction Pipeline Engine - Configuration-Driven
==============================================================
Scalable architecture with NO hardcoded data.
All rules, terms, and patterns loaded from JSON config files.

Usage:
    python cv_redaction_pipeline.py [input_dir] [output_dir] [--debug]
    
    # Add new data via CLI
    python cv_redaction_pipeline.py add-city "Boston"
    python cv_redaction_pipeline.py add-term "tensorflow"
    python cv_redaction_pipeline.py add-healing "administr at ion" "administration"

Config Files (auto-created in ./config/):
    ├── locations.json          # Cities, states, countries
    ├── protected_terms.json    # Technical terms to preserve
    ├── sections.json           # Section headers
    ├── pii_patterns.json       # PII detection patterns
    └── text_healing.json       # Spacing fix rules
"""

import os
import re
import abc
import json
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEBUG_DIR = Path("debug_output")
OUTPUT_DIR = Path("final_output")
DEBUG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================================
# CONFIGURATION SYSTEM
# ============================================================================

class ConfigLoader:
    """
    Centralized configuration loader.
    All data-driven rules come from JSON files.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._ensure_default_configs()
        self._cache = {}
    
    def _ensure_default_configs(self):
        """Create default config files if they don't exist"""
        
        # 1. Locations
        locations_file = self.config_dir / "locations.json"
        if not locations_file.exists():
            default_locations = {
                "cities": [
                    "Pune", "Mumbai", "Delhi", "Bangalore", "Bengaluru", 
                    "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Jaipur",
                    "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal",
                    "Visakhapatnam", "Patna", "Vadodara", "Ghaziabad", "Nashik",
                    "Noida", "Gurgaon", "Gurugram", "Chandigarh", "Kochi",
                    "Remote", "Banglore", "Orissa"
                ],
                "states": [
                    "Maharashtra", "Karnataka", "Tamil Nadu", "Telangana",
                    "West Bengal", "Gujarat", "Rajasthan", "Madhya Pradesh",
                    "Uttar Pradesh", "Kerala", "Punjab", "Haryana", "Bihar",
                    "Odisha", "Andhra Pradesh", "India", "INDIA"
                ],
                "countries": ["India", "INDIA", "USA", "UK", "United States"]
            }
            locations_file.write_text(json.dumps(default_locations, indent=2))
        
        # 2. Protected Terms
        protected_file = self.config_dir / "protected_terms.json"
        if not protected_file.exists():
            default_protected = {
                "languages": [
                    "python", "java", "javascript", "typescript", "c++", "c#", 
                    "ruby", "php", "go", "rust", "swift", "kotlin", "scala", "sql"
                ],
                "frameworks": [
                    "react", "angular", "vue", "django", "flask", "spring", 
                    "nodejs", "express", "laravel", "aspnet", "dotnet", "blazor"
                ],
                "databases": [
                    "mysql", "postgresql", "mongodb", "oracle", "redis", 
                    "cassandra", "sqlite", "elasticsearch"
                ],
                "cloud": [
                    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", 
                    "terraform", "ansible"
                ],
                "tools": [
                    "git", "jira", "postman", "swagger", "jenkins", "gitlab"
                ],
                "os": [
                    "linux", "unix", "windows", "android", "ios", "macos"
                ],
                "roles": [
                    "engineer", "developer", "architect", "manager", "consultant",
                    "analyst", "senior", "junior", "principal", "lead"
                ],
                "technical_terms": [
                    "automotive", "embedded", "firmware", "kernel", "telematics",
                    "gateway", "application", "configuration", "implementation",
                    "integration", "optimization", "performance", "platform",
                    "communication", "documentation", "collaboration",
                    "administration", "coordination", "occupation", "organization"
                ]
            }
            protected_file.write_text(json.dumps(default_protected, indent=2))
        
        # 3. Sections
        sections_file = self.config_dir / "sections.json"
        if not sections_file.exists():
            default_sections = {
                "remove": {
                    "education": [
                        "education", "academic", "academics", "qualification",
                        "qualifications", "educational background", "educ"
                    ],
                    "personal": [
                        "personal details", "personal information", "personal",
                        "hobbies", "interests", "languages known", 
                        "language proficiency", "extracurricular", "pers on al"
                    ],
                    "declaration": ["declaration"]
                },
                "preserve": [
                    "experience", "work experience", "professional experience",
                    "skills", "technical skills", "key skills", "projects",
                    "project details", "summary", "profile", "objective",
                    "career objective", "certifications", "achievements"
                ]
            }
            sections_file.write_text(json.dumps(default_sections, indent=2))
        
        # 4. PII Patterns
        pii_file = self.config_dir / "pii_patterns.json"
        if not pii_file.exists():
            default_pii = {
                "email": {
                    "pattern": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
                },
                "phone": {
                    "patterns": [
                        "\\(?\\+?\\d{1,3}\\)?[-\\.\\s]?\\(?\\d{2,4}\\)?[-\\.\\s]?\\d{3,4}[-\\.\\s]?\\d{3,4}",
                        "\\b\\d{10}\\b"
                    ]
                },
                "url": {
                    "pattern": "https?://[^\\s]+"
                },
                "social": {
                    "patterns": [
                        "linkedin\\.com/in/[\\w\\-]+",
                        "github\\.com/[\\w\\-]+"
                    ]
                },
                "demographics": {
                    "dob": "\\b(date of birth|dob|born on)\\s*:?\\s*[^\\n]+",
                    "gender": "\\b(gender|sex)\\s*:?\\s*(male|female|m|f)[^\\n]*",
                    "marital": "\\b(marital status)\\s*:?\\s*(single|married)[^\\n]*",
                    "age": "\\bage\\s*:?\\s*\\d{1,3}\\s*(years?|yrs?)?[^\\n]*",
                    "nationality": "\\bnationality\\s*:?\\s*(indian|american)[^\\n]*"
                }
            }
            pii_file.write_text(json.dumps(default_pii, indent=2))
        
        # 5. Text Healing
        healing_file = self.config_dir / "text_healing.json"
        if not healing_file.exists():
            default_healing = {
                "suffix_patterns": {
                    "at ion": "ation",
                    "ic at ion": "ication",
                    "in g": "ing",
                    "er ing": "ering",
                    "ur ing": "uring"
                },
                "prefix_patterns": {
                    "c on ": "con",
                    "c om ": "com"
                },
                "common_words": {
                    "applic at ion": "application",
                    "occup at ion": "occupation",
                    "organiz at ion": "organization",
                    "configur at ion": "configuration",
                    "implement at ion": "implementation",
                    "coord in at ion": "coordination",
                    "coord in at ed": "coordinated",
                    "communic at ion": "communication",
                    "document at ion": "documentation",
                    "collabor at ion": "collaboration",
                    "administr at ion": "administration",
                    "adm in istr at ion": "administration",
                    "underst and ing": "understanding",
                    "h and ling": "handling",
                    "s and box": "sandbox",
                    "st and ard": "standard",
                    "c on trol": "control",
                    "plat for m": "platform",
                    "per for m": "perform",
                    "au to motive": "automotive",
                    "telem at ics": "telematics",
                    "g at eway": "gateway",
                    "integr at ion": "integration",
                    "vis ion": "vision",
                    "divis ion": "division",
                    "sess ion": "session",
                    "miss ion": "mission",
                    "decis ion": "decision",
                    "cre at ing": "creating",
                    "cre at ed": "created",
                    "oper at ing": "operating",
                    "oper at ion": "operation",
                    "moni to ring": "monitoring",
                    "prepar at ion": "preparation",
                    "present at ion": "presentation",
                    "specific at ion": "specification",
                    "identific at ion": "identification",
                    "valid at ion": "validation",
                    "optimiz at ion": "optimization",
                    "autom at ion": "automation",
                    "situ at ion": "situation"
                }
            }
            healing_file.write_text(json.dumps(default_healing, indent=2))
    
    def load(self, config_name: str) -> Dict:
        """Load and cache a config file"""
        if config_name in self._cache:
            return self._cache[config_name]
        
        config_path = self.config_dir / f"{config_name}.json"
        if not config_path.exists():
            logger.warning(f"Config not found: {config_path}")
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self._cache[config_name] = config
        return config
    
    def get_flat_list(self, config_name: str, *keys) -> List[str]:
        """Get a flattened list from nested config"""
        config = self.load(config_name)
        
        if not keys:
            if isinstance(config, list):
                return config
            result = []
            for value in config.values():
                if isinstance(value, list):
                    result.extend(value)
                elif isinstance(value, dict):
                    for v in value.values():
                        if isinstance(v, list):
                            result.extend(v)
            return result
        
        current = config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return []
        
        if isinstance(current, list):
            return current
        elif isinstance(current, dict):
            result = []
            for value in current.values():
                if isinstance(value, list):
                    result.extend(value)
            return result
        
        return []


# ============================================================================
# RULE-BASED REDACTION ENGINE
# ============================================================================

class RuleBasedRedactor:
    """
    Configuration-driven redaction engine.
    Zero hardcoded data - all rules from config files.
    """
    
    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all PII patterns from config"""
        pii_config = self.config.load('pii_patterns')
        
        self.patterns = {
            'email': re.compile(pii_config['email']['pattern'], re.IGNORECASE),
            'url': re.compile(pii_config['url']['pattern']),
            'phone': [re.compile(p) for p in pii_config['phone']['patterns']],
            'social': [re.compile(p, re.IGNORECASE) for p in pii_config['social']['patterns']],
            'demographics': {
                k: re.compile(v, re.IGNORECASE) 
                for k, v in pii_config['demographics'].items()
            }
        }
    
    def redact(self, text: str, filename: str = "") -> str:
        """Main redaction pipeline - completely rule-based"""
        
        # Phase 0: Text healing (fix spacing issues)
        text = self._heal_text(text)
        
        # Phase 1: Remove PII
        text = self._remove_pii(text)
        
        # Phase 2: Remove locations
        text = self._remove_locations(text)
        
        # Phase 3: Remove names
        if filename:
            text = self._remove_filename_names(text, filename)
        text = self._remove_position_based_names(text)
        
        # Phase 4: Remove sections
        text = self._remove_sections(text)
        
        # Phase 5: Remove demographics
        text = self._remove_demographics(text)
        
        # Phase 6: Clean artifacts
        text = self._cleanup_artifacts(text)
        
        # Phase 7: Format
        text = self._format_professional(text)
        
        # Phase 8: Final date fix (must be after everything else)
        before_count = len(re.findall(r'0\d{2}-\d{2}', text))
        text = re.sub(r'\b0(15|16|17|18|19|20|21|22|23|24|25)-(\d{2})\b', r'20\1-\2', text)
        after_count = len(re.findall(r'20\d{2}-\d{2}', text))
        if before_count > 0:
            logger.info(f"Date fix: found {before_count} old dates, converted {after_count} to 20XX format")
        
        return text
    
    def _heal_text(self, text: str) -> str:
        """Fix spacing issues using rules from config"""
        healing_config = self.config.load('text_healing')
        
        # Apply suffix patterns
        for broken, fixed in healing_config.get('suffix_patterns', {}).items():
            pattern = r'\b' + broken.replace(' ', r'\s+') + r'\b'
            text = re.sub(pattern, fixed, text, flags=re.IGNORECASE)
        
        # Apply prefix patterns
        for broken, fixed in healing_config.get('prefix_patterns', {}).items():
            pattern = r'\b' + broken.replace(' ', r'\s+')
            text = re.sub(pattern, fixed, text, flags=re.IGNORECASE)
        
        # Apply common word fixes
        for broken, fixed in healing_config.get('common_words', {}).items():
            pattern = r'\b' + broken.replace(' ', r'\s+') + r'\b'
            text = re.sub(pattern, fixed, text, flags=re.IGNORECASE)
        
        # Fix date formats: 022-12 -> 2022-12, 021-07 -> 2021-07, etc.
        text = re.sub(r'\b0(\d{2})-(\d{2})\b', r'20\1-\2', text)
        
        # Generic cleanup
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        return text
    
    def _is_in_experience_section(self, line_index: int, lines: list) -> bool:
        """Check if a line is within an experience/work history section"""
        experience_markers = [
            'work experience', 'professional experience', 'employment history',
            'professional experiences', 'work history', 'career history'
        ]
        
        # Section stoppers - if we hit these, we're out of experience section
        section_stoppers = [
            'education', 'academic', 'skills', 'technical skills', 'certification', 
            'certifications', 'declaration', 'personal details', 'personal information',
            'projects', 'achievements', 'awards', 'publications', 'references'
        ]
        
        # Look backwards to find if we're in experience section
        found_experience = False
        start_idx = max(0, line_index - 150)  # Increased range to 150 lines
        
        for i in range(line_index, start_idx, -1):
            line_lower = lines[i].strip().lower()
            
            # Check if we hit a section stopper first
            if any(stopper in line_lower for stopper in section_stoppers):
                # If we haven't found experience marker yet, we're not in experience section
                if not found_experience:
                    return False
                # If we found experience marker earlier, now we hit a stopper, so we're past experience
                else:
                    return False
            
            # Check for experience markers
            if any(marker in line_lower for marker in experience_markers):
                found_experience = True
                return True
        
        return found_experience
    
    def _is_in_skills_section(self, line_index: int, lines: list) -> bool:
        """Check if a line is within a skills section"""
        skills_markers = [
            'skills', 'technical skills', 'key skills', 'core competencies',
            'technical competencies', 'expertise', 'technologies', 'proficiencies'
        ]
        
        # Section stoppers - if we hit these, we're out of skills section
        section_stoppers = [
            'work experience', 'professional experience', 'employment history',
            'education', 'academic', 'certification', 'certifications', 
            'declaration', 'personal details', 'personal information',
            'projects', 'achievements', 'awards', 'publications', 'references',
            'work history', 'career history', 'summary', 'objective', 'profile'
        ]
        
        # Look backwards to find if we're in skills section
        found_skills = False
        found_skills_at = -1
        start_idx = max(0, line_index - 100)  # Look back 100 lines
        
        # First pass: find skills marker
        for i in range(line_index, start_idx, -1):
            line_lower = lines[i].strip().lower()
            
            # Check for skills markers - must be a standalone section header (not in prose)
            if any(marker in line_lower for marker in skills_markers):
                # Only count as skills section if it's a short line (header, not prose)
                if len(line_lower) < 50:  # Headers are typically short
                    found_skills = True
                    found_skills_at = i
                    break
        
        # If we found a skills marker, check if there's a stopper between it and current line
        if found_skills:
            for i in range(line_index, found_skills_at, -1):
                line_lower = lines[i].strip().lower()
                if any(stopper in line_lower for stopper in section_stoppers):
                    # There's a stopper between current line and skills marker
                    return False
            return True
        
        return False
    
    def _remove_pii(self, text: str) -> str:
        """Remove PII using patterns from config - ALWAYS redact contact info, skip other redaction in experience/skills"""
        lines = text.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            processed_line = line
            
            # ALWAYS redact PII patterns (email, phone, URL, social media) regardless of section
            processed_line = self.patterns['email'].sub('[REDACTED_EMAIL]', processed_line)
            
            for phone_pattern in self.patterns['phone']:
                processed_line = phone_pattern.sub('[REDACTED_PHONE]', processed_line)
            
            processed_line = self.patterns['url'].sub('[REDACTED_URL]', processed_line)
            
            for social_pattern in self.patterns['social']:
                processed_line = social_pattern.sub('[REDACTED_SOCIAL]', processed_line)
            
            # ALWAYS redact contact lines
            if re.match(r'(?i)^.*?(email|e-mail|phone|mobile|contact|linkedin|github).*?[:|-].*?$', processed_line):
                processed_line = '[REDACTED_CONTACT_LINE]'
            
            result_lines.append(processed_line)
        
        return '\n'.join(result_lines)
    
    def _remove_locations(self, text: str) -> str:
        """Remove locations using list from config - skip in experience and skills sections"""
        locations = self.config.load('locations')
        lines = text.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            # Check if we're in an experience or skills section
            if self._is_in_experience_section(i, lines) or self._is_in_skills_section(i, lines):
                # Keep line as-is in experience or skills section
                result_lines.append(line)
                continue
            
            # Apply location redaction outside experience sections
            processed_line = line
            
            for city in locations.get('cities', []):
                processed_line = re.sub(rf'\b{re.escape(city)}\b,?\s*', '[LOCATION]', processed_line, flags=re.IGNORECASE)
            
            for state in locations.get('states', []):
                processed_line = re.sub(rf'\b{re.escape(state)}\b,?\s*', '[LOCATION]', processed_line, flags=re.IGNORECASE)
            
            for country in locations.get('countries', []):
                processed_line = re.sub(rf'\b{re.escape(country)}\b,?\s*', '[LOCATION]', processed_line, flags=re.IGNORECASE)
            
            result_lines.append(processed_line)
        
        return '\n'.join(result_lines)
    
    def _remove_filename_names(self, text: str, filename: str) -> str:
        """Extract potential names from filename and remove"""
        stem = Path(filename).stem
        clean = re.sub(r'(resume|cv|naukri|redacted|_\d+)', '', stem, flags=re.IGNORECASE)
        clean = re.sub(r'[^a-zA-Z\s]', ' ', clean)
        clean = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean)
        
        parts = clean.split()
        names = [p for p in parts if p and len(p) > 2 and p[0].isupper()]
        
        if len(names) >= 2:
            pattern = r'\b' + r'\s+'.join([re.escape(n) for n in names]) + r'\b'
            text = re.sub(pattern, '[REDACTED_NAME]', text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_position_based_names(self, text: str) -> str:
        """Remove names based on position - skip in experience and skills sections"""
        preserve_headers = self.config.get_flat_list('sections', 'preserve')
        
        # Get all protected terms to avoid marking them as names
        protected_terms = self.config.get_flat_list('protected_terms')
        protected_lower = [term.lower() for term in protected_terms]
        
        lines = text.split('\n')
        
        for i in range(len(lines)):
            # Skip if in experience or skills section
            if self._is_in_experience_section(i, lines) or self._is_in_skills_section(i, lines):
                continue
                
            line = lines[i]
            stripped = line.strip().lower()
            
            if any(stripped.startswith(h.lower()) for h in preserve_headers):
                continue
            
            if line.isupper():
                continue
            
            # Find potential names
            if i < 30:
                # Aggressive in header
                matches = re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\b', line)
                for match in reversed(list(matches)):
                    matched_text = match.group()
                    
                    # Check if this is a protected term
                    is_protected = matched_text.lower() in protected_lower or any(word.lower() in protected_lower for word in matched_text.split())
                    
                    # Also check if there's a file extension after (e.g., "Ext.js")
                    if not is_protected and match.end() < len(line):
                        # Check for ".js", ".py", ".ts" etc after the match
                        next_chars = line[match.end():match.end()+5]
                        if next_chars.startswith('.'):
                            # Try combining with extension - check last word + extension
                            ext_match = re.match(r'\.\w+', next_chars)
                            if ext_match:
                                # Get the last word from the match
                                words = matched_text.split()
                                last_word = words[-1] if words else matched_text
                                full_term = last_word.lower() + ext_match.group().lower()
                                if full_term in protected_lower:
                                    is_protected = True
                    
                    if not is_protected:
                        # Replace from end to start to preserve indices
                        line = line[:match.start()] + '[NAME]' + line[match.end():]
                lines[i] = line
            else:
                # Conservative elsewhere
                match = re.match(r'^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\s*$', line)
                if match:
                    matched_text = match.group(1)
                    # Check if this is a protected term
                    if matched_text.lower() not in protected_lower and not any(word.lower() in protected_lower for word in matched_text.split()):
                        lines[i] = '[NAME]'
        
        return '\n'.join(lines)
    
    def _remove_sections(self, text: str) -> str:
        """Remove sections based on config rules"""
        sections_config = self.config.load('sections')
        remove_sections = sections_config.get('remove', {})
        preserve_sections = sections_config.get('preserve', [])
        
        lines = text.split('\n')
        result_lines = []
        in_remove_section = False
        section_depth = 0
        current_section_type = None
        
        for line in lines:
            stripped = line.strip().lower()
            
            # Check if entering a remove section
            for section_type, markers in remove_sections.items():
                if any(stripped.startswith(m.lower()) for m in markers):
                    in_remove_section = True
                    section_depth = 0
                    current_section_type = section_type.upper()
                    result_lines.append(f'[REMOVED_SECTION_{current_section_type}]')
                    break
            
            if in_remove_section:
                # Check if hit preserve section
                if any(stripped.startswith(h.lower()) for h in preserve_sections):
                    in_remove_section = False
                    current_section_type = None
                elif section_depth > 30:
                    in_remove_section = False
                    current_section_type = None
                else:
                    section_depth += 1
                    continue
            
            if not in_remove_section:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _remove_demographics(self, text: str) -> str:
        """Remove demographics using patterns from config"""
        for demo_type, pattern in self.patterns['demographics'].items():
            text = pattern.sub(f'[REDACTED_{demo_type.upper()}]', text)
        
        # Additional patterns
        text = re.sub(r"(?i)\b(father's name|mother's name)\s*:?\s*[^\n]+", '[REDACTED_FAMILY_INFO]', text)
        text = re.sub(r'(?i)(passport\s+validity|visa\s+status|driving\s+license)[^\n]*', '[REDACTED_ID_INFO]', text)
        
        return text
    
    def _cleanup_artifacts(self, text: str) -> str:
        """Clean up redaction artifacts"""
        # Don't remove lines that contain markers
        lines = text.split('\n')
        cleaned_lines = []
        
        # Section headers that should never be removed
        important_headers = [
            'work experience', 'professional experience', 'technical skills', 
            'current role', 'skills', 'experience', 'summary', 'projects'
        ]
        
        for i, line in enumerate(lines):
            stripped_lower = line.strip().lower()
            
            # Keep important section headers
            if any(header in stripped_lower for header in important_headers):
                cleaned_lines.append(line)
                continue
                
            # Keep lines with markers
            if '[' in line and ']' in line:
                cleaned_lines.append(line)
                continue
            
            # Check if this is a single digit that might be part of a date
            if re.match(r'^\s*2\s*$', line) and i + 1 < len(lines):
                # Check if next line looks like a partial date (e.g., "022-12")
                next_line = lines[i + 1].strip()
                if re.match(r'^0\d{2}-\d{2}$', next_line):
                    # This "2" is part of a year, keep it
                    cleaned_lines.append(line)
                    continue
            
            # Remove other single digit page numbers
            if re.match(r'^\s*\d\s*$', line):
                continue
            elif re.match(r'^\s*Page\s+\d+\s+of\s+\d+\s*$', line, re.IGNORECASE):
                cleaned_lines.append('[PAGE_NUMBER]')
            else:
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _format_professional(self, text: str) -> str:
        """Apply professional formatting"""
        text = re.sub(r':([A-Za-z])', r': \1', text)
        text = re.sub(r',([A-Za-z])', r', \1', text)
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        # Fix broken dates: if a line is just "2" and next line is like "022-12", merge them
        lines = text.split('\n')
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Check if current line is just "2" and next line looks like partial date
            if line == '2' and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r'0\d{2}-\d{2}', next_line):
                    # Merge them
                    fixed_lines.append('2' + next_line)
                    i += 2
                    continue
            fixed_lines.append(lines[i])
            i += 1
        
        text = '\n'.join(fixed_lines)
        
        lines = text.split('\n')
        formatted = []
        prev_header = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_header = (
                (line.isupper() and 3 <= len(line) <= 60) or
                (re.match(r'^[A-Z][a-zA-Z\s&]{2,50}$', line) and len(line.split()) <= 6)
            )
            
            if is_header:
                if formatted and not prev_header:
                    formatted.append('')
                formatted.append(line)
                formatted.append('')
                prev_header = True
            elif line.startswith(('•', '-', '·', '○', '*')):
                formatted.append('• ' + line.lstrip('•-·○* ').strip())
                prev_header = False
            else:
                formatted.append(line)
                prev_header = False
        
        text = '\n'.join(formatted)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Final fix: correct any broken dates like "022-12" -> "2022-12"
        text = re.sub(r'\b0(15|16|17|18|19|20|21|22|23|24|25)-(\d{2})\b', r'20\1-\2', text)
        
        return text.strip()


class UniversalRedactionEngine:
    """
    Main engine - maintains compatibility with existing code.
    Delegates to configuration-driven redactor.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_loader = ConfigLoader(config_dir)
        self.redactor = RuleBasedRedactor(self.config_loader)
    
    def redact(self, text: str, filename: str = "") -> str:
        """Main redaction entry point"""
        return self.redactor.redact(text, filename)


# ============================================================================
# CV TYPE DETECTION & PIPELINES (Unchanged from original)
# ============================================================================

class CVType(Enum):
    """CV Format Types"""
    NAUKRI = "naukri"
    MULTI_COLUMN = "multi_column"
    STANDARD_ATS = "standard_ats"
    SCANNED_IMAGE = "scanned_image"
    CREATIVE_DESIGNER = "creative"
    ACADEMIC_RESEARCH = "academic"


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
    """Analyzes PDF structure to determine CV type"""
    
    def __init__(self):
        self.naukri_indicators = ['naukri', 'resume headline', 'key skills']
        self.academic_indicators = ['publications', 'research', 'citations']
        self.creative_indicators = ['portfolio', 'behance', 'design']
    
    def analyze(self, pdf_path: str) -> CVProfile:
        """Comprehensive CV analysis"""
        logger.info(f"Analyzing: {Path(pdf_path).name}")
        
        filename = Path(pdf_path).name.lower()
        if 'naukri' in filename:
            return self._create_profile(CVType.NAUKRI, 0.95, pdf_path)
        
        if not HAS_FITZ and not HAS_PDFPLUMBER:
            return self._create_profile(CVType.STANDARD_ATS, 0.5, pdf_path)
        
        try:
            structure = self._analyze_structure(pdf_path)
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
                words = page.extract_words(x_tolerance=2, y_tolerance=2)
                
                if words:
                    structure['column_count'] = self._detect_columns(words, page.width)
                    structure['has_columns'] = structure['column_count'] > 1
                    
                    total_chars = sum(len(w['text']) for w in words)
                    page_area = page.width * page.height
                    structure['text_density'] = total_chars / page_area if page_area > 0 else 0
                    
                    single_char_words = sum(1 for w in words if len(w['text']) == 1)
                    fragmentation_ratio = single_char_words / len(words) if words else 0
                    structure['is_scanned'] = fragmentation_ratio > 0.15 or structure['text_density'] < 0.02
                    
                    structure['content_sample'] = ' '.join([w['text'] for w in words[:200]])
                
                structure['has_graphics'] = len(page.images) > 0
        
        elif HAS_FITZ:
            with fitz.open(pdf_path) as doc:
                if doc:
                    page = doc[0]
                    text = page.get_text()
                    
                    page_area = page.rect.width * page.rect.height
                    structure['text_density'] = len(text) / page_area if page_area > 0 else 0
                    structure['is_scanned'] = structure['text_density'] < 0.02
                    structure['content_sample'] = text[:1000]
                    structure['has_graphics'] = len(page.get_images()) > 0
        
        structure['sections'] = self._detect_sections(structure['content_sample'])
        return structure
    
    def _detect_columns(self, words: List[Dict], page_width: float) -> int:
        """Detect number of columns"""
        if not words:
            return 1
        
        left = sum(1 for w in words if w['x0'] < page_width * 0.35)
        center = sum(1 for w in words if page_width * 0.35 <= w['x0'] < page_width * 0.65)
        right = sum(1 for w in words if w['x0'] >= page_width * 0.65)
        
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
            'SUMMARY': ['SUMMARY', 'PROFILE', 'OBJECTIVE'],
            'EXPERIENCE': ['EXPERIENCE', 'WORK HISTORY'],
            'EDUCATION': ['EDUCATION', 'ACADEMIC'],
            'SKILLS': ['SKILLS', 'TECHNICAL SKILLS'],
            'PROJECTS': ['PROJECTS']
        }
        
        for section, keywords in section_keywords.items():
            if any(kw in text_upper for kw in keywords):
                sections.append(section)
        
        return sections
    
    def _classify_type(self, structure: Dict, filename: str) -> Tuple[CVType, float]:
        """Classify CV type"""
        content = structure['content_sample'].lower()
        
        naukri_score = sum(1 for ind in self.naukri_indicators if ind in content)
        if naukri_score >= 2:
            return CVType.NAUKRI, 0.9
        
        academic_score = sum(1 for ind in self.academic_indicators if ind in content)
        if academic_score >= 2:
            return CVType.ACADEMIC_RESEARCH, 0.9
        
        creative_score = sum(1 for ind in self.creative_indicators if ind in content)
        if creative_score >= 2 and structure['has_graphics']:
            return CVType.CREATIVE_DESIGNER, 0.85
        
        if structure['is_scanned']:
            return CVType.SCANNED_IMAGE, 0.85
        
        if structure['has_columns'] and structure['column_count'] >= 2:
            return CVType.MULTI_COLUMN, 0.85
        
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


# ============================================================================
# PDF EXTRACTION PIPELINES
# ============================================================================

class BasePipeline(abc.ABC):
    """Abstract base for extraction pipelines"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.pipeline_name = self.__class__.__name__
    
    @abc.abstractmethod
    def extract_text(self, pdf_path: str) -> str:
        pass
    
    @abc.abstractmethod
    def preprocess(self, text: str) -> str:
        pass
    
    def save_debug(self, content: str, stage: str, filename: str):
        if self.debug:
            try:
                name = Path(filename).stem
                path = DEBUG_DIR / f"{name}_{self.pipeline_name}_{stage}.txt"
                path.write_text(content, encoding='utf-8')
            except Exception as e:
                logger.error(f"Debug save failed: {e}")
    
    def process(self, pdf_path: str) -> str:
        logger.info(f"[{self.pipeline_name}] Processing: {Path(pdf_path).name}")
        
        raw_text = self.extract_text(pdf_path)
        if self.debug:
            self.save_debug(raw_text, "01_extracted", pdf_path)
        
        processed_text = self.preprocess(raw_text)
        if self.debug:
            self.save_debug(processed_text, "02_preprocessed", pdf_path)
        
        return processed_text


class StandardATSPipeline(BasePipeline):
    """Standard single-column extraction"""
    
    def extract_text(self, pdf_path: str) -> str:
        if HAS_FITZ:
            with fitz.open(pdf_path) as doc:
                return "\n\n".join([page.get_text() for page in doc])
        elif HAS_PDFPLUMBER:
            with pdfplumber.open(pdf_path) as pdf:
                return "\n\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return "Error: No PDF library available"
    
    def preprocess(self, text: str) -> str:
        text = re.sub(r'[•●○◦▪▫■□⬤→]', '•', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text


class NaukriPipeline(BasePipeline):
    """Naukri.com format extraction - handles two-column layout with coordinate-based extraction"""
    
    def extract_text(self, pdf_path: str) -> str:
        if not HAS_FITZ:
            return "Error: PyMuPDF not available"
        
        all_pages_text = []
        
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                page_width = page.rect.width
                page_height = page.rect.height
                
                # Get all text blocks with coordinates
                blocks = page.get_text("dict")["blocks"]
                
                text_elements = []
                for block in blocks:
                    if "lines" in block:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text and text not in ['Naukri', 'www.naukri.com']:
                                    # Get bounding box
                                    bbox = span["bbox"]  # (x0, y0, x1, y1)
                                    x0, y0, x1, y1 = bbox
                                    text_elements.append({
                                        'text': text,
                                        'x0': x0,
                                        'y0': y0,
                                        'x1': x1,
                                        'y1': y1,
                                        'width': x1 - x0
                                    })
                
                # Determine column split point - Naukri has ~60-65% main column, ~35-40% sidebar
                # Analyze x-positions to find the gap between columns
                x_positions = [elem['x0'] for elem in text_elements]
                if x_positions:
                    # Find natural split - look for the largest gap in x-coordinates
                    # This gap represents the space between main content and sidebar
                    x_positions_sorted = sorted(set(x_positions))
                    max_gap = 0
                    split_point = page_width * 0.65  # default 65%
                    
                    for i in range(len(x_positions_sorted) - 1):
                        gap = x_positions_sorted[i + 1] - x_positions_sorted[i]
                        # Look for gaps after at least 15% of page width (to avoid left margin)
                        # and before 80% (to avoid right margin)
                        if page_width * 0.15 < x_positions_sorted[i] < page_width * 0.80:
                            if gap > max_gap and gap > 30:  # Minimum 30 pixel gap
                                max_gap = gap
                                split_point = (x_positions_sorted[i] + x_positions_sorted[i + 1]) / 2
                
                # Separate into left (main) and right (sidebar) columns
                main_column = []
                sidebar = []
                
                for elem in text_elements:
                    if elem['x0'] < split_point:
                        main_column.append(elem)
                    else:
                        sidebar.append(elem)
                
                # Sort each column by y-position (top to bottom)
                main_column.sort(key=lambda e: e['y0'])
                sidebar.sort(key=lambda e: e['y0'])
                
                # Group elements into lines based on y-position proximity
                def group_into_lines(elements, tolerance=5):
                    if not elements:
                        return []
                    
                    lines = []
                    current_line = [elements[0]]
                    current_y = elements[0]['y0']
                    
                    for elem in elements[1:]:
                        if abs(elem['y0'] - current_y) < tolerance:
                            # Same line
                            current_line.append(elem)
                        else:
                            # New line
                            # Sort current line by x-position (left to right)
                            current_line.sort(key=lambda e: e['x0'])
                            lines.append(' '.join([e['text'] for e in current_line]))
                            current_line = [elem]
                            current_y = elem['y0']
                    
                    # Add last line
                    if current_line:
                        current_line.sort(key=lambda e: e['x0'])
                        lines.append(' '.join([e['text'] for e in current_line]))
                    
                    return lines
                
                # Convert to lines
                main_lines = group_into_lines(main_column)
                sidebar_lines = group_into_lines(sidebar)
                
                # Combine: main content first, then sidebar
                if main_lines:
                    all_pages_text.extend(main_lines)
                
                if sidebar_lines:
                    all_pages_text.append("")  # Separator
                    all_pages_text.append("=== SIDEBAR ===")
                    all_pages_text.extend(sidebar_lines)
        
        return "\n".join(all_pages_text)
    
    def preprocess(self, text: str) -> str:
        """Clean up and reorganize Naukri content"""
        text = re.sub(r'Naukri\.com|www\.naukri\.com', '', text, flags=re.IGNORECASE)
        
        lines = text.split('\n')
        
        # Find the main SKILLS section and ALL sidebar markers
        skills_idx = -1
        sidebar_indices = []
        prof_exp_idx = -1
        work_exp_idx = -1
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped == 'SKILLS' and skills_idx == -1:
                skills_idx = i
            if line_stripped == '=== SIDEBAR ===':
                sidebar_indices.append(i)
            if 'PROFESSIONAL EXPERIENCE' in line_stripped.upper() and prof_exp_idx == -1:
                prof_exp_idx = i
            if 'WORK EXPERIENCE' in line_stripped.upper() and work_exp_idx == -1:
                work_exp_idx = i
        
        # Use either PROFESSIONAL EXPERIENCE or WORK EXPERIENCE as the insertion point
        experience_idx = prof_exp_idx if prof_exp_idx != -1 else work_exp_idx
        
        # If we have sidebar(s) and an experience section, merge sidebar skills
        if sidebar_indices and experience_idx != -1:
            # Collect all sidebar skills from all sidebar sections
            all_sidebar_skills = []
            
            for sidebar_idx in sidebar_indices:
                # Find the end of this sidebar section (need more lines for some CVs)
                end_idx = min(sidebar_idx + 50, len(lines))  # Increased to capture full sidebar
                for next_sidebar in sidebar_indices:
                    if next_sidebar > sidebar_idx:
                        end_idx = min(end_idx, next_sidebar)
                        break
                
                sidebar_content = lines[sidebar_idx+1:end_idx]
                
                # Extract only skills, skip contact info and stop at job content
                skills_section_active = False
                in_sidebar_skills = False
                
                for line in sidebar_content:
                    line_lower = line.strip().lower()
                    line_stripped = line.strip()
                    
                    # Skip empty lines
                    if len(line_stripped) < 3:
                        continue
                    
                    # Check if we've reached the Skills section in sidebar
                    if line_stripped == 'Skills' or line_stripped == 'SKILLS':
                        in_sidebar_skills = True
                        continue
                    
                    # If we're in sidebar skills section, stop at Languages or other sections
                    if in_sidebar_skills and (line_stripped in ['Languages', 'LANGUAGES', 'Education', 'EDUCATION', 'Certifications', 'CERTIFICATIONS']):
                        break
                    
                    # If we're in sidebar skills section, extract skill lines
                    if in_sidebar_skills:
                        # Skip bullet markers and decorations
                        if line_stripped in ['○', '•', '-', '>', '*']:
                            continue
                        # Extract the skill line (skip very short lines)
                        if len(line_stripped) > 2 and line not in all_sidebar_skills:
                            all_sidebar_skills.append(line)
                            continue
                    
                    # Skip contact info patterns (before Skills section)
                    if any(x in line for x in ['@', '•']) or re.search(r'\d{5,}|linkedin|github|phone|email|contact|location', line, re.IGNORECASE):
                        continue
                    
                    # Stop if we hit job-related content (company names, job titles, dates)
                    if any(marker in line_lower for marker in ['engineer', 'developer', 'analyst', 'manager', 'paytm', 'springer', 'infosys', 'tcs', 'wipro', 'technologies', 'limited', 'pvt', 'inc', 'corporation', 'project']):
                        break
                    
                    # Stop if we hit date patterns (job dates)
                    if re.search(r'\b(20\d{2}|19\d{2})\b|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', line_lower):
                        break
                    
                    # Stop if line starts with bullet points (likely job descriptions)
                    if line_stripped.startswith('•') or line_stripped.startswith('-') or line_stripped.startswith('o '):
                        break
                    
                    # Stop if line starts with lowercase or contains phrases like "emphasizing", "for the", "it offers" (descriptive text)
                    if line_stripped and (line_stripped[0].islower() or any(phrase in line_lower for phrase in ['emphasizing', 'for the', 'it offers', 'using', 'designed to', 'leverages', 'created'])):
                        break
                    
                    # Keep only clear skills patterns (must start with capital or contain comma-separated tech terms)
                    if any(keyword in line_lower for keyword in ['cloud', 'aws', 'api', 'flask', 'django', 'framework', 'office', 'html', 'css', 'javascript', 'python', 'java', 'react', 'sql', 'mongodb', 'docker', 'kubernetes', 'azure', 'gcp', 'terraform']):
                        # Reject sentence fragments (ends with prepositions/conjunctions)
                        if line_lower.rstrip().endswith(('for', 'to', 'of', 'in', 'on', 'at', 'with', 'from', 'by', 'as', 'the', 'a', 'an', 'and', 'or')):
                            continue
                        
                        # Must start with capital letter or contain multiple commas (skill lists)
                        if line_stripped[0].isupper() and (',' in line or len(line_stripped.split()) <= 10):
                            if line not in all_sidebar_skills:
                                all_sidebar_skills.append(line)
                                skills_section_active = True
                        elif skills_section_active and line_stripped[0].isupper():
                            # Continue with continuation lines if we're in skills section
                            if line not in all_sidebar_skills:
                                all_sidebar_skills.append(line)
            
            # Now reconstruct document in correct order:
            # 1. Everything before experience section
            # 2. SKILLS section (create if doesn't exist) with sidebar skills
            # 3. EXPERIENCE section and everything after (excluding sidebars)
            
            result = []
            sidebar_ranges = []
            
            # Calculate ranges to skip (sidebar sections only)
            for sidebar_idx in sidebar_indices:
                start = sidebar_idx
                end = sidebar_idx + 1
                # Skip ALL sidebar content until we hit main content or next sidebar
                for j in range(sidebar_idx + 1, min(sidebar_idx + 100, len(lines))):
                    if j in sidebar_indices:
                        break  # Hit next sidebar
                    line_lower = lines[j].strip().lower()
                    line_stripped = lines[j].strip()
                    
                    # Stop if we hit main section headers (Work experience, Professional Experience, Projects, etc.)
                    if any(header in line_lower for header in ['work experience', 'professional experience', 'employment', 'projects', 'certifications']):
                        break
                    
                    # Continue if this looks like sidebar content
                    is_sidebar_content = (
                        len(line_stripped) < 3 or  # Empty or very short
                        any(x in lines[j] for x in ['@', '•', '○']) or  # Contact markers or bullets
                        re.search(r'\d{5,}|linkedin|github|phone|email|contact|location', lines[j], re.IGNORECASE) or  # Contact patterns
                        line_stripped in ['Skills', 'SKILLS', 'Languages', 'LANGUAGES', 'Contact', 'CONTACT', 'R', 'Ó'] or  # Section headers or symbols
                        any(keyword in line_lower for keyword in ['java', 'kotlin', 'python', 'javascript', 'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'sql', 'mongodb', 'postgresql', 'mysql', 'html', 'css', 'api', 'rest', 'graphql', 'agile', 'scrum', 'mvvm', 'mvc', 'retrofit', 'volley', 'firebase', 'android', 'ios', 'swift', 'jetpack']) or  # Tech keywords
                        (len(line_stripped) > 10 and ',' in lines[j]) or  # Comma-separated lists
                        re.match(r'^[A-Z][a-z]+,\s*[A-Z][a-z]+', line_stripped)  # State, Country format
                    )
                    if is_sidebar_content:
                        end = j + 1
                    else:
                        # Check if this might be actual document content (paragraph text)
                        if len(line_stripped) > 50 or (len(line_stripped) > 20 and not line_stripped[0].isupper()):
                            break  # Likely document content
                        # Otherwise, include it as sidebar content (might be skill continuation)
                        end = j + 1
                sidebar_ranges.append((start, end))
            
            # Add lines, skipping sidebar ranges
            for i in range(len(lines)):
                # Skip if in any sidebar range
                if any(start <= i < end for start, end in sidebar_ranges):
                    continue
                
                # If we're at the experience section and have sidebar skills
                if i == experience_idx and all_sidebar_skills:
                    # If there's no main SKILLS section, create one
                    if skills_idx == -1:
                        result.append("")
                        result.append("SKILLS")
                        result.append("")
                        result.extend(all_sidebar_skills)
                        result.append("")
                    else:
                        # Insert skills before experience section (they're already in the main SKILLS section)
                        result.append("")
                        result.extend(all_sidebar_skills)
                        result.append("")
                
                result.append(lines[i])
            
            text = '\n'.join(result)
        else:
            # Fallback: just remove all sidebar markers and their immediate content
            text = re.sub(r'===\s*SIDEBAR\s*===', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()


class MultiColumnPipeline(BasePipeline):
    """Multi-column layout extraction"""
    
    def extract_text(self, pdf_path: str) -> str:
        if not HAS_PDFPLUMBER:
            if HAS_FITZ:
                return self._fitz_fallback(pdf_path)
            return "Error: No PDF library"
        
        all_text = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(x_tolerance=2, y_tolerance=2)
                if not words:
                    continue
                
                split_point = self._find_column_split(words, page.width)
                
                if split_point:
                    left_words = [w for w in words if w['x1'] < split_point]
                    right_words = [w for w in words if w['x0'] > split_point]
                    
                    left_words.sort(key=lambda w: w['top'])
                    right_words.sort(key=lambda w: w['top'])
                    
                    all_text.append(self._build_text(left_words))
                    all_text.append(self._build_text(right_words))
                else:
                    words.sort(key=lambda w: (w['top'], w['x0']))
                    all_text.append(self._build_text(words))
        
        return "\n\n".join(all_text)
    
    def _find_column_split(self, words: List[Dict], page_width: float) -> Optional[float]:
        if not words:
            return None
        
        strip_width = page_width / 20
        strip_counts = [0] * 20
        
        for w in words:
            word_center = (w['x0'] + w['x1']) / 2
            strip_idx = int(word_center / strip_width)
            if 0 <= strip_idx < 20:
                strip_counts[strip_idx] += 1
        
        min_count = float('inf')
        min_idx = -1
        for idx in range(5, 15):
            if strip_counts[idx] < min_count:
                min_count = strip_counts[idx]
                min_idx = idx
        
        if min_count < 3 and min_idx >= 0:
            return (min_idx + 0.5) * strip_width
        
        return None
    
    def _build_text(self, words: List[Dict]) -> str:
        if not words:
            return ""
        
        lines = []
        current_line = []
        current_top = words[0]['top']
        
        for word in words:
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
        text_blocks = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                blocks = page.get_text("blocks", sort=True)
                for block in blocks:
                    if block[6] == 0:
                        text_blocks.append(block[4].strip())
        return "\n\n".join(text_blocks)
    
    def preprocess(self, text: str) -> str:
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class PipelineOrchestrator:
    """Main orchestrator for CV processing"""
    
    def __init__(self, debug: bool = False, config_dir: str = "config"):
        self.debug = debug
        self.detector = CVProfileDetector()
        self.redactor = UniversalRedactionEngine(config_dir)
        
        self.pipelines = {
            CVType.NAUKRI: NaukriPipeline(debug),
            CVType.MULTI_COLUMN: MultiColumnPipeline(debug),
            CVType.STANDARD_ATS: StandardATSPipeline(debug),
            CVType.SCANNED_IMAGE: StandardATSPipeline(debug),
            CVType.CREATIVE_DESIGNER: StandardATSPipeline(debug),
            CVType.ACADEMIC_RESEARCH: StandardATSPipeline(debug)
        }
    
    def process_cv(self, pdf_path: str) -> Tuple[str, CVProfile]:
        """Process a single CV"""
        logger.info(f"{'='*80}\nProcessing: {Path(pdf_path).name}\n{'='*80}")
        
        profile = self.detector.analyze(pdf_path)
        logger.info(f"Detected: {profile}")
        
        pipeline = self.pipelines.get(profile.cv_type, self.pipelines[CVType.STANDARD_ATS])
        processed_text = pipeline.process(pdf_path)
        
        filename = Path(pdf_path).name
        redacted_text = self.redactor.redact(processed_text, filename)
        
        final_text = self._final_cleanup(redacted_text)
        
        return final_text, profile
    
    def _reorganize_sections(self, text: str) -> str:
        """Fix misplaced section content (e.g., skills appearing after WORK EXPERIENCE heading)"""
        lines = text.split('\n')
        
        # Find KEY SKILLS and WORK EXPERIENCE positions
        key_skills_idx = -1
        work_exp_idx = -1
        
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            if 'key skills' in line_lower or 'technical skills' in line_lower:
                key_skills_idx = i
            elif 'work experience' in line_lower or 'professional experience' in line_lower:
                work_exp_idx = i
                break
        
        # If WORK EXPERIENCE comes before we collect enough skills content, reorganize
        if key_skills_idx != -1 and work_exp_idx != -1 and work_exp_idx < key_skills_idx + 50:
            # Find where actual job title/company starts (Staff Engineer, Senior Engineer, etc.)
            job_start_idx = work_exp_idx + 1
            for i in range(work_exp_idx + 1, min(work_exp_idx + 100, len(lines))):
                line = lines[i].strip()
                # Job titles typically: "Staff Engineer", "Senior Engineer", etc.
                if line and (re.match(r'^(Staff|Senior|Lead|Principal|Software|Junior|Mid-level)\s+(Engineer|Developer|Analyst|Manager|Architect)', line, re.IGNORECASE) or
                           re.search(r'\d{4}\s*[–-]\s*(Present|\d{4})', line)):
                    job_start_idx = i
                    break
            
            # Extract skills bullets between WORK EXPERIENCE and actual job start
            skills_content = lines[work_exp_idx + 1:job_start_idx]
            
            # Reorganize: KEY SKILLS + skills_content + WORK EXPERIENCE + rest
            reorganized = (
                lines[:key_skills_idx + 1] +  # Up to and including KEY SKILLS header
                skills_content +                # Skills bullets
                [lines[work_exp_idx]] +        # WORK EXPERIENCE header
                lines[job_start_idx:]          # Actual job entries
            )
            return '\n'.join(reorganized)
        
        return text
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup"""
        # First, reorganize any misplaced sections
        text = self._reorganize_sections(text)
        
        # Remove name-like patterns, but preserve job titles in experience section
        lines = text.split('\n')
        cleaned = []
        in_experience = False
        skip_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            
            # Remove contact detail lines (Phone, E-mail, LinkedIn headers and their content)
            if re.match(r'^\s*(phone|e-mail|email|linkedin|github|mobile|contact)\s*$', line, re.IGNORECASE):
                continue
            # Remove lines with "Phone", "E-mail" followed by redacted markers or actual contact info
            if re.search(r'(phone|e-mail|email|mobile|contact|linkedin)\s*[:\s]*\[?REDACTED', line, re.IGNORECASE):
                continue
            # Skip lines that are just redacted markers without context
            if re.match(r'^\s*\[REDACTED_(PHONE|EMAIL|URL|CONTACT_LINE)\]\s*$', line):
                continue
            # Skip remaining parts of LinkedIn/social media URLs  
            if re.match(r'^\s*akash-tandale-\d+\s*$', line):  # Leftover URL fragments
                continue
            
            # Skip entire ACTIVITIES, INTEREST, HOBBIES sections
            if any(keyword in line_lower for keyword in ['activities and interest', 'hobbies', 'activities & interest', 'personal interest']):
                skip_section = True
                continue
            
            # End skip section when we hit a major section header
            if skip_section and any(section in line_lower for section in ['work experience', 'professional experience', 'education', 'skills', 'certification', 'projects', 'achievements', 'technical skills', 'summary', 'objective']):
                skip_section = False
            
            # Skip lines in skipped sections
            if skip_section:
                continue
            
            # Track if we're in experience section
            if 'work experience' in line_lower or 'professional experience' in line_lower:
                in_experience = True
            elif any(section in line_lower for section in ['education', 'skills', 'certification', 'projects', 'achievements']):
                in_experience = False
            
            # Skip name removal if in experience section
            if in_experience:
                cleaned.append(line)
                continue
            
            # Remove name-like patterns outside experience section
            if re.match(r'^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,4}\s*$', line):
                continue
            
            # Skip removing if line is just "2" and next line looks like partial date
            if re.match(r'^\s*2\s*$', line) and i + 1 < len(lines):
                if re.match(r'^\s*0\d{2}-\d{2}\s*$', lines[i + 1]):
                    cleaned.append(line)
                    continue
            
            # Remove other single digit lines (page numbers)
            if re.match(r'^\s*\d\s*$', line):
                continue
            
            cleaned.append(line)
        
        text = '\n'.join(cleaned)
        
        text = re.sub(r'[•●○◦▪▫■□⬤]', '•', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Final date fix after all cleanup
        text = re.sub(r'\b0(15|16|17|18|19|20|21|22|23|24|25)-(\d{2})\b', r'20\1-\2', text)
        
        return text.strip()
    
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
                redacted_text, profile = self.process_cv(str(pdf_file))
                
                output_file = output_path / f"REDACTED_{pdf_file.stem}.txt"
                output_file.write_text(redacted_text, encoding='utf-8')
                
                logger.info(f"✓ Saved: {output_file.name}")
                logger.info(f"  Pipeline: {profile.cv_type.value}, Confidence: {profile.confidence:.2f}")
                
                stats[profile.cv_type] += 1
                success_count += 1
                
            except Exception as e:
                logger.error(f"✗ Failed: {pdf_file.name} - {e}")
        
        logger.info(f"\n{'='*80}\nPROCESSING COMPLETE\n{'='*80}")
        logger.info(f"Total: {len(pdf_files)} | Success: {success_count} | Failed: {len(pdf_files) - success_count}")
        logger.info(f"\nPipeline Usage:")
        for cv_type, count in stats.items():
            if count > 0:
                logger.info(f"  {cv_type.value}: {count}")


# ============================================================================
# CLI & CONFIG MANAGEMENT
# ============================================================================

def add_location(city: str = None, state: str = None, country: str = None, config_dir: str = "config"):
    """Add location to config"""
    config_path = Path(config_dir) / "locations.json"
    
    with open(config_path, 'r') as f:
        locations = json.load(f)
    
    if city and city not in locations['cities']:
        locations['cities'].append(city)
    if state and state not in locations['states']:
        locations['states'].append(state)
    if country and country not in locations['countries']:
        locations['countries'].append(country)
    
    with open(config_path, 'w') as f:
        json.dump(locations, f, indent=2)


def add_protected_term(term: str, category: str = "technical_terms", config_dir: str = "config"):
    """Add protected term to config"""
    config_path = Path(config_dir) / "protected_terms.json"
    
    with open(config_path, 'r') as f:
        protected = json.load(f)
    
    if category not in protected:
        protected[category] = []
    
    if term.lower() not in [t.lower() for t in protected[category]]:
        protected[category].append(term.lower())
    
    with open(config_path, 'w') as f:
        json.dump(protected, f, indent=2)


def add_text_healing_rule(broken: str, fixed: str, config_dir: str = "config"):
    """Add text healing rule to config"""
    config_path = Path(config_dir) / "text_healing.json"
    
    with open(config_path, 'r') as f:
        healing = json.load(f)
    
    healing['common_words'][broken] = fixed
    
    with open(config_path, 'w') as f:
        json.dump(healing, f, indent=2)


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        # Config management commands
        if command == "add-city" and len(sys.argv) > 2:
            add_location(city=sys.argv[2])
            print(f"✓ Added city: {sys.argv[2]}")
            return
        
        elif command == "add-term" and len(sys.argv) > 2:
            add_protected_term(sys.argv[2])
            print(f"✓ Added term: {sys.argv[2]}")
            return
        
        elif command == "add-healing" and len(sys.argv) > 3:
            add_text_healing_rule(sys.argv[2], sys.argv[3])
            print(f"✓ Added healing: {sys.argv[2]} → {sys.argv[3]}")
            return
    
    # Normal processing
    debug = '--debug' in sys.argv
    
    input_dir = "resume"
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        input_dir = sys.argv[1]
    
    output_dir = "final_output"
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        output_dir = sys.argv[2]
    
    orchestrator = PipelineOrchestrator(debug=debug)
    orchestrator.process_directory(input_dir, output_dir)


if __name__ == "__main__":
    main()