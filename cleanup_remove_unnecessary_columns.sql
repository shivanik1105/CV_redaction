-- ============================================================================
-- CLEANUP MIGRATION: Remove unnecessary columns and fix schema
-- Run this in Supabase SQL Editor
-- ============================================================================

-- 1. Drop recruiter/reviewer columns (always empty, not used)
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS recruiter_override;
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS reviewer_id;
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS reviewer_notes;
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS reviewed_at;

-- 2. Drop verdict column (user requested removal)
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS verdict;

-- 3. Drop match_score (no longer used without verdict)
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS match_score;

-- 4. Drop requires_human_review (not part of current workflow)
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS requires_human_review;

-- 5. Drop best_knowledge_summary (mostly empty, duplicates other fields)
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS best_knowledge_summary;

-- 6. Drop job_description_hash (not tracked at row level)
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS job_description_hash;

-- 7. Drop duplicate years_experience (use years_of_experience)
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS years_experience;

-- 8. Clean up indexes on dropped columns
DROP INDEX IF EXISTS idx_verdict;
DROP INDEX IF EXISTS idx_match_score;
DROP INDEX IF EXISTS idx_confidence_score;
DROP INDEX IF EXISTS idx_requires_human_review;
DROP INDEX IF EXISTS idx_recruiter_override;

-- 9. Re-add useful indexes
CREATE INDEX IF NOT EXISTS idx_confidence_score ON cv_intelligence(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_seniority ON cv_intelligence(seniority_level);
CREATE INDEX IF NOT EXISTS idx_years_experience ON cv_intelligence(years_of_experience);
CREATE INDEX IF NOT EXISTS idx_primary_domain ON cv_intelligence(primary_domain);
CREATE INDEX IF NOT EXISTS idx_created_at ON cv_intelligence(created_at DESC);

-- ============================================================================
-- VERIFY: Show remaining columns
-- ============================================================================
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'cv_intelligence'
ORDER BY ordinal_position;

