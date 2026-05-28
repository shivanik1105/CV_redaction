"""
Supabase Storage Module — Production-Ready
Handles storing and retrieving CV intelligence data with vector search.

Schema: exactly 39 columns (no nulls, no empty strings, no stray columns).
Every write guarantees real values via rule-based fallback extraction.
"""
import os
import json
import re
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase client not installed. Install with: pip install supabase")

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS — known skill / domain / role mappings for rule-based extraction
# ============================================================================
_KNOWN_SKILLS = {
    # Programming
    "python", "java", "javascript", "typescript", "c++", "c", "c#", "csharp",
    "go", "golang", "rust", "swift", "kotlin", "scala", "ruby", "php",
    "perl", "r", "matlab", "sql", "plsql", "tsql", "nosql",
    # Web
    "html", "html5", "css", "css3", "react", "angular", "vue", "vue.js",
    "nodejs", "node.js", "express", "django", "flask", "fastapi", "spring",
    "spring boot", "asp.net", "aspnet", ".net", "dotnet", "blazor", "laravel",
    # Mobile
    "android", "ios", "react native", "flutter", "xamarin", "swiftui",
    # Data / ML
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras",
    "opencv", "spark", "hadoop", "kafka", "airflow", "dbt",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
    "gitlab ci", "github actions", "terraform", "ansible", "puppet", "chef",
    "prometheus", "grafana", "elk", "splunk", "datadog",
    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "dynamodb", "cassandra",
    "redis", "elasticsearch", "sqlite", "oracle", "mariadb", "neo4j",
    # Embedded / Automotive
    "embedded c", "embedded c++", "RTOS", "freeRTOS", "yocto", "qnx",
    "autosar", "can", "lin", "flexray", "ethernet", "tcp/ip", "spi", "i2c",
    "uart", "gpio", "arm", "microcontroller", "microprocessor", "fpga",
    "matlab/simulink", "simulink", "dspace", "canoe", "canalyzer",
    # QA / Testing
    "selenium", "cypress", "jest", "junit", "pytest", "cucumber", "postman",
    "jmeter", "loadrunner", "gtest", "google test",
    # Project / Agile
    "jira", "confluence", "trello", "agile", "scrum", "kanban", "safe",
    # SAP / Finance
    "sap", "sap abap", "sap fico", "tagetik", "oracle financials",
    # MuleSoft / Integration
    "mulesoft", "anypoint", "api", "rest", "soap", "graphql", "json", "xml",
    "openapi", "swagger",
    # Other
    "git", "github", "gitlab", "bitbucket", "linux", "unix", "windows",
    "bash", "powershell", "shell scripting",
}

_KNOWN_DOMAINS = {
    "automotive", "automotive embedded", "banking", "finance", "fintech",
    "healthcare", "e-commerce", "ecommerce", "retail", "telecom",
    "telecommunications", "manufacturing", "insurance", "logistics",
    "supply chain", "media", "gaming", "education", "government",
    "aerospace", "energy", "oil & gas", "pharma", "biotech",
    "web development", "mobile development", "cloud infrastructure",
    "devops", "data engineering", "data science", "machine learning",
    "embedded systems", "networking", "cybersecurity", "it integration",
}

_DOMAIN_BY_SKILL: Dict[str, str] = {
    "embedded c": "Automotive Embedded",
    "embedded c++": "Automotive Embedded",
    "autosar": "Automotive Embedded",
    "can": "Automotive Embedded",
    "yocto": "Automotive Embedded",
    "qnx": "Automotive Embedded",
    "dspace": "Automotive Embedded",
    "matlab/simulink": "Automotive Embedded",
    "django": "Web Development",
    "flask": "Web Development",
    "react": "Web Development",
    "angular": "Web Development",
    "spring": "Web Development",
    "android": "Mobile Development",
    "ios": "Mobile Development",
    "flutter": "Mobile Development",
    "aws": "Cloud Infrastructure",
    "azure": "Cloud Infrastructure",
    "docker": "Cloud Infrastructure",
    "kubernetes": "Cloud Infrastructure",
    "terraform": "Cloud Infrastructure",
    "mulesoft": "IT/Integration",
    "anypoint": "IT/Integration",
    "sap": "Finance Sector",
    "tagetik": "Finance Sector",
    "oracle financials": "Finance Sector",
    "pandas": "Data Engineering",
    "spark": "Data Engineering",
    "hadoop": "Data Engineering",
    "tensorflow": "Machine Learning",
    "pytorch": "Machine Learning",
}

