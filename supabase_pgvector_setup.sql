-- ============================================
-- Supabase pgvector Setup for Efficient Semantic Search
-- ============================================
-- Run this SQL in your Supabase SQL Editor
-- This creates the embedding column and RPC function for fast vector similarity search

-- 1. Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add embedding column to cv_intelligence table
-- Check if column exists first
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cv_intelligence' 
        AND column_name = 'embedding'
    ) THEN
        ALTER TABLE cv_intelligence 
        ADD COLUMN embedding vector(384);  -- 384 dimensions for all-MiniLM-L6-v2
        
        -- If using OpenAI embeddings instead, use:
        -- ADD COLUMN embedding vector(1536);
    END IF;
END $$;

-- 3. Create the match_cv_embeddings RPC function
-- This function uses pgvector's native similarity search with index
CREATE OR REPLACE FUNCTION match_cv_embeddings(
  query_embedding vector(384),  -- Change to 1536 if using OpenAI embeddings
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
  embedding vector(384),  -- Change to 1536 if using OpenAI
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

-- 4. Create vector index for fast similarity search
-- This dramatically speeds up searches (from O(n) to O(log n))
-- Drop existing index if it exists
DROP INDEX IF EXISTS cv_intelligence_embedding_idx;

-- Create IVFFlat index (good for up to 10,000 vectors)
CREATE INDEX cv_intelligence_embedding_idx 
ON cv_intelligence 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Note: For production with 10,000+ CVs, use HNSW index instead:
-- CREATE INDEX cv_intelligence_embedding_idx 
-- ON cv_intelligence 
-- USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- 5. Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO authenticated;
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO anon;

-- 6. Create a helper function to update embeddings
CREATE OR REPLACE FUNCTION update_cv_embedding(
  p_anonymized_id text,
  p_embedding vector(384)  -- Change to 1536 if using OpenAI
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

GRANT EXECUTE ON FUNCTION update_cv_embedding TO authenticated;
GRANT EXECUTE ON FUNCTION update_cv_embedding TO anon;

-- ============================================
-- Performance Notes:
-- ============================================
-- Without index: O(n) - scans all records
-- With IVFFlat index: O(log n) - uses approximate nearest neighbor
-- With HNSW index: O(log n) - even faster, better recall
--
-- Expected performance:
-- - 100 CVs: <10ms
-- - 1,000 CVs: <50ms
-- - 10,000 CVs: <100ms
-- - 100,000 CVs: <500ms
--
-- Compare to fetching all records and computing locally:
-- - 100 CVs: ~500ms
-- - 1,000 CVs: ~5s
-- - 10,000 CVs: ~50s (unacceptable!)
-- ============================================

-- 7. Verify setup
SELECT 
  column_name, 
  data_type 
FROM information_schema.columns 
WHERE table_name = 'cv_intelligence' 
  AND column_name = 'embedding';

-- Should return: embedding | USER-DEFINED (vector type)

-- 8. Test the function (after embeddings are populated)
-- SELECT * FROM match_cv_embeddings(
--   '[0.1, 0.2, ...]'::vector(384),  -- Your query embedding
--   0.7,  -- Similarity threshold
--   10    -- Number of results
-- );

-- ============================================
-- Next Steps:
-- ============================================
-- 1. Run this SQL in Supabase SQL Editor
-- 2. Run backfill_embeddings.py to populate embeddings
-- 3. Restart Flask app
-- 4. Test semantic search - should be 50x faster!
-- ============================================