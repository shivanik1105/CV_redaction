"""
Supabase Storage Module
Handles storing and retrieving CV intelligence data with vector search
"""
import os
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logging.warning("Supabase client not installed. Install with: pip install supabase")

logger = logging.getLogger(__name__)


def _extract_missing_column_name(error: Exception) -> Optional[str]:
    """Parse Supabase/PostgREST missing-column errors and return the column name."""
    error_text = str(error)
    match = re.search(r"Could not find the '([^']+)' column", error_text)
    if match:
        return match.group(1)
    return None


class SupabaseStorage:
    """Store and search CV intelligence in Supabase"""
    
    def __init__(self, url: str = None, key: str = None):
        """
        Initialize Supabase client
        
        Args:
            url: Supabase project URL (reads from SUPABASE_URL env if not provided)
            key: Supabase anon/service key (reads from SUPABASE_KEY env if not provided)
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase client not installed. Install with: pip install supabase"
            )
        
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials required. Set SUPABASE_URL and SUPABASE_KEY "
                "environment variables or pass them as arguments."
            )
        
        self.client: Client = create_client(self.url, self.key)
        self.table_name = "cv_intelligence"
        
    def create_tables(self):
        """
        Create necessary tables in Supabase (run this SQL in Supabase dashboard)
        
        Returns SQL commands to execute
        """
        sql = """
-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create cv_intelligence table (Single Source of Truth)
CREATE TABLE IF NOT EXISTS cv_intelligence (
    -- Primary Keys & Identifiers
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anonymized_id VARCHAR(20) UNIQUE NOT NULL,  -- e.g., "CAND_882"
    original_filename VARCHAR(255),
    analysis_date TIMESTAMP DEFAULT NOW(),
    
    -- Cleaned Content for Search
    cleaned_text TEXT,  -- Pure narrative, no PII, for vector search
    cleaned_narrative TEXT,  -- Professional 2-3 sentence summary
    
    -- Core Metadata (Deep Extraction)
    years_experience DECIMAL(4,1),  -- e.g., 5.5 years
    years_experience_range VARCHAR(20),  -- e.g., "5-6" for display
    seniority_level VARCHAR(20) CHECK (seniority_level IN ('ENTRY', 'MID', 'SENIOR', 'LEAD', 'EXECUTIVE')),
    
    -- Skills (Structured for SQL Filtering)
    core_technical_skills JSONB,  -- Top 10 most important technical skills
    secondary_technical_skills JSONB,  -- Additional technical skills
    frameworks_tools JSONB,  -- Frameworks and tools used
    soft_skills JSONB,  -- Leadership, communication, etc.
    certifications JSONB,  -- Professional certifications
    
    -- Domain & Experience
    primary_domain VARCHAR(100),  -- Main industry/sector
    secondary_domains JSONB,  -- Other domains
    role_types JSONB,  -- Engineer, Lead, Manager, etc.
    leadership_indicators JSONB,  -- Team size, mentoring, hiring, etc.
    
    -- Education
    highest_degree VARCHAR(100),
    field_of_study VARCHAR(100),
    education_level VARCHAR(20) CHECK (education_level IN ('HIGH_SCHOOL', 'BACHELORS', 'MASTERS', 'PHD', 'OTHER')),
    
    -- JD Fitment Analysis (No Auto-Reject Policy)
    verdict VARCHAR(20) CHECK (verdict IN ('SHORTLIST', 'BACKUP', 'REVIEW')) NOT NULL,  -- AI never rejects
    confidence_score INTEGER CHECK (confidence_score BETWEEN 0 AND 100),  -- LLM confidence
    match_score INTEGER CHECK (match_score BETWEEN 0 AND 100),  -- JD match percentage
    verdict_reason TEXT,  -- 2-sentence evidence-based explanation
    requires_human_review BOOLEAN DEFAULT FALSE,  -- Set true if confidence < 70%
    
    -- Detailed Analysis
    matched_requirements JSONB,  -- Array of requirements met
    missing_requirements JSONB,  -- Array of requirements not met
    key_strengths JSONB,  -- Top 5 strengths for this role
    potential_concerns JSONB,  -- Red flags or gaps
    
    -- Search Optimization
    search_keywords JSONB,  -- Keywords for text search
    highlight_achievements JSONB,  -- Notable achievements/projects
    
    -- Metadata
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    extraction_timestamp TIMESTAMP DEFAULT NOW(),
    job_description_hash VARCHAR(64),  -- To track which JD was used
    
    -- Audit Trail (Full Explainability)
    original_cv_hash VARCHAR(64),  -- SHA256 of raw uploaded CV
    llm_prompt_used TEXT,  -- Exact prompt sent to LLM for reproducibility
    llm_raw_response TEXT,  -- Full LLM response before parsing
    recruiter_override VARCHAR(20),  -- Human final decision (SHORTLIST/REJECT/HIRED)
    recruiter_notes TEXT,  -- Human reviewer comments
    recruiter_id VARCHAR(100),  -- Who made the override decision
    reviewed_at TIMESTAMP,  -- When human reviewed
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Vector Embedding for Semantic Search (add later with embeddings)
    embedding VECTOR(1536)  -- For OpenAI embeddings, adjust size as needed
);

