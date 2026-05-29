-- ============================================================================
-- PRODUCTION SCHEMA: cv_intelligence
-- Exactly matches the lean 39-column schema requested.
-- All removed columns: verdict, match_score, requires_human_review,
-- recruiter_override, reviewer_id, reviewer_notes, reviewed_at,
-- best_knowledge_summary, job_description_hash, years_experience (duplicate)
-- ============================================================================

-- Drop any lingering columns not in the approved schema
ALTER TABLE public.cv_intelligence
DROP COLUMN IF EXISTS verdict,
DROP COLUMN IF EXISTS match_score,
DROP COLUMN IF EXISTS requires_human_review,
DROP COLUMN IF EXISTS recruiter_override,
DROP COLUMN IF EXISTS reviewer_id,
DROP COLUMN IF EXISTS reviewer_notes,
DROP COLUMN IF EXISTS reviewed_at,
DROP COLUMN IF EXISTS best_knowledge_summary,
DROP COLUMN IF EXISTS job_description_hash,
DROP COLUMN IF EXISTS years_experience;            -- duplicate of years_of_experience

-- Ensure all columns in the approved schema exist with correct types
-- Columns that already exist will be skipped by IF NOT EXISTS.
DO $$
BEGIN
  -- Core identifiers & audit
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='original_cv_hash') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN original_cv_hash TEXT NOT NULL DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='llm_prompt_used') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN llm_prompt_used TEXT NOT NULL DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='llm_raw_response') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN llm_raw_response TEXT NOT NULL DEFAULT '';
  END IF;

  -- Required scoring / reasoning
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='confidence_score') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='evidence_based_reasoning') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN evidence_based_reasoning TEXT NOT NULL DEFAULT '';
  END IF;

  -- Summary & skills
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='overall_summary') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN overall_summary TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='key_skills') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN key_skills TEXT[] DEFAULT '{}';
  END IF;

  -- Experience
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='years_of_experience') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN years_of_experience DOUBLE PRECISION DEFAULT 0;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='career_level') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN career_level TEXT DEFAULT 'NOT_SPECIFIED';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='years_experience_range') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN years_experience_range TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='seniority_level') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN seniority_level TEXT DEFAULT 'NOT_SPECIFIED';
  END IF;

  -- Domain
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='domain_expertise') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN domain_expertise TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='primary_domain') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN primary_domain TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='secondary_domains') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN secondary_domains TEXT[] DEFAULT '{}';
  END IF;

  -- Content
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='cleaned_narrative') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN cleaned_narrative TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='cleaned_text') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN cleaned_text TEXT DEFAULT '';
  END IF;

  -- Skills (structured)
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='core_technical_skills') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN core_technical_skills TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='secondary_technical_skills') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN secondary_technical_skills TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='frameworks_tools') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN frameworks_tools TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='soft_skills') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN soft_skills TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='certifications') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN certifications TEXT[] DEFAULT '{}';
  END IF;

  -- Education
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='education_level') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN education_level TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='field_of_study') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN field_of_study TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='highest_degree') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN highest_degree TEXT DEFAULT '';
  END IF;

  -- Metadata
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='extraction_timestamp') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN extraction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='llm_model') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN llm_model TEXT DEFAULT '';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='llm_provider') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN llm_provider TEXT DEFAULT '';
  END IF;

  -- Analysis
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='matched_requirements') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN matched_requirements TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='missing_requirements') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN missing_requirements TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='potential_concerns') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN potential_concerns TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='key_strengths') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN key_strengths TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='leadership_indicators') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN leadership_indicators TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='highlight_achievements') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN highlight_achievements TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='role_types') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN role_types TEXT[] DEFAULT '{}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='search_keywords') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN search_keywords TEXT DEFAULT '';
  END IF;

  -- Multi-tenant
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='org_id') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN org_id TEXT DEFAULT 'default_org';
  END IF;

  -- Vector
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='cv_intelligence' AND column_name='embedding') THEN
    ALTER TABLE public.cv_intelligence ADD COLUMN embedding vector(768);
  END IF;
END $$;

