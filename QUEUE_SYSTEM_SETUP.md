# Queue System Setup Guide

This guide explains how to set up and use the Redis + Celery queue system for async CV processing.

## Why Use the Queue System?

The queue system solves several critical problems:

1. **API Quota Management**: Prevents hitting LLM API rate limits by controlling request frequency
2. **Async Processing**: Upload CVs and get results later without blocking
3. **Bulk Processing**: Process 100+ CVs efficiently with automatic rate limiting
4. **Retry Logic**: Automatically retry failed jobs with exponential backoff
5. **Monitoring**: Track job status, queue length, and success rates

## Prerequisites

### 1. Install Redis

**Windows (using Memurai - Redis-compatible)**:
```powershell
# Download Memurai from https://www.memurai.com/get-memurai
# Or use Chocolatey:
choco install memurai-developer
```

**Linux/Mac**:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Mac
brew install redis
```

**Docker (All platforms)**:
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `redis>=5.0.0` - Redis client
- `celery>=5.3.0` - Task queue
- `flower>=2.0.0` - Celery monitoring dashboard

### 3. Configure Environment Variables

Add to your `.env` file:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password

# LLM Provider (for rate limiting)
LLM_PROVIDER=gemini  # or openai, anthropic, ollama
```

## Starting the Queue System

### Step 1: Start Redis

**Windows (Memurai)**:
```powershell
# Memurai runs as a Windows service automatically
# Or start manually:
memurai.exe
```

**Linux/Mac**:
```bash
redis-server
```

**Docker**:
```bash
docker start redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### Step 2: Start Celery Worker

Open a new terminal and run:

```bash
python celery_worker.py
```

Or use Celery CLI directly:

```bash
celery -A celery_worker worker --loglevel=info --concurrency=4
```

**Options**:
- `--concurrency=4`: Run 4 parallel workers (adjust based on CPU cores)
- `--loglevel=info`: Set log level (debug, info, warning, error)
- `--max-tasks-per-child=50`: Restart worker after 50 tasks (prevents memory leaks)

### Step 3: Start Flask App

In another terminal:

```bash
python app.py
```

### Step 4: (Optional) Start Flower Monitoring Dashboard

In another terminal:

```bash
celery -A celery_worker flower --port=5555
```

Then open http://localhost:5555 in your browser to monitor:
- Active workers
- Task queue length
- Task success/failure rates
- Real-time task execution

## Using the Queue System

### API Endpoints

#### 1. Upload CV with Queue Mode

```bash
curl -X POST http://localhost:5000/upload \
  -F "cv_file=@resume.pdf" \
  -F "job_description=Senior Python Developer..." \
  -F "use_queue=true"
