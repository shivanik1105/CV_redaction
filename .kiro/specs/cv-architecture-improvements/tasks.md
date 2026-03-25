# Implementation Tasks: CV Architecture Improvements

## Phase 1: Queue System (HIGHEST PRIORITY)

### Task 1.1: Install Redis and Celery Dependencies
- [ ] Add redis>=5.0.0 to requirements.txt
- [ ] Add celery>=5.3.0 to requirements.txt
- [ ] Add flower>=2.0.0 (Celery monitoring tool)
- [ ] Document Redis installation instructions

### Task 1.2: Create Queue Manager Module
- [ ] Create queue_manager.py with QueueManager class
- [ ] Implement enqueue_cv_processing()
- [ ] Implement get_job_status()
- [ ] Implement cancel_job()
- [ ] Implement get_queue_stats()

### Task 1.3: Create Rate Limiter Module
- [ ] Create rate_limiter.py with RateLimiter class
- [ ] Implement check_quota() for API providers
- [ ] Implement record_api_call()
- [ ] Implement get_wait_time()
- [ ] Add Redis-based quota tracking

### Task 1.4: Create Celery Worker
- [ ] Create celery_worker.py with Celery app configuration
- [ ] Create process_cv_task() Celery task
- [ ] Integrate rate limiter into task
- [ ] Add retry logic with exponential backoff
- [ ] Add error handling and logging

### Task 1.5: Update Flask App for Queue Integration
- [ ] Update /upload endpoint to enqueue jobs
- [ ] Update /api/process-samples to use queue
- [ ] Update /api/batch-extract to use queue
- [ ] Add /api/jobs/<job_id>/status endpoint
- [ ] Add /api/queue/stats endpoint

### Task 1.6: Testing and Documentation
- [ ] Write unit tests for queue_manager
- [ ] Write unit tests for rate_limiter
- [ ] Write integration tests for Celery worker
- [ ] Update README with Redis setup instructions
- [ ] Update README with Celery worker startup commands

## Phase 2: Enhanced Triage (HIGH PRIORITY)

### Task 2.1: Create Enhanced Triage Module
- [ ] Create enhanced_triage.py with EnhancedTriageEngine class
- [ ] Implement extract_keywords() with stopword filtering
- [ ] Implement compute_relevance_score() with set intersection
- [ ] Implement should_process() with multi-tier thresholds
- [ ] Add configurable threshold settings

### Task 2.2: Integrate Triage into Worker
- [ ] Add triage check before redaction in Celery worker
- [ ] Store rejection reason for rejected CVs
- [ ] Add triage metrics to job status
- [ ] Update intelligence JSON schema for rejections

### Task 2.3: Testing and Metrics
- [ ] Write unit tests for keyword extraction
- [ ] Write unit tests for relevance scoring
- [ ] Test with 20 CVs spanning 0-100% overlap
- [ ] Measure triage accuracy (precision/recall)
- [ ] Document triage thresholds and tuning

## Phase 3: Vector Search (MEDIUM PRIORITY)

### Task 3.1: Setup pgvector in Supabase
- [ ] Enable pgvector extension in Supabase
- [ ] Add embedding column to cv_intelligence table
- [ ] Create vector index (IVFFlat with 100 lists)
- [ ] Update database schema migration script

### Task 3.2: Create Vector Search Module
- [ ] Create vector_search.py with VectorSearchEngine class
- [ ] Implement generate_embedding() using sentence-transformers
- [ ] Implement store_embedding() to Supabase
- [ ] Implement semantic_search() with cosine similarity
- [ ] Implement hybrid_search() combining semantic + SQL filters

### Task 3.3: Integrate Embedding Generation
- [ ] Add embedding generation to Celery worker
- [ ] Update supabase_storage.py semantic_search() implementation
- [ ] Create backfill script for existing CVs
- [ ] Add embedding model caching

### Task 3.4: Add Search API Endpoints
- [ ] Add /api/search/semantic endpoint
- [ ] Add /api/search/hybrid endpoint
- [ ] Update dashboard UI for semantic search
- [ ] Add search result ranking display

### Task 3.5: Testing and Optimization
- [ ] Write unit tests for embedding generation
- [ ] Write integration tests for semantic search
- [ ] Test with 10 CVs and various queries
- [ ] Measure search latency (<500ms target)
- [ ] Optimize index parameters if needed

## Phase 4: Native JSON Mode (LOW PRIORITY)

### Task 4.1: Update LLM Extraction for JSON Mode
- [ ] Update OpenAI calls to use response_format={"type": "json_object"}
- [ ] Update Gemini calls to use response_mime_type="application/json"
- [ ] Define strict JSON schema for extraction
- [ ] Implement JSON schema validation

### Task 4.2: Add Fallback Logic
- [ ] Implement fallback to structured prompt parsing
- [ ] Add error logging for JSON parsing failures
- [ ] Test with all LLM providers (OpenAI, Gemini, Anthropic)

### Task 4.3: Testing
- [ ] Write unit tests for JSON validation
- [ ] Test with mock LLM responses
- [ ] Measure JSON parsing success rate (>95% target)

## Phase 5: FastAPI Migration (OPTIONAL)

### Task 5.1: Create FastAPI Application
- [ ] Create fastapi_app.py with FastAPI instance
- [ ] Implement async upload endpoints
- [ ] Implement bulk upload handler
- [ ] Add job status endpoints

### Task 5.2: Run Parallel Deployment
- [ ] Configure FastAPI to run on port 8001
- [ ] Keep Flask running on port 5000
- [ ] Update frontend to use FastAPI endpoints
- [ ] Test both servers in parallel

### Task 5.3: Migration and Cutover
- [ ] Deprecate Flask endpoints with notices
- [ ] Monitor traffic shift to FastAPI
- [ ] Full cutover after validation period
- [ ] Remove Flask dependencies

## Current Status

**Active Phase**: Phase 2 - Enhanced Triage
**Next Task**: Task 2.1 - Create Enhanced Triage Module
**Blocked**: None
**Completed**: 
- Design document created
- Phase 1 (Queue System) - FULLY IMPLEMENTED ✅
  - queue_manager.py created with full job management
  - rate_limiter.py created with LLM API quota tracking
  - celery_worker.py created with async processing
  - Flask app updated with 6 new queue endpoints
  - QUEUE_SYSTEM_SETUP.md documentation created
  - requirements.txt updated with Redis/Celery dependencies
