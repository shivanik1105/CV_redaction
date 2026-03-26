-- Job Description Library Schema
-- Stores JDs for reuse and analytics

-- Create job_descriptions table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jd_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 hash for deduplication
    jd_text TEXT NOT NULL,
    jd_title VARCHAR(255),  -- Extracted job title
    
    -- Extracted metadata
    required_skills JSONB,  -- Array of required skills
    nice_to_have_skills JSONB,  -- Array of nice-to-have skills
    min_years_experience DECIMAL(4,1),
    max_years_experience DECIMAL(4,1),
    seniority_level VARCHAR(20),
    primary_domain VARCHAR(100),
    location VARCHAR(255),
    employment_type VARCHAR(50),  -- Full-time, Contract, etc.
    
    -- Search analytics
    search_count INTEGER DEFAULT 1,  -- How many times searched
    last_searched_at TIMESTAMP DEFAULT NOW(),
    total_matches_found INTEGER DEFAULT 0,  -- Total candidates matched
    avg_match_score DECIMAL(5,2),  -- Average match score
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Full-text search
    search_vector TSVECTOR
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_jd_hash ON job_descriptions(jd_hash);
CREATE INDEX IF NOT EXISTS idx_jd_title ON job_descriptions(jd_title);
CREATE INDEX IF NOT EXISTS idx_jd_search_count ON job_descriptions(search_count DESC);
CREATE INDEX IF NOT EXISTS idx_jd_last_searched ON job_descriptions(last_searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_jd_created ON job_descriptions(created_at DESC);

-- Create GIN indexes for JSONB fields
CREATE INDEX IF NOT EXISTS idx_jd_required_skills ON job_descriptions USING GIN(required_skills);
CREATE INDEX IF NOT EXISTS idx_jd_nice_skills ON job_descriptions USING GIN(nice_to_have_skills);

-- Create full-text search index
CREATE INDEX IF NOT EXISTS idx_jd_search_vector ON job_descriptions USING GIN(search_vector);

-- Create trigger to update search_vector
CREATE OR REPLACE FUNCTION update_jd_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.jd_title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.jd_text, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.primary_domain, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_update_jd_search_vector 
BEFORE INSERT OR UPDATE ON job_descriptions
FOR EACH ROW EXECUTE FUNCTION update_jd_search_vector();

-- Create updated_at trigger
CREATE TRIGGER update_jd_updated_at 
BEFORE UPDATE ON job_descriptions
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create search history table (optional - for detailed analytics)
CREATE TABLE IF NOT EXISTS jd_search_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jd_id UUID REFERENCES job_descriptions(id) ON DELETE CASCADE,
    search_timestamp TIMESTAMP DEFAULT NOW(),
    matches_found INTEGER,
    top_match_score DECIMAL(5,2),
    search_filters JSONB,  -- Store filters used
    user_id VARCHAR(100)  -- Optional: track which recruiter searched
);

CREATE INDEX IF NOT EXISTS idx_search_history_jd ON jd_search_history(jd_id);
CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON jd_search_history(search_timestamp DESC);

-- Helper function to find similar JDs
CREATE OR REPLACE FUNCTION find_similar_jds(
    query_text TEXT,
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    jd_title VARCHAR(255),
    jd_text TEXT,
    similarity_score FLOAT,
    search_count INTEGER,
    last_searched_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        jd.id,
        jd.jd_title,
        jd.jd_text,
        ts_rank(jd.search_vector, plainto_tsquery('english', query_text)) AS similarity_score,
        jd.search_count,
        jd.last_searched_at
    FROM job_descriptions jd
    WHERE jd.search_vector @@ plainto_tsquery('english', query_text)
    ORDER BY similarity_score DESC, jd.search_count DESC
    LIMIT max_results;
END;
$$;

-- Grant permissions
GRANT ALL ON job_descriptions TO authenticated;
GRANT ALL ON jd_search_history TO authenticated;
GRANT EXECUTE ON FUNCTION find_similar_jds TO authenticated;

-- Sample queries for analytics

-- Most searched JDs
-- SELECT jd_title, search_count, last_searched_at 
-- FROM job_descriptions 
-- ORDER BY search_count DESC 
-- LIMIT 10;

-- JDs with best match rates
-- SELECT jd_title, avg_match_score, total_matches_found, search_count
-- FROM job_descriptions 
-- WHERE search_count > 5
-- ORDER BY avg_match_score DESC 
-- LIMIT 10;

-- Recent JDs
-- SELECT jd_title, created_at, search_count
-- FROM job_descriptions 
-- ORDER BY created_at DESC 
-- LIMIT 10;
