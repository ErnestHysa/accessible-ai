# AccessibleAI - Implementation Plan

**Date:** 2026-03-14
**Status:** Active Development

---

## Progress Checklist

### Phase 1: Foundation & Infrastructure
- [x] Market research completed
- [x] Design document written
- [x] Project structure created
- [ ] Git repository initialized
- [ ] .gitignore configured
- [ ] README.md written
- [ ] Docker Compose setup (local development)

### Phase 2: Backend Core
- [ ] FastAPI project initialized
- [ ] Database models defined (SQLAlchemy)
- [ ] Database migration system (Alembic)
- [ ] PostgreSQL schema created
- [ ] Redis cache setup
- [ ] Celery task queue configured
- [ ] JWT authentication system
- [ ] User registration/login endpoints
- [ ] API key authentication

### Phase 3: Scanning Engine
- [ ] axe-core integration
- [ ] WCAG 2.1 rule set implementation
- [ ] HTML scraper and parser
- [ ] Scanner service (async)
- [ ] Scan result processor
- [ ] Score calculation algorithm
- [ ] Issue categorization logic

### Phase 4: AI Integration
- [ ] OpenAI API integration
- [ ] Fix generation service
- [ ] Prompt engineering for accessibility fixes
- [ ] Fix validation system
- [ ] AI caching strategy

### Phase 5: Frontend Dashboard
- [ ] Next.js project initialized
- [ ] shadcn/ui component library setup
- [ ] Landing page
- [ ] Authentication pages (login/signup)
- [ ] Dashboard layout
- [ ] Website management UI
- [ ] Scan results display
- [ ] Issues list with filtering
- [ ] Fix suggestion viewer
- [ ] Settings page

### Phase 6: WordPress Plugin
- [ ] WordPress plugin scaffold
- [ ] Plugin admin page
- [ ] API client for SaaS communication
- [ ] Real-time scanner integration
- [ ] Quick fix buttons
- [ ] Dashboard widget
- [ ] Settings page
- [ ] Plugin build process

### Phase 7: Payment & Subscriptions
- [ ] Stripe account setup
- [ ] Product/pricing configuration
- [ ] Checkout flow
- [ ] Webhook handlers
- [ ] Subscription management
- [ ] Usage tracking
- [ ] Tier enforcement

### Phase 8: Testing & Quality
- [ ] Unit tests (backend)
- [ ] Integration tests (API)
- [ ] E2E tests (Playwright)
- [ ] Accessibility audit of own UI
- [ ] Performance testing
- [ ] Security audit

### Phase 9: Deployment
- [ ] Production server setup
- [ ] Domain configuration
- [ ] SSL certificates
- [ ] Database backup strategy
- [ ] Monitoring setup (Sentry)
- [ ] Analytics setup (PostHog)
- [ ] Error alerting

### Phase 10: Launch Preparation
- [ ] Documentation site
- [ ] API documentation
- [ ] User guides
- [ ] Landing page copy
- [ ] Pricing page
- [ ] Terms of service
- [ ] Privacy policy

---

## Detailed Implementation Steps

### Step 1: Project Initialization ✅ IN PROGRESS

**Files to create:**
1. `README.md` - Project overview and quick start
2. `.gitignore` - Python, Node, IDE ignores
3. `docker-compose.yml` - Local development environment
4. `Makefile` - Common commands
5. `LICENSE` - MIT License

**Commands:**
```bash
cd accessible-ai
git init
git add .
git commit -m "Initial project structure"
```

---

### Step 2: Backend Setup

**Dependencies:**
```txt
fastapi
uvicorn[standard]
sqlalchemy
alembic
asyncpg
redis
celery
pydantic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
stripe
openai
axe-core-python
httpx
beautifulsoup4
playwright
sentry-sdk
```

**Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── dependencies.py         # DI containers
│   ├── db/
│   │   ├── base.py            # Base model
│   │   ├── session.py         # DB session
│   │   └── migrations/
│   ├── models/
│   │   ├── user.py
│   │   ├── website.py
│   │   ├── scan.py
│   │   └── issue.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── website.py
│   │   └── scan.py
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── websites.py
│   │       ├── scans.py
│   │       └── subscriptions.py
│   ├── core/
│   │   ├── security.py
│   │   ├── jwt.py
│   │   └── stripe_client.py
│   └── services/
│       ├── scanner.py
│       ├── ai_fixer.py
│       └── email.py
├── tests/
├── pyproject.toml
└── alembic.ini
```

---

### Step 3: Frontend Setup

**Dependencies:**
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Zustand
- React Hook Form
- Recharts
- Axios/Fetch

**Structure:**
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx           # Landing page
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── websites/
│   │   │   ├── scans/
│   │   │   └── settings/
│   │   └── api/
│   ├── components/
│   │   ├── ui/                # shadcn components
│   │   ├── layout/
│   │   ├── dashboard/
│   │   └── landing/
│   ├── lib/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── utils.ts
│   ├── stores/
│   │   └── useStore.ts
│   └── types/
│       └── index.ts
├── public/
├── tailwind.config.ts
├── next.config.js
└── tsconfig.json
```

---

### Step 4: WordPress Plugin

**Structure:**
```
wordpress/
├── accessible-ai.php
├── includes/
│   ├── class-plugin.php
│   ├── class-scanner.php
│   ├── class-fixer.php
│   ├── class-api.php
│   ├── class-admin.php
│   └── class-dashboard.php
├── assets/
│   ├── src/
│   │   ├── admin.js
│   │   ├── scanner.js
│   │   └── fixer.js
│   └── build/
├── templates/
│   └── dashboard-widget.php
├── package.json
└── README.txt
```

---

## API Endpoints Specification

### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

### Websites
```
POST   /api/v1/websites          # Add website
GET    /api/v1/websites          # List user's websites
GET    /api/v1/websites/:id      # Get website details
PUT    /api/v1/websites/:id      # Update website
DELETE /api/v1/websites/:id      # Remove website
POST   /api/v1/websites/:id/scan # Trigger scan
```

### Scans
```
GET    /api/v1/scans             # List scans
GET    /api/v1/scans/:id         # Get scan details
GET    /api/v1/scans/:id/issues  # Get scan issues
DELETE /api/v1/scans/:id         # Delete scan
```

### Issues
```
GET    /api/v1/issues/:id        # Get issue details
POST   /api/v1/issues/:id/fix    # Apply fix
GET    /api/v1/issues/:id/fix-code # Get fix code
```

### Subscriptions
```
GET    /api/v1/subscription      # Get current subscription
POST   /api/v1/checkout          # Create checkout session
POST   /api/v1/portal            # Create customer portal session
POST   /api/v1/webhook/stripe    # Stripe webhooks
```

---

## Database Schema Quick Reference

### Tables
- **users** - User accounts and authentication
- **websites** - Websites being monitored
- **scans** - Accessibility scan records
- **issues** - Individual accessibility issues
- **subscriptions** - User subscriptions
- **usage_events** - Usage tracking for billing

### Relationships
- User → Websites (1:N)
- User → Subscription (1:1)
- Website → Scans (1:N)
- Scan → Issues (1:N)

---

## Environment Variables

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/accessible_ai
REDIS_URL=redis://localhost:6379/0

# Auth
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI
OPENAI_API_KEY=sk-...

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_FREE=price_...
STRIPE_PRICE_ID_STARTER=price_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_AGENCY=price_...

# Application
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000

# Monitoring
SENTRY_DSN=https://...
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_SENTRY_DSN=https://...
```

---

## Development Workflow

### Starting Local Development
```bash
# Start services
docker-compose up -d

# Backend
cd backend
poetry install
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# WordPress (for plugin testing)
cd plugins/wordpress
npm install
npm run build
```

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test

# E2E
npm run test:e2e
```

---

## Launch Checklist

### Pre-Launch
- [ ] All core features working
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Accessibility audit passed (irony!)
- [ ] Documentation complete
- [ ] Support process defined

### Launch Day
- [ ] DNS configured
- [ ] SSL certificates active
- [ ] Monitoring active
- [ ] Error tracking active
- [ ] Backup processes verified
- [ ] Payment processing tested

### Post-Launch
- [ ] Customer feedback collection
- [ ] Bug tracking
- [ ] Feature requests prioritized
- [ ] Marketing campaigns active
- [ ] Content marketing (blog, guides)

---

**Current Phase:** Foundation & Infrastructure
**Last Updated:** 2026-03-14
