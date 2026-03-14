@echo off
REM Production startup script for AccessibleAI Backend (Windows)

echo Starting AccessibleAI Backend in Production Mode...

REM Check Python version
python --version

REM Run database migrations
echo Running database migrations...
alembic upgrade head

REM Start Gunicorn server (using uvicorn for Windows dev)
echo Starting server...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

pause