```

Response:
```json
{
  "success": true,
  "mode": "queued",
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "CV queued for processing",
  "status_url": "http://localhost:5000/api/jobs/a1b2c3d4.../status"
}
```

#### 2. Check Job Status

```bash
curl http://localhost:5000/api/jobs/{job_id}/status
```

Response:
```json
{
  "success": true,
  "job": {
    "job_id": "a1b2c3d4...",
    "status": "completed",
    "created_at": "2024-03-25T10:30:00",
    "started_at": "2024-03-25T10:30:05",
    "completed_at": "2024-03-25T10:30:45",
    "result": {
      "intelligence": {...},
      "similarity_score": 95.2
    }
  }
}
```

**Job Statuses**:
- `queued`: Waiting in queue
- `processing`: Currently being processed
- `completed`: Successfully completed
- `failed`: Processing failed
- `rate_limited`: Waiting due to API rate limit
- `cancelled`: Cancelled by user

#### 3. Get Queue Statistics

```bash
curl http://localhost:5000/api/queue/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "total_jobs": 150,
    "queued_jobs": 12,
    "processing_jobs": 4,
    "completed_jobs": 130,
    "failed_jobs": 4,
    "success_rate": 97.01,
    "queue_length": 12
  }
}
```

#### 4. Get Rate Limit Statistics

```bash
curl http://localhost:5000/api/rate-limit/stats
```

Response:
```json
{
  "success": true,
  "stats": {
    "gemini": {
      "provider": "gemini",
      "minute_usage": "3/10 (30.0%)",
      "day_usage": "145/1500 (9.7%)",
      "minute_remaining": 7,
      "day_remaining": 1355,
      "wait_time_seconds": 0,
      "quota_available": true
    }
  }
}
```

#### 5. Cancel a Job

```bash
curl -X POST http://localhost:5000/api/jobs/{job_id}/cancel
```

#### 6. Get Queued Jobs List

```bash
curl http://localhost:5000/api/queue/jobs?limit=50
```

## Rate Limiting Configuration

Default rate limits (free tier):

| Provider   | RPM (Requests/Minute) | RPD (Requests/Day) |
|------------|----------------------|-------------------|
| Gemini     | 10                   | 1,500             |
| OpenAI     | 3                    | 200               |
| Anthropic  | 5                    | 1,000             |
| Ollama     | 1,000                | 100,000           |

### Custom Rate Limits

To override defaults, modify `rate_limiter.py`:

```python
rate_limiter = RateLimiter(redis_client, custom_limits={
    "gemini": {"rpm": 60, "rpd": 10000},  # Paid tier
    "openai": {"rpm": 60, "rpd": 5000}
})
```

Or use environment variables (future enhancement):
```env
GEMINI_RPM=60
GEMINI_RPD=10000
```

## Monitoring and Troubleshooting

### Check Redis Connection

```bash
redis-cli ping
# Should return: PONG
```

### Check Celery Workers

```bash
celery -A celery_worker inspect active
```

### View Celery Logs

Celery worker logs show:
- Jobs being processed
- Rate limit waits
- Errors and retries

```
[2024-03-25 10:30:05] INFO - Starting task for job a1b2c3d4...
[2024-03-25 10:30:10] INFO - Redacting CV: uploads/resume.pdf
[2024-03-25 10:30:25] INFO - Extracting intelligence for job a1b2c3d4...
[2024-03-25 10:30:45] INFO - Completed job a1b2c3d4 successfully
```

### Common Issues

**Issue**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solution**: 
- Check Redis is running: `redis-cli ping`
- Check REDIS_HOST and REDIS_PORT in .env
- Check firewall settings

---

**Issue**: Jobs stuck in "queued" status

**Solution**:
- Check Celery worker is running
- Check worker logs for errors
- Restart Celery worker: `Ctrl+C` then restart

---

**Issue**: Rate limit errors even with queue

**Solution**:
- Check rate limit stats: `/api/rate-limit/stats`
- Reduce worker concurrency: `--concurrency=2`
- Increase wait time between jobs in `celery_worker.py`

---

**Issue**: Jobs failing with "CV not anonymized"

**Solution**:
- Ensure CV goes through redaction pipeline first
- Check redaction markers in CV text
- Verify `is_cv_anonymized()` function

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/celery-cv-worker.service`:

```ini
[Unit]
Description=Celery Worker for CV Processing
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/cv-redaction-pipeline
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A celery_worker worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=50 \
    --pidfile=/var/run/celery-cv-worker.pid \
    --logfile=/var/log/celery-cv-worker.log
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable celery-cv-worker
sudo systemctl start celery-cv-worker
sudo systemctl status celery-cv-worker
```

### Docker Compose

```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  celery-worker:
    build: .
    command: celery -A celery_worker worker --loglevel=info --concurrency=4
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - LLM_PROVIDER=gemini
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./redacted_output:/app/redacted_output
      - ./llm_analysis:/app/llm_analysis

  flask-app:
    build: .
    command: python app.py
    ports:
      - "5000:5000"
    depends_on:
      - redis
      - celery-worker
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - LLM_PROVIDER=gemini
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}

volumes:
  redis-data:
```

Run with:
```bash
docker-compose up -d
```

## Performance Tuning

### Optimal Worker Concurrency

- **Free tier LLM (10 RPM)**: `--concurrency=2` (safe)
- **Paid tier LLM (60 RPM)**: `--concurrency=8-12`
- **Local Ollama**: `--concurrency=4-8` (CPU-bound)

### Queue Priority

Jobs are processed by priority (lower number = higher priority):

```python
# High priority (urgent candidate review)
job_id = queue_manager.enqueue_cv_processing(
    cv_path=path,
    job_description=jd,
    priority=QueueManager.PRIORITY_HIGH  # 0
)

# Normal priority (standard processing)
priority=QueueManager.PRIORITY_NORMAL  # 5

# Low priority (batch processing)
priority=QueueManager.PRIORITY_LOW  # 10
```

### Cleanup Old Jobs

Run periodic cleanup to free Redis memory:

```python
# In celery_worker.py, schedule with Celery beat:
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'celery_worker.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
}
```

Start Celery beat:
```bash
celery -A celery_worker beat --loglevel=info
```

## Next Steps

1. **Phase 2**: Implement Enhanced Triage to reduce unnecessary LLM calls
2. **Phase 3**: Add Vector Search for semantic candidate matching
3. **Phase 4**: Upgrade to Native JSON Mode for LLM extraction
4. **Phase 5**: Migrate to FastAPI for better async support

See `COMPLETE_GUIDE.md` for full architecture details.
