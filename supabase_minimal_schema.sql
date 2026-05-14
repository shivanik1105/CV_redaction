-- Minimal Supabase schema for this repo
-- Goal: keep ONLY what the running app actually needs.
-- Notes:
-- - The Python code (supabase_storage.py) retries writes if optional columns are missing.
-- - If you do NOT use semantic search, you can skip the pgvector bits entirely.
-- - Prefer running this in Supabase SQL Editor.

-- UUID helper
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- 1) REQUIRED: cv_intelligence (core candidate records)
-- =========================================================
CREATE TABLE IF NOT EXISTS public.cv_intelligence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Core identity used everywhere
  anonymized_id text UNIQUE NOT NULL,  -- e.g. CAND_123

  -- Core fields commonly displayed / used
  verdict text DEFAULT 'BACKUP',
  confidence_score integer,
  match_score integer,
  overall_summary text,
  cleaned_text text,

  -- Timestamps
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Helpful indexes (optional but cheap)
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_created_at ON public.cv_intelligence (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cv_intelligence_verdict ON public.cv_intelligence (verdict);

-- updated_at trigger (optional)
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_cv_intelligence_updated_at ON public.cv_intelligence;
CREATE TRIGGER update_cv_intelligence_updated_at
BEFORE UPDATE ON public.cv_intelligence
FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- =========================================================
-- 2) OPTIONAL: semantic search (pgvector)
--    Only needed if you use /api/quick-search and vector matching.
-- =========================================================
-- Enable pgvector
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column (choose ONE dimension that matches your embedding model)
-- Common dims in this repo:
-- - 384  : sentence-transformers all-MiniLM-L6-v2
-- - 768  : larger sentence-transformers models
-- - 1536 : OpenAI text-embedding-3-small style dims (legacy examples)
--
-- ALTER TABLE public.cv_intelligence
--   ADD COLUMN IF NOT EXISTS embedding vector(384);
--
-- CREATE INDEX IF NOT EXISTS idx_cv_intelligence_embedding
--   ON public.cv_intelligence USING ivfflat (embedding vector_cosine_ops)
--   WITH (lists = 100);

-- RPC used by supabase_storage.py: match_cv_embeddings
-- See supabase_pgvector_setup.sql for a full implementation.


-- =========================================================
-- 3) OPTIONAL: filename mapping table
--    Only needed if you want to map anonymized_id -> original uploaded filename in DB.
-- =========================================================
CREATE TABLE IF NOT EXISTS public.cv_filename_mapping (
  anonymized_id text PRIMARY KEY REFERENCES public.cv_intelligence(anonymized_id) ON DELETE CASCADE,
  original_filename text NOT NULL,
  anonymized_filename text NOT NULL,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cv_filename_mapping_original_filename
  ON public.cv_filename_mapping (original_filename);


-- =========================================================
-- 4) OPTIONAL: job tracking tables
--    Only needed if you want durable async status across restarts / multiple instances.
-- =========================================================
-- CREATE TABLE IF NOT EXISTS public.upload_jobs (...);
-- CREATE TABLE IF NOT EXISTS public.processing_jobs (...);
--
-- RPC cleanup_old_upload_jobs is also optional.


-- =========================================================
-- 5) OPTIONAL: audit logging
--    Only needed for compliance and debugging.
-- =========================================================
-- CREATE TABLE IF NOT EXISTS public.audit_log (...);