-- Create indexes for fast filtering
CREATE INDEX IF NOT EXISTS idx_verdict ON cv_intelligence(verdict);
CREATE INDEX IF NOT EXISTS idx_seniority ON cv_intelligence(seniority_level);
CREATE INDEX IF NOT EXISTS idx_match_score ON cv_intelligence(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_confidence_score ON cv_intelligence(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_years_experience ON cv_intelligence(years_experience);
CREATE INDEX IF NOT EXISTS idx_primary_domain ON cv_intelligence(primary_domain);
CREATE INDEX IF NOT EXISTS idx_created_at ON cv_intelligence(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_requires_human_review ON cv_intelligence(requires_human_review) WHERE requires_human_review = TRUE;
CREATE INDEX IF NOT EXISTS idx_recruiter_override ON cv_intelligence(recruiter_override) WHERE recruiter_override IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_original_cv_hash ON cv_intelligence(original_cv_hash);

-- Create GIN indexes for JSONB fields (for array/object searches)
CREATE INDEX IF NOT EXISTS idx_core_technical_skills ON cv_intelligence USING GIN(core_technical_skills);
CREATE INDEX IF NOT EXISTS idx_frameworks_tools ON cv_intelligence USING GIN(frameworks_tools);
CREATE INDEX IF NOT EXISTS idx_secondary_domains ON cv_intelligence USING GIN(secondary_domains);
CREATE INDEX IF NOT EXISTS idx_search_keywords ON cv_intelligence USING GIN(search_keywords);

-- Create vector index for similarity search (requires pgvector extension)
CREATE INDEX IF NOT EXISTS idx_embedding ON cv_intelligence 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create full-text search index
CREATE INDEX IF NOT EXISTS idx_cleaned_text_fts ON cv_intelligence 
USING GIN(to_tsvector('english', cleaned_text));

-- Create filename mapping table (secure backend tracking)
CREATE TABLE IF NOT EXISTS cv_filename_mapping (
    anonymized_id TEXT PRIMARY KEY REFERENCES cv_intelligence(anonymized_id),
    original_filename TEXT NOT NULL,
    anonymized_filename TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mapping_anonymized ON cv_filename_mapping(anonymized_id);
CREATE INDEX IF NOT EXISTS idx_mapping_original ON cv_filename_mapping(original_filename);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE cv_intelligence ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_filename_mapping ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users (adjust as needed)
CREATE POLICY "Enable all access for authenticated users" 
ON cv_intelligence FOR ALL 
TO authenticated 
USING (true);

CREATE POLICY "Enable all access for authenticated users" 
ON cv_filename_mapping FOR ALL 
TO authenticated 
USING (true);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cv_intelligence_updated_at BEFORE UPDATE ON cv_intelligence
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""
        return sql
    
    def store_intelligence(self, intelligence_data: Dict) -> Dict:
        """
        Store CV intelligence in Supabase, mapped to existing table schema.
        
        Existing table columns:
            anonymized_id, career_level, confidence_score, created_at,
            domain_expertise (text[]), evidence_based_reasoning, key_skills (text[]),
            llm_prompt_used, llm_raw_response, original_cv_hash, overall_summary,
            recruiter_override, reviewed_at, reviewer_id, reviewer_notes,
            updated_at, verdict, years_of_experience
        
        Args:
            intelligence_data: Dictionary from CVIntelligenceExtractor
            
        Returns:
            Response from Supabase
        """
        try:
            allowed_verdicts = {"SHORTLIST", "BACKUP"}

            # CRITICAL: Verify data has an anonymized_id
            anon_id = intelligence_data.get("anonymized_id")
            if not anon_id:
                raise ValueError("Cannot store intelligence without anonymized_id")
            
            # CRITICAL: Check for error indicating CV was not anonymized
            if intelligence_data.get("error") == "CV_NOT_ANONYMIZED":
                raise ValueError(
                    "CV is not anonymized. Please run through redaction pipeline first. "
                    "Only anonymized CVs can be stored in the database."
                )
            
            # Build domain expertise array: primary + secondary domains
            domains = []
            if intelligence_data.get("primary_domain"):
                domains.append(intelligence_data["primary_domain"])
            domains.extend(intelligence_data.get("secondary_domains", []))
            
            # Build accurate overall_summary from the LLM's actual analysis
            # Priority: use the LLM-generated cleaned_narrative (executive summary)
            # NOT raw CV text — this should be the analyst's own summary
            overall_summary = self._build_accurate_summary(intelligence_data)
            
            # Strip any PII from the JSON backup before storing
            # Remove original_filename_raw (contains real names) from DB copy
            safe_data = {k: v for k, v in intelligence_data.items() 
                        if k != "original_filename_raw" and k != "llm_prompt_used"}
            full_json_backup = json.dumps(safe_data, default=str)
            
            # Map to existing table columns  
            raw_verdict = (intelligence_data.get("verdict") or "").upper().strip()
            normalized_verdict = raw_verdict if raw_verdict in allowed_verdicts else "BACKUP"

            flat_data = {
                "anonymized_id": anon_id,
                # Keep verdict compatible with table constraint in extraction-only mode.
                "verdict": normalized_verdict,
                "confidence_score": intelligence_data.get("confidence_score", 0),
                "match_score": intelligence_data.get("match_score"),
                "requires_human_review": intelligence_data.get("requires_human_review", False),
                "years_of_experience": intelligence_data.get("years_experience", 0),
                "career_level": intelligence_data.get("seniority_level", "") or "",
                "key_skills": intelligence_data.get("core_technical_skills", []),
                "domain_expertise": domains if domains else [],
                "evidence_based_reasoning": intelligence_data.get("verdict_reason", ""),
                "overall_summary": overall_summary,
                "cleaned_text": intelligence_data.get("cleaned_text") or intelligence_data.get("cleaned_narrative", ""),
                "original_cv_hash": intelligence_data.get("original_cv_hash", ""),
                "llm_prompt_used": f"{intelligence_data.get('llm_provider', 'unknown')}:{intelligence_data.get('llm_model', 'unknown')}",
                "llm_raw_response": full_json_backup,
            }
            
            # Remove None values (Supabase doesn't like explicit nulls for some columns)
            flat_data = {k: v for k, v in flat_data.items() if v is not None}
            
            # Insert or upsert. Some deployed Supabase environments may still be on
            # an older schema, so retry without optional columns that are missing.
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
                        logger.warning(
                            f"Supabase schema missing optional column '{missing_column}', retrying without it"
                        )
                        attempted_data.pop(missing_column, None)
                        continue
                    raise schema_error
            
            logger.info(f"✓ Stored intelligence for {flat_data['anonymized_id']}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error storing intelligence: {e}")
            raise
    
    def _build_accurate_summary(self, intelligence_data: Dict) -> str:
        """
        Build an accurate overall_summary for the database from the LLM's analysis.
        
        Priority order:
        1. LLM-generated cleaned_narrative (Section 1 executive summary) — if it looks
           like an original analysis (not copy-pasted CV text)
        2. Verdict reason + key metadata (years, skills, domain) — always accurate
        3. Fallback: construct from structured fields
        
        The summary stored in DB should be a professional recruiter-style assessment,
        NOT raw text copied from the CV.
        """
        import re as _re
        
        narrative = (intelligence_data.get("cleaned_narrative") or "").strip()
        verdict_reason = (intelligence_data.get("verdict_reason") or "").strip()
        years = intelligence_data.get("years_experience", 0)
        seniority = intelligence_data.get("seniority_level", "N/A")
        skills = intelligence_data.get("core_technical_skills", [])
        domain = intelligence_data.get("primary_domain", "")
        verdict = intelligence_data.get("verdict", "REVIEW")
        confidence = intelligence_data.get("confidence_score", 0)
        match_score = intelligence_data.get("match_score", 0)
        
        # Detect if cleaned_narrative is just copy-pasted CV text (common LLM issue)
        # We check multiple patterns and flag if ANY pattern matches
        is_raw_cv_text = False
        if narrative:
            # 1. Keyword-based indicators: CV-style section headers, bullets, redaction markers
            cv_indicators = [
                "OBJECTIVE :", "OBJECTIVE:", "SUMMARY\n", "SKILLS\n", "WORK EXPERIENCE",
                "➢", "●", "✓", "Currently Working as", "was working",
                "[REDACTED", "[NAME]", "Profile:", "Functional:",
                "Github", "LinkedIn", "Linked In", "EDUCATION", "CERTIF",
            ]
            indicator_count = sum(1 for ind in cv_indicators if ind in narrative)
            
            # 2. Company name in parentheses like (Capgemini), (TCS), (Infosys)
            has_company_parens = bool(_re.search(r'\([A-Z][a-zA-Z]{2,}\)', narrative))
            
            # 3. Date patterns like "August 2021 -" or "January 2020"
            months = "January|February|March|April|May|June|July|August|September|October|November|December"
            has_date_pattern = bool(_re.search(rf'\b({months})\s+\d{{4}}\b', narrative))
            
            # 4. Repeated job title at start (e.g., "Senior Developer Senior Developer")
            words = narrative.split()
            has_title_repeat = False
            if len(words) >= 4:
                for n in range(2, min(5, len(words) // 2 + 1)):
                    if ' '.join(words[:n]).lower() == ' '.join(words[n:2*n]).lower():
                        has_title_repeat = True
                        break
            
            # 5. Bullet character "•" (common in CVs)
            has_bullets = '•' in narrative
            
            # Flag as raw CV text if ANY strong signal is present
            if (indicator_count >= 1 or has_company_parens or has_date_pattern
                    or has_title_repeat or has_bullets or len(narrative) > 1000):
                is_raw_cv_text = True
        
        # Build the summary
        parts = []
        
        if narrative and not is_raw_cv_text and len(narrative) >= 30:
            # The LLM generated a proper analytical summary — use it
            # Truncate to reasonable length for DB field
            parts.append(narrative[:500])
        else:
            # Build a structured summary from metadata
            experience_str = f"{years} years" if years else "unspecified experience"
            skills_str = ", ".join(skills[:6]) if skills else "not specified"
            domain_str = domain if domain else "Software Development"
            
            parts.append(
                f"{seniority.title() if seniority != 'N/A' else 'Mid'}-level professional "
                f"with {experience_str} in {domain_str}. "
                f"Core skills: {skills_str}."
            )
        
        # Always append the assessment verdict
        if verdict_reason:
            parts.append(f"Assessment: {verdict_reason}")
        else:
            parts.append(f"Verdict: {verdict} (Confidence: {confidence}%, Match: {match_score}%)")
        
        # Add education if available
        if intelligence_data.get("highest_degree"):
            edu = intelligence_data["highest_degree"]
            if intelligence_data.get("field_of_study"):
                edu += f" in {intelligence_data['field_of_study']}"
            parts.append(f"Education: {edu}")
        
        return " | ".join(parts)
    
    def _db_record_to_app_format(self, record: Dict) -> Dict:
        """
        Convert a Supabase DB record back to the app's expected format.
        First tries to restore from the full JSON backup in llm_raw_response,
        then falls back to mapping from the 18 DB columns.
        """
        # Try to restore full data from JSON backup
        raw = record.get("llm_raw_response", "")
        if raw and raw.startswith("{"):
            try:
                full_data = json.loads(raw)
                full_data["_source"] = "supabase"
                # Ensure critical fields are present
                full_data["anonymized_id"] = record.get("anonymized_id", full_data.get("anonymized_id", "UNKNOWN"))
                full_data["verdict"] = record.get("verdict", full_data.get("verdict", "REVIEW"))
                full_data["confidence_score"] = record.get("confidence_score", full_data.get("confidence_score", 0))
                full_data["years_experience"] = record.get("years_of_experience", full_data.get("years_experience", 0))
                full_data["seniority_level"] = record.get("career_level", full_data.get("seniority_level", "")) or ""
                return full_data
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Fallback: map DB columns back to app format
        domains = record.get("domain_expertise", []) or []
        skills = record.get("key_skills", []) or []
        
        return {
            "anonymized_id": record.get("anonymized_id", "UNKNOWN"),
            "verdict": record.get("verdict", "REVIEW"),
            "confidence_score": record.get("confidence_score", 0),
            "match_score": record.get("match_score", 0),
            "years_experience": record.get("years_of_experience", 0),
            "years_of_experience": record.get("years_of_experience", 0),  # Both formats
            "seniority_level": record.get("career_level", "") or "",
            "career_level": record.get("career_level", "") or "",  # Both formats
            "core_technical_skills": skills,
            "key_skills": skills,  # Both formats
            "primary_domain": domains[0] if domains else "",
            "domain_expertise": domains,  # Both formats
            "secondary_domains": domains[1:] if len(domains) > 1 else [],
            "cleaned_narrative": record.get("overall_summary", ""),
            "overall_summary": record.get("overall_summary", ""),  # Both formats
            "verdict_reason": record.get("evidence_based_reasoning", ""),
            "evidence_based_reasoning": record.get("evidence_based_reasoning", ""),  # Both formats
            "original_cv_hash": record.get("original_cv_hash", ""),
            "recruiter_override": record.get("recruiter_override"),
            "requires_human_review": False,
            "created_at": record.get("created_at", ""),
            "updated_at": record.get("updated_at", ""),
            "_source": "supabase",
        }
    
    def batch_store(self, intelligence_list: List[Dict]) -> List[Dict]:
        """
        Store multiple CV intelligence records in batch
        
        Args:
            intelligence_list: List of intelligence dictionaries
            
        Returns:
            List of stored records
        """
        results = []
        for intelligence in intelligence_list:
            if "error" not in intelligence:
                try:
                    result = self.store_intelligence(intelligence)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to store {intelligence.get('anonymized_id')}: {e}")
        
        return results
    
    def store_filename_mapping(
        self,
        anonymized_id: str,
        original_filename: str,
        anonymized_filename: str = None
    ) -> Dict:
        """
        Store filename mapping in secure backend table
        
        Args:
            anonymized_id: The anonymized candidate ID (e.g., "CAND_882")
            original_filename: Original uploaded filename
            anonymized_filename: Anonymized/redacted filename (optional)
            
        Returns:
            Mapping record
        """
        try:
            mapping_data = {
                "anonymized_id": anonymized_id,
                "original_filename": original_filename,
                "anonymized_filename": anonymized_filename or original_filename
            }
            
            response = self.client.table("cv_filename_mapping").upsert(
                mapping_data,
                on_conflict="anonymized_id"
            ).execute()
            
            logger.info(f"✓ Stored mapping: {original_filename} → {anonymized_id}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error storing filename mapping: {e}")
            raise
    
    def get_original_filename(self, anonymized_id: str) -> Optional[str]:
        """
        Retrieve original filename from anonymized ID (backend only)
        
        Args:
            anonymized_id: The anonymized candidate ID
            
        Returns:
            Original filename or None
        """
        try:
            response = self.client.table("cv_filename_mapping").select(
                "original_filename"
            ).eq("anonymized_id", anonymized_id).execute()
            
            if response.data:
                return response.data[0]["original_filename"]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving filename: {e}")
            return None
    
    def search_by_filters(
        self,
        verdict: Optional[str] = None,
        seniority_level: Optional[str] = None,
        min_match_score: Optional[int] = None,
        min_confidence_score: Optional[int] = None,
        required_skills: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        primary_domain: Optional[str] = None,
        min_years_experience: Optional[float] = None,
        max_years_experience: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search CVs using SQL filters
        
        Args:
            verdict: Filter by verdict (SHORTLIST/BACKUP/REJECT)
            seniority_level: Filter by seniority level (ENTRY/MID/SENIOR/LEAD/EXECUTIVE)
            min_match_score: Minimum match score (0-100)
            min_confidence_score: Minimum confidence score (0-100)
            required_skills: Filter by required technical skills (checks core_technical_skills)
            domains: Filter by secondary domains
            primary_domain: Filter by primary domain
            min_years_experience: Minimum years of experience
            max_years_experience: Maximum years of experience
            limit: Maximum results to return
            
        Returns:
            List of matching CV records
        """
        query = self.client.table(self.table_name).select("*")
        
        # Apply filters
        if verdict:
            query = query.eq("verdict", verdict)
        
        if seniority_level:
            query = query.eq("career_level", seniority_level.upper())
        
        if min_match_score is not None:
            query = query.gte("match_score", min_match_score)
        
        if min_confidence_score is not None:
            query = query.gte("confidence_score", min_confidence_score)
        
        if required_skills:
            # Check if key_skills contains all required skills (case-insensitive via client-side filter)
            # PostgREST array contains is case-sensitive, so we filter after fetch
            pass  # Will filter client-side below
        
        if primary_domain:
            # domain_expertise is text[] - PostgREST contains is case-sensitive
            # so we filter client-side for better UX
            pass  # Will filter client-side below
        
        if domains:
            # Check if domain_expertise overlaps with requested domains
            pass  # Will filter client-side below
        
        if min_years_experience is not None:
            query = query.gte("years_of_experience", min_years_experience)
        
        if max_years_experience is not None:
            query = query.lte("years_of_experience", max_years_experience)
        
        # Order by match score first, then confidence
        query = query.order("match_score", desc=True).order("confidence_score", desc=True).limit(limit)
        
        response = query.execute()
        results = response.data
        
        # Client-side filters for case-insensitive text/array matching
        if required_skills:
            def has_all_skills(record):
                rec_skills = [s.lower() for s in (record.get("key_skills") or [])]
                # Also check llm_raw_response backup for core_technical_skills
                raw = record.get("llm_raw_response", "")
                if raw and raw.startswith("{"):
                    try:
                        full = json.loads(raw)
                        rec_skills += [s.lower() for s in (full.get("core_technical_skills") or [])]
                        rec_skills += [s.lower() for s in (full.get("secondary_technical_skills") or [])]
                    except Exception:
                        pass
                return all(
                    any(skill.lower() in rs for rs in rec_skills)
                    for skill in required_skills
                )
            results = [r for r in results if has_all_skills(r)]
        
        if primary_domain:
            pd_lower = primary_domain.lower()
            def matches_domain(record):
                domains_list = record.get("domain_expertise") or []
                if any(pd_lower in d.lower() for d in domains_list):
                    return True
                # Check in llm_raw_response backup
                raw = record.get("llm_raw_response", "")
                if raw and raw.startswith("{"):
                    try:
                        full = json.loads(raw)
                        p = (full.get("primary_domain") or "").lower()
                        s = [d.lower() for d in (full.get("secondary_domains") or [])]
                        skills = [sk.lower() for sk in (full.get("core_technical_skills") or [])]
                        narrative = (full.get("cleaned_narrative") or "").lower()
                        if pd_lower in p or any(pd_lower in d for d in s) or any(pd_lower in sk for sk in skills) or pd_lower in narrative:
                            return True
                    except Exception:
                        pass
                summary = (record.get("overall_summary") or "").lower()
                return pd_lower in summary
            results = [r for r in results if matches_domain(r)]
        
        if domains:
            def matches_any_domain(record):
                domains_list = [d.lower() for d in (record.get("domain_expertise") or [])]
                return any(
                    any(d.lower() in dl for dl in domains_list)
                    for d in domains
                )
            results = [r for r in results if matches_any_domain(r)]
        
        return results
    
    def semantic_search(
        self,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        filters: Dict = None
    ) -> List[Dict]:
        """
        Perform semantic search using vector embeddings with pgvector
        
        Args:
            query_text: Natural language query
            limit: Maximum results
            similarity_threshold: Minimum similarity (0-1)
            filters: Additional SQL filters (verdict, seniority_level, etc.)
            
        Returns:
            List of matching CV records with similarity scores
        """
        try:
            from vector_search import get_vector_search_engine
            
            # Generate embedding for query
            engine = get_vector_search_engine()
            query_embedding = engine.generate_embedding(query_text)
            
            if not engine.validate_embedding(query_embedding):
                logger.error("Invalid query embedding generated")
                return []
            
            # Use pgvector RPC function for efficient similarity search
            # This searches only in the database using vector index
            try:
                # Call the match_cv_embeddings RPC function
                # This uses pgvector's <=> operator with index
                response = self.client.rpc(
                    'match_cv_embeddings',
                    {
                        'query_embedding': query_embedding,
                        'match_threshold': similarity_threshold,
                        'match_count': limit
                    }
                ).execute()
                
                if response.data:
                    # Apply additional filters in Python if needed
                    results = response.data
                    
                    if filters:
                        if filters.get('verdict'):
                            results = [r for r in results if r.get('verdict') == filters['verdict']]
                        if filters.get('seniority_level'):
                            results = [r for r in results if r.get('seniority_level') == filters['seniority_level']]
                        if filters.get('min_match_score'):
                            results = [r for r in results if r.get('match_score', 0) >= filters['min_match_score']]
                    
                    return results[:limit]
                    
            except Exception as rpc_error:
                logger.warning(f"pgvector RPC not available, falling back to local search: {rpc_error}")
                # Fall back to local computation if RPC function doesn't exist
                pass
            
            # FALLBACK: Local computation (less efficient but works without RPC)
            # Only fetch records matching filters to reduce data transfer
            query = self.client.table('cv_intelligence').select('*')
            
            # Apply filters BEFORE fetching to reduce data
            if filters:
                if filters.get('verdict'):
                    query = query.eq('verdict', filters['verdict'])
                if filters.get('seniority_level'):
                    query = query.eq('seniority_level', filters['seniority_level'])
                if filters.get('min_match_score'):
                    query = query.gte('match_score', filters['min_match_score'])
                if filters.get('min_years_experience'):
                    query = query.gte('years_experience', filters['min_years_experience'])
            
            # Only fetch records that have embeddings
            query = query.not_.is_('embedding', 'null')
            
            # Limit to reasonable number for local computation
            response = query.limit(min(limit * 10, 100)).execute()
            
            if not response.data:
                return []
            
            # Compute similarities locally
            results = []
            for record in response.data:
                # Get embedding from record
                embedding_data = record.get('embedding')
                if not embedding_data:
                    continue
                
                # Parse embedding (stored as JSON array)
                if isinstance(embedding_data, str):
                    import json
                    embedding = json.loads(embedding_data)
                else:
                    embedding = embedding_data
                
                # Compute similarity
                similarity = engine.cosine_similarity(query_embedding, embedding)
                
                if similarity >= similarity_threshold:
                    record['similarity_score'] = similarity
                    results.append(record)
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Return top K
            return results[:limit]
            
        except ImportError:
            logger.error("vector_search module not available")
            return []
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def hybrid_search(
        self,
        query_text: str,
        filters: Dict,
        limit: int = 10,
        semantic_weight: float = 0.7
    ) -> List[Dict]:
        """
        Hybrid search combining semantic similarity and SQL filters
        
        Args:
            query_text: Natural language query
            filters: SQL filters (verdict, skills, etc.)
            limit: Maximum results
            semantic_weight: Weight for semantic score (0-1), rest is SQL match score
            
        Returns:
            List of candidates ranked by combined score
        """
        try:
            # Get semantic search results
            semantic_results = self.semantic_search(
                query_text,
                limit=limit * 2,  # Get more for reranking
                similarity_threshold=0.5,
                filters=filters
            )
            
            # Combine semantic similarity with match_score
            for result in semantic_results:
                semantic_score = result.get('similarity_score', 0)
                match_score = result.get('match_score', 0) / 100.0  # Normalize to 0-1
                
                # Weighted combination
                combined_score = (semantic_weight * semantic_score) + \
                                ((1 - semantic_weight) * match_score)
                
                result['combined_score'] = combined_score
            
            # Sort by combined score
            semantic_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
            
            return semantic_results[:limit]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    def store_embedding(
        self,
        anonymized_id: str,
        embedding: List[float],
        embedding_model: str = None
    ) -> bool:
        """
        Store embedding vector for a candidate
        
        Args:
            anonymized_id: Candidate ID
            embedding: Embedding vector (list of floats)
            embedding_model: Model used to generate embedding (ignored if column doesn't exist)
            
        Returns:
            True if stored successfully
        """
        try:
            # pgvector expects the embedding as a list, not JSON string
            # Supabase Python client handles the conversion automatically
            
            update_data = {
                'embedding': embedding,  # Pass as list, client converts to vector
                'updated_at': datetime.now().isoformat()
            }
            
            # Note: embedding_model column may not exist in simplified schema
            # We only update the embedding vector itself
            
            # Update record with embedding
            response = self.client.table('cv_intelligence').update(
                update_data
            ).eq('anonymized_id', anonymized_id).execute()
            
            if response.data:
                logger.info(f"✓ Stored embedding for {anonymized_id}")
                return True
            else:
                logger.warning(f"No record found for {anonymized_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            return False
    
    def get_candidate(self, anonymized_id: str) -> Optional[Dict]:
        """
        Get a specific candidate by anonymized ID
        
        Args:
            anonymized_id: Anonymized candidate ID (e.g., CAND_123)
            
        Returns:
            Candidate data or None
        """
        response = self.client.table(self.table_name).select("*").eq(
            "anonymized_id", anonymized_id
        ).execute()
        
        return response.data[0] if response.data else None
    
    def get_all_candidates(self, limit: int = 100) -> List[Dict]:
        """
        Get all candidates with pagination
        
        Args:
            limit: Maximum results
            
        Returns:
            List of candidate records
        """
        response = self.client.table(self.table_name).select("*").order(
            "created_at", desc=True
        ).limit(limit).execute()
        
        return response.data
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about stored CVs
        
        Returns:
            Dictionary with statistics including confidence scores
        """
        try:
            # Get all records
            all_records = self.get_all_candidates(limit=1000)
            
            # Calculate stats
            total = len(all_records)
            shortlisted = len([r for r in all_records if r.get("verdict") == "SHORTLIST"])
            backup = len([r for r in all_records if r.get("verdict") == "BACKUP"])
            review_needed = len([r for r in all_records if r.get("verdict") == "REVIEW"])
            requires_human = len([r for r in all_records if r.get("requires_human_review") == True])
            recruiter_reviewed = len([r for r in all_records if r.get("recruiter_override") is not None])
            
            avg_confidence_score = sum(r.get("confidence_score", 0) for r in all_records) / total if total > 0 else 0
            avg_match_score = sum((r.get("match_score") or 0) for r in all_records) / total if total > 0 else 0
            
            return {
                "total_candidates": total,
                "shortlisted": shortlisted,
                "backup": backup,
                "review_needed": review_needed,
                "requires_human_review": requires_human,
                "recruiter_reviewed": recruiter_reviewed,
                "average_match_score": round(avg_match_score, 2),
                "average_confidence_score": round(avg_confidence_score, 2),
                "data_source": "supabase"
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def add_recruiter_override(
        self,
        anonymized_id: str,
        recruiter_decision: str,
        recruiter_notes: str = "",
        recruiter_id: str = "recruiter"
    ) -> Dict:
        """
        Add human recruiter override decision to candidate record
        
        Args:
            anonymized_id: Candidate ID to update
            recruiter_decision: Final decision (SHORTLIST/REJECT/HIRED)
            recruiter_notes: Optional recruiter comments
            recruiter_id: Identifier of the recruiter making the decision
            
        Returns:
            Updated candidate record
        """
        try:
            from datetime import datetime
            
            update_data = {
                "recruiter_override": recruiter_decision,
                "recruiter_notes": recruiter_notes,
                "recruiter_id": recruiter_id,
                "reviewed_at": datetime.now().isoformat()
            }
            
            response = self.client.table(self.table_name).update(
                update_data
            ).eq("anonymized_id", anonymized_id).execute()
            
            logger.info(f"✓ Recruiter override added for {anonymized_id}: {recruiter_decision}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error adding recruiter override: {e}")
            raise
    
    def get_candidates_requiring_review(self, limit: int = 100) -> List[Dict]:
        """
        Get all candidates that require human review (confidence < 70%)
        
        Args:
            limit: Maximum results
            
        Returns:
            List of candidates requiring human review
        """
        try:
            response = self.client.table(self.table_name).select("*").or_(
                "requires_human_review.eq.true,verdict.eq.REVIEW"
            ).is_("recruiter_override", "null").order(
                "confidence_score", desc=False
            ).limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Error fetching review queue: {e}")

            # Backward compatibility: older schemas may not have requires_human_review.
            # In that case, fall back to verdict-only review queue instead of returning empty.
            if "requires_human_review" in err_msg or "42703" in err_msg:
                try:
                    response = self.client.table(self.table_name).select("*").eq(
                        "verdict", "REVIEW"
                    ).is_("recruiter_override", "null").order(
                        "confidence_score", desc=False
                    ).limit(limit).execute()
                    return response.data
                except Exception as fallback_error:
                    logger.error(f"Fallback review queue query failed: {fallback_error}")

            return []


def main():
    """CLI entry point for Supabase operations"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manage CV intelligence storage in Supabase"
    )
    parser.add_argument(
        "--action",
        choices=["setup", "store", "search", "stats"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--input",
        help="Input JSON file (for 'store' action)"
    )
    parser.add_argument(
        "--verdict",
        choices=["SHORTLIST", "BACKUP", "REVIEW"],
        help="Filter by verdict (for 'search' action) - NO AUTO-REJECT POLICY"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        help="Minimum match score (for 'search' action)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.action == "setup":
        storage = SupabaseStorage()
        print("\n" + "="*60)
        print("Supabase Table Setup SQL")
        print("="*60)
        print("\nExecute this SQL in your Supabase dashboard:\n")
        print(storage.create_tables())
        print("="*60 + "\n")
    
    elif args.action == "store":
        if not args.input:
            print("Error: --input required for store action")
            return
        
        storage = SupabaseStorage()
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        result = storage.store_intelligence(data)
        print(f"✓ Stored candidate: {result.get('candidate_id')}")
    
    elif args.action == "search":
        storage = SupabaseStorage()
        results = storage.search_by_filters(
            verdict=args.verdict,
            min_match_score=args.min_score
        )
        
        print(f"\nFound {len(results)} candidates:")
        for r in results:
            print(f"  - {r['candidate_id']}: {r['verdict']} (Score: {r['match_score']})")
    
    elif args.action == "stats":
        storage = SupabaseStorage()
        stats = storage.get_statistics()
        
        print("\n" + "="*60)
        print("CV Database Statistics")
        print("="*60)
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
