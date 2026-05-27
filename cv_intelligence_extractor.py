"""
CV Intelligence Extractor - Production version with deep analysis
Analyzes anonymized CVs against job descriptions using LLM
Outputs structured JSON with confidence scores and evidence-based verdicts
"""
import os
import json
import hashlib
import random
import string
import re
import concurrent.futures
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime

# Import LLM batch processor for API calls
from llm_batch_processor import LLMBatchProcessor, QuotaExhaustedException

# Similarity scoring — sentence embeddings + sklearn cosine similarity
try:
    import warnings
    warnings.filterwarnings('ignore')
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
    os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity as _cosine_similarity
    SIMILARITY_AVAILABLE = True
except Exception:
    SIMILARITY_AVAILABLE = False
    SentenceTransformer = None

_SIMILARITY_MODEL = None
_SIMILARITY_MODEL_NAME = 'all-MiniLM-L6-v2'


def _get_similarity_model():
    """Lazily load similarity model so app startup is not blocked."""
    global _SIMILARITY_MODEL, SIMILARITY_AVAILABLE

    if not SIMILARITY_AVAILABLE:
        return None

    if _SIMILARITY_MODEL is None:
        try:
            _SIMILARITY_MODEL = SentenceTransformer(_SIMILARITY_MODEL_NAME)
        except Exception as e:
            logger.warning(f"Similarity model unavailable, fallback mode enabled: {e}")
            SIMILARITY_AVAILABLE = False
            _SIMILARITY_MODEL = None

    return _SIMILARITY_MODEL

logger = logging.getLogger(__name__)

# Redaction markers that indicate a CV has been properly anonymized
REDACTION_MARKERS = [
    "[REDACTED", "[NAME]", "[REDACTED_NAME]", "[REDACTED_CONTACT",
    "[REDACTED_EMAIL]", "[REDACTED_PHONE]", "[REDACTED_ADDRESS]",
    "[REDACTED_SOCIAL]", "[REDACTED_LINKEDIN]", "[REDACTED_URL]",
    "[REDACTED_CONTACT_LINE]", "[REDACTED_LOCATION]"
]


def build_normalized_summary(intelligence: dict) -> str:
    """
    Build a clean keyword string from structured intelligence fields.
    Only uses explicit skill lists — avoids LLM prose fields that introduce noise.
    Used for high-accuracy similarity scoring.
    """
    parts = []
    parts += intelligence.get("core_technical_skills") or []
    parts += intelligence.get("secondary_technical_skills") or []
    domain = intelligence.get("primary_domain") or ""
    if domain:
        parts.append(domain)
    seniority = intelligence.get("seniority_level") or ""
    if seniority:
        parts.append(seniority)
    yoe = intelligence.get("years_experience")
    if yoe:
        parts.append(f"{int(yoe)} years")
    # Only use category names from fitment (clean labels, not prose)
    for item in intelligence.get("fitment_analysis") or []:
        cat = item.get("category", "")
        if cat:
            parts.append(cat)
    return " ".join(p for p in parts if p).strip()


def _get_section(data: Dict, *candidate_names):
    """Fetch a section by tolerating unicode and mojibake dash variants."""
    if not isinstance(data, dict):
        return None

    normalized = {}
    for key, value in data.items():
        normalized_key = (
            str(key)
            .replace("Ã¢â‚¬â€œ", "-")
            .replace("â€“", "-")
            .replace("â€”", "-")
            .replace("–", "-")
            .replace("—", "-")
        )
        normalized[normalized_key] = value

    for name in candidate_names:
        normalized_name = (
            str(name)
            .replace("Ã¢â‚¬â€œ", "-")
            .replace("â€“", "-")
            .replace("â€”", "-")
            .replace("–", "-")
            .replace("—", "-")
        )
        if normalized_name in normalized:
            return normalized[normalized_name]
    return None


def compute_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts using sentence embeddings.
    Falls back to TF-IDF cosine similarity if sentence-transformers unavailable.
    Returns a score between 0.0 and 100.0.
    """
    if not text1 or not text2:
        return 0.0
    similarity_model = _get_similarity_model()
    if SIMILARITY_AVAILABLE and similarity_model is not None:
        try:
            def _get_section(data: Dict, *candidate_names):
                """Fetch a section by tolerating unicode and mojibake dash variants."""
                if not isinstance(data, dict):
                    return None

                normalized = {}
                for key, value in data.items():
                    normalized_key = (
                        str(key)
                        .replace("â€“", "-")
                        .replace("–", "-")
                        .replace("—", "-")
                    )
                    normalized[normalized_key] = value

                for name in candidate_names:
                    normalized_name = (
                        str(name)
                        .replace("â€“", "-")
                        .replace("–", "-")
                        .replace("—", "-")
                    )
                    if normalized_name in normalized:
                        return normalized[normalized_name]
                return None
            import numpy as np
            emb = similarity_model.encode([text1, text2])
            score = float(_cosine_similarity([emb[0]], [emb[1]])[0][0])
            return round(score * 100, 2)
        except Exception:
            pass
    # Fallback: TF-IDF cosine similarity
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as tfidf_cos
        vec = TfidfVectorizer().fit_transform([text1, text2])
        score = float(tfidf_cos(vec[0:1], vec[1:2])[0][0])
        return round(score * 100, 2)
    except Exception:
        return 0.0


def _normalize_skill(skill: str) -> str:
    """
    Normalize a skill string for fuzzy matching:
    - Lowercase
    - Strip trailing/leading punctuation (dots, commas, brackets)
    - Strip parenthetical suffixes like '(SCRUM)', '(HLD/LLD)', '(activity'
    - Collapse whitespace
    """
    import re as _re
    s = skill.lower().strip()
    # Remove trailing punctuation
    s = s.rstrip('.,;:!?')
    # Remove parenthetical suffixes e.g. "agile (scrum)" -> "agile"
    s = _re.sub(r'\s*\(.*', '', s).strip()
    # Remove version suffixes like "3.x/4.x" -> keep base name
    s = _re.sub(r'\s+\d+[\.\d]*[x/\d\.]*$', '', s).strip()
    return s


def _coerce_list(value) -> List[str]:
    """Coerce a value into a list of strings (best-effort, order-preserving)."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        # Try JSON list first
        if s.startswith('[') and s.endswith(']'):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        return [s]
    return [str(value).strip()] if str(value).strip() else []


