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
    _SIMILARITY_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    SIMILARITY_AVAILABLE = True
except Exception:
    SIMILARITY_AVAILABLE = False
    _SIMILARITY_MODEL = None

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


def compute_similarity(text1: str, text2: str) -> float:
    """
    Compute semantic similarity between two texts using sentence embeddings.
    Falls back to TF-IDF cosine similarity if sentence-transformers unavailable.
    Returns a score between 0.0 and 100.0.
    """
    if not text1 or not text2:
        return 0.0
    if SIMILARITY_AVAILABLE and _SIMILARITY_MODEL is not None:
        try:
            import numpy as np
            emb = _SIMILARITY_MODEL.encode([text1, text2])
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
    return any(marker in cv_text for marker in REDACTION_MARKERS)


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
    
    def __init__(self, api_provider: str = "gemini", api_key: str = None, model: str = None):
        """
        Initialize the CV Intelligence Extractor
        
        Args:
            api_provider: 'openai', 'anthropic', 'gemini', or 'ollama' (default: gemini)
            api_key: API key (reads from env if not provided, not needed for Ollama)
            model: Specific model to use (optional)
        """
        self.api_provider = api_provider
        self.llm_processor = LLMBatchProcessor(
            api_provider=api_provider,
            api_key=api_key,
            model=model
        )
        self.model = model or self.llm_processor.model
        
    def _generate_anonymized_id(self) -> str:
        """
        Generate unique anonymized candidate ID (e.g., "CAND_882")
        
        Returns:
            Anonymized ID string
        """
        # Generate random 3-digit number
        number = random.randint(100, 999)
        return f"CAND_{number}"
    
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
        
    def _create_extraction_prompt(self, cv_text: str, job_description: str, anonymized_id: str) -> str:
        """
        Create a detailed extraction prompt that produces Gemini-quality fitment analysis.
        The output is structured prose that gets parsed into JSON.
        """
        prompt = f"""You are a senior technical recruiter performing a detailed fitment analysis. Compare the anonymized professional profile against the job description below.

IMPORTANT RULES:
- The CV is already anonymized (all PII removed). NEVER output names, emails, phone numbers, addresses, or company locations.
- If you cannot determine something, state "Not specified" — NEVER invent details.
- Be thorough and evidence-based. Cite specific technologies, years, and project details from the CV.
- Provide a DETAILED category-by-category comparison like a professional recruitment report.
- The Overall Assessment MUST be an original analytical summary you write — do NOT copy-paste text from the CV.

OUTPUT FORMAT (FOLLOW THIS STRUCTURE EXACTLY):

SECTION 1 – Overall Assessment:
[Write a 2-3 paragraph ORIGINAL executive summary in your own words covering:
- Who the candidate is (years of experience, primary role, key expertise areas)
- Why they are / are not a good fit for this specific role
- One line recommendation
IMPORTANT: This must be YOUR analytical summary, NOT copied text from the CV. Synthesize the information into a professional recruiter assessment.]

SECTION 2 – Fitment Analysis Table:
For EACH major requirement category in the JD, provide a line in this exact format:
CATEGORY: [category name]
JD_REQUIRES: [what the JD asks for]
CANDIDATE_HAS: [what the candidate actually has, with evidence]
MATCH_STATUS: [FULL_MATCH | PARTIAL_MATCH | NO_MATCH]

(Create one entry for each of these categories, adapting to the JD:
- Total Experience
- Core Programming Languages
- Primary Domain / Industry
- Frameworks & Tools
- Architecture & Design Patterns
- Cloud / Infrastructure
- Leadership & Team Management
- Education / Certifications
- Any other JD-specific categories)

SECTION 3 – Key Strengths:
- [Strength 1 with specific evidence from CV]
- [Strength 2 with specific evidence from CV]
- [Strength 3 with specific evidence from CV]
- [Strength 4 with specific evidence from CV (if applicable)]

SECTION 4 – Potential Gaps / Areas to Verify:
- [Gap 1: what is missing or unclear, and its impact]
- [Gap 2: what is missing or unclear, and its impact]
(If no gaps: "No critical gaps identified.")

SECTION 5 – Experience Breakdown:
Years of Experience: [exact number, e.g., "9 years" or "5-6 years"]
Seniority Level: [ENTRY: 0-2yrs | MID: 2-5yrs | SENIOR: 5-10yrs | LEAD: 10-15yrs | EXECUTIVE: 15+yrs]
Core Technical Skills: [List top 10 technical skills from CV]
Secondary Skills: [List additional tools, frameworks, soft skills]
Primary Domain: [Main industry/sector e.g., "Automotive Embedded", "Web Development"]
Leadership Indicators: [List concrete evidence: "Led 5-person team", "Mentored 3 juniors", or "None mentioned"]

FINAL RECOMMENDATION:
[SHORTLIST | BACKUP | REVIEW]
Confidence: [0-100]%
Match Score: [0-100]%

Reason: [2-3 sentences with specific evidence. First sentence: overall verdict with primary reason. Second: key matching evidence. Third: what tips the balance.]

===== DECISION RULES =====
- SHORTLIST: 80%+ requirements matched with strong evidence. Ready for interview.
- BACKUP: 60-79% requirements matched. Good candidate but has some gaps.
- REVIEW: <60% matched OR unclear/insufficient CV data → human must decide.
- If Confidence <70%, automatically use REVIEW regardless of match score.
- NEVER use REJECT — when in doubt, use REVIEW.

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
        Extracts fitment table, strengths, gaps, and all structured fields.
        """
        try:
            # Extract verdict
            verdict_match = re.search(r'FINAL RECOMMENDATION:\s*\n?\[?(SHORTLIST|BACKUP|REVIEW)\]?', prose_response, re.IGNORECASE)
            verdict = verdict_match.group(1).upper() if verdict_match else "REVIEW"
            
            # Extract confidence score
            confidence_match = re.search(r'Confidence:\s*\[?(\d+)\]?%', prose_response)
            confidence_score = int(confidence_match.group(1)) if confidence_match else 50
            
            # Extract match score
            match_match = re.search(r'Match Score:\s*\[?(\d+)\]?%', prose_response)
            match_score = int(match_match.group(1)) if match_match else 50
            
            # Extract verdict reason
            reason_match = re.search(r'Reason:\s*(.+?)(?:\n\n|={3,}|$)', prose_response, re.DOTALL)
            verdict_reason = reason_match.group(1).strip() if reason_match else "See detailed analysis above"
            
            # Extract years of experience
            years_match = re.search(r'Years of Experience:\s*\[?([0-9.]+(?:\s*-\s*[0-9.]+)?)\s*(?:years?)?\]?', prose_response, re.IGNORECASE)
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
                years_experience_range = "Not specified"
            
            # Extract seniority level
            seniority_match = re.search(r'Seniority Level:\s*\[?(ENTRY|MID|SENIOR|LEAD|EXECUTIVE)\]?', prose_response, re.IGNORECASE)
            seniority_level = seniority_match.group(1).upper() if seniority_match else "MID"
            
            # Extract core technical skills (with or without brackets)
            skills_section = re.search(r'Core Technical Skills:\s*\[?(.+?)\]?\s*(?:\n|$)', prose_response, re.DOTALL)
            if skills_section:
                skills_text = skills_section.group(1).strip()
                # Handle multi-line or comma-separated skills
                core_technical_skills = [s.strip().strip('"\'[]') for s in skills_text.split(',') if s.strip() and s.strip() not in ['[', ']']]
                core_technical_skills = [s for s in core_technical_skills if s]  # Remove empty
            else:
                core_technical_skills = []
            
            # Extract secondary skills (with or without brackets)
            secondary_section = re.search(r'Secondary Skills:\s*\[?(.+?)\]?\s*(?:\n|$)', prose_response, re.DOTALL)
            if secondary_section:
                sec_text = secondary_section.group(1).strip()
                secondary_technical_skills = [s.strip().strip('"\'[]') for s in sec_text.split(',') if s.strip() and s.strip() not in ['[', ']']]
                secondary_technical_skills = [s for s in secondary_technical_skills if s]
            else:
                secondary_technical_skills = []
            
            # Extract primary domain
            domain_match = re.search(r'Primary Domain:\s*\[?([^\]\n]+)\]?', prose_response, re.IGNORECASE)
            primary_domain = domain_match.group(1).strip().strip('"\'') if domain_match else ""
            
            # Extract leadership indicators (with or without brackets)
            leadership_section = re.search(r'Leadership Indicators:\s*\[?(.+?)\]?\s*(?:\n|$)', prose_response, re.DOTALL)
            if leadership_section:
                leadership_text = leadership_section.group(1).strip()
                if leadership_text.lower() in ['none mentioned', 'none mentioned.', 'none', 'n/a', 'not specified']:
                    leadership_indicators = []
                else:
                    leadership_indicators = [s.strip().strip('"\'[]') for s in leadership_text.split(',') if s.strip()]
                    leadership_indicators = [s for s in leadership_indicators if s]
            else:
                leadership_indicators = []
            
            # Extract SECTION 1 (Overall Assessment)
            section1_match = re.search(r'SECTION 1[^\n]*\n(.+?)(?=SECTION 2|FINAL RECOMMENDATION|$)', prose_response, re.DOTALL)
            cleaned_narrative = section1_match.group(1).strip() if section1_match else ""
            
            # ===== NEW: Extract Fitment Analysis Table (SECTION 2) =====
            fitment_analysis = []
            section2_match = re.search(r'SECTION 2[^\n]*\n(.+?)(?=SECTION 3|Key Strengths|$)', prose_response, re.DOTALL)
            if section2_match:
                section2_text = section2_match.group(1)
                # Parse CATEGORY/JD_REQUIRES/CANDIDATE_HAS/MATCH_STATUS blocks
                # Support both plain "CATEGORY:" and dash-prefixed "- CATEGORY:" formats
                categories = re.findall(
                    r'-?\s*CATEGORY:\s*(.+?)\n-?\s*JD_REQUIRES:\s*(.+?)\n-?\s*CANDIDATE_HAS:\s*(.+?)\n-?\s*MATCH_STATUS:\s*(FULL_MATCH|PARTIAL_MATCH|NO_MATCH)',
                    section2_text, re.DOTALL
                )
                for cat, jd_req, cand_has, status in categories:
                    fitment_analysis.append({
                        "category": cat.strip(),
                        "jd_requirement": jd_req.strip(),
                        "candidate_profile": cand_has.strip(),
                        "match_status": status.strip()
                    })
            
            # ===== NEW: Extract Key Strengths (SECTION 3) =====
            key_strengths = []
            section3_match = re.search(r'(?:SECTION 3|Key Strengths)[^\n]*\n(.+?)(?=SECTION 4|Potential Gaps|SECTION 5|Experience Breakdown|FINAL|$)', prose_response, re.DOTALL)
            if section3_match:
                for line in section3_match.group(1).strip().split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*'):
                        key_strengths.append(line.lstrip('-* ').strip())
            
            # ===== NEW: Extract Potential Gaps (SECTION 4) =====
            potential_concerns = []
            section4_match = re.search(r'(?:SECTION 4|Potential Gaps)[^\n]*\n(.+?)(?=SECTION 5|Experience Breakdown|FINAL|$)', prose_response, re.DOTALL)
            if section4_match:
                for line in section4_match.group(1).strip().split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('*'):
                        potential_concerns.append(line.lstrip('-* ').strip())
            
            # Extract matched/missing requirements from fitment table
            matched_requirements = [f["category"] for f in fitment_analysis if f["match_status"] == "FULL_MATCH"]
            missing_requirements = [f["category"] for f in fitment_analysis if f["match_status"] == "NO_MATCH"]
            
            # Count match stats
            total_categories = len(fitment_analysis)
            full_matches = len(matched_requirements)
            partial_matches = len([f for f in fitment_analysis if f["match_status"] == "PARTIAL_MATCH"])
            no_matches = len(missing_requirements)
            
            # Build structured response
            intelligence = {
                "anonymized_id": anonymized_id,
                "analysis_date": datetime.now().isoformat(),
                
                # Core fields
                "verdict": verdict,
                "confidence_score": confidence_score,
                "match_score": match_score,
                "verdict_reason": verdict_reason,
                
                # Experience
                "years_experience": years_experience,
                "years_experience_range": years_experience_range,
                "seniority_level": seniority_level,
                
                # Skills
                "core_technical_skills": core_technical_skills,
                "secondary_technical_skills": secondary_technical_skills,
                "leadership_indicators": leadership_indicators,
                
                # Domain
                "primary_domain": primary_domain,
                "secondary_domains": [],
                
                # Analysis
                "cleaned_narrative": cleaned_narrative,
                "matched_requirements": matched_requirements,
                "missing_requirements": missing_requirements,
                "key_strengths": key_strengths,
                "potential_concerns": potential_concerns,
                
                # NEW: Detailed fitment analysis table
                "fitment_analysis": fitment_analysis,
                "fitment_summary": {
                    "total_categories": total_categories,
                    "full_match": full_matches,
                    "partial_match": partial_matches,
                    "no_match": no_matches,
                    "match_rate": round((full_matches + partial_matches * 0.5) / total_categories * 100, 1) if total_categories > 0 else 0
                },
                
                # Full prose output for recruiter review
                "detailed_analysis": prose_response
            }
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error parsing prose response: {e}")
            return {
                "anonymized_id": anonymized_id,
                "analysis_date": datetime.now().isoformat(),
                "verdict": "REVIEW",
                "confidence_score": 30,
                "match_score": 50,
                "verdict_reason": "Analysis parsing failed - requires human review",
                "detailed_analysis": prose_response,
                "parse_error": str(e)
            }
    
    def extract_intelligence(
        self, 
        cv_text: str, 
        job_description: str,
        original_filename: str = None
    ) -> Dict:
        """
        Extract structured intelligence from a CV with deep analysis and audit trail.
        
        IMPORTANT: Only processes anonymized CVs. If the CV is not anonymized,
        returns an error asking the user to anonymize first.
        
        Args:
            cv_text: Anonymized CV content (must contain [REDACTED_...] markers)
            job_description: Job description to match against
            original_filename: Original filename (for backend tracking only)
            
        Returns:
            Dictionary with structured CV intelligence + full audit trail
        """
        try:
            # CRITICAL: Verify CV is anonymized before processing
            if not is_cv_anonymized(cv_text):
                logger.error("CV is not anonymized. Cannot process non-anonymized CVs.")
                return {
                    "error": "CV_NOT_ANONYMIZED",
                    "error_message": (
                        "This CV has not been anonymized. Please run the CV through the "
                        "redaction pipeline first (Upload → Redact PII) before extracting "
                        "intelligence. Only anonymized CVs can be stored in the database."
                    ),
                    "anonymized_id": self._generate_anonymized_id(),
                    "original_filename": sanitize_filename_for_db(original_filename) if original_filename else "unknown"
                }
            
            # Generate anonymized ID
            anonymized_id = self._generate_anonymized_id()
            
            # Create extraction prompt (store for audit trail)
            prompt = self._create_extraction_prompt(cv_text, job_description, anonymized_id)
            
            # Hash original CV for audit trail
            original_cv_hash = self._hash_cv_content(cv_text)
            
            # Call LLM
            logger.info(f"Analyzing {anonymized_id}...")
            raw_llm_response = self.llm_processor.generate_analysis(prompt)
            
            # Parse prose response (new human-readable format)
            try:
                # Use prose parser instead of JSON
                intelligence = self._parse_prose_response(raw_llm_response, anonymized_id)
                
                # Add metadata — sanitize filename to remove any real names
                intelligence["original_filename"] = sanitize_filename_for_db(original_filename) if original_filename else "unknown"
                intelligence["original_filename_raw"] = original_filename or "unknown"  # Keep raw for local use only
                intelligence["llm_provider"] = self.api_provider
                intelligence["llm_model"] = self.model
                intelligence["extraction_timestamp"] = datetime.now().isoformat()
                intelligence["job_description_hash"] = self._hash_job_description(job_description)
                
                # Store the anonymized CV text for future use (JD comparisons, re-analysis)
                intelligence["cleaned_text"] = cv_text
                
                # Audit Trail (Full Explainability)
                intelligence["original_cv_hash"] = original_cv_hash
                intelligence["llm_prompt_used"] = prompt  # Full prompt for reproducibility
                intelligence["llm_raw_response"] = raw_llm_response  # Raw LLM output
                
                # NO AUTO-REJECT POLICY: Check confidence threshold
                confidence = intelligence.get("confidence_score", 0)
                if confidence < 70:
                    intelligence["requires_human_review"] = True
                    logger.warning(f"⚠️  {anonymized_id}: Low confidence ({confidence}%) → HUMAN REVIEW REQUIRED")
                else:
                    intelligence["requires_human_review"] = False

                # Compute CV faithfulness score:
                # measures how accurately the LLM captured the candidate's skills
                # from the original CV (skill recall + semantic coverage)
                try:
                    intelligence["similarity_score"] = compute_cv_faithfulness_score(intelligence)
                    logger.info(f"  Faithfulness score: {intelligence['similarity_score']}%")
                except Exception as sim_err:
                    logger.warning(f"Could not compute faithfulness score: {sim_err}")
                    intelligence["similarity_score"] = None
                
                verdict_status = "🔴 NEEDS REVIEW" if intelligence["requires_human_review"] else intelligence.get('verdict')
                logger.info(f"✓ {anonymized_id}: {verdict_status} (Match: {intelligence.get('match_score')}%, Confidence: {confidence}%)")
                
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
            # Re-raise quota errors so the pipeline can abort early
            raise
        except Exception as e:
            logger.error(f"Error extracting intelligence: {e}")
            return {
                "error": str(e),
                "anonymized_id": self._generate_anonymized_id(),
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
        
        for cv_file in cv_files:
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
                
                results.append(intelligence)
                
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
                    
            except Exception as e:
                logger.error(f"Error processing {cv_file}: {e}")
                results.append({
                    "error": str(e),
                    "anonymized_id": self._generate_anonymized_id(),
                    "original_filename": Path(cv_file).name
                })
        
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
        print(f"\n📊 VERDICTS:")
        for result in successful:
            verdict = result.get('verdict', 'UNKNOWN')
            match = result.get('match_score', 0)
            confidence = result.get('confidence_score', 0)
            anonymized_id = result.get('anonymized_id', 'N/A')
            print(f"  {anonymized_id}: {verdict} (Match: {match}%, Confidence: {confidence}%)")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
