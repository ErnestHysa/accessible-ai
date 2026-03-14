# Multi-stage build for production
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
COPY frontend/tsconfig.json ./
COPY frontend/tailwind.config.ts ./
COPY frontend/postcss.config.js ./
COPY frontend/components.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Backend production image
FROM python:3.11-slim AS backend
WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir -Ue pip
RUN pip install --no-cache-dir -e .

# Copy application code
COPY backend/app/ ./app/
COPY backend/alembic.ini .
COPY backend/alembic/ ./alembic/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