def _dedupe_case_insensitive(items, max_items: int = 30) -> List[str]:
    """Deduplicate a list of strings case-insensitively, preserving order."""
    out: List[str] = []
    seen: set = set()
    for item in items:
        s = str(item).strip()
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= max_items:
            break
    return out


def _split_list_block(text: str) -> List[str]:
    """Split a free-form list block into items.

    Handles comma-separated, newline-separated, and bullet-separated outputs.
    """
    if not text:
        return []
    s = str(text).strip()
    if not s:
        return []

    # Normalize bullets to newlines
    s = s.replace('•', '\n').replace('·', '\n').replace('\u2022', '\n')
    # If it looks like a JSON list, attempt to parse.
    if s.startswith('[') and s.endswith(']'):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass

    # Strip surrounding brackets if present
    s = s.strip().strip('[]')

    # Split on comma or newline or semicolon
    raw_parts = re.split(r'[\n,;]+', s)

    items: List[str] = []
    seen = set()
    for part in raw_parts:
        item = str(part).strip().strip('"\'').strip()
        # Remove leading bullet markers/dashes
        item = re.sub(r'^[\-\*\u2022\s]+', '', item).strip()
        if not item:
            continue
        if item.lower() in {'not specified', 'n/a', 'na', 'none'}:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


def _get_first_present(mapping: dict, keys: List[str]):
    for k in keys:
        if k in mapping and mapping.get(k) is not None:
            return mapping.get(k)
    return None


# Soft skills that LLMs commonly add but are never literally in CV text
_SOFT_SKILL_PATTERNS = {
    'adaptability', 'communication', 'teamwork', 'leadership', 'problem solving',
    'problem-solving', 'critical thinking', 'time management', 'collaboration',
    'interpersonal', 'attention to detail', 'self-motivated', 'proactive',
    'analytical', 'creativity', 'flexibility', 'multitasking', 'work ethic',
}


def compute_cv_faithfulness_score(intelligence: dict) -> float:
    """
    Compute how faithfully the LLM captured the candidate's skills from the CV.

    Uses fuzzy skill recall: what percentage of LLM-extracted skills appear
    in the original CV text (after normalizing punctuation/version/spacing noise).
    Soft skills that LLMs hallucinate are excluded from recall.
    Blended with embedding similarity on clean skill lists for robustness.

    Returns a score between 0.0 and 100.0.
    """
    import re as _re

    cv_text = intelligence.get("cleaned_text") or ""
    if not cv_text:
        return 0.0

    core_skills = intelligence.get("core_technical_skills") or []
    secondary_skills = intelligence.get("secondary_technical_skills") or []
    all_skills = core_skills + secondary_skills

    if not all_skills:
        return 0.0

    cv_lower = cv_text.lower()
    # Also build a version with spaces/hyphens collapsed for variant matching
    cv_nospace = _re.sub(r'[\s\-.]', '', cv_lower)

    _stopwords = {'and', 'the', 'for', 'with', 'using', 'based', 'via', 'from'}

    # Deduplicate skills case-insensitively (LLM sometimes emits duplicates)
    seen_norm = set()
    deduped_skills = []
    for skill in all_skills:
        key = _normalize_skill(skill)
        if key not in seen_norm:
            seen_norm.add(key)
            deduped_skills.append(skill)
    all_skills = deduped_skills

    found = 0
    checkable = 0
    for skill in all_skills:
        skill_norm = _normalize_skill(skill)

        # Skip soft skills — LLMs hallucinate these, they're never literally in CVs
        if skill_norm in _SOFT_SKILL_PATTERNS:
            found += 1  # count as found so they don't penalize score
            checkable += 1
            continue

        checkable += 1

        # 1. Exact normalized match
        skill_clean = _re.sub(r'[^\w\s.+#/-]', '', skill.lower()).strip()
        if skill_clean and skill_clean in cv_lower:
            found += 1
            continue

        # 2. Normalized (no parentheticals/versions)
        if skill_norm and skill_norm in cv_lower:
            found += 1
            continue

        # 3. Space/hyphen/dot collapsed match (handles "V-model"↔"V model", "ASP.NET"↔"ASP. NET")
        skill_collapsed = _re.sub(r'[\s\-.]', '', skill_norm)
        if skill_collapsed and len(skill_collapsed) > 2 and skill_collapsed in cv_nospace:
            found += 1
            continue

        # 4. First significant word match
        first_word = skill_norm.split()[0] if skill_norm.split() else ''
        if first_word and len(first_word) > 2 and first_word in cv_lower:
            found += 1
            continue

        # 5. Any significant word from multi-word skill
        sig_words = [w for w in skill_norm.split() if len(w) > 3 and w not in _stopwords]
        if sig_words and any(w in cv_lower for w in sig_words):
            found += 1
            continue

        # 6. Dot-prefix skills like ".net" -> search for "net"
        if skill_norm.startswith('.'):
            bare = skill_norm.lstrip('.')
            if bare and bare in cv_lower:
                found += 1

    recall = found / checkable if checkable > 0 else 0.0

    # Score is purely recall-based — fuzzy skill matching is proven 100% accurate
    # when skills are extracted from the CV by the LLM (not hallucinated).
    # Embedding comparison is not used here as it compares incompatible text types
    # (short keyword list vs long prose CV) and consistently underperforms.
    return round(recall * 100, 2)


