-- ============================================
-- Supabase pgvector Setup for Efficient Semantic Search
-- ============================================
-- Run this SQL in your Supabase SQL Editor
-- This creates an RPC function for fast vector similarity search

-- 1. Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the match_cv_embeddings RPC function
-- This function uses pgvector's native similarity search with index
CREATE OR REPLACE FUNCTION match_cv_embeddings(
  query_embedding vector(384),  -- Change to 1536 if using OpenAI embeddings
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  anonymized_id text,
  verdict text,
  match_score int,
  confidence_score int,
  years_experience float,
  seniority_level text,
  core_technical_skills jsonb,
  primary_domain text,
  secondary_domains jsonb,
  cleaned_narrative text,
  similarity_score float,
  embedding vector(384)  -- Change to 1536 if using OpenAI
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    cv.anonymized_id,
    cv.verdict,
    cv.match_score,
    cv.confidence_score,
    cv.years_experience,
    cv.seniority_level,
    cv.core_technical_skills,
    cv.primary_domain,
    cv.secondary_domains,
    cv.cleaned_narrative,
    1 - (cv.embedding <=> query_embedding) AS similarity_score,
    cv.embedding
  FROM cv_intelligence cv
  WHERE cv.embedding IS NOT NULL
    AND 1 - (cv.embedding <=> query_embedding) >= match_threshold
  ORDER BY cv.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 3. Create vector index for fast similarity search
-- This dramatically speeds up searches (from O(n) to O(log n))
CREATE INDEX IF NOT EXISTS cv_intelligence_embedding_idx 
ON cv_intelligence 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Note: For production with 10,000+ CVs, use HNSW index instead:
-- CREATE INDEX IF NOT EXISTS cv_intelligence_embedding_idx 
-- ON cv_intelligence 
-- USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- 4. Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO authenticated;
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO anon;

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

-- 5. Test the function
-- SELECT * FROM match_cv_embeddings(
--   '[0.1, 0.2, ...]'::vector(384),  -- Your query embedding
--   0.7,  -- Similarity threshold
--   10    -- Number of results
-- );
