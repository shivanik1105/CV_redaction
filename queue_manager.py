"""
Queue Manager for CV Processing Pipeline
Handles job enqueueing, status tracking, and queue statistics using Redis
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, List
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class QueueManager:
    """Manages CV processing job queue using Redis"""
    
    # Priority levels
    PRIORITY_HIGH = 0
    PRIORITY_NORMAL = 5
    PRIORITY_LOW = 10
    
    # Job statuses
    STATUS_QUEUED = "queued"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_RATE_LIMITED = "rate_limited"
    STATUS_CANCELLED = "cancelled"
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0, redis_password: str = None):
        """
        Initialize Queue Manager with Redis connection
        
        Args:
            redis_host: Redis server hostname
            redis_port: Redis server port
            redis_db: Redis database number
            redis_password: Redis password (optional)
        """
        try:
            self.redis = Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def enqueue_cv_processing(
        self,
        cv_path: str,
        job_description: str,
        priority: int = PRIORITY_NORMAL,
        metadata: Dict = None
    ) -> str:
        """
        Enqueue a CV processing job
        
        Args:
            cv_path: Path to the CV file (original or redacted)
            job_description: Job description text for matching
            priority: Job priority (0=HIGH, 5=NORMAL, 10=LOW)
            metadata: Additional metadata (original_filename, user_id, etc.)
        
        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "cv_path": cv_path,
            "job_description": job_description,
            "priority": priority,
            "status": self.STATUS_QUEUED,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "retry_count": 0,
            "max_retries": 3,
            "metadata": metadata or {}
        }
        
        try:
            # Store job data in Redis hash
            self.redis.hset(f"job:{job_id}", mapping={
                k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                for k, v in job_data.items()
            })
            
            # Add job to priority queue (sorted set by priority + timestamp)
            score = priority + (datetime.now().timestamp() / 1e10)  # Priority first, then FIFO
            self.redis.zadd("cv_processing_queue", {job_id: score})
            
            # Increment queue stats
            self.redis.incr("stats:total_jobs")
            self.redis.incr("stats:queued_jobs")
            
            logger.info(f"Enqueued job {job_id} with priority {priority}")
            return job_id
            
        except RedisError as e:
            logger.error(f"Failed to enqueue job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get job status and details
        
        Args:
            job_id: Job identifier
        
        Returns:
            Job data dictionary or None if not found
        """
        try:
            job_data = self.redis.hgetall(f"job:{job_id}")
            
            if not job_data:
                return None
            
            # Parse JSON fields
            for key in ["result", "metadata"]:
                if key in job_data and job_data[key]:
                    try:
                        job_data[key] = json.loads(job_data[key])
                    except json.JSONDecodeError:
                        pass
            
            # Convert numeric fields
            for key in ["priority", "retry_count", "max_retries"]:
                if key in job_data:
                    job_data[key] = int(job_data[key])
            
            return job_data
            
        except RedisError as e:
            logger.error(f"Failed to get job status: {e}")
            return None
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Dict = None,
        error: str = None
    ) -> bool:
        """
        Update job status
        
        Args:
            job_id: Job identifier
            status: New status
            result: Job result data (for completed jobs)
            error: Error message (for failed jobs)
        
        Returns:
            True if updated successfully
        """
        try:
            updates = {"status": status}
            
            if status == self.STATUS_PROCESSING:
                updates["started_at"] = datetime.now().isoformat()
                self.redis.decr("stats:queued_jobs")
                self.redis.incr("stats:processing_jobs")
            
            elif status == self.STATUS_COMPLETED:
                updates["completed_at"] = datetime.now().isoformat()
                if result:
                    updates["result"] = json.dumps(result)
                self.redis.decr("stats:processing_jobs")
                self.redis.incr("stats:completed_jobs")
            
            elif status == self.STATUS_FAILED:
                updates["completed_at"] = datetime.now().isoformat()
                if error:
                    updates["error"] = error
                self.redis.decr("stats:processing_jobs")
                self.redis.incr("stats:failed_jobs")
            
            elif status == self.STATUS_RATE_LIMITED:
                # Job goes back to queue, don't change processing count
                pass
            
            # Update job hash
            self.redis.hset(f"job:{job_id}", mapping=updates)
            
            logger.info(f"Updated job {job_id} status to {status}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to update job status: {e}")
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued job
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if cancelled successfully
        """
        try:
            job_data = self.get_job_status(job_id)
            
            if not job_data:
                logger.warning(f"Job {job_id} not found")
                return False
            
            if job_data["status"] not in [self.STATUS_QUEUED, self.STATUS_RATE_LIMITED]:
                logger.warning(f"Cannot cancel job {job_id} with status {job_data['status']}")
                return False
            
            # Remove from queue
            self.redis.zrem("cv_processing_queue", job_id)
            
            # Update status
            self.update_job_status(job_id, self.STATUS_CANCELLED)
            
            self.redis.decr("stats:queued_jobs")
            self.redis.incr("stats:cancelled_jobs")
            
            logger.info(f"Cancelled job {job_id}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to cancel job: {e}")
            return False
    
    def get_next_job(self) -> Optional[Dict]:
        """
        Get next job from queue (lowest priority score)
        
        Returns:
            Job data or None if queue is empty
        """
        try:
            # Get job with lowest score (highest priority + oldest)
            result = self.redis.zpopmin("cv_processing_queue", 1)
            
            if not result:
                return None
            
            job_id, score = result[0]
            job_data = self.get_job_status(job_id)
            
            if job_data:
                # Update status to processing
                self.update_job_status(job_id, self.STATUS_PROCESSING)
            
            return job_data
            
        except RedisError as e:
            logger.error(f"Failed to get next job: {e}")
            return None
    
    def requeue_job(self, job_id: str, delay_seconds: int = 0) -> bool:
        """
        Requeue a job (for rate limiting or retries)
        
        Args:
            job_id: Job identifier
            delay_seconds: Delay before job can be processed again
        
        Returns:
            True if requeued successfully
        """
        try:
            job_data = self.get_job_status(job_id)
            
            if not job_data:
                return False
            
            # Increment retry count
            retry_count = job_data.get("retry_count", 0) + 1
            self.redis.hset(f"job:{job_id}", "retry_count", retry_count)
            
            # Check max retries
            max_retries = job_data.get("max_retries", 3)
            if retry_count > max_retries:
                self.update_job_status(job_id, self.STATUS_FAILED, error="Max retries exceeded")
                return False
            
            # Add back to queue with delay
            priority = job_data.get("priority", self.PRIORITY_NORMAL)
            score = priority + ((datetime.now().timestamp() + delay_seconds) / 1e10)
            self.redis.zadd("cv_processing_queue", {job_id: score})
            
            # Update status
            self.update_job_status(job_id, self.STATUS_RATE_LIMITED if delay_seconds > 0 else self.STATUS_QUEUED)
            
            logger.info(f"Requeued job {job_id} with {delay_seconds}s delay (retry {retry_count}/{max_retries})")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to requeue job: {e}")
            return False
    
    def get_queue_stats(self) -> Dict:
        """
        Get queue statistics
        
        Returns:
            Dictionary with queue stats
        """
        try:
            stats = {
                "total_jobs": int(self.redis.get("stats:total_jobs") or 0),
                "queued_jobs": int(self.redis.get("stats:queued_jobs") or 0),
                "processing_jobs": int(self.redis.get("stats:processing_jobs") or 0),
                "completed_jobs": int(self.redis.get("stats:completed_jobs") or 0),
                "failed_jobs": int(self.redis.get("stats:failed_jobs") or 0),
                "cancelled_jobs": int(self.redis.get("stats:cancelled_jobs") or 0),
                "queue_length": self.redis.zcard("cv_processing_queue"),
            }
            
            # Calculate success rate
            total_finished = stats["completed_jobs"] + stats["failed_jobs"]
            if total_finished > 0:
                stats["success_rate"] = round(stats["completed_jobs"] / total_finished * 100, 2)
            else:
                stats["success_rate"] = 0.0
            
            return stats
            
        except RedisError as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    def get_queued_jobs(self, limit: int = 100) -> List[Dict]:
        """
        Get list of queued jobs
        
        Args:
            limit: Maximum number of jobs to return
        
        Returns:
            List of job data dictionaries
        """
        try:
            # Get job IDs from queue (without removing them)
            job_ids = self.redis.zrange("cv_processing_queue", 0, limit - 1)
            
            jobs = []
            for job_id in job_ids:
                job_data = self.get_job_status(job_id)
                if job_data:
                    jobs.append(job_data)
            
            return jobs
            
        except RedisError as e:
            logger.error(f"Failed to get queued jobs: {e}")
            return []
    
    def clear_completed_jobs(self, older_than_hours: int = 24) -> int:
        """
        Clear completed/failed jobs older than specified hours
        
        Args:
            older_than_hours: Clear jobs older than this many hours
        
        Returns:
            Number of jobs cleared
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            # Scan for job keys
            cleared = 0
            for key in self.redis.scan_iter("job:*"):
                job_data = self.redis.hgetall(key)
                
                if job_data.get("status") in [self.STATUS_COMPLETED, self.STATUS_FAILED, self.STATUS_CANCELLED]:
                    completed_at = job_data.get("completed_at")
                    if completed_at:
                        completed_time = datetime.fromisoformat(completed_at)
                        if completed_time < cutoff_time:
                            self.redis.delete(key)
                            cleared += 1
            
            logger.info(f"Cleared {cleared} old jobs")
            return cleared
            
        except RedisError as e:
            logger.error(f"Failed to clear completed jobs: {e}")
            return 0