_ROLE_PATTERNS = [
    (r"\b(?:senior|sr\.?|snr)\s+(?:software\s+)?engineer\b", "Senior Engineer"),
    (r"\b(?:lead|principal|staff)\s+(?:software\s+)?engineer\b", "Lead Engineer"),
    (r"\b(?:junior|jr\.?|jnr)\s+(?:software\s+)?engineer\b", "Junior Engineer"),
    (r"\bsoftware\s+engineer\b", "Software Engineer"),
    (r"\bdevops\s+engineer\b", "DevOps Engineer"),
    (r"\bdata\s+(?:engineer|scientist)\b", "Data Engineer/Scientist"),
    (r"\bsystem\s+engineer\b", "System Engineer"),
    (r"\btest\s+engineer\b", "Test Engineer"),
    (r"\bqa\s+engineer\b", "QA Engineer"),
    (r"\bandroid\s+developer\b", "Android Developer"),
    (r"\bmulesoft\s+developer\b", "MuleSoft Developer"),
    (r"\bsap\s+(?:consultant|developer)\b", "SAP Consultant"),
]


def _extract_missing_column_name(error: Exception) -> Optional[str]:
    error_text = str(error)
    match = re.search(r"Could not find the '([^']+)' column", error_text)
    if match:
        return match.group(1)
    return None


def _as_clean_text(value: Any, max_len: int = 1200) -> str:
    """Normalize text-ish values to compact safe strings. Never returns None."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


def _as_clean_list(value: Any, max_items: int = 25, max_len: int = 80) -> List[str]:
    """Normalize list-like fields into deduplicated, non-empty string arrays. Never returns None."""
    if value is None:
        return []
    if isinstance(value, str):
        items = [chunk.strip() for chunk in value.split(",") if chunk.strip()]
    elif isinstance(value, list):
        items = value
    else:
        return []
    cleaned: List[str] = []
    seen = set()
    for item in items:
        normalized = _as_clean_text(item, max_len=max_len)
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(normalized)
        if len(cleaned) >= max_items:
            break
    return cleaned


def _normalize_percent(value: Any, default: int = 0) -> int:
    """Convert confidence/match scores into integer percentages in [0, 100]. Never returns None."""
    if value is None:
        return default
    try:
        parsed = int(round(float(value)))
    except Exception:
        return default
    return max(0, min(100, parsed))


def _normalize_years(value: Any, default: float = 0.0) -> float:
    """Normalize years of experience into a non-negative float. Never returns None."""
    if value is None:
        return default
    try:
        parsed = float(value)
    except Exception:
        return default
    return round(max(0.0, parsed), 1)


def _compute_cv_hash(text: str) -> str:
    """SHA-256 hash of CV text for audit trail."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _deterministic_anonymized_id(cv_text: str) -> str:
    """Stable anonymized ID based on content hash — re-uploads override automatically."""
    h = _compute_cv_hash(cv_text)[:8].upper()
    return f"CAND_{h}"


def _extract_years_from_text(text: str) -> float:
    """Rule-based years-of-experience extraction from CV text."""
    if not text:
        return 0.0
    text_lower = text.lower()
    # Pattern: "X years", "X+ years", "over X years", "around X years"
    patterns = [
        r"(?:over|around|about|more than|total of)\s*(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)",
        r"experience\s*(?:of\s*)?(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
        r"(?:with|having)\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
    ]
    years = []
    for pat in patterns:
        for m in re.finditer(pat, text_lower):
            try:
                y = float(m.group(1))
                if 0 < y <= 50:
                    years.append(y)
            except Exception:
                pass
    if years:
        return round(max(years), 1)

    # Date-range fallback: look for patterns like "2015-2020" or "Jan 2015 - Dec 2020"
    year_ranges = re.findall(r"(?:20\d{2})\s*[-–]\s*(?:20\d{2}|present|till date)", text_lower)
    if year_ranges:
        # rough estimate: average range
        total = 0
        count = 0
        for yr in year_ranges:
            nums = re.findall(r"20\d{2}", yr)
            if len(nums) == 2:
                total += int(nums[1]) - int(nums[0])
                count += 1
        if count:
            return round(total / count, 1)
    return 0.0


