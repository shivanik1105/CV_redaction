web: gunicorn app:app --workers 4 --preload --timeout 120 --bind 0.0.0.0:$PORT
worker: celery -A celery_app.celery worker --loglevel=info --concurrency=4
