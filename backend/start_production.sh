#!/bin/bash
# Production startup script for AccessibleAI Backend

set -e

echo "🚀 Starting AccessibleAI Backend in Production Mode..."

# Check required environment variables
required_vars=("DATABASE_URL" "SECRET_KEY" "REDIS_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set"
        exit 1
    fi
done

# Run database migrations
echo "📊 Running database migrations..."
alembic upgrade head

# Start Celery worker (in background)
echo "🔄 Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=${CELERY_CONCURRENCY:-5} &
CELERY_PID=$!

# Start Gunicorn server
echo "🌐 Starting Gunicorn server..."
exec gunicorn app.main:app \
    --config=gunicorn_config.py \
    --worker-tmp-dir=/dev/shm \
    --access-logfile=- \
    --error-logfile=-