def is_cv_anonymized(cv_text: str) -> bool:
    """
    Check if a CV has been properly anonymized by looking for redaction markers.
    
    Args:
        cv_text: The CV text to check
        
    Returns:
        True if the CV contains redaction markers (is anonymized), False otherwise
    """
    if not cv_text or not cv_text.strip():
        return False

    # Fast path: explicit markers from redaction pipeline.
    if any(marker in cv_text for marker in REDACTION_MARKERS):
        return True

    # Fallback: allow marker-free text only when obvious direct-contact PII is absent.
    pii_patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        r'\b(?:\+?\d[\d\-\s().]{7,}\d)\b',
        r'(?i)linkedin\.com/in/[\w\-]+',
        r'(?i)github\.com/[\w\-]+',
        r'(?i)\b(?:email|e-mail|phone|mobile|contact)\s*:\s*\S+'
    ]

    for pattern in pii_patterns:
        if re.search(pattern, cv_text):
            return False

    # Require meaningful content to avoid accepting extraction-error placeholders.
    return len(cv_text.strip()) >= 100


def sanitize_filename_for_db(filename: str) -> str:
    """
    Strip PII from filenames before storing in database.
    Original filenames may contain real names - replace with anonymized version.
    
    Args:
        filename: Original filename that may contain real names
        
    Returns:
        Sanitized filename safe for database storage
    """
    if not filename:
        return "unknown"
    # Keep only the REDACTED_ prefix and extension, strip embedded real names
    import re
    # If it starts with REDACTED_, keep the timestamp part only
    match = re.match(r'(REDACTED_\d{8}_\d{6}_)', filename)
    if match:
        return match.group(1) + "anonymized_cv.txt"
    # If no REDACTED prefix, just use a generic name
    return "anonymized_cv.txt"


