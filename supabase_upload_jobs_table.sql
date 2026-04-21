-- Create upload_jobs table for tracking async upload job status across multiple app instances
-- This solves the issue where jobs created in one Render instance are not visible in another

CREATE TABLE IF NOT EXISTS upload_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    upload_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    job_description TEXT,
    job_description_provided BOOLEAN DEFAULT FALSE,
    force_reprocess BOOLEAN DEFAULT FALSE,
    error TEXT,
    pipeline_result JSONB,
    llm_runtime_config JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for faster job lookups
CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_jobs(status);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_completed_at ON upload_jobs(completed_at);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_upload_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists, then recreate
DROP TRIGGER IF EXISTS upload_jobs_updated_at ON upload_jobs;

CREATE TRIGGER upload_jobs_updated_at
    BEFORE UPDATE ON upload_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_upload_jobs_updated_at();

-- Function to cleanup old completed/failed jobs (older than 1 hour)
CREATE OR REPLACE FUNCTION cleanup_old_upload_jobs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM upload_jobs
    WHERE status IN ('completed', 'failed')
    AND completed_at < NOW() - INTERVAL '1 hour';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust role name as needed)
ALTER TABLE upload_jobs ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Service role can manage upload_jobs" ON upload_jobs;
DROP POLICY IF EXISTS "Anyone can read upload_jobs" ON upload_jobs;

-- Allow service role to do everything
CREATE POLICY "Service role can manage upload_jobs"
    ON upload_jobs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Allow anon role to read their own jobs (if needed for frontend)
CREATE POLICY "Anyone can read upload_jobs"
    ON upload_jobs
    FOR SELECT
    TO anon, authenticated
    USING (true);
