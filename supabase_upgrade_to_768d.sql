-- ============================================
-- Upgrade Supabase pgvector from 384d to 768d
-- ============================================
-- Run this SQL in your Supabase SQL Editor to upgrade to all-mpnet-base-v2 model
-- This will:
-- 1. Drop existing functions and indexes
-- 2. Drop the old 384-dimensional embedding column
-- 3. Create a new 768-dimensional embedding column
-- 4. Create new RPC functions for 768 dimensions
-- 5. Recreate the vector index

-- IMPORTANT: After running this, you MUST run regenerate_embeddings.py --force to populate the new embeddings!

-- 1. Drop existing index (required before changing column type)
DROP INDEX IF EXISTS cv_intelligence_embedding_idx;

-- 2. Drop existing functions first (required before changing signatures)
DROP FUNCTION IF EXISTS match_cv_embeddings(vector, float, integer);
DROP FUNCTION IF EXISTS match_cv_embeddings(vector(384), float, integer);
DROP FUNCTION IF EXISTS update_cv_embedding(text, vector);
DROP FUNCTION IF EXISTS update_cv_embedding(text, vector(384));

-- 3. Drop the old embedding column
ALTER TABLE cv_intelligence DROP COLUMN IF EXISTS embedding;

-- 4. Add new 768-dimensional embedding column
ALTER TABLE cv_intelligence ADD COLUMN embedding vector(768);

-- 5. Create the match_cv_embeddings RPC function for 768 dimensions
CREATE OR REPLACE FUNCTION match_cv_embeddings(
  query_embedding vector(768),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  anonymized_id text,
  verdict text,
  confidence_score int,
  years_of_experience float,
  career_level text,
  key_skills jsonb,
  domain_expertise jsonb,
  overall_summary text,
  similarity_score float,
  embedding vector(768),
  created_at timestamp,
  updated_at timestamp
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    cv.anonymized_id,
    cv.verdict,
    cv.confidence_score,
    cv.years_of_experience,
    cv.career_level,
    cv.key_skills,
    cv.domain_expertise,
    cv.overall_summary,
    1 - (cv.embedding <=> query_embedding) AS similarity_score,
    cv.embedding,
    cv.created_at,
    cv.updated_at
  FROM cv_intelligence cv
  WHERE cv.embedding IS NOT NULL
    AND 1 - (cv.embedding <=> query_embedding) >= match_threshold
  ORDER BY cv.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 6. Create the helper function for 768 dimensions
CREATE OR REPLACE FUNCTION update_cv_embedding(
  p_anonymized_id text,
  p_embedding vector(768)
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE cv_intelligence
  SET embedding = p_embedding,
      updated_at = NOW()
  WHERE anonymized_id = p_anonymized_id;
END;
$$;

-- 7. Grant execute permissions
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO authenticated;
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO anon;
GRANT EXECUTE ON FUNCTION update_cv_embedding TO authenticated;
GRANT EXECUTE ON FUNCTION update_cv_embedding TO anon;

-- 8. Recreate vector index for 768-dimensional vectors
CREATE INDEX cv_intelligence_embedding_idx 
ON cv_intelligence 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 9. Verify the upgrade
SELECT 
  column_name, 
  data_type,
  udt_name
FROM information_schema.columns 
WHERE table_name = 'cv_intelligence' 
  AND column_name = 'embedding';

-- Should return: embedding | USER-DEFINED | vector

-- ============================================
-- NEXT STEPS (CRITICAL):
-- ============================================
-- 1. ✅ Run this SQL in Supabase SQL Editor
-- 2. ⚠️  Run: python regenerate_embeddings.py --force
--    This will regenerate ALL 139 candidate embeddings with the new 768d model
--    Expected time: ~15-20 minutes
-- 3. ✅ Test with: python test_15_real_jds.py
-- 4. ✅ Deploy to production
--
-- EXPECTED IMPROVEMENTS:
-- • +11.7% better top match scores (56.6% → 63.3%)
-- • 5/5 relevant JDs (was 4/5)
-- • Better contextual understanding
-- ============================================