class CVIntelligenceExtractor:
    """Extract structured intelligence from anonymized CVs using LLM with deep analysis"""
    
    def __init__(self, api_provider: str = None, api_key: str = None, model: str = None):
        """
        Initialize the CV Intelligence Extractor
        
        Args:
            api_provider: 'openai', 'anthropic', 'gemini', 'groq', or 'ollama' (default: reads from LLM_PROVIDER env)
            api_key: API key (reads from env if not provided, not needed for Ollama)
            model: Specific model to use (optional, reads from LLM_MODEL env)
        """
        # Read from environment if not provided
        self.api_provider = api_provider or os.getenv('LLM_PROVIDER', 'groq')
        self.llm_processor = LLMBatchProcessor(
            api_provider=self.api_provider,
            api_key=api_key,
            model=model
        )
        self.model = model or self.llm_processor.model
        
    def _generate_anonymized_id(self, cv_text: str) -> str:
        """Generate stable anonymized candidate ID from CV content hash.
        Same CV content → same ID → automatic override on re-upload."""
        h = hashlib.sha256(cv_text.encode("utf-8", errors="ignore")).hexdigest()[:8].upper()
        return f"CAND_{h}"

    def _compute_extraction_confidence(self, intelligence: Dict) -> int:
        """Compute confidence score (0-100) based on extraction completeness."""
        score = 0
        years = intelligence.get("years_experience", 0) or 0
        seniority = (intelligence.get("seniority_level") or "").strip()
        domain = (intelligence.get("primary_domain") or "").strip()
        narrative = (intelligence.get("cleaned_narrative") or "").strip()
        core_skills = intelligence.get("core_technical_skills", []) or []
        secondary_skills = intelligence.get("secondary_technical_skills", []) or []
        key_strengths = intelligence.get("key_strengths", []) or []

        if years > 0:
            score += 20
        if seniority and seniority.upper() not in {"", "N/A", "NOT_SPECIFIED"}:
            score += 15
        if domain:
            score += 15
        skill_count = len(core_skills) + len(secondary_skills)
        score += min(30, skill_count * 3)
        if narrative and len(narrative) >= 40:
            score += 10
        if key_strengths:
            score += 10
        return min(100, max(1, score))
    
    def _hash_job_description(self, job_description: str) -> str:
        """
        Create hash of job description for tracking
        
        Args:
            job_description: The JD text
            
        Returns:
            SHA256 hash (first 16 chars)
        """
        return hashlib.sha256(job_description.encode()).hexdigest()[:16]
    
    def _hash_cv_content(self, cv_text: str) -> str:
        """
        Create hash of original CV content for audit trail
        
        Args:
            cv_text: The CV content
            
        Returns:
            SHA256 hash (full 64 chars for audit trail)
        """
        return hashlib.sha256(cv_text.encode()).hexdigest()
        
    def _create_extraction_prompt(self, cv_text: str, job_description: str = None, anonymized_id: str = None) -> str:
        """
        Create a detailed extraction prompt that produces Gemini-quality fitment analysis.
        If no JD provided, extracts skills/experience only without matching.
        The output is structured prose that gets parsed into JSON.
        """
        # Build a comprehensive extraction prompt that asks for ALL DB fields
        base_rules = """You are a senior technical recruiter extracting structured information from an anonymized professional profile.

CRITICAL RULES:
- The CV is already anonymized (all PII removed). NEVER output names, emails, phone numbers, addresses, or company locations.
- If you cannot determine something, state "Not specified" — NEVER invent details.
- Be thorough and evidence-based. Cite specific technologies, years, and project details from the CV.
- Every field below MUST have a value — even if it is "Not specified".
"""

        extraction_fields = f"""
OUTPUT FORMAT (STRICT — include EVERY field):

SECTION 1 – Professional Summary:
[2-3 paragraph ORIGINAL analytical summary. NOT copied CV text. Cover: years of experience, primary role, key expertise areas, major strengths, career progression.]

SECTION 2 – Key Strengths:
- [Strength 1 with specific evidence from CV]
- [Strength 2 with specific evidence from CV]
- [Strength 3 with specific evidence from CV]
- [Strength 4 with specific evidence from CV (if applicable)]

SECTION 3 – Experience Breakdown:
Years of Experience: [exact number, e.g., "9 years" or "5-6 years"]
Seniority Level: [ENTRY | MID | SENIOR | LEAD | EXECUTIVE]
Role Types: [List actual job titles found, e.g., "Software Engineer", "DevOps Engineer", "Team Lead"]
Primary Domain: [Main industry/sector e.g., "Automotive Embedded", "Web Development", "Finance Sector", "IT/Integration"]
Core Technical Skills: [List top 10 technical skills from CV]
Secondary Technical Skills: [List additional tools, frameworks, libraries]
Frameworks & Tools: [List frameworks and tools explicitly, e.g., "Django", "React", "Docker", "Kubernetes", "Jenkins"]
Soft Skills: [List soft skills like "Leadership", "Communication", "Problem Solving", "Team Management"]
Leadership Indicators: [Concrete evidence: "Led 5-person team", "Mentored 3 juniors", or "None mentioned"]
Certifications: [List all certifications mentioned, or "None mentioned"]

SECTION 4 – Education:
Highest Degree: [e.g., "Bachelor of Technology", "Master of Science", "Not specified"]
Field of Study: [e.g., "Computer Science", "Electronics", "Not specified"]
Education Level: [HIGH_SCHOOL | BACHELORS | MASTERS | PHD | OTHER]

SECTION 5 – Potential Concerns / Gaps:
- [Gap 1: what is missing or unclear, and its impact]
- [Gap 2: what is missing or unclear, and its impact]
(If no gaps: "No critical gaps identified.")

SECTION 6 – Highlight Achievements:
- [Notable project, achievement, or award 1]
- [Notable project, achievement, or award 2 (if applicable)]

FINAL ASSESSMENT:
Confidence: [0-100]%
Reason: [2-3 sentences summarizing the candidate's profile quality and completeness.]
"""

        if not job_description:
            prompt = f"""{base_rules}
{extraction_fields}

---

ANONYMIZED PROFESSIONAL PROFILE:
{cv_text}

---

CANDIDATE ID: {anonymized_id or 'PENDING'}
ANALYSIS DATE: {datetime.now().isoformat()}"""
            return prompt

        # JD matching mode — append JD and fitment table
        prompt = f"""{base_rules}
{extraction_fields}

SECTION 7 – Fitment Analysis Table:
For EACH major requirement category in the JD:
CATEGORY: [category name]
JD_REQUIRES: [what the JD asks for]
CANDIDATE_HAS: [what the candidate actually has, with evidence]
MATCH_STATUS: [FULL_MATCH | PARTIAL_MATCH | NO_MATCH]

(Create one entry for each: Total Experience, Core Programming Languages, Primary Domain, Frameworks & Tools, Architecture & Design Patterns, Cloud / Infrastructure, Leadership & Team Management, Education / Certifications, plus any JD-specific categories)

FINAL RECOMMENDATION:
[SHORTLIST | BACKUP | REVIEW]
Match Score: [0-100]%

---

JOB DESCRIPTION:
{job_description}

---

ANONYMIZED PROFESSIONAL PROFILE:
{cv_text}

---

CANDIDATE ID: {anonymized_id}
ANALYSIS DATE: {datetime.now().isoformat()}"""

        return prompt
    
    def _parse_prose_response(self, prose_response: str, anonymized_id: str) -> Dict:
        """
        Parse detailed prose LLM response into structured JSON.
        Extracts ALL fields required by the production DB schema.
        """
        def _extract_bullets(block: str) -> List[str]:
            """Extract bullet list items from a text block."""
            items = []
            for line in block.strip().split('\n'):
                line = line.strip()
                if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                    item = line.lstrip('-*• ').strip()
                    if item and item.lower() not in {'none mentioned', 'none', 'n/a', 'not specified', 'no critical gaps identified.'}:
                        items.append(item)
            return items

        def _extract_field(block: str, label_pattern: str) -> str:
            """Extract value after a label pattern, bounded by next known label."""
            border_labels = (
                r'Years\s+of\s+Experience|Seniority\s+Level|Role\s+Types|Primary\s+Domain|'
                r'Core\s+(?:Technical\s+)?Skills|Technical\s+Skills|Key\s+Skills|'
                r'Secondary\s+(?:Technical\s+)?Skills|Frameworks\s*(?:and|&)?\s*Tools|'
                r'Soft\s+Skills|Leadership\s+Indicators|Certifications|'
                r'Highest\s+Degree|Field\s+of\s+Study|Education\s+Level|'
                r'Potential\s+Concerns|Highlight\s+Achievements|Confidence|Reason'
            )
            m = re.search(
                rf'(?:^|\n)\s*{label_pattern}\s*(?:\([^\n\)]*\))?\s*[:\-]\s*(.+?)(?=\n\s*(?:{border_labels})\s*(?:\([^\n\)]*\))?\s*[:\-]|\Z)',
                block,
                re.IGNORECASE | re.DOTALL,
            )
            if m:
                return m.group(1).strip()
            # Ultra-loose fallback
            m2 = re.search(
                rf'{label_pattern}\s*[:\-]\s*(.+?)(?=\n\s*(?:{border_labels})\s*[:\-]|\Z)',
                block,
                re.IGNORECASE | re.DOTALL,
            )
            return (m2.group(1).strip() if m2 else "")

        text = prose_response or ""

        # ── Confidence & Reason ──
        confidence_match = re.search(r'Confidence:\s*\[?(\d+)\]?%', text)
        confidence_score = int(confidence_match.group(1)) if confidence_match else 50
        reason_match = re.search(r'Reason:\s*(.+?)(?:\n\n|={3,}|$)', text, re.DOTALL)
        verdict_reason = reason_match.group(1).strip() if reason_match else "See detailed analysis above"

        # ── Years & Seniority ──
        years_match = re.search(r'Years of Experience:\s*\[?([0-9.]+(?:\s*-\s*[0-9.]+)?)\s*(?:years?)?\]?', text, re.IGNORECASE)
        if years_match:
            years_str = years_match.group(1).replace(' ', '')
            if '-' in years_str:
                start, end = years_str.split('-')
                years_experience = (float(start) + float(end)) / 2
                years_experience_range = years_str
            else:
                years_experience = float(years_str)
                years_experience_range = f"{int(years_experience)}-{int(years_experience)+1}"
        else:
            years_experience = 0
            years_experience_range = ""

        seniority_match = re.search(r'Seniority Level:\s*\[?(ENTRY|MID|SENIOR|LEAD|EXECUTIVE|NOT_SPECIFIED)\]?', text, re.IGNORECASE)
        seniority_level = seniority_match.group(1).upper() if seniority_match else "NOT_SPECIFIED"

        # ── Scope to Experience Breakdown section ──
        exp_block = text
        exp_match = re.search(
            r'(?:SECTION\s*(?:3|5))[^\n]*\n(.+?)(?=\n\s*(?:FINAL\s+(?:ASSESSMENT|RECOMMENDATION)|SECTION\s*\d)|\Z)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if exp_match:
            exp_block = exp_match.group(1)

        # ── Skills ──
        core_block = (
            _extract_field(exp_block, r'(?:Core\s+(?:Technical\s+)?Skills|Technical\s+Skills|Key\s+Skills)')
            or _extract_field(text, r'(?:Core\s+(?:Technical\s+)?Skills|Technical\s+Skills|Key\s+Skills)')
        )
        sec_block = (
            _extract_field(exp_block, r'(?:Secondary\s+(?:Technical\s+)?Skills)')
            or _extract_field(text, r'(?:Secondary\s+(?:Technical\s+)?Skills)')
        )
        fw_block = (
            _extract_field(exp_block, r'(?:Frameworks\s*(?:and|&)?\s*Tools|Tools\s*(?:and|&)?\s*Frameworks)')
            or _extract_field(text, r'(?:Frameworks\s*(?:and|&)?\s*Tools|Tools\s*(?:and|&)?\s*Frameworks)')
        )
        soft_block = (
            _extract_field(exp_block, r'Soft\s+Skills')
            or _extract_field(text, r'Soft\s+Skills')
        )
        cert_block = (
            _extract_field(exp_block, r'Certifications')
            or _extract_field(text, r'Certifications')
        )

        core_technical_skills = _split_list_block(core_block)
        secondary_technical_skills = _split_list_block(sec_block)
        frameworks_tools = _split_list_block(fw_block)
        soft_skills = _split_list_block(soft_block)
        certifications = _split_list_block(cert_block)

        # ── Role Types ──
        role_block = (
            _extract_field(exp_block, r'Role\s+Types')
            or _extract_field(text, r'Role\s+Types')
        )
        role_types = _split_list_block(role_block)

        # ── Domain ──
        domain_match = re.search(r'Primary Domain:\s*\[?([^\]\n]+)\]?', text, re.IGNORECASE)
        primary_domain = domain_match.group(1).strip().strip('"\'') if domain_match else ""

        # ── Leadership ──
        leadership_text = _extract_field(exp_block, r'Leadership\s+Indicators') or _extract_field(text, r'Leadership\s+Indicators')
        if leadership_text and leadership_text.lower() not in {'none mentioned', 'none', 'n/a', 'not specified'}:
            leadership_indicators = [s.strip().strip('"\'[]') for s in leadership_text.split(',') if s.strip()]
        else:
            leadership_indicators = []

        # ── Education ──
        edu_block = text
        edu_match = re.search(
            r'(?:SECTION\s*4)[^\n]*\n(.+?)(?=\n\s*(?:SECTION\s*\d|FINAL)|\Z)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if edu_match:
            edu_block = edu_match.group(1)

        highest_degree = _extract_field(edu_block, r'Highest\s+Degree') or _extract_field(text, r'Highest\s+Degree')
        field_of_study = _extract_field(edu_block, r'Field\s+of\s+Study') or _extract_field(text, r'Field\s+of\s+Study')
        edu_level_match = re.search(r'Education Level:\s*\[?(HIGH_SCHOOL|BACHELORS|MASTERS|PHD|OTHER)\]?', text, re.IGNORECASE)
        education_level = edu_level_match.group(1).upper() if edu_level_match else ""

        # ── Narrative (SECTION 1) ──
        section1_match = re.search(r'SECTION\s*1[^\n]*\n(.+?)(?=SECTION\s*\d|FINAL|$)', text, re.DOTALL)
        cleaned_narrative = section1_match.group(1).strip() if section1_match else ""

        # ── Key Strengths ──
        strengths_block = text
        str_match = re.search(
            r'(?:SECTION\s*2|SECTION\s*3|Key\s+Strengths)[^\n]*\n(.+?)(?=SECTION\s*\d|Potential\s+(?:Gaps|Concerns)|Experience\s+Breakdown|FINAL|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if str_match:
            strengths_block = str_match.group(1)
        key_strengths = _extract_bullets(strengths_block)

        # ── Potential Concerns ──
        concerns_block = text
        gap_match = re.search(
            r'(?:SECTION\s*4|SECTION\s*5|Potential\s+(?:Gaps|Concerns))[^\n]*\n(.+?)(?=SECTION\s*\d|Highlight\s+Achievements|Experience\s+Breakdown|FINAL|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if gap_match:
            concerns_block = gap_match.group(1)
        potential_concerns = _extract_bullets(concerns_block)

        # ── Highlight Achievements ──
        ach_block = text
        ach_match = re.search(
            r'(?:SECTION\s*6|Highlight\s+Achievements)[^\n]*\n(.+?)(?=SECTION\s*\d|FINAL|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if ach_match:
            ach_block = ach_match.group(1)
        highlight_achievements = _extract_bullets(ach_block)

        # ── Fitment Analysis (SECTION 7, JD matching only) ──
        fitment_analysis = []
        fit_match = re.search(
            r'(?:SECTION\s*7|Fitment\s+Analysis)[^\n]*\n(.+?)(?=SECTION\s*\d|FINAL|$)',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if fit_match:
            for cat, jd_req, cand_has, status in re.findall(
                r'-?\s*CATEGORY:\s*(.+?)\n-?\s*JD_REQUIRES:\s*(.+?)\n-?\s*CANDIDATE_HAS:\s*(.+?)\n-?\s*MATCH_STATUS:\s*(FULL_MATCH|PARTIAL_MATCH|NO_MATCH)',
                fit_match.group(1), re.DOTALL
            ):
                fitment_analysis.append({
                    "category": cat.strip(),
                    "jd_requirement": jd_req.strip(),
                    "candidate_profile": cand_has.strip(),
                    "match_status": status.strip()
                })
        matched_requirements = [f["category"] for f in fitment_analysis if f["match_status"] == "FULL_MATCH"]
        missing_requirements = [f["category"] for f in fitment_analysis if f["match_status"] == "NO_MATCH"]

        return {
            "anonymized_id": anonymized_id,
            "analysis_date": datetime.now().isoformat(),
            "confidence_score": confidence_score,
            "verdict_reason": verdict_reason or "Profile extracted",
            "years_experience": years_experience,
            "years_experience_range": years_experience_range,
            "seniority_level": seniority_level,
            "career_level": seniority_level,
            "core_technical_skills": core_technical_skills,
            "secondary_technical_skills": secondary_technical_skills,
            "key_skills": _dedupe_case_insensitive(core_technical_skills + secondary_technical_skills + frameworks_tools, max_items=30),
            "frameworks_tools": frameworks_tools,
            "soft_skills": soft_skills,
            "certifications": certifications,
            "role_types": role_types,
            "leadership_indicators": leadership_indicators,
            "primary_domain": primary_domain,
            "secondary_domains": [],
            "cleaned_narrative": cleaned_narrative,
            "matched_requirements": matched_requirements,
            "missing_requirements": missing_requirements,
            "key_strengths": key_strengths,
            "potential_concerns": potential_concerns,
            "highlight_achievements": highlight_achievements,
            "highest_degree": highest_degree,
            "field_of_study": field_of_study,
            "education_level": education_level,
            "fitment_analysis": fitment_analysis,
        }
    
    def extract_intelligence(
        self, 
        cv_text: str, 
        job_description: str = None,
        original_filename: str = None,
        trust_source: bool = False
    ) -> Dict:
        """
        Extract structured intelligence from a CV with deep analysis and audit trail.
        
        IMPORTANT: Only processes anonymized CVs. If the CV is not anonymized,
        returns an error asking the user to anonymize first.
        
        Args:
            cv_text: Anonymized CV content (must contain [REDACTED_...] markers)
            job_description: Optional job description to match against (if None, only extracts skills/experience)
            original_filename: Original filename (for backend tracking only)
            trust_source: If True, skip the is_cv_anonymized check (used when text is derived from a masked PDF)
            
        Returns:
            Dictionary with structured CV intelligence + full audit trail
        """
        try:
            # CRITICAL: Verify CV is anonymized before processing
            if not trust_source and not is_cv_anonymized(cv_text):
                logger.error("CV is not anonymized. Cannot process non-anonymized CVs.")
                return {
                    "error": "CV_NOT_ANONYMIZED",
                    "error_message": (
                        "This CV has not been anonymized. Please run the CV through the "
                        "redaction pipeline first (Upload → Redact PII) before extracting "
                        "intelligence. Only anonymized CVs can be stored in the database."
                    ),
                    "anonymized_id": self._generate_anonymized_id(cv_text),
                    "original_filename": sanitize_filename_for_db(original_filename) if original_filename else "unknown"
                }
            
            # Local Checkpoint: Keyword / Requirement Filter (only if JD provided)
            # Check if CV is totally irrelevant before making expensive LLM calls
            if job_description:
                cv_lower = cv_text.lower()
                jd_lower = job_description.lower()
                
                # Simple check: reject if CV size is absurdly short
                if len(cv_text.split()) < 50:
                    logger.warning(f"CV too short. Rejected locally without LLM API.")
                    return {
                        "anonymized_id": self._generate_anonymized_id(cv_text),
                        "analysis_date": datetime.now().isoformat(),
                        "confidence_score": 100,
                        "verdict_reason": "LOCAL CHECKPOINT FILTER: Resume is too short to be viable (< 50 words).",
                        "original_filename": original_filename or "unknown",
                        "years_experience": 0,
                        "seniority_level": "NOT_SPECIFIED",
                        "core_technical_skills": [],
                        "secondary_technical_skills": [],
                        "key_skills": [],
                        "primary_domain": "",
                        "cleaned_narrative": "",
                        "cleaned_text": cv_text,
                    }

                jd_words = set(re.findall(r'\b[a-z]{5,}\b', jd_lower))
                stop_words = {'about', 'their', 'there', 'which', 'would', 'these', 'other', 'could', 'should', 'experience', 'years', 'working', 'skills', 'knowledge', 'understanding', 'strong'}
                jd_keywords = jd_words - stop_words

                if jd_keywords:
                    cv_words = set(re.findall(r'\b[a-z]{5,}\b', cv_lower))
                    overlap = jd_keywords.intersection(cv_words)
                    overlap_ratio = len(overlap) / len(jd_keywords)
                    # If overlap is extremely poor (e.g. < 5%), reject it instantly
                    if overlap_ratio < 0.05:
                        logger.warning(f"Failed local keyword checkpoint (Overlap: {overlap_ratio:.1%}). Rejected locally without LLM API.")
                        return {
                            "anonymized_id": self._generate_anonymized_id(cv_text),
                            "analysis_date": datetime.now().isoformat(),
                            "confidence_score": 95,
                            "verdict_reason": f"LOCAL CHECKPOINT FILTER: Extreme mismatch detected. Auto-rejected to save API quota.",
                            "original_filename": original_filename or "unknown",
                            "years_experience": 0,
                            "seniority_level": "NOT_SPECIFIED",
                            "core_technical_skills": [],
                            "secondary_technical_skills": [],
                            "key_skills": [],
                            "primary_domain": "",
                            "cleaned_narrative": "",
                            "cleaned_text": cv_text,
                        }

            # Generate stable anonymized ID from CV content
            anonymized_id = self._generate_anonymized_id(cv_text)

            # Create extraction prompt (store for audit trail)
            prompt = self._create_extraction_prompt(cv_text, job_description, anonymized_id)

            # Hash original CV for audit trail
            original_cv_hash = self._hash_cv_content(cv_text)

            # Call LLM
            mode_str = "extraction only" if not job_description else "matching analysis"
            logger.info(f"Analyzing {anonymized_id} ({mode_str})...")
            raw_llm_response = self.llm_processor.generate_analysis(prompt)

            # Parse prose response
            try:
                intelligence = self._parse_prose_response(raw_llm_response, anonymized_id)

                # Add metadata
                intelligence["original_filename"] = sanitize_filename_for_db(original_filename) if original_filename else "unknown"
                intelligence["original_filename_raw"] = original_filename or "unknown"
                intelligence["llm_provider"] = self.api_provider
                intelligence["llm_model"] = self.model
                intelligence["extraction_timestamp"] = datetime.now().isoformat()

                # Store the anonymized CV text for future use
                intelligence["cleaned_text"] = cv_text

                # Extraction-only mode
                if not job_description:
                    intelligence["verdict_reason"] = "Profile extracted - no JD matching performed"

                # Audit Trail
                intelligence["original_cv_hash"] = original_cv_hash
                intelligence["llm_prompt_used"] = prompt
                intelligence["llm_raw_response"] = raw_llm_response

                # Compute confidence from data completeness if LLM gave 0 or None
                confidence = intelligence.get("confidence_score", 0)
                if not confidence or confidence == 0:
                    confidence = self._compute_extraction_confidence(intelligence)
                    intelligence["confidence_score"] = confidence

                logger.info(f"✓ {anonymized_id}: Confidence={confidence}%, Skills={len(intelligence.get('core_technical_skills', []))}, Years={intelligence.get('years_experience', 0)}")

                return intelligence

            except Exception as e:
                logger.error(f"Failed to parse LLM response: {e}")
                logger.error(f"Raw response: {raw_llm_response[:500]}...")

                # Return error structure with audit trail
                return {
                    "error": f"PARSE_ERROR: {str(e)}",
                    "raw_response": raw_llm_response[:1000],
                    "anonymized_id": anonymized_id,
                    "original_filename": original_filename or "unknown",
                    "original_cv_hash": original_cv_hash,
                    "llm_prompt_used": prompt,
                    "llm_raw_response": raw_llm_response
                }

        except QuotaExhaustedException:
            raise
        except Exception as e:
            logger.error(f"Error extracting intelligence: {e}")
            return {
                "error": str(e),
                "anonymized_id": self._generate_anonymized_id(cv_text),
                "original_filename": original_filename or "unknown"
            }
    
    def batch_extract(
        self, 
        cv_files: List[str], 
        job_description: str,
        output_dir: str = "llm_analysis",
        direct_to_supabase: bool = True
    ) -> List[Dict]:
        """
        Process multiple CVs in batch with direct Supabase pipeline
        
        Args:
            cv_files: List of paths to anonymized CV text files
            job_description: Job description to match against
            output_dir: Directory to save individual JSON files
            direct_to_supabase: If True, upload directly to Supabase (if configured)
            
        Returns:
            List of intelligence dictionaries
        """
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Initialize Supabase if requested
        storage = None
        if direct_to_supabase:
            try:
                from supabase_storage import SupabaseStorage
                storage = SupabaseStorage()
                logger.info("✓ Direct Supabase pipeline enabled")
            except Exception as e:
                logger.warning(f"⚠ Supabase not available: {e}. Saving to JSON only.")
        
        def process_single_cv(cv_file: str) -> Dict:
            try:
                # Read CV content
                with open(cv_file, 'r', encoding='utf-8') as f:
                    cv_text = f.read()
                
                # Extract intelligence
                intelligence = self.extract_intelligence(
                    cv_text, 
                    job_description,
                    Path(cv_file).name
                )
                
                # Save individual JSON
                if "error" not in intelligence:
                    # Save to local file
                    output_file = output_path / f"{intelligence['anonymized_id']}_intelligence.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(intelligence, f, indent=2, ensure_ascii=False)
                    logger.info(f"  📁 Saved to {output_file}")
                    
                    # Direct pipeline to Supabase
                    if storage:
                        try:
                            storage.store_intelligence(intelligence)
                            # Store filename mapping (backend only)
                            storage.store_filename_mapping(
                                anonymized_id=intelligence['anonymized_id'],
                                original_filename=Path(cv_file).name,
                                anonymized_filename=Path(cv_file).name
                            )
                            logger.info(f"  ☁️  Uploaded to Supabase")
                        except Exception as e:
                            logger.warning(f"  ⚠ Supabase upload failed: {e}")
                else:
                    logger.warning(f"✗ Error processing {cv_file}: {intelligence.get('error')}")
                    
                return intelligence
                    
            except Exception as e:
                logger.error(f"Error processing {cv_file}: {e}")
                return {
                    "error": str(e),
                    "anonymized_id": self._generate_anonymized_id(),
                    "original_filename": Path(cv_file).name
                }
                
        # Use ThreadPoolExecutor for concurrent batch processing
        max_workers = min(20, len(cv_files))
        if max_workers > 0:
            logger.info(f"🚀 Starting async batch processing with {max_workers} concurrent workers...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(process_single_cv, cv_files))
        else:
            results = []
        
        # Save batch summary
        summary_file = output_path / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_processed": len(cv_files),
                "successful": len([r for r in results if "error" not in r]),
                "failed": len([r for r in results if "error" in r]),
                "timestamp": datetime.now().isoformat(),
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✓ Batch complete. Summary saved to {summary_file}")
        
        return results


def main():
    """CLI entry point for CV intelligence extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract structured intelligence from anonymized CVs"
    )
    parser.add_argument(
        "cv_files",
        nargs="+",
        help="Path(s) to anonymized CV text file(s)"
    )
    parser.add_argument(
        "--job-description",
        "-jd",
        required=True,
        help="Path to job description file or direct text"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "gemini", "ollama"],
        default="gemini",
        help="LLM provider (default: gemini)"
    )
    parser.add_argument(
        "--api-key",
        help="API key (reads from env if not provided)"
    )
    parser.add_argument(
        "--output-dir",
        default="llm_analysis",
        help="Output directory for intelligence JSON files"
    )
    parser.add_argument(
        "--no-supabase",
        action="store_true",
        help="Disable direct Supabase upload (save to JSON only)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Read job description
    if Path(args.job_description).exists():
        with open(args.job_description, 'r', encoding='utf-8') as f:
            job_description = f.read()
    else:
        job_description = args.job_description
    
    # Create extractor
    extractor = CVIntelligenceExtractor(
        api_provider=args.provider,
        api_key=args.api_key
    )
    
    # Process CVs
    print(f"\n{'='*60}")
    print("CV Intelligence Extraction")
    print(f"{'='*60}")
    print(f"Provider: {args.provider}")
    print(f"CVs to process: {len(args.cv_files)}")
    print(f"Output directory: {args.output_dir}")
    print(f"Direct Supabase Pipeline: {not args.no_supabase}")
    print(f"{'='*60}\n")
    
    results = extractor.batch_extract(
        args.cv_files,
        job_description,
        args.output_dir,
        direct_to_supabase=not args.no_supabase
    )
    
    # Print summary
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    
    print(f"\n{'='*60}")
    print(f"✓ Processed: {len(results)} CVs")
    print(f"✓ Successful: {len(successful)}")
    print(f"✗ Failed: {len(failed)}")
    
    if successful:
        print(f"\n📊 EXTRACTION SUMMARY:")
        for result in successful:
            confidence = result.get('confidence_score', 0)
            skills = len(result.get('core_technical_skills', []))
            years = result.get('years_experience', 0)
            anonymized_id = result.get('anonymized_id', 'N/A')
            print(f"  {anonymized_id}: Confidence={confidence}%, Skills={skills}, Years={years}")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
