# AccessibleAI Deployment Guide

**Production deployment guide for AccessibleAI SaaS platform**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Docker Deployment](#docker-deployment)
5. [Manual Deployment](#manual-deployment)
6. [Health Checks](#health-checks)
7. [Monitoring](#monitoring)
8. [Backup & Recovery](#backup--recovery)
9. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Services

| Service | Version | Purpose |
|---------|---------|---------|
| PostgreSQL | 15+ | Primary database |
| Redis | 7+ | Caching & task queue |
| nginx | 1.24+ | Reverse proxy |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Orchestration |

### Required API Keys

| Service | Environment Variable |
|---------|---------------------|
| OpenAI | `OPENAI_API_KEY` |
| Stripe | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` |
| Resend (optional) | `RESEND_API_KEY` |
| Sentry (optional) | `SENTRY_DSN` |

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/accessible-ai.git
cd accessible-ai
```

### 2. Configure Environment Variables

**Backend (`backend/.env`):**

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```bash
# Application
APP_NAME=AccessibleAI
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-super-secret-key-change-this

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/accessibleai

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=https://your-domain.com

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Stripe
STRIPE_SECRET_KEY=sk_live_your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
STRIPE_PRICE_ID_STARTER=price_xxxxx
STRIPE_PRICE_ID_PRO=price_xxxxx
STRIPE_PRICE_ID_AGENCY=price_xxxxx

# Email (optional)
RESEND_API_KEY=re_your-resend-key
FROM_EMAIL=noreply@your-domain.com

# Sentry (optional)
SENTRY_DSN=https://your-sentry-dsn
```

**Frontend (`frontend/.env.local`):**

```bash
cp frontend/.env.local.example frontend/.env.local
```

Edit `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_APP_URL=https://your-domain.com
```

---

## Database Setup

### 1. Create Database

```bash
# PostgreSQL
createdb accessibleai
```

### 2. Run Migrations

```bash
cd backend

# Using Alembic directly
alembic upgrade head

# Or using Docker
docker-compose exec backend alembic upgrade head
```

### 3. Verify Schema

```bash
psql -d accessibleai -c "\dt"
```

Expected tables:
- `users`
- `websites`
- `scans`
- `issues`
- `subscriptions`
- `usage_records`

---

## Docker Deployment

### Production Docker Compose

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Build Images Manually

```bash
# Backend
docker build -t accessibleai-backend:latest ./backend

# Frontend
docker build -t accessibleai-frontend:latest ./frontend
```

### Container Health Check

```bash
docker-compose ps
```

All services should show `healthy` status.

---

## Manual Deployment

### Backend (FastAPI)

```bash
cd backend

# Install dependencies
pip install -e .

# Run migrations
alembic upgrade head

# Start with Gunicorn (production)
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Start production server
npm start
```

### Celery Worker

```bash
cd backend

# Start Celery worker
celery -A app.worker.celery worker \
    --loglevel=info \
    --concurrency=4

# Start Celery beat (scheduler)
celery -A app.worker.celery beat \
    --loglevel=info
```

---

## Health Checks

### API Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Basic health check |
| `GET /health/db` | Database connectivity |
| `GET /health/redis` | Redis connectivity |
| `GET /health/celery` | Celery worker status |

### Monitoring Health Checks

```bash
# Add to crontab for monitoring
*/5 * * * * curl -f https://api.your-domain.com/health || alert-admin
```

---

## Monitoring

### Application Logs

**Backend:**
```bash
# Docker
docker-compose logs -f backend

# Manual
tail -f /var/log/accessibleai/backend.log
```

**Frontend:**
```bash
# Docker
docker-compose logs -f frontend

# Vercel/Netlify
# Use their dashboard
```

### Metrics to Monitor

| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| API Response Time | Sentry/APM | >500ms (p95) |
| Error Rate | Sentry | >1% |
| Database Connections | PostgreSQL | >80% max |
| Redis Memory | Redis | >80% max |
| Queue Depth | Celery | >1000 |

### Sentry Integration

```python
# Already configured in backend/app/logging_config.py
# Errors will automatically report to Sentry if SENTRY_DSN is set
```

---

## Backup & Recovery

### Database Backups

**Automated Daily Backup:**

```bash
#!/bin/bash
# /etc/cron.daily/accessibleai-backup

DATE=$(date +%Y%m%d)
BACKUP_DIR=/backups/accessibleai
pg_dump -U postgres accessibleai | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

**Restore from Backup:**

```bash
gunzip < /backups/accessibleai/db_20260314.sql.gz | psql accessibleai
```

### Redis Backups

```bash
# Enable Redis persistence in redis.conf
save 900 1
save 300 10
save 60 10000
```

---

## Rollback Procedures

### Docker Rollback

```bash
# Rollback to previous version
docker-compose -f docker-compose.prod.yml down
git checkout previous-tag
docker-compose -f docker-compose.prod.yml up -d
```

### Database Rollback

```bash
# List migrations
alembic history

# Rollback to specific version
alembic downgrade <revision>
```

### Emergency Rollback Checklist

- [ ] Stop all services
- [ ] Restore database from backup
- [ ] Checkout previous git tag
- [ ] Restart services
- [ ] Verify health endpoints
- [ ] Monitor error rates

---

## Security Checklist

### Before Going Live

- [ ] Change all default passwords
- [ ] Set `DEBUG=false`
- [ ] Configure CORS for production domain only
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up firewall rules (only allow necessary ports)
- [ ] Configure rate limiting (nginx)
- [ ] Set log aggregation
- [ ] Configure backup automation
- [ ] Test disaster recovery procedure

### SSL Certificate (Let's Encrypt)

```bash
certbot --nginx -d api.your-domain.com -d your-domain.com
```

### nginx Rate Limiting

Already configured in `nginx.conf`:

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req zone=api burst=20 nodelay;
```

---

## Troubleshooting

### Common Issues

**Issue: Database connection refused**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection string in .env
echo $DATABASE_URL
```

**Issue: Scan tasks not processing**
```bash
# Check Celery worker is running
docker-compose logs celery-worker

# Check Redis connection
redis-cli ping
```

**Issue: Frontend build fails**
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_scans_website_id ON scans(website_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_issues_severity ON issues(severity);
```

### Application Caching

```python
# Redis caching is already implemented
# Cache times are configurable via env vars:
# CACHE_TTL_SHORT=300  (5 minutes)
# CACHE_TTL_MEDIUM=3600 (1 hour)
# CACHE_TTL_LONG=86400  (24 hours)
```

---

## Support

For deployment issues:
- Email: support@accessibleai.com
- Documentation: https://docs.accessibleai.com
- Status Page: https://status.accessibleai.com

---

**Last updated:** 2026-03-14
