-- ============================================================
-- Database Migration: Remove Verdict & Review Columns
-- ============================================================
-- Run this in Supabase SQL Editor
-- Date: 2026-03-26

-- Step 1: Drop verdict column
ALTER TABLE cv_intelligence 
DROP COLUMN IF EXISTS verdict CASCADE;

-- Step 2: Drop requires_human_review column  
ALTER TABLE cv_intelligence 
DROP COLUMN IF EXISTS requires_human_review CASCADE;

-- Step 3: Drop verdict-related indexes
DROP INDEX IF EXISTS idx_verdict;
DROP INDEX IF EXISTS idx_requires_human_review;

-- Step 4: Rename evidence_based_reasoning to assessment_reason (optional but recommended)
-- Note: This will fail if column doesn't exist or is already renamed
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'cv_intelligence' 
        AND column_name = 'evidence_based_reasoning'
    ) THEN
        ALTER TABLE cv_intelligence 
        RENAME COLUMN evidence_based_reasoning TO assessment_reason;
        RAISE NOTICE 'Column renamed successfully';
    ELSE
        RAISE NOTICE 'Column evidence_based_reasoning does not exist or already renamed';
    END IF;
END $$;

-- Verify changes
SELECT 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name = 'cv_intelligence' 
ORDER BY ordinal_position;

-- Show sample data to verify
SELECT 
    anonymized_id,
    confidence_score,
    match_score,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'cv_intelligence' 
            AND column_name = 'assessment_reason'
        ) THEN 'assessment_reason column exists'
        ELSE 'using evidence_based_reasoning'
    END as column_status
FROM cv_intelligence 
LIMIT 1;
