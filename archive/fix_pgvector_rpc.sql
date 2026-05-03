-- Fix the match_cv_embeddings RPC function
-- The issue is that similarity_score should be named 'similarity' to match Python code

-- Step 1: Drop the existing function first
DROP FUNCTION IF EXISTS match_cv_embeddings(vector, float, int);
DROP FUNCTION IF EXISTS match_cv_embeddings(vector(384), float, int);

-- Step 2: Create the corrected function
CREATE OR REPLACE FUNCTION match_cv_embeddings(
  query_embedding vector(384),
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
  similarity float,
  embedding vector(384),
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
    (1 - (cv.embedding <=> query_embedding))::float AS similarity,
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

-- Grant permissions
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO authenticated;
GRANT EXECUTE ON FUNCTION match_cv_embeddings TO anon;
