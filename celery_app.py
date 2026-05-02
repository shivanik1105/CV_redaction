"""
Celery application factory for async task processing.
Replaces in-memory queue with Redis-backed distributed queue.
"""
import os
from celery import Celery


def make_celery(app):
    """
    Create Celery instance and configure it with Flask app context.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery instance
    """
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    # Update Celery config from Flask config
    celery.conf.update(app.config)
    
    # Task configuration
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minutes hard limit
        task_soft_time_limit=270,  # 4.5 minutes soft limit
        worker_prefetch_multiplier=1,  # Fetch one task at a time
        worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    )
    
    # Task routing - prioritize search over uploads
    celery.conf.task_routes = {
        'tasks.process_cv_task': {'queue': 'uploads', 'priority': 5},
        'tasks.generate_embedding_task': {'queue': 'embeddings', 'priority': 7},
        'tasks.search_candidates_task': {'queue': 'search', 'priority': 9},
    }
    
    # Make Celery work with Flask app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery


# Standalone Celery instance for worker process
celery = Celery(
    'cv_redactor',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configure standalone instance
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=270,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
