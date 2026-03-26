"""
Unit tests for Queue Manager
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from queue_manager import QueueManager


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.hgetall.return_value = {}
    redis_mock.get.return_value = "0"
    redis_mock.zcard.return_value = 0
    return redis_mock


@pytest.fixture
def queue_manager(mock_redis):
    """Create QueueManager with mocked Redis"""
    with patch('queue_manager.Redis', return_value=mock_redis):
        qm = QueueManager()
        qm.redis = mock_redis
        return qm


class TestQueueManager:
    """Test suite for QueueManager"""
    
    def test_enqueue_cv_processing(self, queue_manager, mock_redis):
        """Test job enqueueing"""
        job_id = queue_manager.enqueue_cv_processing(
            cv_path="/path/to/cv.pdf",
            job_description="Senior Python Developer",
            priority=QueueManager.PRIORITY_NORMAL
        )
        
        # Verify job_id is UUID format
        assert len(job_id) == 36
        assert job_id.count('-') == 4
        
        # Verify Redis operations called
        assert mock_redis.hset.called
        assert mock_redis.zadd.called
        assert mock_redis.incr.called
    
    def test_job_priority_ordering(self, queue_manager, mock_redis):
        """Test jobs are ordered by priority"""
        # Enqueue jobs with different priorities
        job_high = queue_manager.enqueue_cv_processing(
            cv_path="/cv1.pdf",
            job_description="JD",
            priority=QueueManager.PRIORITY_HIGH
        )
        
        job_normal = queue_manager.enqueue_cv_processing(
            cv_path="/cv2.pdf",
            job_description="JD",
            priority=QueueManager.PRIORITY_NORMAL
        )
        
        job_low = queue_manager.enqueue_cv_processing(
            cv_path="/cv3.pdf",
            job_description="JD",
            priority=QueueManager.PRIORITY_LOW
        )
        
        # Verify zadd was called with correct scores
        calls = mock_redis.zadd.call_args_list
        assert len(calls) == 3
        
        # Extract scores (priority + timestamp fraction)
        scores = [list(call[0][1].values())[0] for call in calls]
        
        # High priority should have lowest score
        assert scores[0] < scores[1] < scores[2]
    
    def test_get_job_status(self, queue_manager, mock_redis):
        """Test retrieving job status"""
        mock_redis.hgetall.return_value = {
            'job_id': 'test-123',
            'status': 'queued',
            'priority': '5',
            'retry_count': '0',
            'max_retries': '3'
        }
        
        job_data = queue_manager.get_job_status('test-123')
        
        assert job_data is not None
        assert job_data['job_id'] == 'test-123'
        assert job_data['status'] == 'queued'
        assert job_data['priority'] == 5  # Converted to int
    
    def test_get_job_status_not_found(self, queue_manager, mock_redis):
        """Test retrieving non-existent job"""
        mock_redis.hgetall.return_value = {}
        
        job_data = queue_manager.get_job_status('nonexistent')
        
        assert job_data is None
    
    def test_update_job_status_to_processing(self, queue_manager, mock_redis):
        """Test updating job status to processing"""
        success = queue_manager.update_job_status(
            'test-123',
            QueueManager.STATUS_PROCESSING
        )
        
        assert success
        assert mock_redis.hset.called
        assert mock_redis.decr.called  # Decrement queued_jobs
        assert mock_redis.incr.called  # Increment processing_jobs
    
    def test_update_job_status_to_completed(self, queue_manager, mock_redis):
        """Test updating job status to completed"""
        result = {'intelligence': {'verdict': 'SHORTLIST'}}
        
        success = queue_manager.update_job_status(
            'test-123',
            QueueManager.STATUS_COMPLETED,
            result=result
        )
        
        assert success
        assert mock_redis.hset.called
        
        # Verify result was JSON serialized
        call_args = mock_redis.hset.call_args
        assert 'result' in call_args[1]
    
    def test_cancel_job_queued(self, queue_manager, mock_redis):
        """Test cancelling a queued job"""
        mock_redis.hgetall.return_value = {
            'job_id': 'test-123',
            'status': 'queued'
        }
        
        success = queue_manager.cancel_job('test-123')
        
        assert success
        assert mock_redis.zrem.called  # Remove from queue
    
    def test_cancel_job_processing(self, queue_manager, mock_redis):
        """Test cannot cancel processing job"""
        mock_redis.hgetall.return_value = {
            'job_id': 'test-123',
            'status': 'processing'
        }
        
        success = queue_manager.cancel_job('test-123')
        
        assert not success
        assert not mock_redis.zrem.called
    
    def test_requeue_job(self, queue_manager, mock_redis):
        """Test requeueing a job"""
        mock_redis.hgetall.return_value = {
            'job_id': 'test-123',
            'status': 'processing',
            'priority': '5',
            'retry_count': '0',
            'max_retries': '3'
        }
        
        success = queue_manager.requeue_job('test-123', delay_seconds=60)
        
        assert success
        assert mock_redis.hset.called  # Update retry_count
        assert mock_redis.zadd.called  # Add back to queue
    
    def test_requeue_job_max_retries(self, queue_manager, mock_redis):
        """Test requeueing fails after max retries"""
        mock_redis.hgetall.return_value = {
            'job_id': 'test-123',
            'status': 'processing',
            'priority': '5',
            'retry_count': '3',
            'max_retries': '3'
        }
        
        success = queue_manager.requeue_job('test-123')
        
        assert not success
        # Job should be marked as failed
        assert mock_redis.hset.called
    
    def test_get_queue_stats(self, queue_manager, mock_redis):
        """Test getting queue statistics"""
        mock_redis.get.side_effect = lambda key: {
            'stats:total_jobs': '100',
            'stats:queued_jobs': '10',
            'stats:processing_jobs': '5',
            'stats:completed_jobs': '80',
            'stats:failed_jobs': '5',
            'stats:cancelled_jobs': '0'
        }.get(key, '0')
        
        mock_redis.zcard.return_value = 10
        
        stats = queue_manager.get_queue_stats()
        
        assert stats['total_jobs'] == 100
        assert stats['queued_jobs'] == 10
        assert stats['completed_jobs'] == 80
        assert stats['failed_jobs'] == 5
        assert stats['success_rate'] == 94.12  # 80/(80+5) * 100
    
    def test_get_next_job(self, queue_manager, mock_redis):
        """Test getting next job from queue"""
        mock_redis.zpopmin.return_value = [('job-123', 5.0)]
        mock_redis.hgetall.return_value = {
            'job_id': 'job-123',
            'status': 'queued',
            'cv_path': '/cv.pdf'
        }
        
        job_data = queue_manager.get_next_job()
        
        assert job_data is not None
        assert job_data['job_id'] == 'job-123'
        assert mock_redis.zpopmin.called
    
    def test_get_next_job_empty_queue(self, queue_manager, mock_redis):
        """Test getting job from empty queue"""
        mock_redis.zpopmin.return_value = []
        
        job_data = queue_manager.get_next_job()
        
        assert job_data is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
