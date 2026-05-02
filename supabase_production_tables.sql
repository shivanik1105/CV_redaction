-- Production tables for CV Redactor
-- Run this in Supabase SQL Editor before deploying to production

-- ============================================================================
-- 1. Processing Jobs Table (Crash Recovery & Status Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS processing_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'done', 'failed')),
    stage_completed TEXT,  -- 'extracting', 'redacting', 'extracting_intelligence', 'generating_embedding', 'storing', 'completed'
    candidate_id TEXT,     -- anonymized CAND_XXX
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status, created_at DESC);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_processing_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS processing_jobs_updated_at ON processing_jobs;
CREATE TRIGGER processing_jobs_updated_at
    BEFORE UPDATE ON processing_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_processing_jobs_updated_at();

-- Cleanup old completed jobs (older than 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_processing_jobs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM processing_jobs
    WHERE status IN ('done', 'failed')
    AND updated_at < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 2. Audit Log Table (GDPR Article 30 Compliance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL CHECK (action IN ('upload', 'search', 'view', 'export', 'delete', 'update')),
    candidate_id TEXT,              -- anonymized CAND_XXX
    recruiter_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    metadata JSONB,                 -- search query, match score, filters, etc.
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for GDPR Article 30 lookups (by org and date)
CREATE INDEX IF NOT EXISTS idx_audit_log_org_created ON audit_log(org_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_candidate ON audit_log(candidate_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_recruiter ON audit_log(recruiter_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action, created_at DESC);

-- Function to get audit trail for a candidate
CREATE OR REPLACE FUNCTION get_candidate_audit_trail(p_candidate_id TEXT, p_org_id TEXT)
RETURNS TABLE (
    action TEXT,
    recruiter_id TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.action,
        a.recruiter_id,
        a.metadata,
        a.created_at
    FROM audit_log a
    WHERE a.candidate_id = p_candidate_id
    AND a.org_id = p_org_id
    ORDER BY a.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get org activity summary
CREATE OR REPLACE FUNCTION get_org_activity_summary(p_org_id TEXT, p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    action TEXT,
    count BIGINT,
    unique_recruiters BIGINT,
    unique_candidates BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.action,
        COUNT(*) as count,
        COUNT(DISTINCT a.recruiter_id) as unique_recruiters,
        COUNT(DISTINCT a.candidate_id) as unique_candidates
    FROM audit_log a
    WHERE a.org_id = p_org_id
    AND a.created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY a.action
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. HNSW Index for Faster Vector Search
-- ============================================================================

-- Drop old IVFFlat index if exists
DROP INDEX IF EXISTS candidates_embedding_idx;
DROP INDEX IF EXISTS cv_intelligence_embedding_idx;

-- Create HNSW index (faster for < 100k rows, no probe tuning needed)
-- Note: Adjust table name based on your schema (candidates or cv_intelligence)
CREATE INDEX IF NOT EXISTS candidates_embedding_hnsw 
ON cv_intelligence 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Set search quality at query time (add this to your Python code)
-- SET hnsw.ef_search = 64;

-- ============================================================================
-- 4. Add org_id Column (Multi-Tenant Support)
-- ============================================================================

-- Add org_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'cv_intelligence' 
        AND column_name = 'org_id'
    ) THEN
        ALTER TABLE cv_intelligence ADD COLUMN org_id TEXT DEFAULT 'default_org';
        CREATE INDEX idx_cv_intelligence_org_id ON cv_intelligence(org_id);
    END IF;
END $$;

-- ============================================================================
-- 5. Row Level Security (Multi-Tenant Isolation) - OPTIONAL
-- ============================================================================

-- IMPORTANT: Only enable RLS if you're deploying for multiple organizations
-- For single-org deployment, skip this section

-- Enable RLS on cv_intelligence table
-- ALTER TABLE cv_intelligence ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
-- DROP POLICY IF EXISTS "org_isolation" ON cv_intelligence;
-- DROP POLICY IF EXISTS "service_role_full_access" ON cv_intelligence;

-- Service role has full access (for backend operations)
-- CREATE POLICY "service_role_full_access"
-- ON cv_intelligence
-- FOR ALL
-- TO service_role
-- USING (true)
-- WITH CHECK (true);

-- Recruiters only see their org's candidates
-- Note: You need to set app.org_id in your Python code before queries
-- Example: storage.client.rpc('set_config', {'setting': 'app.org_id', 'value': org_id})
-- CREATE POLICY "org_isolation"
-- ON cv_intelligence
-- FOR ALL
-- TO authenticated
-- USING (org_id = current_setting('app.org_id', true))
-- WITH CHECK (org_id = current_setting('app.org_id', true));

-- Enable RLS on audit_log
-- ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- DROP POLICY IF EXISTS "audit_org_isolation" ON audit_log;
-- DROP POLICY IF EXISTS "audit_service_role_full_access" ON audit_log;

-- CREATE POLICY "audit_service_role_full_access"
-- ON audit_log
-- FOR ALL
-- TO service_role
-- USING (true)
-- WITH CHECK (true);

-- CREATE POLICY "audit_org_isolation"
-- ON audit_log
-- FOR SELECT
-- TO authenticated
-- USING (org_id = current_setting('app.org_id', true));

-- ============================================================================
-- 5. Utility Functions
-- ============================================================================

-- Function to get processing job status
CREATE OR REPLACE FUNCTION get_processing_status(p_job_id TEXT)
RETURNS TABLE (
    job_id TEXT,
    status TEXT,
    stage_completed TEXT,
    candidate_id TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    processing_time_seconds INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pj.job_id,
        pj.status,
        pj.stage_completed,
        pj.candidate_id,
        pj.error_message,
        pj.created_at,
        pj.updated_at,
        EXTRACT(EPOCH FROM (pj.updated_at - pj.created_at))::INTEGER as processing_time_seconds
    FROM processing_jobs pj
    WHERE pj.job_id = p_job_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get stuck jobs (processing for > 10 minutes)
CREATE OR REPLACE FUNCTION get_stuck_jobs()
RETURNS TABLE (
    job_id TEXT,
    status TEXT,
    stage_completed TEXT,
    stuck_for_minutes INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pj.job_id,
        pj.status,
        pj.stage_completed,
        EXTRACT(EPOCH FROM (NOW() - pj.updated_at))::INTEGER / 60 as stuck_for_minutes
    FROM processing_jobs pj
    WHERE pj.status = 'processing'
    AND pj.updated_at < NOW() - INTERVAL '10 minutes'
    ORDER BY pj.updated_at ASC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. Scheduled Cleanup (Optional - requires pg_cron extension)
-- ============================================================================

-- Uncomment if you have pg_cron enabled in Supabase
-- SELECT cron.schedule(
--     'cleanup-old-processing-jobs',
--     '0 2 * * *',  -- Run at 2 AM daily
--     $$SELECT cleanup_old_processing_jobs()$$
-- );

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('processing_jobs', 'audit_log');

-- Check if indexes exist
SELECT indexname 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('processing_jobs', 'audit_log', 'cv_intelligence');

-- Check RLS status
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('cv_intelligence', 'audit_log');

-- Test processing job insert
-- INSERT INTO processing_jobs (job_id, status) VALUES ('test_job_123', 'queued');
-- SELECT * FROM processing_jobs WHERE job_id = 'test_job_123';
-- DELETE FROM processing_jobs WHERE job_id = 'test_job_123';