-- ============================================================================
-- Drop obsolete indexes
-- ============================================================================
DROP INDEX IF EXISTS idx_verdict;
DROP INDEX IF EXISTS idx_match_score;
DROP INDEX IF EXISTS idx_requires_human_review;
DROP INDEX IF EXISTS idx_recruiter_override;
DROP INDEX IF EXISTS idx_original_cv_hash;
DROP INDEX IF EXISTS idx_cv_intelligence_extraction_timestamp;

-- ============================================================================
-- Essential indexes ONLY (exactly as requested)
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_org_id ON public.cv_intelligence USING btree (org_id);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_seniority_level ON public.cv_intelligence USING btree (seniority_level);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_primary_domain ON public.cv_intelligence USING btree (primary_domain);
CREATE INDEX IF NOT EXISTS idx_confidence_score ON public.cv_intelligence USING btree (confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_core_skills_gin ON public.cv_intelligence USING gin (core_technical_skills);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_frameworks_gin ON public.cv_intelligence USING gin (frameworks_tools);
CREATE INDEX IF NOT EXISTS cv_intelligence_embedding_idx ON public.cv_intelligence USING ivfflat (embedding vector_cosine_ops) WITH (lists = '100');

-- ============================================================================
-- Backfill: ensure every existing row has non-null values for NOT NULL columns
-- ============================================================================
UPDATE public.cv_intelligence
SET
  original_cv_hash = COALESCE(NULLIF(original_cv_hash, ''), 'unknown_' || anonymized_id),
  llm_prompt_used = COALESCE(NULLIF(llm_prompt_used, ''), 'unknown:unknown'),
  llm_raw_response = COALESCE(NULLIF(llm_raw_response, ''), '{}'),
  confidence_score = COALESCE(confidence_score, 0),
  evidence_based_reasoning = COALESCE(NULLIF(evidence_based_reasoning, ''), 'No reasoning provided'),
  overall_summary = COALESCE(NULLIF(overall_summary, ''), 'Summary not available'),
  key_skills = COALESCE(key_skills, '{}'),
  years_of_experience = COALESCE(years_of_experience, 0),
  career_level = COALESCE(NULLIF(career_level, ''), 'NOT_SPECIFIED'),
  seniority_level = COALESCE(NULLIF(seniority_level, ''), 'NOT_SPECIFIED'),
  domain_expertise = COALESCE(domain_expertise, '{}'),
  primary_domain = COALESCE(primary_domain, ''),
  secondary_domains = COALESCE(secondary_domains, '{}'),
  cleaned_narrative = COALESCE(NULLIF(cleaned_narrative, ''), 'Narrative not available'),
  cleaned_text = COALESCE(NULLIF(cleaned_text, ''), 'Text not available'),
  core_technical_skills = COALESCE(core_technical_skills, '{}'),
  secondary_technical_skills = COALESCE(secondary_technical_skills, '{}'),
  frameworks_tools = COALESCE(frameworks_tools, '{}'),
  soft_skills = COALESCE(soft_skills, '{}'),
  certifications = COALESCE(certifications, '{}'),
  education_level = COALESCE(education_level, ''),
  field_of_study = COALESCE(field_of_study, ''),
  highest_degree = COALESCE(highest_degree, ''),
  extraction_timestamp = COALESCE(extraction_timestamp, NOW()),
  llm_model = COALESCE(llm_model, ''),
  llm_provider = COALESCE(llm_provider, ''),
  matched_requirements = COALESCE(matched_requirements, '{}'),
  missing_requirements = COALESCE(missing_requirements, '{}'),
  potential_concerns = COALESCE(potential_concerns, '{}'),
  key_strengths = COALESCE(key_strengths, '{}'),
  leadership_indicators = COALESCE(leadership_indicators, '{}'),
  highlight_achievements = COALESCE(highlight_achievements, '{}'),
  role_types = COALESCE(role_types, '{}'),
  search_keywords = COALESCE(search_keywords, ''),
  org_id = COALESCE(org_id, 'default_org'),
  years_experience_range = COALESCE(years_experience_range, '');

-- ============================================================================
-- Verify final schema
-- ============================================================================
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'cv_intelligence'
ORDER BY ordinal_position;
