"""
Supabase Storage Module
Handles storing and retrieving CV intelligence data with vector search
"""
import os
import json
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
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anonymized_id VARCHAR(20) UNIQUE NOT NULL REFERENCES cv_intelligence(anonymized_id),
    original_filename VARCHAR(255) NOT NULL,
    redacted_filename VARCHAR(255),
    upload_timestamp TIMESTAMP DEFAULT NOW(),
    uploaded_by VARCHAR(100),  -- For multi-user systems
    UNIQUE(original_filename, uploaded_by)
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
        Store CV intelligence in Supabase with new schema
        
        Args:
            intelligence_data: Dictionary from CVIntelligenceExtractor
            
        Returns:
            Response from Supabase
        """
        try:
            # Flatten the nested structure for storage
            flat_data = {
                # Identifiers
                "anonymized_id": intelligence_data.get("anonymized_id"),
                "original_filename": intelligence_data.get("original_filename"),
                "analysis_date": intelligence_data.get("analysis_date"),
                
                # Cleaned Content
                "cleaned_text": intelligence_data.get("cleaned_text"),
                "cleaned_narrative": intelligence_data.get("cleaned_narrative"),
                
                # Core Metadata
                "years_experience": intelligence_data.get("years_experience"),
                "years_experience_range": intelligence_data.get("years_experience_range"),
                "seniority_level": intelligence_data.get("seniority_level"),
                
                # Skills
                "core_technical_skills": intelligence_data.get("core_technical_skills", []),
                "secondary_technical_skills": intelligence_data.get("secondary_technical_skills", []),
                "frameworks_tools": intelligence_data.get("frameworks_tools", []),
                "soft_skills": intelligence_data.get("soft_skills", []),
                "certifications": intelligence_data.get("certifications", []),
                
                # Domain & Experience
                "primary_domain": intelligence_data.get("primary_domain"),
                "secondary_domains": intelligence_data.get("secondary_domains", []),
                "role_types": intelligence_data.get("role_types", []),
                "leadership_indicators": intelligence_data.get("leadership_indicators", []),
                
                # Education
                "highest_degree": intelligence_data.get("highest_degree"),
                "field_of_study": intelligence_data.get("field_of_study"),
                "education_level": intelligence_data.get("education_level"),
                
                # JD Fitment
                "verdict": intelligence_data.get("verdict"),
                "confidence_score": intelligence_data.get("confidence_score"),
                "match_score": intelligence_data.get("match_score"),
                "verdict_reason": intelligence_data.get("verdict_reason"),
                "requires_human_review": intelligence_data.get("requires_human_review", False),
                
                # Detailed Analysis
                "matched_requirements": intelligence_data.get("matched_requirements", []),
                "missing_requirements": intelligence_data.get("missing_requirements", []),
                "key_strengths": intelligence_data.get("key_strengths", []),
                "potential_concerns": intelligence_data.get("potential_concerns", []),
                
                # Search Optimization
                "search_keywords": intelligence_data.get("search_keywords", []),
                "highlight_achievements": intelligence_data.get("highlight_achievements", []),
                
                # Metadata
                "llm_provider": intelligence_data.get("llm_provider"),
                "llm_model": intelligence_data.get("llm_model"),
                "extraction_timestamp": intelligence_data.get("extraction_timestamp"),
                "job_description_hash": intelligence_data.get("job_description_hash"),
                
                # Audit Trail
                "original_cv_hash": intelligence_data.get("original_cv_hash"),
                "llm_prompt_used": intelligence_data.get("llm_prompt_used"),
                "llm_raw_response": intelligence_data.get("llm_raw_response"),
            }
            
            # Insert or upsert
            response = self.client.table(self.table_name).upsert(
                flat_data,
                on_conflict="anonymized_id"
            ).execute()
            
            logger.info(f"✓ Stored intelligence for {flat_data['anonymized_id']}")
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Error storing intelligence: {e}")
            raise
    
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
        redacted_filename: str = None,
        uploaded_by: str = "system"
    ) -> Dict:
        """
        Store filename mapping in secure backend table
        
        Args:
            anonymized_id: The anonymized candidate ID (e.g., "CAND_882")
            original_filename: Original uploaded filename
            redacted_filename: Redacted/anonymized filename (optional)
            uploaded_by: User identifier (for multi-user systems)
            
        Returns:
            Mapping record
        """
        try:
            mapping_data = {
                "anonymized_id": anonymized_id,
                "original_filename": original_filename,
                "redacted_filename": redacted_filename,
                "uploaded_by": uploaded_by
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
            query = query.eq("seniority_level", seniority_level)
        
        if min_match_score is not None:
            query = query.gte("match_score", min_match_score)
        
        if min_confidence_score is not None:
            query = query.gte("confidence_score", min_confidence_score)
        
        if required_skills:
            # Check if core_technical_skills contains all required skills
            for skill in required_skills:
                query = query.contains("core_technical_skills", [skill])
        
        if primary_domain:
            query = query.eq("primary_domain", primary_domain)
        
        if domains:
            # Check if secondary_domains overlaps with requested domains
            for domain in domains:
                query = query.contains("secondary_domains", [domain])
        
        if min_years_experience is not None:
            query = query.gte("years_experience", min_years_experience)
        
        if max_years_experience is not None:
            query = query.lte("years_experience", max_years_experience)
        
        # Order by match score descending, then confidence descending
        query = query.order("match_score", desc=True).order("confidence_score", desc=True).limit(limit)
        
        response = query.execute()
        return response.data
    
    def semantic_search(
        self,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Perform semantic search using vector embeddings
        
        Note: This requires generating embeddings for the query text first
        You'll need to implement embedding generation using OpenAI or similar
        
        Args:
            query_text: Natural language query
            limit: Maximum results
            similarity_threshold: Minimum similarity (0-1)
            
        Returns:
            List of matching CV records with similarity scores
        """
        # TODO: Generate embedding for query_text
        # embedding = generate_embedding(query_text)
        
        # For now, return a placeholder
        logger.warning("Semantic search requires embedding generation - not implemented yet")
        return []
    
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
            
            avg_match_score = sum(r.get("match_score", 0) for r in all_records) / total if total > 0 else 0
            avg_confidence_score = sum(r.get("confidence_score", 0) for r in all_records) / total if total > 0 else 0
            
            return {
                "total_candidates": total,
                "shortlisted": shortlisted,
                "backup": backup,
                "review_needed": review_needed,
                "requires_human_review": requires_human,
                "recruiter_reviewed": recruiter_reviewed,
                "average_match_score": round(avg_match_score, 2),
                "average_confidence_score": round(avg_confidence_score, 2)
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
            response = self.client.table(self.table_name).select("*").eq(
                "requires_human_review", True
            ).is_("recruiter_override", "null").order(
                "confidence_score", desc=False
            ).limit(limit).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error fetching review queue: {e}")
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
