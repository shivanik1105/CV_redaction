-- Create cv_embeddings table for storing vector embeddings
-- Run this in Supabase SQL Editor

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table
CREATE TABLE IF NOT EXISTS cv_embeddings (
    anonymized_id TEXT PRIMARY KEY REFERENCES cv_intelligence(anonymized_id) ON DELETE CASCADE,
    embedding vector(384),  -- 384 dimensions for all-MiniLM-L6-v2
    embedding_model TEXT DEFAULT 'all-MiniLM-L6-v2',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search (HNSW is faster than IVFFlat)
CREATE INDEX IF NOT EXISTS cv_embeddings_embedding_idx 
ON cv_embeddings 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cv_embeddings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS cv_embeddings_updated_at ON cv_embeddings;
CREATE TRIGGER cv_embeddings_updated_at
    BEFORE UPDATE ON cv_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_cv_embeddings_updated_at();

-- Verify table was created
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'cv_embeddings'
ORDER BY ordinal_position;

