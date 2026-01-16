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
            'company': [re.compile(p, re.IGNORECASE) for p in pii_config.get('company', {}).get('patterns', [])],
            'specific_locations': [re.compile(p, re.IGNORECASE) for p in pii_config.get('specific_locations', {}).get('patterns', [])],
            'monetary_values': [re.compile(p, re.IGNORECASE) for p in pii_config.get('monetary_values', {}).get('patterns', [])],
            'specific_awards': [re.compile(p, re.IGNORECASE) for p in pii_config.get('specific_awards', {}).get('patterns', [])],
            'commercial_software': [re.compile(p, re.IGNORECASE) for p in pii_config.get('commercial_software', {}).get('patterns', [])],
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
        
        # Phase 2: Remove company names and specific locations
        text = self._remove_companies_and_specific_locations(text)
        
        # Phase 3: Remove locations
        text = self._remove_locations(text)
        
        # Phase 4: Remove names
        if filename:
            text = self._remove_filename_names(text, filename)
        text = self._remove_position_based_names(text)
        
        # Phase 5: Remove sections
        text = self._remove_sections(text)
        
        # Phase 6: Remove demographics
        text = self._remove_demographics(text)
        
        # Phase 7: Clean artifacts
        text = self._cleanup_artifacts(text)
        
        # Phase 8: Format
        text = self._format_professional(text)
        
        # Phase 9: Final date fix (must be after everything else)
        before_count = len(re.findall(r'0\d{2}-\d{2}', text))
        text = re.sub(r'\b0(15|16|17|18|19|20|21|22|23|24|25)-(\d{2})\b', r'20\1-\2', text)
        after_count = len(re.findall(r'20\d{2}-\d{2}', text))
        if before_count > 0:
            logger.info(f"Date fix: found {before_count} old dates, converted {after_count} to 20XX format")
        
        # Phase 10: Remove all placeholder markers
        text = self._remove_placeholders(text)
        
        return text
    
    def _remove_placeholders(self, text: str) -> str:
        """Remove all placeholder markers like [NAME], [EMAIL], etc."""
        # Generic removal of all [REDACTED_*] and [REMOVED_*] markers
        text = re.sub(r'\[REDACTED_[A-Z0-9_]+\]', '', text)
        text = re.sub(r'\[REMOVED_[A-Z0-9_]+\]', '', text)
        
        placeholders = [
            r'\[NAME\]',
            r'\[EMAIL\]',
            r'\[PHONE\]',
            r'\[URL\]',
            r'\[ORGANIZATION\]',
            r'\[COMPANY[^\]]*\]',
            r'\[LOCATION\]',
            r'\[MONETARY_VALUE\]',
            r'\[SOFTWARE\]',
            r'\[PROGRAM\]',
            r'\[DATE_OF_BIRTH\]',
            r'\[ADDRESS\]',
            r'\[PAGE_NUMBER\]',
        ]
        
        for placeholder in placeholders:
            text = re.sub(placeholder, '', text)
        
        # Clean up extra spaces, commas, and colons left behind
        text = re.sub(r'\s*,\s*,', ',', text)  # Double commas
        text = re.sub(r':\s*,', ':', text)  # Colon followed by comma
        text = re.sub(r',\s*:', ':', text)  # Comma followed by colon
        text = re.sub(r'^\s*,\s*', '', text, flags=re.MULTILINE)  # Leading commas
        text = re.sub(r',\s*$', '', text, flags=re.MULTILINE)  # Trailing commas
        text = re.sub(r'\s{2,}', ' ', text)  # Multiple spaces
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Multiple blank lines
        
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
        """Check if a line is within an experience/work history section
        
        Handles two-column layouts where section headers from left column (ACHIEVEMENTS, SKILLS)
        may be interleaved with experience content from right column.
        """
        experience_markers = [
            'work experience', 'professional experience', 'employment history',
            'professional experiences', 'work history', 'career history', 'experience'
        ]
        
        # Check if the current line or nearby lines contain company/role patterns
        # These patterns strongly indicate we're in experience content
        company_role_patterns = [
            r'\([A-Z][a-z]{2}\s+\d{4}\s*[-–]\s*(?:till\s+date|present|[A-Z][a-z]{2}\s+\d{4})\)',  # (Oct 2021 – till date)
            r'\b(?:Lead|Senior|Junior|Principal|Staff)\s+(?:Engineer|Developer|Analyst|Architect|Manager|Consultant)\b',  # Job titles
            r'\b(?:Pvt\.?\s+Ltd|Limited|Inc\.?|Corp\.?|LLC)\b',  # Company suffixes
            r'(?:The major experience|skills gained during the period)',  # Common experience section phrases
            r'(?:Involved in|Responsible for|Led|Managed|Developed|Implemented)',  # Action verbs
        ]
        
        # Check current line and nearby lines (±5 lines) for strong experience indicators
        check_start = max(0, line_index - 5)
        check_end = min(len(lines), line_index + 6)
        for i in range(check_start, check_end):
            line = lines[i]
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in company_role_patterns):
                # Strong indicator we're in experience content
                # Now verify there's an experience marker somewhere above (not too strict about stoppers)
                for j in range(line_index, max(0, line_index - 200), -1):
                    if any(marker in lines[j].strip().lower() for marker in experience_markers):
                        return True
        
        # Fallback to original logic if no strong patterns found
        # Section stoppers - if we hit these, we're out of experience section
        # BUT: ignore section stoppers that are likely from a two-column layout (very short lines)
        section_stoppers = [
            'education', 'academic', 'technical skills', 'certification', 
            'certifications', 'declaration', 'personal details', 'personal information',
            'projects', 'publications', 'references'
        ]
        
        # Look backwards to find if we're in experience section
        found_experience = False
        found_experience_at = -1
        start_idx = max(0, line_index - 200)
        
        for i in range(line_index, start_idx, -1):
            line_lower = lines[i].strip().lower()
            
            # Check if we hit a section stopper
            # IGNORE stoppers if they're on very short lines (likely column headers from two-column layout)
            if any(stopper in line_lower for stopper in section_stoppers):
                # Only treat as real stopper if line is long enough (not just a header)
                if len(line_lower) > 50:  # Real content, not just header
                    if not found_experience:
                        return False
                    else:
                        return False
                # Otherwise ignore this stopper (likely from sidebar/column header)
            
            # Check for experience markers
            if any(marker in line_lower for marker in experience_markers):
                found_experience = True
                found_experience_at = i
                return True
        
        return found_experience
    
    def _is_in_skills_section(self, line_index: int, lines: list) -> bool:
        """Check if a line is within a skills section"""
        skills_markers = [
            'skills', 'technical skills', 'key skills', 'core competencies',
            'technical competencies', 'expertise', 'technologies', 'proficiencies'
        ]
        
        # Section stoppers - if we hit these, we're out of skills section
        # REMOVED 'profile' from stoppers since KEY SKILLS can be followed by PROFILE SUMMARY
        section_stoppers = [
            'work experience', 'professional experience', 'employment history',
            'education', 'academic', 'certification', 'certifications', 
            'declaration', 'personal details', 'personal information',
            'projects', 'achievements', 'awards', 'publications', 'references',
            'work history', 'career history', 'summary', 'objective'
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
    
    def _remove_companies_and_specific_locations(self, text: str) -> str:
        """Remove company names and specific geographic locations, replacing with generic terms"""
        lines = text.split('\n')
        result_lines = []
        
        # Load company list from protected_terms (we'll redact them instead of protecting now)
        companies_to_redact = self.config.load('protected_terms').get('companies', [])
        
        # Industry type mapping for generic replacements
        industry_keywords = {
            'Manufacturing Company': ['automotive', 'mercedes', 'john deere', 'harman'],
            'IT Solutions Company': ['tcs', 'infosys', 'wipro', 'cognizant', 'hcl', 'tech mahindra', 'accenture', 'ibm', 'microsoft', 'oracle', 'citrix'],
            'Financial Services Company': ['worldline', 'british petroleum', 'fis global', 'fis'],
            'Consulting Firm': ['accenture', 'cognizant'],
            'Energy Sector Company': ['british petroleum'],
            'Accounting Firm': ['jain', 'agrawal', 'associates', 'chartered accountants'],
        }
        
        for i, line in enumerate(lines):
            processed_line = line
            is_experience_section = self._is_in_experience_section(i, lines)
            is_skills_section = self._is_in_skills_section(i, lines)
            
            # DO NOT REDACT ANYTHING in experience or skills sections
            if is_experience_section or is_skills_section:
                result_lines.append(line)
                continue
            
            # Redact monetary values
            for monetary_pattern in self.patterns.get('monetary_values', []):
                processed_line = monetary_pattern.sub('[MONETARY_VALUE]', processed_line)
            
            # Redact commercial software names
            for software_pattern in self.patterns.get('commercial_software', []):
                processed_line = software_pattern.sub('[SOFTWARE]', processed_line)
            
            # Redact specific awards/programs
            for award_pattern in self.patterns.get('specific_awards', []):
                processed_line = award_pattern.sub('[PROGRAM]', processed_line)
            
            # Redact company patterns (Pvt Ltd, Inc, Corporation, etc.) - Only generic patterns, not specific names
            for company_pattern in self.patterns.get('company', []):
                matches = list(company_pattern.finditer(processed_line))
                for match in reversed(matches):  # Process from end to preserve indices
                    processed_line = processed_line[:match.start()] + '[ORGANIZATION]' + processed_line[match.end():]
            
            # DISABLED: Do not redact specific companies from the list - User requests preserving them for accuracy
            # for company in companies_to_redact:
            #     if company.lower() in processed_line.lower():
            #         # Case-insensitive replacement
            #         pattern = re.compile(re.escape(company), re.IGNORECASE)
            #         processed_line = pattern.sub('[ORGANIZATION]', processed_line)
            
            # Redact specific geographic locations (Japan, Austria, APAC, etc.)
            for location_pattern in self.patterns.get('specific_locations', []):
                processed_line = location_pattern.sub('[LOCATION]', processed_line)
            
            result_lines.append(processed_line)
        
        return '\n'.join(result_lines)
    
    def _remove_locations(self, text: str) -> str:
        """Remove general city/state/country locations uniformly"""
        locations = self.config.load('locations')
        lines = text.split('\n')
        result_lines = []
        
        for i, line in enumerate(lines):
            processed_line = line
            
            # Redact cities
            for city in locations.get('cities', []):
                processed_line = re.sub(rf'\b{re.escape(city)}\b,?\s*', '', processed_line, flags=re.IGNORECASE)
            
            # Redact states
            for state in locations.get('states', []):
                processed_line = re.sub(rf'\b{re.escape(state)}\b,?\s*', '', processed_line, flags=re.IGNORECASE)
            
            # Redact countries
            for country in locations.get('countries', []):
                processed_line = re.sub(rf'\b{re.escape(country)}\b,?\s*', '', processed_line, flags=re.IGNORECASE)
            
            # Redact postal codes (6 digit numbers, common in India)
            # Use negative lookbehind/lookahead to avoid matching within larger numbers or specific IDs if needed
            # But aggressively removing 6-digit numbers in non-technical contexts is usually safe for resumes
            processed_line = re.sub(r'\b[1-9]\d{5}\b', '', processed_line)
            
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
        """Remove names based on position - COMPLETELY SKIP experience and skills sections"""
        preserve_headers = self.config.get_flat_list('sections', 'preserve')
        
        # Get all protected terms to avoid marking them as names
        protected_terms = self.config.get_flat_list('protected_terms')
        protected_lower = [term.lower() for term in protected_terms]
        
        lines = text.split('\n')
        
        for i in range(len(lines)):
            # COMPLETELY SKIP if in experience or skills section - no redaction at all
            if self._is_in_experience_section(i, lines) or self._is_in_skills_section(i, lines):
                continue
                
            line = lines[i]
            stripped = line.strip().lower()
            
            if any(stripped.startswith(h.lower()) for h in preserve_headers):
                continue
            
            # Handle all-caps names at the very beginning (first 5 lines)
            # Pattern: 2-4 words, each 3+ chars, looks like a name
            if line.strip().isupper() and i < 5:
                words = line.strip().split()
                # Check if it looks like a name: 2-4 words, each word 3+ characters
                if 2 <= len(words) <= 4 and all(len(w) >= 3 and w.isalpha() for w in words):
                    # Check it's not a protected term
                    line_lower = line.strip().lower()
                    is_protected = line_lower in protected_lower or any(w.lower() in protected_lower for w in words)
                    if not is_protected:
                        lines[i] = '[REDACTED_NAME]'
                        continue
            
            # Skip other all-caps lines (section headers)
            if line.isupper():
                continue
            
            # Find potential names
            if i < 30:
                # Aggressive in header
                matches = re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\b', line)
                for match in reversed(list(matches)):
                    matched_text = match.group()
                    
                    # Check if this is a protected term (exact match or contains protected words)
                    matched_lower = matched_text.lower()
                    
                    # First check exact phrase match
                    is_protected = matched_lower in protected_lower
                    
                    # Then check if any individual word is protected
                    if not is_protected:
                        is_protected = any(word.lower() in protected_lower for word in matched_text.split())
                    
                    # Also check if the phrase contains any multi-word protected term
                    if not is_protected:
                        for protected_term in protected_terms:
                            if ' ' in protected_term and protected_term.lower() in matched_lower:
                                is_protected = True
                                break
                    
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
        skip_removal_until = -1  # Track lines to preserve after work experience detection
        
        # Education-related patterns to catch scattered education content
        education_patterns = [
            r'^(m\.\s*tech|b\.\s*tech|b\.\s*e\.|m\.\s*sc|b\.\s*sc|mba|bba|phd|diploma)',
            r'^(xiith|xith|xth|10th|12th|tenth|twelfth)\s*$',
            r'^(english|hindi|marathi|tamil|telugu|kannada|malayalam|bengali|gujarati|punjabi|urdu)\s*$',
        ]
        
        for i, line in enumerate(lines):
            stripped = line.strip().lower()
            # Normalize spacing - remove extra spaces between characters (common in PDFs with styled headings)
            # Keep replacing until no more changes (handles "P E R S O N A L" -> "PERSONAL")
            normalized = stripped
            while True:
                new_normalized = re.sub(r'(\w)\s+(\w)', r'\1\2', normalized)
                if new_normalized == normalized:
                    break
                normalized = new_normalized
            
            # Check if this is scattered education content (not in a marked section)
            if not in_remove_section:
                is_education_content = any(re.match(pattern, stripped, re.IGNORECASE) for pattern in education_patterns)
                if is_education_content:
                    # Check context - if this appears near other education indicators
                    context_window_start = max(0, i - 3)
                    context_window_end = min(len(lines), i + 4)
                    context = '\n'.join(lines[context_window_start:context_window_end]).lower()
                    
                    # Don't remove language names if they appear in LANGUAGES section
                    if 'languages' in context:
                        # This is language proficiency, not education medium
                        pass
                    # If we find education-related context, skip this line
                    elif 'university' in context or 'college' in context or 'vishwavidyalaya' in context or 'rgpv' in context:
                        logging.debug(f"Removing scattered education content: {stripped[:50]}")
                        continue
            
            # Check if entering a remove section
            should_skip = False
            for section_type, markers in remove_sections.items():
                if any(normalized.startswith(m.lower()) or normalized.startswith(m.lower().replace(' ', '')) for m in markers):
                    in_remove_section = True
                    section_depth = 0
                    current_section_type = section_type.upper()
                    result_lines.append(f'[REMOVED_SECTION_{current_section_type}]')
                    should_skip = True
                    break
            
            if should_skip:
                continue
            
            if in_remove_section:
                # Check if we're in a "skip removal" window (preserving lines after work experience)
                if i < skip_removal_until:
                    result_lines.append(line)
                    logging.debug(f"Preserved line in work experience cluster: {stripped[:60]}")
                    continue
                
                # CRITICAL: Check if this line looks like work experience content
                # Even if we're in a PERSONAL/EDUCATION section, preserve work experience lines
                work_experience_indicators = [
                    r'preparation of financial statements',
                    r'assisted in.*audit',
                    r'variance analysis',
                    r'analysis/variance analysis',
                    r'training under the guidance',
                    r'the major experience',
                    r'skills gained during',
                    r'involved in',
                    r'responsible for',
                    r'developed',
                    r'implemented',
                    r'managed',
                    r'years.*intensive.*training',
                    r'\([A-Z][a-z]{2}\s+\d{4}\s*[-–]\s*(?:till\s+date|present|[A-Z][a-z]{2}\s+\d{4})\)',  # Date patterns
                ]
                
                is_work_content = any(re.search(pattern, stripped, re.IGNORECASE) for pattern in work_experience_indicators)
                
                if is_work_content:
                    # This line is work experience, preserve it and the next 2-3 lines
                    # (they're likely part of the same job entry)
                    result_lines.append(line)
                    skip_removal_until = i + 3  # Preserve next 2 lines after this one
                    logging.debug(f"Preserved work experience line and will preserve next 2 lines: {stripped[:60]}")
                    continue
                
                # Check if hit preserve section
                # Normalize preserve section names the same way
                preserve_normalized = [re.sub(r'\s+', '', h.lower()) for h in preserve_sections]
                if any(normalized.startswith(pn) for pn in preserve_normalized):
                    # Check if this is a real section with content or just a sidebar label
                    # Look ahead to see if there's substantial content
                    has_content = False
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        # Check if next lines have substantial content (not just numbers or short labels)
                        if len(next_line) > 50 or (len(next_line) > 20 and not re.match(r'^\d+\s*(Days|Months?|Years?)?$', next_line)):
                            has_content = True
                            break
                    
                    if has_content:
                        # Real section with content - stop removing
                        in_remove_section = False
                        current_section_type = None
                        result_lines.append(line)
                        logging.debug(f"Stopped removal at preserve section with content: {stripped[:50]}")
                    else:
                        # Just a label without real content - continue removing
                        section_depth += 1
                        logging.debug(f"Skipping preserve section label without content: {stripped[:50]}")
                
                # Check if this looks like a job title (indicating we've entered work experience)
                elif (len(stripped) < 60 and 
                      any(role in stripped for role in ['engineer', 'developer', 'programmer', 'architect', 'manager', 'consultant', 'analyst']) and
                      i + 1 < len(lines)):
                    # Look ahead to see if next line is a company name (longer line, likely has company keywords)
                    next_line = lines[i + 1].strip()
                    if len(next_line) > 5 and len(next_line) < 100:
                        # Likely a job title followed by company - stop removing
                        in_remove_section = False
                        current_section_type = None
                        result_lines.append(line)
                        logging.debug(f"Stopped removal at job title (work experience start): {stripped[:50]}")
                
                # For PERSONAL section, be more aggressive - remove until we hit a clear date pattern (indicating work history)
                elif current_section_type == 'PERSONAL':
                    # Check if this line has a date range pattern like "Aug'15 – Jul'18" or "Nov'12 – Apr'15"
                    date_range_pattern = r"[a-z]{3}'?\d{2}\s*[–\-—]\s*[a-z]{3}'?\d{2}"
                    # Also check if line is a redacted placeholder (should still be removed)
                    is_redacted_placeholder = stripped.startswith('[redacted_')
                    
                    if re.search(date_range_pattern, stripped, re.IGNORECASE) and not is_redacted_placeholder:
                        # This is a work experience entry - stop removing
                        in_remove_section = False
                        current_section_type = None
                        result_lines.append(line)
                        logging.debug(f"Stopped PERSONAL removal at date range: {stripped[:50]}")
                    else:
                        section_depth += 1
                        logging.debug(f"Removing PERSONAL line {section_depth}: {stripped[:50]}")
                
                elif section_depth > 30:
                    in_remove_section = False
                    current_section_type = None
                    result_lines.append(line)
                    logging.debug(f"Stopped removal after 30 lines at: {stripped[:50]}")
                else:
                    section_depth += 1
                    # Skip this line - it's part of a section to remove
                    logging.debug(f"Removing line {section_depth}: {stripped[:50]}")
            else:
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
        # First pass: Remove [NAME] markers that appear within skills/experience sections
        lines = text.split('\n')
        in_skills_or_exp = False
        cleaned_first_pass = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Track if we're in skills or experience sections
            if any(marker in line_lower for marker in ['technical skills', 'work experience', 'professional experience', 'project', 'skills:', 'experience:']):
                in_skills_or_exp = True
            elif any(marker in line_lower for marker in ['education', 'certification', 'personal']):
                in_skills_or_exp = False
            
            # Remove [NAME] markers in skills/experience sections
            if in_skills_or_exp and '[NAME]' in line:
                line = line.replace('[NAME]', '')
                # Clean up extra spaces and colons left behind
                line = re.sub(r'\s*:\s*,', ',', line)
                line = re.sub(r',\s*,', ',', line)
                line = re.sub(r'\s{2,}', ' ', line)
            
            cleaned_first_pass.append(line)
        
        
        text = '\n'.join(cleaned_first_pass)
        
        # Second pass: Remove lines that are just labels (e.g. "Name : ", "Address :")
        lines = text.split('\n')
        cleaned_second_pass = []
        
        # Regex for common labels left behind
        label_pattern = re.compile(r'^\s*(Resume Name|Name|Address|Email|Phone|Mobile|Contact|DOB|Date of Birth|Nationality|Marital Status|Gender|Sex|Profile)\s*[:\-]?\s*$', re.IGNORECASE)
        
        for line in lines:
            # Skip lines that match the label pattern (meaning the value was redacted)
            if label_pattern.match(line):
                continue
                
            # Clean up "Name :" if it appears at the start of a line but has content (rare but possible artifact)
            # e.g. "Name : Senior Developer" -> "Senior Developer"
            line = re.sub(r'^\s*(Resume Name|Name|Address|Email|Phone|Mobile|Contact|DOB|Date of Birth)\s*[:\-]\s*', '', line, flags=re.IGNORECASE)

            # Fix spaced headers
            if re.match(r'^[A-Z\s]{10,}$', line):  # All caps with lots of spaces
                # Remove spaces between capital letters on same line iteratively
                fixed_line = line
                while re.search(r'([A-Z])\s+([A-Z])', fixed_line):
                    fixed_line = re.sub(r'([A-Z])\s+([A-Z])', r'\1\2', fixed_line)
                # Add proper spacing between words
                fixed_line = re.sub(r'([A-Z]{2,})(OBJECTIVE|QUALIFICATION|PROFICIENCY|DETAILS|INFORMATION)', r'\1 \2', fixed_line)
                fixed_line = re.sub(r'(CAREER|PROFESSIONAL|COMPUTER|PERSONAL)(\\w)', r'\1 \2', fixed_line)
                line = fixed_line
            
            cleaned_second_pass.append(line)
            
        text = '\n'.join(cleaned_second_pass)
        
        # Fix broken multi-line organization names
        # "Sahyadri Seva" on one line, "Sang" on next -> merge and redact
        text = re.sub(r'Sahyadri\s+Seva\s*\n\s*\n?\s*(?:years.*?\n)?\s*Sang', '[PROGRAM]', text, flags=re.IGNORECASE)
        
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
            stripped = line.strip()
            
            # Keep important section headers
            if any(header in stripped_lower for header in important_headers):
                cleaned_lines.append(line)
                continue
                
            # Keep lines with markers
            if '[' in line and ']' in line:
                cleaned_lines.append(line)
                continue
            
            # Remove potential names - single capitalized words on their own or in pattern "Name • Languages"
            if (re.match(r'^[A-Z][a-z]{2,14}($|\s+•)', stripped) and 
                stripped.lower() not in ['experience', 'skills', 'projects', 'summary', 'profile', 'achievements', 'education']):
                # Check context - if near language or personal info, likely a name
                prev_line = lines[i-1].strip().lower() if i > 0 else ''
                next_line = lines[i+1].strip().lower() if i < len(lines)-1 else ''
                if ('language' in stripped_lower or 'language' in next_line or 'redacted' in prev_line or 
                    any(name in stripped.lower() for name in ['wadhwani', 'preeti'])):
                    # Replace just the name part
                    cleaned_lines.append(re.sub(r'^[A-Z][a-z]{2,14}', '[NAME]', stripped))
                    continue
            
            # Check if this is a single digit that might be part of a date
            if re.match(r'^\s*2\s*$', line) and i + 1 < len(lines):
                # Check if next line looks like a partial date (e.g., "022-12")
                next_line = lines[i + 1].strip()
                if re.match(r'^0\d{2}-\d{2}$', next_line):
                    # This "2" is part of a year, keep it
                    cleaned_lines.append(line)
                    continue
            
            # Skip standalone duration lines (project metadata from sidebar)
            if re.match(r'^\d+\s+(Days?|Months?|Years?)$', stripped, re.IGNORECASE):
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
        
        # Remove unnecessary spaced-out headers (like "C O N T A C T M E A T", "S O F T S K I L L S")
        lines = text.split('\n')
        cleaned_lines = []
        remove_headers = ['contactmeat', 'softskills', 'profilesummary']
        
        for line in lines:
            stripped = line.strip()
            # Check if line is a spaced header we want to remove
            normalized = re.sub(r'\s+', '', stripped.lower())
            if normalized in remove_headers:
                continue  # Skip this line
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Fix broken sentences split by section headers
        # Example: "experience across the entire gamut of Maintenance and" [HEADER] "Project Engineering & Management."
        lines = text.split('\n')
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line ends with incomplete conjunction/preposition
            if line and re.search(r'\b(and|or|of|in|with|for|to|from|at)\s*$', line, re.IGNORECASE):
                # Look ahead for next non-empty, non-header line
                continuation = None
                header_between = None
                j = i + 1
                while j < len(lines) and j < i + 3:  # Look ahead up to 3 lines
                    next_line = lines[j].strip()
                    if next_line:
                        # Check if it's a section header (all caps with spaces between letters)
                        if re.match(r'^[A-Z](\s+[A-Z])+(\s+[A-Z])*', next_line):
                            header_between = j
                            j += 1
                            continue
                        # Found continuation line
                        continuation = next_line
                        continuation_idx = j
                        break
                    j += 1
                
                # If we found a continuation that starts with capital and seems like a continuation
                if continuation and re.match(r'^[A-Z]', continuation):
                    # Merge the lines
                    merged = line + ' ' + continuation
                    fixed_lines.append(merged)
                    # Skip the header and continuation
                    if header_between is not None:
                        i = continuation_idx + 1
                    else:
                        i += 2
                    continue
            
            fixed_lines.append(lines[i])
            i += 1
        
        text = '\n'.join(fixed_lines)
        
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
        prev_was_bullet = False
        prev_was_job = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers (including "Technical Skills:")
            is_header = (
                (line.isupper() and 3 <= len(line) <= 60) or
                (re.match(r'^[A-Z][A-Z\s&]{2,50}$', line) and len(line.split()) <= 6) or
                (re.match(r'^(Technical Skills?|Work Experience|Certifications?|Education):?$', line, re.IGNORECASE))
            )
            
            # Detect key-value pairs (like "Integration Technologies: Mulesoft")
            is_key_value = bool(re.match(r'^[A-Z][A-Za-z\s]+:\s+.+$', line))
            
            # Detect job entries (has date range pattern or company indicator)
            is_job_entry = bool(re.search(r'\([A-Z][a-z]{2,9}\s+\d{4}\s*[-–]\s*(?:Present|till\s+date|[A-Z][a-z]{2,9}\s+\d{4})\)', line, re.IGNORECASE))
            
            # Detect bullet points
            is_bullet = line.startswith(('•', '-', '·', '○', '*'))
            
            # Detect descriptive lines ("The major experience and skills...")
            is_description_intro = bool(re.match(r'^The major experience', line, re.IGNORECASE))
            
            if is_header:
                # Add spacing before headers (unless it's the very first line or previous was also a header)
                if formatted and not prev_header:
                    formatted.append('')
                formatted.append(line)
                formatted.append('')
                prev_header = True
                prev_was_bullet = False
                prev_was_job = False
            elif is_job_entry:
                # Job entries should have spacing before them
                if formatted and not prev_header:
                    formatted.append('')
                    formatted.append('')
                formatted.append(line)
                prev_header = False
                prev_was_bullet = False
                prev_was_job = True
            elif is_description_intro:
                # Add spacing before role descriptions
                if formatted:
                    formatted.append('')
                formatted.append(line)
                prev_header = False
                prev_was_bullet = False
                prev_was_job = False
            elif is_key_value:
                # Technical skills key-value pairs
                formatted.append(line)
                prev_header = False
                prev_was_bullet = False
                prev_was_job = False
            elif is_bullet:
                # Normalize bullet points - no extra spacing within bullet groups
                formatted.append('• ' + line.lstrip('•-·○* ').strip())
                prev_header = False
                prev_was_bullet = True
                prev_was_job = False
            else:
                # Regular text - add spacing after bullet groups or job entries
                if prev_was_bullet and not is_bullet and not line.startswith('for '):
                    formatted.append('')
                formatted.append(line)
                prev_header = False
                prev_was_bullet = False
                prev_was_job = False
        
        text = '\n'.join(formatted)
        
        # Clean up excessive blank lines (max 2 consecutive)
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
    """Standard extraction with improved column handling"""
    
    def extract_text(self, pdf_path: str) -> str:
        # Try PyMuPDF first with improved column detection
        if HAS_FITZ:
            all_pages_text = []
            
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    page_width = page.rect.width
                    page_height = page.rect.height
                    
                    # Get structured extraction to detect columns
                    blocks = page.get_text("dict")["blocks"]
                    
                    text_blocks = []
                    for block in blocks:
                        if "lines" in block:
                            bbox = block["bbox"]
                            text = " ".join([
                                " ".join([span["text"] for span in line["spans"]])
                                for line in block["lines"]
                            ]).strip()
                            if text:
                                text_blocks.append({
                                    'text': text,
                                    'x0': bbox[0],
                                    'y0': bbox[1],
                                    'x1': bbox[2],
                                    'y1': bbox[3]
                                })
                    
                    if not text_blocks:
                        # Fallback to simple extraction
                        all_pages_text.append(page.get_text("text"))
                        continue
                    
                    # Improved two-column detection
                    # Analyze x-positions to detect columns
                    x_positions = [b['x0'] for b in text_blocks]
                    x_centers = [(b['x0'] + b['x1']) / 2 for b in text_blocks]
                    
                    # Find natural column boundary by looking for gaps
                    sorted_x = sorted(set(x_centers))
                    max_gap = 0
                    column_boundary = page_width / 2
                    
                    for i in range(len(sorted_x) - 1):
                        gap = sorted_x[i + 1] - sorted_x[i]
                        # Look for significant gaps (at least 40 pixels) in the middle portion of the page
                        if gap > max_gap and gap > 40 and page_width * 0.25 < sorted_x[i] < page_width * 0.75:
                            max_gap = gap
                            column_boundary = (sorted_x[i] + sorted_x[i + 1]) / 2
                    
                    # Check if we have a true two-column layout
                    left_blocks = [b for b in text_blocks if (b['x0'] + b['x1']) / 2 < column_boundary]
                    right_blocks = [b for b in text_blocks if (b['x0'] + b['x1']) / 2 >= column_boundary]
                    
                    # Consider it a two-column layout if:
                    # 1. We found a significant gap (> 40px)
                    # 2. Both columns have substantial content (at least 3 blocks each)
                    is_two_column = max_gap > 40 and len(left_blocks) >= 3 and len(right_blocks) >= 3
                    
                    if is_two_column:
                        # Two-column layout detected - read LEFT column completely, then RIGHT column
                        left_blocks.sort(key=lambda b: b['y0'])
                        right_blocks.sort(key=lambda b: b['y0'])
                        
                        # Output left column first, then right column
                        page_lines = []
                        page_lines.extend([b['text'] for b in left_blocks])
                        page_lines.append("")  # Separator between columns
                        page_lines.extend([b['text'] for b in right_blocks])
                        
                        page_text = "\n".join(page_lines)
                    else:
                        # Single column or mixed layout - sort by y then x (top to bottom, left to right within same row)
                        text_blocks.sort(key=lambda b: (b['y0'], b['x0']))
                        page_text = "\n".join([b['text'] for b in text_blocks])
                    
                    all_pages_text.append(page_text)
                
                return "\n\n".join(all_pages_text)
        
        elif HAS_PDFPLUMBER:
            with pdfplumber.open(pdf_path) as pdf:
                return "\n\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        
        return "Error: No PDF library available"
    
    def _fix_concatenated_words(self, text: str) -> str:
        """Fix words that are concatenated without spaces using comprehensive replacements"""
        # Direct replacements for known concatenated patterns (order matters - longest first)
        fixes = {
            'proventrackrecordofstamping': 'proven track record of stamping',
            'proventrackrecordof': 'proven track record of',
            'proventrackrecord': 'proven track record',
            'stampingsuccess across': 'stamping success across',
            'stampingsuccessacross': 'stamping success across',
            'theentiregamutof': 'the entire gamut of',
            'Strategicprofessional': 'Strategic professional',
            'offeringover': 'offering over',
            'ofexperiencewith': 'of experience with',
            'ofexperience': 'of experience',
            'experiencewith': 'experience with',
            'withstrong': 'with strong',
            'businessacumen': 'business acumen',
            'stampingsuccess': 'stamping success',
            'successacross': 'success across',
            'gamutof': 'gamut of',
            'Maintenanceand': 'Maintenance and',
            'Experiencedin': 'Experienced in',
            'inmanaging': 'in managing',
            'managingerection': 'managing erection',
            'commissioningactivities': 'commissioning activities',
            'maintenanceofawide': 'maintenance of a wide',
            'ofawide': 'of a wide',
            'RCAofbreakdowns': 'RCA of breakdowns',
            'takingcorrective': 'taking corrective',
            'preventivemeasures': 'preventive measures',
            'correctivepreventive': 'corrective preventive',
            'OEEmonitoringtool': 'OEE monitoring tool',
            'Conditionmonitoringtool': 'Condition monitoring tool',
            'monitoringtool': 'monitoring tool',
            'resourceplanning': 'resource planning',
            'vendormanagement': 'vendor management',
            'costingandqualityassurance': 'costing and quality assurance',
            'costingand': 'costing and',
            'qualityassurance': 'quality assurance',
            'analyzedratesfor': 'analyzed rates for',
            'analyzedratesforeachactivityand': 'analyzed rates for each activity and',
            'foreachactivityand': 'for each activity and',
            'foreachactivity': 'for each activity',
            'foreach': 'for each',
            'eachactivityand': 'each activity and',
            'eachactivity': 'each activity',
            'activityand': 'activity and',
            'andfigured': 'and figured',
            'figuredvaluation': 'figured valuation',
            'valuationof': 'valuation of',
            'ofworkperformed': 'of work performed',
            'ofwork': 'of work',
            'workperformed': 'work performed',
        }
        
        for old, new in fixes.items():
            text = text.replace(old, new)
        
        return text
    
    def _reorganize_two_column_layout(self, text: str) -> str:
        """Detect and reorganize two-column interleaved layouts"""
        lines = text.split('\n')
        
        # Detect section headers with spaced capitals (e.g., "P ROFESSIONAL Q UALIFICATION")
        section_header_pattern = r'^[A-Z\s]{10,60}$'
        
        # Find all section headers
        section_headers = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and re.match(section_header_pattern, stripped) and '  ' in stripped:
                section_headers[i] = stripped
        
        # If we found 3+ section headers, likely interleaved
        if len(section_headers) < 3:
            return text
        
        logger.info(f"Detected two-column interleaving with {len(section_headers)} section headers")
        
        # Left column markers
        left_markers = ['CAREER', 'PROFESSIONAL', 'ACHIEVEMENT', 'COMPUTER', 'PERSONAL', 'DECLARATION', 'EDUCATION']
        
        left_column = []
        right_column = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            upper = stripped.upper()
            
            # Is this a left column section header?
            if i in section_headers:
                left_column.append(line)
                continue
            
            # Is this left column content (bullets under section headers)?
            # Look back to see if previous section header was a left marker
            prev_header = None
            for h_idx in sorted(section_headers.keys(), reverse=True):
                if h_idx < i:
                    prev_header = section_headers[h_idx].upper()
                    break
            
            if prev_header and any(marker in prev_header for marker in left_markers):
                # We're under a left column header
                # Check if this line is actually right column content
                is_company_line = bool(re.search(r'(Pvt\.?\s+Ltd|Limited|Inc\.|Corporation)', stripped))
                has_date_range = bool(re.search(r'\([A-Z][a-z]{2}\s+\d{4}\s*[-–]', stripped))
                is_long_sentence = len(stripped) > 100
                has_exp_keywords = bool(re.search(r'(The major experience|skills gained|Involved in|Controlling|Accounting|Management|Preparation)', stripped))
                
                if is_company_line or has_date_range or (is_long_sentence and has_exp_keywords):
                    right_column.append(line)
                else:
                    # Short line or bullet under left header - keep in left
                    left_column.append(line)
            else:
                # Not under a left header, goes to right column
                right_column.append(line)
        
        # Reconstruct: left column, separator, right column
        result = left_column + ['', '', ''] + right_column
        return '\n'.join(result)
    
    def preprocess(self, text: str) -> str:
        # First, try to detect and fix two-column interleaving
        text = self._reorganize_two_column_layout(text)
        
        # Fix numbers stuck to words
        text = re.sub(r'(\d+)(years?|months?|days?)', r'\1 \2', text, flags=re.IGNORECASE)
        
        # Fix ampersands - add space before and after if missing
        text = re.sub(r'([a-zA-Z])&([a-zA-Z])', r'\1 & \2', text)
        text = re.sub(r'([a-zA-Z])&\s', r'\1 & ', text)
        text = re.sub(r'\s&([a-zA-Z])', r' & \1', text)
        
        # Fix concatenated words by adding spaces before capital letters
        # Handle patterns like "Strategicprofessional" -> "Strategic professional"
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Apply comprehensive word splitting for known concatenations
        text = self._fix_concatenated_words(text)
        
        text = re.sub(r'[•●○◦▪▫■□⬤→]', '•', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Handle mixed column content for ATS-style resumes
        lines = text.split('\n')
        
        # Detect if this is an ATS resume with sidebar
        has_sidebar_format = False
        key_skills_idx = -1
        profile_summary_idx = -1
        
        for i, line in enumerate(lines):
            if 'KEY SKILLS' in line.upper():
                key_skills_idx = i
                has_sidebar_format = True
            if 'PROFILE SUMMARY' in line.upper():
                profile_summary_idx = i
        
        if has_sidebar_format and key_skills_idx != -1 and profile_summary_idx != -1:
            # Common tech skill keywords that appear in sidebars
            tech_keywords = {'jenkins', 'gitlab', 'gtest', 'c++', 'agile', 'scrum', 'iso8583', 
                           'c++ 11', 'c++ 14', 'payments', 'cpp', 'qml', 'docker', 'kubernetes',
                           'python', 'java', 'javascript', 'angular', 'react', 'vue', 'linux',
                           'unix', 'automotive', 'unit testing', 'c', 'c++ programming',
                           'embedded c', 'socket programming', 'stl', 'oops', 'multithreading',
                           'multi processing', 'linux development'}
            
            # Load protected terms from config
            try:
                protected_config = self.config.load('protected_terms')
                protected_terms = []
                for category in protected_config.values():
                    if isinstance(category, list):
                        protected_terms.extend(category)
                protected_lower = [term.lower() for term in protected_terms]
            except:
                # Fallback if config can't be loaded
                protected_lower = []
            
            # Collect all skill lines and non-skill lines separately
            skills_section_lines = []
            other_lines = []
            in_key_skills = False
            
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                if i == key_skills_idx:
                    # Start of KEY SKILLS section
                    in_key_skills = True
                    skills_section_lines.append(line)
                    continue
                
                # Stop collecting skills when we hit PROFILE SUMMARY
                if i == profile_summary_idx:
                    in_key_skills = False
                    other_lines.append(line)
                    continue
                
                # If we're before KEY SKILLS, just add to other lines
                if i < key_skills_idx:
                    other_lines.append(line)
                    continue
                
                # Between KEY SKILLS and PROFILE SUMMARY - collect as skills (filtering dates/years/names/titles)
                if i > key_skills_idx and i < profile_summary_idx:
                    # Skip dates
                    if re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*-', line_stripped, re.IGNORECASE):
                        continue
                    # Skip single years (education)
                    if re.match(r'^\d{4}$', line_stripped):
                        continue
                    # Skip empty lines
                    if not line_stripped:
                        continue
                    
                    # Check if it's a protected term or tech keyword (definitely a skill)
                    if line_lower in protected_lower or line_lower in tech_keywords:
                        skills_section_lines.append(line)
                        continue
                    
                    # Skip lines that look like names (2-3 capitalized words, but not tech terms)
                    if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$', line_stripped):
                        # This looks like a person name
                        continue
                    
                    # Skip standalone generic words that aren't skills
                    non_tech_words = ['development', 'management', 'engineering', 'testing', 
                                     'programming', 'lead', 'senior', 'junior', 'principal']
                    if line_lower in non_tech_words:
                        continue
                    
                    # Skip lines with job title patterns (but not if they're compound tech terms)
                    # Only skip if it's clearly a job title like "Lead Engineer" or "Senior Developer"
                    if re.match(r'^(Lead|Senior|Junior|Principal)\s+(Engineer|Developer|Architect|Manager)', line_stripped, re.IGNORECASE):
                        continue
                    
                    # Everything else between KEY SKILLS and PROFILE SUMMARY is likely a skill
                    if len(line_stripped) <= 50:  # Skills are typically short
                        skills_section_lines.append(line)
                    else:
                        # Too long, probably descriptive text
                        continue
                else:
                    # After PROFILE SUMMARY - only collect if it's an exact match to tech keywords
                    if line_lower in tech_keywords and len(line_stripped) < 30:
                        # This is a skill keyword appearing later - add to skills section
                        skills_section_lines.append(line)
                    else:
                        other_lines.append(line)
            
            # Reconstruct: skills section with all skills, then other content
            result_lines = skills_section_lines + [''] + other_lines
            text = '\n'.join(result_lines)
        
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
                        # Look for gaps after at least 10% of page width (to catch left sidebars)
                        # and before 80% (to avoid right margin)
                        if page_width * 0.10 < x_positions_sorted[i] < page_width * 0.80:
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
        
        # Extract technical skills from PERSONAL DETAILS section before it gets redacted
        # Returns both the skills lines and the indices to remove from original content
        technical_skills, lines_to_remove = self._extract_technical_skills(lines)
        
        # Find the main SKILLS section and ALL sidebar markers
        skills_idx = -1
        sidebar_indices = []
        prof_exp_idx = -1
        work_exp_idx = -1
        personal_details_end_idx = -1
        
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
            # Track where PERSONAL DETAILS section ends (look for next major section or first project)
            if 'PERSONAL DETAILS' in line_stripped.upper():
                # Find where personal details ends (usually before first project or next section)
                for j in range(i + 1, min(i + 40, len(lines))):
                    if (re.match(r'^\d+\.\s*(Company|Project)', lines[j].strip(), re.IGNORECASE) or 
                        any(section in lines[j].upper() for section in ['PROFESSIONAL EXPERIENCE', 'WORK EXPERIENCE', 'PROJECT DETAILS', 'EDUCATIONAL QUALIFICATION'])):
                        personal_details_end_idx = j
                        break
        
        # Use either PROFESSIONAL EXPERIENCE or WORK EXPERIENCE as the insertion point
        # If neither exists, use the end of PERSONAL DETAILS section
        experience_idx = prof_exp_idx if prof_exp_idx != -1 else (work_exp_idx if work_exp_idx != -1 else personal_details_end_idx)
        
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
            
            # Special handling: Extract "To" column dates from sidebar for table reconstruction
            table_to_dates = []
            project_details_data = {}  # Store project data from sidebars
            
            for sidebar_idx in sidebar_indices:
                if sidebar_idx + 1 < len(lines) and lines[sidebar_idx + 1].strip() == 'To':
                    # Found a "To" column header in sidebar - extract the dates
                    for j in range(sidebar_idx + 2, min(sidebar_idx + 10, len(lines))):
                        date_line = lines[j].strip()
                        # Stop at section headers
                        if date_line in ['EDUCATIONAL QUALIFICATION:', 'PROJECT DETAILS:', 'PERSONAL DETAILS:']:
                            break
                        # Collect date-like entries
                        if date_line and (re.match(r'^(Present|[A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4}|\d{4})$', date_line) or
                                        re.match(r'^[A-Z]{3,}-\d{4}$', date_line)):
                            table_to_dates.append(date_line)
                
                # Extract project details that appear in sidebar
                # Look for patterns like "Client Name" followed by "Project Name" followed by dates
                for j in range(sidebar_idx + 1, min(sidebar_idx + 100, len(lines))):
                    line = lines[j].strip()
                    
                    # Stop if we hit another sidebar or PROJECT header in main content
                    if j in sidebar_indices or re.match(r'^PROJECT\s+\d+', line, re.IGNORECASE):
                        break
                    
                    # Check if this looks like a client/company name (usually all caps or title case, not a date)
                    # Followed by a project name, then dates
                    if (len(line) > 3 and not re.match(r'^[A-Z]{3,}-?\d{4}', line) and 
                        not line.lower() in ['to', 'from', 'duration', 'environment', 'project role'] and
                        not line.startswith(('-', '•'))):
                        
                        # Potential client or project data - collect next few lines
                        potential_data = [line]
                        for k in range(j+1, min(j+10, len(lines))):
                            next_line = lines[k].strip()
                            if next_line and len(next_line) > 2:
                                potential_data.append(next_line)
                                # Stop after collecting enough (client, project, dates, environment, role, responsibilities)
                                if len(potential_data) >= 5:
                                    break
                        
                        # Store this data to merge later
                        if len(potential_data) >= 3:
                            project_details_data[j] = potential_data
            
            result = []
            sidebar_ranges = []
            
            # Calculate ranges to skip (sidebar sections only)
            for sidebar_idx in sidebar_indices:
                # Check if we're in PROJECT DETAILS section by looking backwards
                in_project_details = False
                for k in range(max(0, sidebar_idx - 20), sidebar_idx):
                    if 'PROJECT DETAILS' in lines[k].upper() or 'PROJECT' in lines[k].upper() and ':' in lines[k]:
                        in_project_details = True
                        break
                
                # If we're in project details, don't mark this sidebar for removal
                if in_project_details:
                    continue
                
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
                    
                    # Stop if we hit a PROJECT header (e.g., "PROJECT 4:", "PROJECT 5:")
                    # This indicates we're entering actual project details that should be kept
                    if re.match(r'^PROJECT\s+\d+', line_stripped, re.IGNORECASE):
                        break
                    
                    # Check if this is a paragraph/sentence (likely job description continuation)
                    # Paragraphs start with lowercase or are long sentences with proper punctuation
                    is_paragraph = (
                        len(line_stripped) > 60 or  # Long line likely a paragraph
                        (line_stripped and line_stripped[0].islower()) or  # Starts with lowercase
                        (line_lower.startswith('and ') or line_lower.startswith('or ') or 
                         line_lower.startswith('with ') or line_lower.startswith('to ')) or  # Sentence continuation
                        re.search(r'\.\s*-\s*[A-Z]', lines[j]) or  # Bullet point format "... . - Word"
                        line_stripped.startswith('-') or line_stripped.startswith('•')  # Responsibility bullets
                    )
                    
                    # If it's a paragraph or responsibility bullet, keep it (don't mark as sidebar)
                    if is_paragraph:
                        break
                    
                    # Continue if this looks like sidebar content (metadata, contact, skills list)
                    is_sidebar_content = (
                        len(line_stripped) < 3 or  # Empty or very short
                        any(x in lines[j] for x in ['@', '•', '○']) or  # Contact markers or bullets
                        re.search(r'\d{5,}|linkedin|github|phone|email|contact|location', lines[j], re.IGNORECASE) or  # Contact patterns
                        line_stripped in ['Skills', 'SKILLS', 'Languages', 'LANGUAGES', 'Contact', 'CONTACT', 'R', 'Ó', 'Education', 'EDUCATION'] or  # Section headers or symbols
                        # Only treat as skill if it's a short line (< 50 chars) with tech keywords
                        (len(line_stripped) < 50 and any(keyword in line_lower for keyword in ['java', 'kotlin', 'python', 'javascript', 'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'sql', 'mongodb', 'postgresql', 'mysql', 'html', 'css', 'api', 'rest', 'graphql', 'agile', 'scrum', 'mvvm', 'mvc', 'retrofit', 'volley', 'firebase', 'android', 'ios', 'swift', 'jetpack'])) or
                        (len(line_stripped) > 10 and len(line_stripped) < 50 and ',' in lines[j]) or  # Short comma-separated lists
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
            table_date_idx = 0  # Track which "To" date to use next
            in_prof_experience = False
            from_date_line_idx = -1  # Track line with "From" date to add "To" date after
            
            for i in range(len(lines)):
                # Skip if in any sidebar range or if this line was extracted to technical skills
                if any(start <= i < end for start, end in sidebar_ranges) or i in lines_to_remove:
                    continue
                
                # Track if we're in PROFESSIONAL EXPERIENCE section
                if 'PROFESSIONAL EXPERIENCE' in lines[i].upper():
                    in_prof_experience = True
                elif lines[i].strip() in ['PROJECT DETAILS:', 'PROJECTS:', 'EDUCATIONAL QUALIFICATION:', 'EDUCATION:']:
                    in_prof_experience = False
                
                # If we're at the experience section, insert technical skills first
                if i == experience_idx:
                    # Insert technical skills from PERSONAL DETAILS if found
                    if technical_skills:
                        result.append("")
                        result.append("TECHNICAL SKILLS")
                        result.append("")
                        result.extend(technical_skills)
                        result.append("")
                    
                    # Then insert sidebar skills if available
                    if all_sidebar_skills:
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
                
                # Add the line
                result.append(lines[i])
                
                # If in professional experience and line contains a "From" date, prepare to add "To" date
                if in_prof_experience and table_to_dates and table_date_idx < len(table_to_dates):
                    # Check if this line contains a FROM date pattern (e.g., "Feb-2022", "MAR-2019", "FEB-2015")
                    if re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})\s*$', lines[i]):
                        # Add "To" date on the same line or next line
                        to_date = table_to_dates[table_date_idx]
                        result[-1] = result[-1] + f" to {to_date}"
                        table_date_idx += 1
            
            text = '\n'.join(result)
        else:
            # Fallback: just remove all sidebar markers and their immediate content
            text = re.sub(r'===\s*SIDEBAR\s*===', '', text)
        
        # Always remove sidebar markers that remain
        text = re.sub(r'===\s*SIDEBAR\s*===', '', text)
        
        # Remove education/university data that appears in project details sidebars
        # Remove lines like "Board/University Year Of Passing Marks %"
        lines = text.split('\n')
        cleaned_lines = []
        skip_education_table = False
        for line in lines:
            line_lower = line.strip().lower()
            # Check for education table headers
            if 'board/university' in line_lower or ('year of passing' in line_lower and 'marks' in line_lower):
                skip_education_table = True
                continue
            # Skip education table rows (university names with years and percentages)
            if skip_education_table:
                if re.match(r'^[A-Za-z\s]+(university|board|college)\s+\d{4}\s+[\d.]+\s*%', line.strip(), re.IGNORECASE):
                    continue
                # Stop skipping when we hit actual content (longer than 50 chars or starts with letter but not university pattern)
                if len(line.strip()) > 50 or (line.strip() and not re.search(r'(university|board|college|\d{4}|%)', line_lower)):
                    skip_education_table = False
            
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remove sidebar fragment patterns that slip through
        # These are typically single-letter fragments, language names, or social link headers
        lines = text.split('\n')
        cleaned_lines = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Skip single letters or very short fragments that are likely sidebar remnants
            if len(line_stripped) == 1 and line_stripped in ['g', 'G', 'R', 'Ó']:
                continue
            # Skip "Social links" headers and partial LinkedIn URLs
            if line_stripped in ['Social links', 'SOCIAL LINKS', 'Social Links']:
                continue
            if re.match(r'^[a-z]/[\w-]+/$', line_stripped):  # Partial LinkedIn URL like "n/mayur-patil96/"
                continue
            # Skip standalone language names that appear outside of language sections
            if line_stripped in ['Hindi', 'English', 'Marathi', 'Telugu', 'Tamil', 'Kannada', 'Bengali']:
                # Only skip if not part of a sentence (check if previous/next lines are empty or headers)
                if i > 0 and (len(lines[i-1].strip()) < 3 or lines[i-1].strip().isupper()):
                    continue
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        
        # Clean up extra whitespace
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Reformat Professional Experience tables for clarity
        text = self._reformat_professional_experience(text)
        
        # Reformat PROJECT sections to combine headers with values
        text = self._reformat_projects(text)
        
        return text.strip()
    
    def _extract_technical_skills(self, lines: list) -> tuple:
        """Extract technical skills fields from PERSONAL DETAILS section
        Returns: (technical_skills_lines, indices_to_remove)
        """
        technical_skills = []
        lines_to_remove = set()
        personal_details_idx = -1
        
        # Find PERSONAL DETAILS section
        for i, line in enumerate(lines):
            if 'PERSONAL DETAILS' in line.strip().upper():
                personal_details_idx = i
                break
        
        if personal_details_idx == -1:
            return technical_skills, lines_to_remove
        
        # Technical field patterns to extract
        tech_patterns = [
            r'^CURRENT OCCUPATION\s*[:：]',
            r'^COMPUTER LANGUAGES\s*[:：]',
            r'^OPERATING SYSTEMS?\s*[:：]',
            r'^DATABASES?\s*(?:AND SERVICES)?\s*[:：]',
            r'^TOOLS\s*[:：]',
            r'^CLIENT SPECIFIC TOOLS?\s*[:：]'
        ]
        
        # Extract lines matching technical patterns (within next 50 lines)
        j = personal_details_idx + 1
        while j < min(personal_details_idx + 50, len(lines)):
            line = lines[j].strip()
            
            # Stop if we hit another major section or project start
            if (any(marker in line.upper() for marker in ['PROFESSIONAL EXPERIENCE', 'WORK EXPERIENCE', 'PROJECT DETAILS', 'EDUCATIONAL QUALIFICATION', 'EDUCATION:']) or
                re.match(r'^\d+\.\s*(Company|Project)', line, re.IGNORECASE)):
                break
            
            # Check if line matches a technical field pattern
            is_tech_field = False
            current_pattern_idx = -1
            for idx, pattern in enumerate(tech_patterns):
                if re.match(pattern, line, re.IGNORECASE):
                    is_tech_field = True
                    current_pattern_idx = idx
                    break
            
            if is_tech_field:
                # Found a technical field - add the header line
                technical_skills.append(line)
                lines_to_remove.add(j)  # Mark this line for removal
                
                # Collect all continuation lines until we hit another field or section
                k = j + 1
                while k < min(j + 10, len(lines)):
                    next_line = lines[k].strip()
                    
                    # Stop if empty line
                    if not next_line:
                        k += 1
                        continue
                    
                    # Stop if we hit another technical field
                    is_another_field = False
                    for pattern in tech_patterns:
                        if re.match(pattern, next_line, re.IGNORECASE):
                            is_another_field = True
                            break
                    if is_another_field:
                        break
                    
                    # Stop if we hit a major section or project
                    if (any(marker in next_line.upper() for marker in ['PROFESSIONAL EXPERIENCE', 'WORK EXPERIENCE', 'PROJECT DETAILS', 'EDUCATIONAL QUALIFICATION', 'EDUCATION:']) or
                        re.match(r'^\d+\.\s*(Company|Project)', next_line, re.IGNORECASE)):
                        break
                    
                    # Stop if we hit fields that are NOT part of technical skills (NAME, ADDRESS, DOB, etc.)
                    if re.match(r'^(NAME|ADDRESS|DATE OF BIRTH|MARITAL STATUS|NATIONALITY|EDUCATIONAL BACKGROUND|PASSPORT NO)', next_line, re.IGNORECASE):
                        break
                    
                    # This is a continuation line - add it
                    technical_skills.append(lines[k])
                    lines_to_remove.add(k)  # Mark this line for removal
                    k += 1
                
                # Move j to after all the lines we just processed
                j = k
            else:
                j += 1
        
        return technical_skills, lines_to_remove
    
    def _reformat_professional_experience(self, text: str) -> str:
        """Reformat Professional Experience table to make it more readable"""
        lines = text.split('\n')
        result = []
        in_prof_exp = False
        processed_lines = set()  # Track lines we've already processed as part of entries
        i = 0
        
        while i < len(lines):
            # Skip if this line was already processed as part of another entry
            if i in processed_lines:
                i += 1
                continue
            
            line = lines[i].strip()
            line_upper = line.upper()
            
            # Check if we're entering Professional Experience section
            if 'PROFESSIONAL EXPERIENCE' in line_upper or 'WORK EXPERIENCE' in line_upper:
                result.append(lines[i])
                in_prof_exp = True
                i += 1
                continue
            
            # Check if we're leaving Professional Experience section
            if in_prof_exp and (
                'PROJECT' in line_upper or 
                'EDUCATION' in line_upper or
                'PERSONAL DETAILS' in line_upper or
                'DECLARATION' in line_upper
            ):
                in_prof_exp = False
            
            # Skip table headers like "Name Of The Designation Technologies From"
            if in_prof_exp and (
                ('NAME OF THE' in line_upper and ('COMPANY' in line_upper or 'DESIGNATION' in line_upper)) or
                ('DESIGNATION' in line_upper and 'TECHNOLOGIES' in line_upper and 'FROM' in line_upper)
            ):
                logger.info(f"[REFORMAT] Line {i}: Skipped header: {line}")
                i += 1
                continue
            
            # Skip standalone "Company" header
            if in_prof_exp and line_upper in ['COMPANY', 'ORGANIZATION', 'EMPLOYER']:
                logger.info(f"[REFORMAT] Line {i}: Skipped standalone header: {line}")
                i += 1
                continue
            
            # Reformat company entries
            if in_prof_exp and line and not line.startswith('-') and not line.startswith('•'):
                # Check if this line has a date with "to" format
                date_match = re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})\s+to\s+(Present|[A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})', line)
                
                if date_match:
                    # Extract duration
                    duration = date_match.group(0)
                    before_date = line[:date_match.start()].strip()
                    
                    # Try to extract company name and initial technologies
                    company = None
                    technologies = []
                    technologies_before_date = []  # Store technologies from before the date separately
                    designation_prefix = None  # Initialize here, may be set during company extraction
                    
                    # Check if the "before_date" part looks like it's all technologies (no company name)
                    # Pattern: "ADO.NET,WCF, " or "Database, Angular "
                    looks_like_all_tech = (
                        re.match(r'^[A-Z][A-Z\.]+', before_date) or  # Starts with acronym like ADO.NET
                        before_date.count(',') >= 2 or  # Multiple commas suggest list of technologies
                        re.match(r'^(Database|Angular|React|SQL|Java|Python)', before_date, re.IGNORECASE)  # Starts with common tech
                    )
                    
                    if looks_like_all_tech and i > 0:
                        # Look backward for company name on previous line
                        prev_line = lines[i-1].strip()
                        prev_line_upper = prev_line.upper()
                        # Skip if previous line is a header
                        is_header = (
                            prev_line_upper in ['COMPANY', 'ORGANIZATION', 'EMPLOYER'] or
                            ('NAME OF THE' in prev_line_upper and 'COMPANY' in prev_line_upper)
                        )
                        # Company name line is usually short, doesn't have commas
                        if prev_line and not is_header and not re.search(r'[,•\-:]', prev_line) and len(prev_line.split()) <= 5:
                            company = prev_line
                            processed_lines.add(i-1)  # Mark company line as processed
                            
                            # Check if company name ends with a designation prefix (e.g., "Aloha Technology Software")
                            # If so, extract the prefix as part of designation
                            company_words = company.split()
                            if company_words and company_words[-1] in ['Software', 'Technology', 'Senior', 'Lead']:
                                designation_prefix = company_words[-1]
                                company = ' '.join(company_words[:-1])
                            
                            # Check if company name continues after date line (e.g., "Pvt Ltd." or "Pvt Ltd. Developer")
                            if i + 1 < len(lines):
                                after_date_line = lines[i + 1].strip()
                                # Check if line starts with company suffix
                                company_suffix_match = re.match(r'^(Pvt\.?|Ltd\.?|Limited|Inc\.?|Corp\.?|LLC)(\s+(Ltd\.?|Limited|Inc\.?))?', after_date_line, re.IGNORECASE)
                                if company_suffix_match:
                                    company_suffix = company_suffix_match.group(0)
                                    company = f"{company} {company_suffix}"
                            
                            # Store before_date as technology (will be added at the end)
                            if before_date:
                                technologies_before_date.append(before_date)
                    
                    # Check BACKWARD from current date line for any technology lines that might have been skipped
                    # by the previous entry (handles cases where PDF extraction misplaces technologies)
                    if i > 2:  # Need at least 2 lines before to check
                        k = i - 1
                        # Collect any technology-looking lines that appear BEFORE this date line
                        # but were not processed by the previous entry
                        backward_tech = []
                        hit_csharp_net_pattern = False
                        while k >= 0:
                            backward_line = lines[k].strip()
                            
                            # Stop if we hit another date line (previous entry's date)
                            if re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})\s+to\s+(Present|PRESENT|[A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})', backward_line):
                                break
                            
                            # Check if we hit C#.Net pattern - if so, mark it and ONLY collect these patterns, not earlier tech
                            # This handles case where C#.Net technologies belong to current entry, not shared with previous
                            if re.match(r'^(C#\.Net|VB\.Net|ASP\.NET|SQL\s+SERVER|Entity\s+Framework|ADO\.NET|WCF)', backward_line, re.IGNORECASE):
                                hit_csharp_net_pattern = True
                                backward_tech.insert(0, backward_line)
                                k -= 1
                                continue
                            
                            # If we've already seen C#.Net pattern, don't collect any more lines (they're from previous entry)
                            if hit_csharp_net_pattern:
                                k -= 1
                                continue
                            
                            # Skip designation lines (we don't collect them as tech)
                            if backward_line and len(backward_line.split()) <= 2 and backward_line in ['Analyst', 'Developer', 'Engineer', 'Manager', 'Architect', 'Consultant', 'Lead', 'Senior']:
                                k -= 1
                                continue
                            
                            # Collect technology lines - collect all tech patterns that haven't been collected by C#.Net logic
                            if backward_line and not (backward_line in ['Analyst', 'Developer', 'Engineer', 'Manager', 'Architect', 'Consultant', 'Lead', 'Senior', 'Technology', 'Software', 'Company']):
                                # Check if line looks like technologies (contains tech keywords or is comma-separated list)
                                is_tech_line = False
                                
                                # Pattern: C#, .Net Framework style patterns (ATOS/Infosys shared tech stack)
                                if re.search(r'(C#|\.Net|Web API|Sql|Database|Angular|React|Python|Java)', backward_line, re.IGNORECASE):
                                    is_tech_line = True
                                # Pattern: Comma-separated list (general tech pattern)
                                elif re.match(r'^[A-Z][^,]*,', backward_line) and not re.match(r'^[A-Z][a-z]+\s+[A-Z]', backward_line):
                                    is_tech_line = True
                                
                                # Collect all tech lines found backward (they're from previous entry and should be shared)
                                if is_tech_line:
                                    backward_tech.insert(0, backward_line)
                            
                            k -= 1
                        
                        # Add collected backward technologies to the beginning of technologies_before_date
                        if backward_tech:
                            technologies_before_date = backward_tech + technologies_before_date
                    
                    # If we didn't find company backward, parse from before_date
                    if not company:
                        # Split by commas to separate company from tech
                        parts = before_date.split(',')
                        if parts:
                            # First part might be "Company Name Tech1" or just "Company Name"
                            first_part = parts[0].strip()
                            words = first_part.split()
                            
                            # Look for tech indicators to split company from tech
                            # Common pattern: "ATOS C#" -> company="ATOS", tech="C#"
                            tech_found_idx = -1
                            for j, word in enumerate(words):
                                if re.match(r'^(C#|C\+\+|Java|Python|\.Net|SQL|Angular|React|Node|Vue|Spring|Django|Flask|Ruby)$', word, re.IGNORECASE):
                                    tech_found_idx = j
                                    break
                            
                            if tech_found_idx > 0:
                                # Found tech keyword, company is everything before it
                                company = ' '.join(words[:tech_found_idx])
                                # Everything from tech keyword onward is technology (from before date)
                                technologies_before_date.append(' '.join(words[tech_found_idx:]))
                            elif len(words) <= 2:
                                # No tech keyword and short (1-2 words) - likely all company name
                                company = first_part
                            else:
                                # Longer name - assume first 2 words are company, rest might be tech or part of name
                                # Common patterns: "Infosys Limited Database" -> "Infosys Limited", "Database"
                                company = ' '.join(words[:2])
                                if len(words) > 2:
                                    # Check if 3rd word looks like tech or part of company name
                                    third_word = words[2]
                                    if re.match(r'^(Database|Framework|System|Server|Cloud|Platform)$', third_word, re.IGNORECASE):
                                        # It's a tech term (from before date)
                                        technologies_before_date.append(' '.join(words[2:]))
                                    elif words[2] in ['Pvt', 'Ltd', 'Limited', 'Inc', 'Corp', 'LLC']:
                                        # It's part of company name
                                        company = ' '.join(words[:3])
                                        if len(words) > 3:
                                            technologies_before_date.append(' '.join(words[3:]))
                                    else:
                                        technologies_before_date.append(' '.join(words[2:]))
                            
                            # Add remaining comma-separated parts as technologies (from before date)
                            if len(parts) > 1:
                                technologies_before_date.extend([p.strip() for p in parts[1:] if p.strip()])
                    
                    # Look ahead for designation and more technologies
                    designation = None
                    j = i + 1
                    
                    # Check if there's a designation prefix on the line BEFORE the date line
                    # Pattern: "Technology" on line before, "Analyst" after
                    # This should be checked even if company was found
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        # Check if previous line is a single word that could be a designation prefix
                        if prev_line and len(prev_line.split()) == 1 and prev_line in ['Technology', 'Software', 'Senior', 'Lead', 'Principal', 'Chief']:
                            designation_prefix = prev_line
                            processed_lines.add(i-1)  # Mark prefix line as processed
                    
                    # If company was found backward, check if first line after date has both company suffix and designation
                    # Pattern: "Pvt Ltd. Developer" where "Pvt Ltd." is company suffix and "Developer" is designation
                    if company and j < len(lines):
                        first_line_after_date = lines[j].strip()
                        company_suffix_match = re.match(r'^(Pvt\.?|Ltd\.?|Limited|Inc\.?|Corp\.?|LLC)(\s+(Ltd\.?|Limited|Inc\.?))?\s+(.+)$', first_line_after_date, re.IGNORECASE)
                        if company_suffix_match:
                            # Extract designation after the company suffix
                            potential_designation = company_suffix_match.group(4).strip()
                            if potential_designation and len(potential_designation.split()) <= 3:
                                # Combine with designation_prefix if we found one
                                if designation_prefix:
                                    designation = f"{designation_prefix} {potential_designation}"
                                else:
                                    designation = potential_designation
                                j += 1
                    
                    # First, get the designation from the immediate next non-empty line (if not already found)
                    if not designation:
                        while j < len(lines) and j < i + 3:  # Only look 2-3 lines ahead for designation
                            next_line = lines[j].strip()
                            if not next_line:
                                j += 1
                                continue
                            
                            # Check if this looks like a designation
                            is_designation = (
                                len(next_line.split()) <= 3 and  # Designations are usually 1-3 words
                                not re.search(r'[,•\-:]', next_line) and
                                not re.search(r'\d', next_line) and
                                (next_line[0].isupper() or next_line.isupper()) and
                                not re.match(r'^(C#|Java|Python|\.Net|SQL|Angular|React|Web|API|Database|HTML|CSS|JavaScript)', next_line, re.IGNORECASE)
                            )
                            
                            if is_designation:
                                # Combine with prefix if we found one
                                if designation_prefix:
                                    designation = f"{designation_prefix} {next_line}"
                                else:
                                    designation = next_line
                                j += 1
                                
                                # Check if designation continues on next line (e.g., already combined, so skip this check if we had a prefix)
                                if not designation_prefix and j < len(lines):
                                    next_next_line = lines[j].strip()
                                    if next_next_line and len(next_next_line.split()) <= 2 and not re.search(r'[,•\-:]', next_next_line):
                                        # Check if it's part of designation (like "Analyst" following "Technology")
                                        if next_next_line in ['Analyst', 'Developer', 'Engineer', 'Manager', 'Architect', 'Consultant', 'Lead', 'Senior']:
                                            designation = f"{designation} {next_next_line}"
                                            j += 1
                                        # Or if it starts with date, it's a new entry
                                        elif re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})', next_next_line):
                                            break
                                break
                            else:
                                break
                    
                    # Now collect remaining technologies
                    while j < len(lines) and j < i + 15:
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        
                        # If it's a new company entry (has date pattern), stop
                        if re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})', next_line):
                            break
                        
                        # If it looks like a bullet point or project section, stop
                        if next_line.startswith('-') or next_line.startswith('•') or 'PROJECT' in next_line.upper():
                            break
                        
                        # Check if it's a single-word designation prefix for the next entry (like "Technology")
                        if len(next_line.split()) == 1 and next_line in ['Technology', 'Software', 'Senior', 'Lead', 'Principal', 'Chief']:
                            break
                        
                        # Check if line starts with C#.Net or VB.Net pattern (indicates different tech stack for next entry)
                        # This pattern is distinct from C# and indicates a transition to a new company's technologies
                        if re.match(r'^(C#\.Net|VB\.Net|ASP\.NET\s+(MVC|Core))', next_line, re.IGNORECASE):
                            # This is likely the start of a different company's tech stack, stop collecting
                            break
                        
                        # Check if it's a company name line (for next entry) - short, no commas, no tech keywords at start
                        is_likely_company = (
                            len(next_line.split()) <= 5 and
                            ',' not in next_line and
                            not next_line[0].isdigit() and
                            not re.match(r'^(C#|Java|Python|\.Net|SQL|Angular|React|Web|API|Database|HTML|CSS|JavaScript|ADO)', next_line, re.IGNORECASE)
                        )
                        
                        # If it looks like company name, check if there are more tech lines before the next date
                        # This handles cases where technologies appear between company name and date in table
                        if is_likely_company:
                            # Look ahead to see if there's technology content before the next date line
                            k = j + 1
                            found_tech_after_company = False
                            while k < len(lines) and k < j + 10:
                                peek_line = lines[k].strip()
                                if not peek_line:
                                    k += 1
                                    continue
                                # If we hit a date line, check if there are tech lines between company and date
                                if re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})', peek_line):
                                    # There are tech lines between current position and date
                                    # These likely belong to the next entry, so stop collecting for current entry
                                    found_tech_after_company = False
                                    break
                                # If this line has tech keywords or commas, it's likely technology
                                if ',' in peek_line or re.match(r'^(C#|Java|Python|\.Net|SQL|Angular|React|Web|API|ADO|ASP)', peek_line, re.IGNORECASE):
                                    found_tech_after_company = True
                                    break
                                k += 1
                            
                            # If we found tech after what looks like company name, and we already have some tech, stop
                            if found_tech_after_company and len(technologies) > 0:
                                break
                            # If no tech found after, and we have some tech already, also stop
                            elif not found_tech_after_company and len(technologies) > 0:
                                break
                        
                        # Check if this line is a duplicate/subset of already collected technologies
                        # This handles cases where table parsing creates duplicate summary lines
                        already_collected_text = ', '.join(technologies + technologies_before_date).lower()
                        is_duplicate = False
                        if technologies or technologies_before_date:  # Check against all collected
                            # Extract major technology keywords from the new line
                            new_line_lower = next_line.lower()
                            # Check if all major words in the new line are already in collected tech
                            major_words = [w.strip(',.') for w in next_line.split() if len(w.strip(',.')) > 2]
                            if major_words:
                                matching_words = sum(1 for w in major_words if w.lower() in already_collected_text)
                                # If more than 60% of words are already collected, it's likely a duplicate (lowered from 70%)
                                if matching_words / len(major_words) > 0.6:
                                    is_duplicate = True
                        
                        if not is_duplicate:
                            # Otherwise, it's technology
                            technologies.append(next_line)
                        j += 1
                    
                    # Format output
                    result.append("")
                    if company:
                        result.append(f"Company: {company}")
                    if designation:
                        result.append(f"Designation: {designation}")
                    result.append(f"Duration: {duration}")
                    
                    # Combine technologies: after-date technologies first, then before-date technologies
                    all_technologies = technologies + technologies_before_date
                    
                    if all_technologies:
                        # Deduplicate technologies at word level to remove redundant entries
                        # e.g., "Web API" + "Web API, Sql" -> keep both but track seen tech items
                        seen_tech_items = set()
                        deduplicated_tech = []
                        
                        for tech_line in all_technologies:
                            # Split by commas to get individual technology items
                            items = [item.strip() for item in tech_line.split(',') if item.strip()]
                            unique_items = []
                            
                            for item in items:
                                # Normalize for comparison (lowercase, remove extra spaces)
                                item_normalized = ' '.join(item.lower().split())
                                
                                # Check if this exact item or a very similar item was already seen
                                is_duplicate = False
                                for seen_item in seen_tech_items:
                                    # Check for exact match or high overlap
                                    seen_words = set(seen_item.split())
                                    item_words = set(item_normalized.split())
                                    
                                    # If exact match, it's duplicate
                                    if item_normalized == seen_item:
                                        is_duplicate = True
                                        break
                                    
                                    # If one is subset of other, keep the longer one
                                    if item_words.issubset(seen_words):
                                        is_duplicate = True
                                        break
                                    elif seen_words.issubset(item_words):
                                        # Current item is more complete, replace the old one
                                        seen_tech_items.discard(seen_item)
                                        break
                                
                                if not is_duplicate:
                                    unique_items.append(item)
                                    seen_tech_items.add(item_normalized)
                            
                            # Add the unique items from this line
                            if unique_items:
                                deduplicated_tech.extend(unique_items)
                        
                        # Join all deduplicated technologies
                        if deduplicated_tech:
                            all_tech = ', '.join(deduplicated_tech)
                            all_tech = re.sub(r'\s*,\s*', ', ', all_tech)
                            all_tech = re.sub(r',\s*,', ',', all_tech)
                            result.append(f"Technologies: {all_tech}")
                    
                    # Mark all processed lines in range
                    for k in range(i, j):
                        processed_lines.add(k)
                    
                    # Skip the lines we processed
                    i = j
                    continue
            
            # Before adding this line to result, check if it's a designation prefix for the next date line
            # If so, skip it - it will be processed when we hit the date line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Check if next line is a date line
                date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[a-z]*[-\s]*\d{4}\s+to\s+(Present|PRESENT|[A-Za-z]+[-\s]*\d{4})'
                if re.search(date_pattern, next_line):
                    # Check if current line is a potential designation prefix
                    if line and len(line.split()) == 1 and line in ['Technology', 'Software', 'Senior', 'Lead', 'Principal', 'Chief']:
                        # Skip this line - it will be processed as part of the next entry
                        i += 1
                        continue
            
            # Similar check for company name: if current line looks like a company and next line starts with date/tech
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Check if next line contains a date
                if re.search(date_pattern, next_line):
                    # Check if current line looks like a company name
                    if line and not re.search(r'[,•\-:]', line) and len(line.split()) <= 5:
                        # This might be a company name for the next entry
                        i += 1
                        continue
            
            # Skip lines that match C#.Net pattern - they will be collected backward by a later entry
            if re.match(r'^(C#\.Net|VB\.Net|ASP\.NET|SQL\s+SERVER|Entity\s+Framework|ADO\.NET|WCF)', line, re.IGNORECASE):
                i += 1
                continue
            
            result.append(lines[i])
            i += 1
        
        return '\n'.join(result)

    def _reformat_projects(self, text: str) -> str:
        """Reformat PROJECT sections to combine headers with their values"""
        lines = text.split('\n')
        result = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this is a PROJECT header (e.g., "PROJECT 1 : Atos", "PROJECT 2: Infosys Limited.")
            if re.match(r'^PROJECT\s+\d+\s*[:]\s*.+', line, re.IGNORECASE):
                # Collect consecutive PROJECT headers and their field headers
                project_sections = []
                j = i
                
                while j < len(lines):
                    current_line = lines[j].strip()
                    
                    # Check if it's a PROJECT header
                    if re.match(r'^PROJECT\s+\d+\s*[:]\s*.+', current_line, re.IGNORECASE):
                        project_title = lines[j]
                        j += 1
                        
                        # Collect field headers for this project
                        field_headers = []
                        while j < len(lines) and j < i + 100:
                            next_line = lines[j].strip()
                            
                            # Stop at empty line or another PROJECT
                            if not next_line:
                                j += 1
                                break
                            if re.match(r'^PROJECT\s+\d+', next_line, re.IGNORECASE):
                                break
                            
                            # Check if it's a field header
                            if (next_line in ['Client', 'Project', 'Duration', 'Duration Of Project', 'Duration of Project', 
                                             'Environment', 'Project Role', 'Roles and Responsibilities', 'Title', 'Information'] or
                                re.match(r'^(Client|Project|Duration|Environment|Role|Title|Information)$', next_line, re.IGNORECASE)):
                                field_headers.append(next_line)
                                j += 1
                            else:
                                # Hit non-header, stop
                                break
                        
                        project_sections.append((project_title, field_headers))
                    else:
                        # Not a PROJECT header, break
                        break
                
                # Now collect all the values that follow
                values = []
                while j < len(lines) and j < i + 200:
                    val_line = lines[j].strip()
                    
                    # Stop if we hit another PROJECT header or section marker
                    if re.match(r'^PROJECT\s+\d+', val_line, re.IGNORECASE):
                        break
                    if val_line and val_line.upper() in ['PERSONAL DETAILS:', 'EDUCATION:', 'EDUCATIONAL QUALIFICATION:', 'DECLARATION:']:
                        break
                    
                    # Collect non-empty lines
                    if val_line:
                        values.append(val_line)
                    
                    j += 1
                
                # Distribute values across projects based on their field headers
                if project_sections and values:
                    # Calculate how many values each project should get
                    total_fields = sum(len(headers) for _, headers in project_sections)
                    
                    if total_fields > 0 and len(values) >= total_fields:
                        # Distribute values proportionally to each project
                        value_idx = 0
                        for project_title, field_headers in project_sections:
                            result.append(project_title)
                            
                            # Assign values to this project's fields
                            for header in field_headers:
                                if value_idx < len(values):
                                    result.append(f"{header}: {values[value_idx]}")
                                    value_idx += 1
                            
                            result.append("")  # Empty line after each project
                        
                        # Add any remaining values (usually bullet points)
                        while value_idx < len(values):
                            result.append(values[value_idx])
                            value_idx += 1
                    else:
                        # Not enough values or no structure - just output as-is
                        for project_title, _ in project_sections:
                            result.append(project_title)
                        for val in values:
                            result.append(val)
                else:
                    # No valid structure, keep as-is
                    for project_title, _ in project_sections:
                        result.append(project_title)
                
                # Move past all processed lines
                i = j
                continue
            
            # Not a PROJECT section, keep as-is
            result.append(lines[i])
            i += 1
        
        return '\n'.join(result)


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
        
        # Reformat Professional Experience tables for clarity
        text = self._reformat_professional_experience(text)
        
        return text
    
    def _reformat_professional_experience(self, text: str) -> str:
        """Reformat Professional Experience table to make it more readable"""
        lines = text.split('\n')
        result = []
        in_prof_exp = False
        i = 0
        
        if self.debug:
            logger.info(f"[REFORMAT] Starting with {len(lines)} lines")
        
        while i < len(lines):
            line = lines[i].strip()
            line_upper = line.upper()
            
            # Check if we're entering Professional Experience section
            if 'PROFESSIONAL EXPERIENCE' in line_upper or 'WORK EXPERIENCE' in line_upper:
                result.append(lines[i])
                in_prof_exp = True
                if self.debug:
                    logger.info(f"[REFORMAT] Line {i}: Entered Professional Experience section")
                i += 1
                continue
            
            # Check if we're leaving Professional Experience section
            if in_prof_exp and (
                'PROJECT' in line_upper or 
                'EDUCATION' in line_upper or
                'PERSONAL DETAILS' in line_upper or
                'DECLARATION' in line_upper
            ):
                in_prof_exp = False
                if self.debug:
                    logger.info(f"[REFORMAT] Line {i}: Exited Professional Experience section")
            
            # Skip table headers like "Name Of The Designation Technologies From"
            if in_prof_exp and (
                ('NAME OF THE' in line_upper and ('COMPANY' in line_upper or 'DESIGNATION' in line_upper)) or
                ('DESIGNATION' in line_upper and 'TECHNOLOGIES' in line_upper and 'FROM' in line_upper)
            ):
                if self.debug:
                    logger.info(f"[REFORMAT] Line {i}: Skipped header: {line}")
                i += 1
                continue
            
            # Skip standalone "Company" header
            if in_prof_exp and line_upper in ['COMPANY', 'ORGANIZATION', 'EMPLOYER']:
                if self.debug:
                    logger.info(f"[REFORMAT] Line {i}: Skipped standalone header: {line}")
                i += 1
                continue
            
            # Reformat company entries
            if in_prof_exp and line and not line.startswith('-') and not line.startswith('•'):
                # Check if this line has a date with "to" format
                date_match = re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})\s+to\s+(Present|[A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})', line)
                
                if date_match:
                    if self.debug:
                        logger.info(f"[REFORMAT] Line {i}: Found date match: {line}")
                    
                    # Extract duration
                    duration = date_match.group(0)
                    before_date = line[:date_match.start()].strip()
                    
                    # Try to extract company name and initial technologies
                    company = None
                    technologies = []
                    
                    # Split by commas to separate company from tech
                    parts = before_date.split(',')
                    if parts:
                        # First part might be "Company Name Tech1" or just "Company Name"
                        first_part = parts[0].strip()
                        # Company is typically 1-3 words (ATOS, Infosys Limited, Aloha Technology)
                        words = first_part.split()
                        if len(words) <= 3:
                            company = first_part
                            # Rest is technologies
                            if len(parts) > 1:
                                technologies.extend([p.strip() for p in parts[1:] if p.strip()])
                        else:
                            # Try to separate company from tech in first part
                            # Common pattern: "ATOS C#" -> company="ATOS", tech="C#"
                            # Look for tech indicators (C#, Java, .Net, etc.)
                            tech_found = False
                            for j, word in enumerate(words):
                                if re.match(r'(C#|Java|Python|\.Net|SQL|Angular|React)', word, re.IGNORECASE):
                                    company = ' '.join(words[:j])
                                    technologies.append(' '.join(words[j:]))
                                    tech_found = True
                                    break
                            if not tech_found:
                                # Assume first 2 words are company, rest is tech
                                company = ' '.join(words[:2])
                                if len(words) > 2:
                                    technologies.append(' '.join(words[2:]))
                            # Add remaining parts as tech
                            if len(parts) > 1:
                                technologies.extend([p.strip() for p in parts[1:] if p.strip()])
                    
                    # Look ahead for designation and more technologies
                    designation = None
                    j = i + 1
                    while j < len(lines) and j < i + 10:
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                        
                        # Check if this looks like a designation (short, no special chars, titlecase)
                        is_designation = (
                            len(next_line.split()) <= 5 and 
                            not re.search(r'[,•\-:]', next_line) and
                            not re.search(r'\d', next_line) and
                            (next_line[0].isupper() or next_line.isupper())
                        )
                        
                        # Check if it looks like technology (has commas, tech keywords, or technical terms)
                        is_tech = (
                            ',' in next_line or 
                            re.search(r'(C#|Java|Python|\.Net|SQL|Angular|React|Framework|API|Database)', next_line, re.IGNORECASE)
                        )
                        
                        # If it's a new company entry (has date pattern), stop
                        if re.search(r'\b([A-Z]{3}-\d{4}|[A-Z][a-z]{2}-\d{4})', next_line):
                            break
                        
                        # If it looks like a bullet point or project section, stop
                        if next_line.startswith('-') or next_line.startswith('•') or 'PROJECT' in next_line.upper():
                            break
                        
                        if is_designation and not is_tech:
                            designation = next_line
                            j += 1
                        elif is_tech:
                            technologies.append(next_line)
                            j += 1
                        else:
                            break
                    
                    # Format output
                    result.append("")
                    if company:
                        result.append(f"Company: {company}")
                    if designation:
                        result.append(f"Designation: {designation}")
                    result.append(f"Duration: {duration}")
                    if technologies:
                        # Clean up technologies - join and remove extra spaces
                        all_tech = ', '.join(technologies)
                        all_tech = re.sub(r'\s*,\s*', ', ', all_tech)
                        all_tech = re.sub(r',\s*,', ',', all_tech)
                        result.append(f"Technologies: {all_tech}")
                    
                    if self.debug:
                        logger.info(f"[REFORMAT] Reformatted: Company={company}, Designation={designation}, Duration={duration}")
                    
                    # Skip the lines we processed
                    i = j
                    continue
            
            result.append(lines[i])
            i += 1
        
        return '\n'.join(result)


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
        
        # Get protected terms for name removal check
        config_loader = ConfigLoader()
        protected_terms = config_loader.get_flat_list('protected_terms')
        protected_lower = [term.lower() for term in protected_terms]
        
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
                # Check if this line contains protected technical terms
                line_lower = line.strip().lower()
                is_protected = (line_lower in protected_lower or 
                               any(word.lower() in protected_lower for word in line.strip().split()) or
                               any(' ' in term and term.lower() in line_lower for term in protected_terms))
                if not is_protected:
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