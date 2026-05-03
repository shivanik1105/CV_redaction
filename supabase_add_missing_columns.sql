-- Add missing columns to cv_intelligence table
-- Run this in Supabase SQL Editor to add all the new columns

-- Add new columns (IF NOT EXISTS to avoid errors if already added)
ALTER TABLE cv_intelligence 
ADD COLUMN IF NOT EXISTS best_knowledge_summary TEXT,
ADD COLUMN IF NOT EXISTS certifications TEXT[],
ADD COLUMN IF NOT EXISTS cleaned_narrative TEXT,
ADD COLUMN IF NOT EXISTS cleaned_text TEXT,
ADD COLUMN IF NOT EXISTS core_technical_skills TEXT[],
ADD COLUMN IF NOT EXISTS education_level TEXT,
ADD COLUMN IF NOT EXISTS extraction_timestamp TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS field_of_study TEXT,
ADD COLUMN IF NOT EXISTS frameworks_tools TEXT[],
ADD COLUMN IF NOT EXISTS highest_degree TEXT,
ADD COLUMN IF NOT EXISTS highlight_achievements TEXT[],
ADD COLUMN IF NOT EXISTS job_description_hash TEXT,
ADD COLUMN IF NOT EXISTS key_strengths TEXT[],
ADD COLUMN IF NOT EXISTS leadership_indicators TEXT[],
ADD COLUMN IF NOT EXISTS llm_model TEXT,
ADD COLUMN IF NOT EXISTS llm_provider TEXT,
ADD COLUMN IF NOT EXISTS matched_requirements TEXT[],
ADD COLUMN IF NOT EXISTS missing_requirements TEXT[],
ADD COLUMN IF NOT EXISTS potential_concerns TEXT[],
ADD COLUMN IF NOT EXISTS primary_domain TEXT,
ADD COLUMN IF NOT EXISTS requires_human_review BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS role_types TEXT[],
ADD COLUMN IF NOT EXISTS search_keywords TEXT,
ADD COLUMN IF NOT EXISTS secondary_domains TEXT[],
ADD COLUMN IF NOT EXISTS secondary_technical_skills TEXT[],
ADD COLUMN IF NOT EXISTS seniority_level TEXT,
ADD COLUMN IF NOT EXISTS soft_skills TEXT[],
ADD COLUMN IF NOT EXISTS years_experience NUMERIC,
ADD COLUMN IF NOT EXISTS years_experience_range TEXT,
ADD COLUMN IF NOT EXISTS match_score NUMERIC;

-- Add indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_primary_domain ON cv_intelligence(primary_domain);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_seniority_level ON cv_intelligence(seniority_level);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_years_experience ON cv_intelligence(years_experience);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_requires_review ON cv_intelligence(requires_human_review);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_extraction_timestamp ON cv_intelligence(extraction_timestamp DESC);

-- Add GIN indexes for array columns (for fast array searches)
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_core_skills_gin ON cv_intelligence USING GIN(core_technical_skills);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_secondary_skills_gin ON cv_intelligence USING GIN(secondary_technical_skills);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_frameworks_gin ON cv_intelligence USING GIN(frameworks_tools);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_certifications_gin ON cv_intelligence USING GIN(certifications);

-- Add full-text search index on search_keywords
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_search_keywords_gin ON cv_intelligence USING GIN(to_tsvector('english', COALESCE(search_keywords, '')));

-- Verify columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'cv_intelligence' 
ORDER BY ordinal_position;