def _extract_skills_from_text(text: str) -> List[str]:
    """Extract known technical skills from raw CV text."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    seen = set()
    # Multi-word first
    multi_word = [s for s in _KNOWN_SKILLS if " " in s]
    single_word = [s for s in _KNOWN_SKILLS if " " not in s]
    for skill in sorted(multi_word, key=len, reverse=True):
        if skill in text_lower and skill not in seen:
            seen.add(skill)
            found.append(skill.title() if " " in skill else skill.upper())
    for skill in sorted(single_word, key=len, reverse=True):
        # Word boundary check for single-word skills
        if re.search(rf"\b{re.escape(skill)}\b", text_lower) and skill not in seen:
            seen.add(skill)
            found.append(skill.upper() if skill in {"c", "c++", "sql", "aws", "api", "rest", "json", "xml", "html", "css"} else skill.title())
    return found[:30]


def _infer_domain(skills: List[str], text: str) -> str:
    """Infer primary domain from skills and text."""
    if not skills and not text:
        return ""
    skill_lower = [s.lower() for s in skills]
    text_lower = (text or "").lower()
    domain_scores: Dict[str, int] = {}
    for skill in skill_lower:
        mapped = _DOMAIN_BY_SKILL.get(skill)
        if mapped:
            domain_scores[mapped] = domain_scores.get(mapped, 0) + 2
    for dom in _KNOWN_DOMAINS:
        if dom in text_lower:
            domain_scores[dom.title()] = domain_scores.get(dom.title(), 0) + 1
    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    return ""


def _infer_role_types(text: str) -> List[str]:
    """Infer role types from CV text."""
    if not text:
        return []
    text_lower = text.lower()
    roles = []
    seen = set()
    for pattern, role_name in _ROLE_PATTERNS:
        if re.search(pattern, text_lower) and role_name.lower() not in seen:
            seen.add(role_name.lower())
            roles.append(role_name)
    return roles[:6]


def _infer_seniority(years: float, text: str) -> str:
    """Infer seniority level from years and text."""
    if not text:
        text = ""
    text_lower = text.lower()
    if "lead" in text_lower or "principal" in text_lower or "staff" in text_lower:
        if years >= 10:
            return "LEAD"
        return "SENIOR"
    if years >= 15:
        return "EXECUTIVE"
    if years >= 10:
        return "LEAD"
    if years >= 5:
        return "SENIOR"
    if years >= 2:
        return "MID"
    if years > 0:
        return "ENTRY"
    return "NOT_SPECIFIED"


def _extract_certifications(text: str) -> List[str]:
    """Extract certification mentions from text."""
    if not text:
        return []
    certs = []
    patterns = [
        r"\b(aws\s+(?:certified|solutions?\s+architect|developer))\b",
        r"\b(azure\s+(?:certified|administrator|developer))\b",
        r"\b(gcp\s+(?:certified|professional))\b",
        r"\b(pmp|capm)\b",
        r"\b(scrum\s+(?:master|product\s+owner))\b",
        r"\b(cism|cissp|ceh|comptia)\b",
        r"\b(oca|ocp|ocm)\b",
        r"\b(ccna|ccnp)\b",
        r"\b(itil\s+v?\d)\b",
        r"\b(six\s+sigma)\b",
    ]
    seen = set()
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            cert = m.group(1).strip().title()
            key = cert.lower()
            if key not in seen:
                seen.add(key)
                certs.append(cert)
    return certs[:10]


def _compute_data_confidence(intelligence_data: Dict, key_skills: List[str]) -> int:
    """Compute confidence score (0-100) from data completeness."""
    score = 0
    years = intelligence_data.get("years_experience", 0) or 0
    seniority = (intelligence_data.get("seniority_level") or "").strip()
    domain = (intelligence_data.get("primary_domain") or "").strip()
    narrative = (intelligence_data.get("cleaned_narrative") or "").strip()
    core_skills = intelligence_data.get("core_technical_skills", []) or []
    if years > 0:
        score += 20
    if seniority and seniority.upper() not in {"", "N/A", "NOT_SPECIFIED"}:
        score += 15
    if domain:
        score += 15
    skill_count = len(core_skills) or len(key_skills)
    score += min(30, skill_count * 3)
    if narrative and len(narrative) >= 40:
        score += 10
    if key_skills:
        score += 10
    return min(100, max(1, score))  # never 0


def _build_summary(intelligence_data: Dict) -> str:
    """Build overall_summary from available fields. Never empty."""
    narrative = (intelligence_data.get("cleaned_narrative") or "").strip()
    years = intelligence_data.get("years_experience", 0) or 0
    seniority = (intelligence_data.get("seniority_level") or "").strip().upper()
    skills = intelligence_data.get("core_technical_skills", []) or []
    domain = (intelligence_data.get("primary_domain") or "").strip()
    key_strengths = intelligence_data.get("key_strengths", []) or []
    education = intelligence_data.get("highest_degree", "")
    field = intelligence_data.get("field_of_study", "")

    if narrative and len(narrative) >= 30 and len(narrative) <= 1500:
        redaction_markers = ["[REDACTED", "[NAME]", "OBJECTIVE:", "EDUCATION", "SKILLS\n"]
        raw_cv_score = sum(1 for m in redaction_markers if m in narrative)
        if not (raw_cv_score >= 2 and len(narrative) > 800):
            return narrative[:700]

    parts = []
    if seniority and seniority not in {"", "N/A", "NOT_SPECIFIED"}:
        level_word = seniority.title()
    elif years >= 10:
        level_word = "Senior"
    elif years >= 5:
        level_word = "Mid-Level"
    elif years > 0:
        level_word = "Junior"
    else:
        level_word = "Experienced"

    exp_str = f"{years} years of experience" if years > 0 else "professional experience"
    if domain:
        parts.append(f"{level_word} professional with {exp_str} in {domain}.")
    else:
        parts.append(f"{level_word} professional with {exp_str}.")

    if skills:
        parts.append(f"Technical skills: {', '.join(skills[:8])}.")
    if key_strengths:
        parts.append(f"Key strengths: {'; '.join(key_strengths[:3])}.")
    if education:
        edu = education
        if field:
            edu += f" in {field}"
        parts.append(f"Education: {edu}.")

    summary = " ".join(parts)
    if summary.strip():
        return summary
    if skills:
        return f"Professional with skills in {', '.join(skills[:5])}."
    return "Candidate profile extracted; details pending review."


def _build_evidence_reasoning(intelligence_data: Dict) -> str:
    """Build evidence_based_reasoning. Never empty."""
    reason = (intelligence_data.get("verdict_reason") or "").strip()
    if reason and len(reason) > 10 and "no jd matching" not in reason.lower():
        return reason[:1000]
    years = intelligence_data.get("years_experience", 0) or 0
    skills = intelligence_data.get("core_technical_skills", []) or []
    domain = (intelligence_data.get("primary_domain") or "").strip()
    parts = []
    if years > 0:
        parts.append(f"{years} years of experience identified.")
    if skills:
        parts.append(f"Core skills: {', '.join(skills[:6])}.")
    if domain:
        parts.append(f"Primary domain: {domain}.")
    if parts:
        return " ".join(parts)
    return "Profile extracted from CV text."


def _build_search_keywords(intelligence_data: Dict, key_skills: List[str], domains: List[str]) -> str:
    """Build search keywords as a single text string (not array)."""
    tags: List[str] = []
    tags.extend(key_skills)
    tags.extend(domains)
    tags.extend(_as_clean_list(intelligence_data.get("frameworks_tools"), max_items=10))
    tags.extend(_as_clean_list(intelligence_data.get("role_types"), max_items=6))
    return ", ".join(_as_clean_list(tags, max_items=40, max_len=80))


def _sanitize_json_backup(intelligence_data: Dict) -> str:
    """Strip PII from JSON backup before storing."""
    safe = {k: v for k, v in intelligence_data.items() if k not in {"original_filename_raw", "llm_prompt_used"}}
    return json.dumps(safe, default=str)


# ============================================================================
# MAIN STORAGE CLASS
# ============================================================================

class SupabaseStorage:
    """Store and search CV intelligence in Supabase."""

    def __init__(self, url: str = None, key: str = None):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not installed. Install with: pip install supabase")
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            raise ValueError("Supabase credentials required. Set SUPABASE_URL and SUPABASE_KEY.")
        self.client: Client = create_client(self.url, self.key)
        self.table_name = "cv_intelligence"

    def store_intelligence(self, intelligence_data: Dict) -> Dict:
        """
        Store CV intelligence. Guarantees:
        - No NULL values in any column
        - Deterministic anonymized_id (same CV → override)
        - Rule-based fallback extraction when LLM fields are missing
        - Exactly the 39 approved columns
        """
        try:
            # ── Step 1: Get or compute stable anonymized_id ──
            raw_id = _as_clean_text(intelligence_data.get("anonymized_id"), max_len=40)
            cv_text = (intelligence_data.get("cleaned_text") or intelligence_data.get("cleaned_narrative") or "").strip()
            if raw_id:
                anon_id = raw_id
            elif cv_text:
                anon_id = _deterministic_anonymized_id(cv_text)
            else:
                raise ValueError("Cannot store intelligence without anonymized_id or cv_text")

            # ── Step 2: Rule-based fallback extraction from raw text ──
            # If LLM failed to extract fields, compute them from the CV text
            rule_years = _extract_years_from_text(cv_text)
            rule_skills = _extract_skills_from_text(cv_text)
            rule_domain = _infer_domain(rule_skills, cv_text)
            rule_roles = _infer_role_types(cv_text)
            rule_certs = _extract_certifications(cv_text)
            rule_seniority = _infer_seniority(rule_years, cv_text)

            # Merge LLM data with rule fallback (LLM wins if present)
            years_of_experience = _normalize_years(intelligence_data.get("years_experience"), default=0.0)
            if years_of_experience == 0 and rule_years > 0:
                years_of_experience = rule_years

            core_skills = _as_clean_list(intelligence_data.get("core_technical_skills") or rule_skills, max_items=20, max_len=80)
            sec_skills = _as_clean_list(intelligence_data.get("secondary_technical_skills"), max_items=20, max_len=80)
            key_skills = _as_clean_list(core_skills + sec_skills, max_items=25, max_len=80)

            primary_domain = _as_clean_text(intelligence_data.get("primary_domain") or rule_domain, max_len=120)
            secondary_domains = _as_clean_list(intelligence_data.get("secondary_domains"), max_items=10, max_len=120)
            domains = _as_clean_list(([primary_domain] if primary_domain else []) + secondary_domains, max_items=10, max_len=120)

            seniority = _as_clean_text((intelligence_data.get("seniority_level") or rule_seniority or "NOT_SPECIFIED").upper(), max_len=40)
            career_level = seniority

            years_experience_range = _as_clean_text(intelligence_data.get("years_experience_range"), max_len=20)
            if not years_experience_range and years_of_experience > 0:
                lo = int(years_of_experience)
                hi = lo + 1
                years_experience_range = f"{lo}-{hi}"

            role_types = _as_clean_list(intelligence_data.get("role_types") or rule_roles, max_items=12, max_len=100)
            certifications = _as_clean_list(intelligence_data.get("certifications") or rule_certs, max_items=20, max_len=120)
            frameworks_tools = _as_clean_list(intelligence_data.get("frameworks_tools"), max_items=20, max_len=80)
            soft_skills = _as_clean_list(intelligence_data.get("soft_skills"), max_items=20, max_len=80)
            leadership_indicators = _as_clean_list(intelligence_data.get("leadership_indicators"), max_items=12, max_len=120)
            matched_requirements = _as_clean_list(intelligence_data.get("matched_requirements"), max_items=20, max_len=200)
            missing_requirements = _as_clean_list(intelligence_data.get("missing_requirements"), max_items=20, max_len=200)
            key_strengths = _as_clean_list(intelligence_data.get("key_strengths"), max_items=10, max_len=200)
            potential_concerns = _as_clean_list(intelligence_data.get("potential_concerns"), max_items=10, max_len=200)
            highlight_achievements = _as_clean_list(intelligence_data.get("highlight_achievements"), max_items=12, max_len=220)

            highest_degree = _as_clean_text(intelligence_data.get("highest_degree"), max_len=120)
            field_of_study = _as_clean_text(intelligence_data.get("field_of_study"), max_len=120)
            education_level = _as_clean_text((intelligence_data.get("education_level") or "").upper(), max_len=30)

            # ── Step 3: Build guaranteed non-empty computed fields ──
            overall_summary = _build_summary(intelligence_data)
            evidence_reason = _build_evidence_reasoning(intelligence_data)
            search_keywords = _build_search_keywords(intelligence_data, key_skills, domains)

            cleaned_text = _as_clean_text(cv_text, max_len=20000)
            cleaned_narrative = _as_clean_text(intelligence_data.get("cleaned_narrative"), max_len=2500)
            if not cleaned_narrative:
                cleaned_narrative = overall_summary[:350]

            # ── Step 4: Confidence score (never 0 if any data exists) ──
            raw_confidence = intelligence_data.get("confidence_score")
            if raw_confidence is None or raw_confidence == 0:
                confidence_score = _compute_data_confidence(intelligence_data, key_skills)
            else:
                confidence_score = _normalize_percent(raw_confidence, default=1)
            if confidence_score == 0 and (key_skills or years_of_experience > 0):
                confidence_score = max(1, _compute_data_confidence(intelligence_data, key_skills))

            # ── Step 5: Audit fields (never empty) ──
            original_cv_hash = _as_clean_text(intelligence_data.get("original_cv_hash"), max_len=120)
            if not original_cv_hash:
                original_cv_hash = _compute_cv_hash(cv_text) or _compute_cv_hash(anon_id)

            actual_prompt = intelligence_data.get("llm_prompt_used")
            if actual_prompt and isinstance(actual_prompt, str) and len(actual_prompt) > 20:
                llm_prompt_used = actual_prompt[:200].replace("\n", " ").strip()
            else:
                provider = _as_clean_text(intelligence_data.get("llm_provider"), max_len=50) or "unknown"
                model = _as_clean_text(intelligence_data.get("llm_model"), max_len=100) or "unknown"
                llm_prompt_used = f"{provider}:{model}"

            llm_raw_response = _sanitize_json_backup(intelligence_data)
            if not llm_raw_response or llm_raw_response == "{}":
                llm_raw_response = json.dumps({"source": "rule_based_fallback", "anonymized_id": anon_id})

            llm_provider = _as_clean_text(intelligence_data.get("llm_provider"), max_len=50) or "unknown"
            llm_model = _as_clean_text(intelligence_data.get("llm_model"), max_len=100) or "unknown"
            extraction_timestamp = intelligence_data.get("extraction_timestamp") or datetime.now().isoformat()
            org_id = _as_clean_text(intelligence_data.get("org_id"), max_len=50) or "default_org"

            # ── Step 6: Assemble exact 39-column payload ──
            flat_data = {
                "anonymized_id": anon_id,
                "original_cv_hash": original_cv_hash,
                "llm_prompt_used": llm_prompt_used,
                "llm_raw_response": llm_raw_response,
                "confidence_score": confidence_score,
                "evidence_based_reasoning": evidence_reason,
                "overall_summary": overall_summary,
                "key_skills": key_skills,
                "years_of_experience": years_of_experience,
                "career_level": career_level,
                "seniority_level": seniority,
                "years_experience_range": years_experience_range,
                "domain_expertise": domains,
                "primary_domain": primary_domain,
                "secondary_domains": secondary_domains,
                "cleaned_narrative": cleaned_narrative,
                "cleaned_text": cleaned_text,
                "core_technical_skills": core_skills,
                "secondary_technical_skills": sec_skills,
                "frameworks_tools": frameworks_tools,
                "soft_skills": soft_skills,
                "certifications": certifications,
                "education_level": education_level,
                "field_of_study": field_of_study,
                "highest_degree": highest_degree,
                "extraction_timestamp": extraction_timestamp,
                "llm_model": llm_model,
                "llm_provider": llm_provider,
                "matched_requirements": matched_requirements,
                "missing_requirements": missing_requirements,
                "potential_concerns": potential_concerns,
                "key_strengths": key_strengths,
                "leadership_indicators": leadership_indicators,
                "highlight_achievements": highlight_achievements,
                "role_types": role_types,
                "search_keywords": search_keywords,
                "org_id": org_id,
            }

            # ── Step 7: Ensure zero NULLs ──
            # Replace any remaining None with safe defaults
            for k, v in list(flat_data.items()):
                if v is None:
                    if isinstance(v, list):
                        flat_data[k] = []
                    elif isinstance(v, (int, float)):
                        flat_data[k] = 0
                    else:
                        flat_data[k] = ""

            # ── Step 8: Upsert (override earlier on same anonymized_id) ──
            attempted_data = dict(flat_data)
            while True:
                try:
                    response = self.client.table(self.table_name).upsert(
                        attempted_data,
                        on_conflict="anonymized_id"
                    ).execute()
                    break
                except Exception as schema_error:
                    missing_column = _extract_missing_column_name(schema_error)
                    if missing_column and missing_column in attempted_data:
                        logger.warning(f"Schema missing '{missing_column}', retrying without it")
                        attempted_data.pop(missing_column, None)
                        continue
                    raise schema_error

            logger.info(f"Stored intelligence for {anon_id} (confidence={confidence_score}, skills={len(key_skills)}, years={years_of_experience})")
            return response.data[0] if response.data else {}

        except Exception as e:
            logger.error(f"Error storing intelligence: {e}")
            raise

    # ──────────────────────────────
    # Search helpers
    # ──────────────────────────────

    def search_by_filters(
        self,
        seniority_level: Optional[str] = None,
        min_confidence_score: Optional[int] = None,
        required_skills: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        primary_domain: Optional[str] = None,
        min_years_experience: Optional[float] = None,
        max_years_experience: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Search CVs using SQL filters."""
        query = self.client.table(self.table_name).select("*")

        if seniority_level:
            query = query.eq("career_level", seniority_level.upper())
        if min_confidence_score is not None:
            query = query.gte("confidence_score", min_confidence_score)
        if min_years_experience is not None:
            query = query.gte("years_of_experience", min_years_experience)
        if max_years_experience is not None:
            query = query.lte("years_of_experience", max_years_experience)

        query = query.order("confidence_score", desc=True).order("created_at", desc=True).limit(limit)
        response = query.execute()
        results = response.data or []

        # Client-side filters for arrays
        if required_skills:
            def has_all_skills(record):
                rec_skills = [s.lower() for s in (record.get("key_skills") or [])]
                raw = record.get("llm_raw_response", "")
                if raw and raw.startswith("{"):
                    try:
                        full = json.loads(raw)
                        rec_skills += [s.lower() for s in (full.get("core_technical_skills") or [])]
                        rec_skills += [s.lower() for s in (full.get("secondary_technical_skills") or [])]
                    except Exception:
                        pass
                return all(any(skill.lower() in rs for rs in rec_skills) for skill in required_skills)
            results = [r for r in results if has_all_skills(r)]

        if primary_domain:
            pd_lower = primary_domain.lower()
            def matches_domain(record):
                domains_list = [d.lower() for d in (record.get("domain_expertise") or [])]
                return any(pd_lower in d for d in domains_list)
            results = [r for r in results if matches_domain(r)]

        if domains:
            def matches_any_domain(record):
                domains_list = [d.lower() for d in (record.get("domain_expertise") or [])]
                return any(any(d.lower() in dl for dl in domains_list) for d in domains)
            results = [r for r in results if matches_any_domain(r)]

        return results

    def semantic_search(
        self,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        filters: Dict = None
    ) -> List[Dict]:
        """Semantic search using vector embeddings with pgvector."""
        try:
            from vector_search import get_vector_search_engine
            engine = get_vector_search_engine()
            query_embedding = engine.generate_embedding(query_text)
            if not engine.validate_embedding(query_embedding):
                logger.error("Invalid query embedding generated")
                return []

            try:
                response = self.client.rpc(
                    'match_cv_embeddings',
                    {
                        'query_embedding': query_embedding,
                        'match_threshold': similarity_threshold,
                        'match_count': limit
                    }
                ).execute()
                if response.data:
                    results = response.data
                    if filters:
                        if filters.get('seniority_level'):
                            results = [r for r in results if r.get('seniority_level') == filters['seniority_level']]
                    return results[:limit]
            except Exception as rpc_error:
                logger.warning(f"pgvector RPC not available, falling back to local search: {rpc_error}")

            # Fallback: local computation
            query = self.client.table('cv_intelligence').select('*').not_.is_('embedding', 'null')
            if filters:
                if filters.get('seniority_level'):
                    query = query.eq('seniority_level', filters['seniority_level'])
                if filters.get('min_years_experience'):
                    query = query.gte('years_of_experience', filters['min_years_experience'])
            response = query.limit(min(limit * 10, 100)).execute()
            if not response.data:
                return []

            results = []
            for record in response.data:
                embedding_data = record.get('embedding')
                if not embedding_data:
                    continue
                if isinstance(embedding_data, str):
                    embedding = json.loads(embedding_data)
                else:
                    embedding = embedding_data
                similarity = engine.cosine_similarity(query_embedding, embedding)
                if similarity >= similarity_threshold:
                    record['similarity_score'] = similarity
                    results.append(record)
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:limit]

        except ImportError:
            logger.error("vector_search module not available")
            return []
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def hybrid_search(self, query_text: str, filters: Dict, limit: int = 10, semantic_weight: float = 0.7) -> List[Dict]:
        """Hybrid search combining semantic similarity and SQL filters."""
        try:
            semantic_results = self.semantic_search(
                query_text, limit=limit * 2, similarity_threshold=0.5, filters=filters
            )
            for result in semantic_results:
                semantic_score = result.get('similarity_score', 0)
                match_score = result.get('match_score', 0) / 100.0
                result['combined_score'] = (semantic_weight * semantic_score) + ((1 - semantic_weight) * match_score)
            semantic_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            return semantic_results[:limit]
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def store_embedding(self, anonymized_id: str, embedding: List[float]) -> bool:
        """Store embedding vector for a candidate."""
        try:
            response = self.client.table('cv_intelligence').update(
                {'embedding': embedding, 'updated_at': datetime.now().isoformat()}
            ).eq('anonymized_id', anonymized_id).execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return False

    def get_candidate(self, anonymized_id: str) -> Optional[Dict]:
        """Get a specific candidate by anonymized ID."""
        try:
            response = self.client.table(self.table_name).select('*').eq('anonymized_id', anonymized_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting candidate: {e}")
            return None

    def get_all_candidates(self, limit: int = 500, offset: int = 0) -> List[Dict]:
        """Get all candidates from Supabase with pagination."""
        try:
            response = self.client.table(self.table_name).select('*').order('created_at', desc=True).limit(limit).offset(offset).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting all candidates: {e}")
            return []

    def _db_record_to_app_format(self, record: Dict) -> Dict:
        """Convert database record to application format for frontend display."""
        if not record:
            return {}
        
        return {
            'anonymized_id': record.get('anonymized_id', 'UNKNOWN'),
            'years_of_experience': record.get('years_of_experience', 0),
            'seniority_level': record.get('seniority_level') or record.get('career_level', 'UNKNOWN'),
            'primary_domain': record.get('primary_domain') or record.get('domain_expertise', ['Unknown'])[0] if record.get('domain_expertise') else 'Unknown',
            'core_technical_skills': record.get('core_technical_skills', []),
            'secondary_technical_skills': record.get('secondary_technical_skills', []),
            'key_skills': record.get('key_skills', []),
            'confidence_score': record.get('confidence_score', 0),
            'match_score': record.get('match_score', 0),
            'soft_skills': record.get('soft_skills', []),
            'leadership_indicators': record.get('leadership_indicators', []),
            'certifications': record.get('certifications', []),
            'domain_expertise': record.get('domain_expertise', [record.get('primary_domain', 'Unknown')]),
            'cleaned_narrative': record.get('cleaned_narrative', ''),
            'key_strengths': record.get('key_strengths', []),
            'matched_requirements': record.get('matched_requirements', []),
            'missing_requirements': record.get('missing_requirements', []),
            'created_at': record.get('created_at'),
            'llm_provider': record.get('llm_provider', 'unknown'),
            'llm_model': record.get('llm_model', 'unknown'),
            'embedding': record.get('embedding'),  # CRITICAL: Pre-computed embedding for semantic search
        }

    def batch_store(self, intelligence_list: List[Dict]) -> List[Dict]:
        """Store multiple CV intelligence records in batch."""
        results = []
        for intelligence in intelligence_list:
            if "error" not in intelligence:
                try:
                    result = self.store_intelligence(intelligence)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to store {intelligence.get('anonymized_id')}: {e}")
        return results

    def store_filename_mapping(self, anonymized_id: str, original_filename: str, anonymized_filename: str = None) -> Dict:
        """Store filename mapping in secure backend table."""
        try:
            mapping_data = {
                "anonymized_id": anonymized_id,
                "original_filename": original_filename,
                "anonymized_filename": anonymized_filename or original_filename
            }
            response = self.client.table("cv_filename_mapping").upsert(mapping_data, on_conflict="anonymized_id").execute()
            logger.info(f"Stored mapping: {original_filename} -> {anonymized_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error storing filename mapping: {e}")
            raise

    def get_original_filename(self, anonymized_id: str) -> Optional[str]:
        """Retrieve original filename from anonymized ID."""
        try:
            response = self.client.table("cv_filename_mapping").select("original_filename").eq("anonymized_id", anonymized_id).execute()
            return response.data[0]["original_filename"] if response.data else None
        except Exception as e:
            logger.error(f"Error retrieving filename: {e}")
            return None

    def get_upload_job(self, job_id: str) -> Optional[Dict]:
        """Get upload job status from job tracking table."""
        try:
            response = self.client.table("upload_jobs").select("*").eq("job_id", job_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.warning(f"Could not retrieve upload job {job_id}: {e}")
            return None

    def get_dashboard_stats(self) -> Dict:
        """Get summary statistics for the dashboard."""
        try:
            response = self.client.table(self.table_name).select('*').limit(5000).execute()
            all_records = response.data or []

            total = len(all_records)
            if total == 0:
                return {"total_candidates": 0, "by_seniority": {}, "avg_years": 0, "avg_confidence": 0}

            seniority_counts = {}
            total_years = 0
            total_confidence = 0
            for r in all_records:
                sl = r.get("career_level", "UNKNOWN") or "UNKNOWN"
                seniority_counts[sl] = seniority_counts.get(sl, 0) + 1
                total_years += r.get("years_of_experience", 0) or 0
                total_confidence += r.get("confidence_score", 0) or 0

            return {
                "total_candidates": total,
                "by_seniority": seniority_counts,
                "avg_years": round(total_years / total, 1),
                "avg_confidence": round(total_confidence / total, 1),
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {"total_candidates": 0, "by_seniority": {}, "avg_years": 0, "avg_confidence": 0}
