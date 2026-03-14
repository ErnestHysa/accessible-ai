# AccessibleAI - Design Document

**Date:** 2026-03-14
**Status:** Design Approved
**Version:** 1.0

---

## 1. Executive Summary

**AccessibleAI** is an AI-powered accessibility compliance SaaS that helps small businesses achieve ADA/WCAG compliance without expensive consultants or complex enterprise software.

### The Problem
- 98% of websites fail ADA/WCAG compliance
- Accessibility lawsuits cost businesses $50K+ per incident
- Current solutions cost $500-$2000/month (prohibitive for SMBs)
- Existing tools are technical overlays that don't actually fix code

### Our Solution
- Affordable AI-powered scanning ($49-$249/month)
- Automated code fixes, not just overlays
- Simple, non-technical user experience
- WordPress plugin for easy implementation (40%+ market share)

### Business Model
- SaaS subscription with tiered pricing
- Free tier for lead generation
- Focus on small-to-medium businesses

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Frontend Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Landing     │  │   Dashboard  │  │  WordPress   │  │   Shopify    │ │
│  │    Page      │  │   (Next.js)  │  │   Plugin     │  │   App        │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              API Gateway                                 │
│                    (FastAPI + Rate Limiting + Auth)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   Scanning    │          │     AI        │          │  Business     │
│   Service     │          │   Service     │          │   Logic       │
│               │          │               │          │               │
│ - WCAG Rules  │          │ - Fix Gen     │          │ - Users       │
│ - HTML Parse  │          │ - Priority    │          │ - Subs        │
│ - PDF Scan    │          │ - Explanations│          │ - Billing     │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ PostgreSQL   │  │    Redis     │  │   S3/MinIO   │  │   Queue      │ │
│  │  (Primary)   │  │   (Cache)    │  │  (Reports)   │  │  (Celery)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           External Services                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Stripe     │  │    OpenAI    │  │   Sentry     │  │  PostHog     │ │
│  │  (Payments)  │  │   (AI)       │  │  (Errors)    │  │ (Analytics)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

### Backend
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| API Framework | FastAPI | Fast, async, Python for AI |
| Task Queue | Celery + Redis | Proven, scalable |
| Database | PostgreSQL | ACID, JSONB for scan results |
| Caching | Redis | Fast lookups, rate limiting |
| Accessibility Engine | axe-core (Python) | Industry standard |
| AI/ML | OpenAI API + LangChain | Fix generation, explanations |
| Payment | Stripe | Industry standard |
| Auth | JWT + bcrypt | Simple, secure |

### Frontend
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Framework | Next.js 14 | SSR, great DX |
| UI | shadcn/ui | Modern, customizable |
| Styling | Tailwind CSS | Fast development |
| State | Zustand | Simple, small |
| Forms | React Hook Form | Performant |
| Charts | Recharts | Simple, integrated |

### WordPress Plugin
| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | PHP | WordPress standard |
| JS | React + WP Scripts | Modern development |
| Build | Webpack | WP standard |

---

## 4. Data Model

### Core Tables

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    stripe_customer_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Websites
CREATE TABLE websites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    name VARCHAR(255),
    platform VARCHAR(50) DEFAULT 'generic', -- wordpress, shopify, generic
    api_key VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_scan_at TIMESTAMP
);

-- Scans
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    website_id UUID REFERENCES websites(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    score INTEGER, -- 0-100 accessibility score
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    serious_issues INTEGER DEFAULT 0,
    moderate_issues INTEGER DEFAULT 0,
    minor_issues INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    report_url VARCHAR(500)
);

-- Issues
CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL, -- wcag-2.1 identifier
    severity VARCHAR(20) NOT NULL, -- critical, serious, moderate, minor
    selector VARCHAR(500), -- CSS selector for element
    description TEXT NOT NULL,
    impact TEXT,
    fix_suggestion TEXT,
    fix_code TEXT, -- AI-generated fix
    is_fixed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscriptions
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    tier VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL, -- active, canceled, past_due, trial
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Usage tracking
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL, -- scan, api_call, fix_applied
    resource_id UUID,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 5. WCAG Compliance Rules

### Automated Checks (Phase 1)

| Category | Rules | Priority |
|----------|-------|----------|
| Images | Alt text present and meaningful | Critical |
| Color | Contrast ratio ≥ 4.5:1 (normal), 3:1 (large) | Serious |
| Forms | Labels associated with inputs | Critical |
| Links | Descriptive link text (not "click here") | Moderate |
| Headings | Proper heading hierarchy (h1-h6) | Moderate |
| ARIA | Proper ARIA labels on interactive elements | Serious |
| Keyboard | All interactive elements keyboard accessible | Critical |
| Language | Page language declared | Minor |
| Tables | Headers properly defined | Serious |
| Documents | PDF tagged and accessible | Moderate |

### Manual Checks (Phase 2)
- Video captions quality
- Audio description quality
- Content readability scores
- Keyboard-only navigation flow
- Screen reader compatibility

---

## 6. AI Fix Generation

### Fix Categories

1. **Simple Fixes** (Auto-applied)
   - Add alt text placeholders
   - Add ARIA labels
   - Fix heading structure
   - Add form labels

2. **Complex Fixes** (Suggested code)
   - Color contrast adjustments
   - Layout restructures
   - Interactive component redesigns
   - Keyboard navigation fixes

### Prompt Engineering

```
You are an accessibility expert. Given this HTML element and WCAG violation,
provide:
1. A clear explanation of the problem
2. Specific code to fix it
3. Why this fix works
4. Alternative approaches if applicable

Element: {element_html}
Violation: {wcag_rule}
Context: {page_context}
```

---

## 7. API Design

### Core Endpoints

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me

POST   /api/v1/websites
GET    /api/v1/websites
GET    /api/v1/websites/{id}
DELETE /api/v1/websites/{id}

POST   /api/v1/scans
GET    /api/v1/scans/{id}
GET    /api/v1/scans/{id}/issues

POST   /api/v1/issues/{id}/fix
GET    /api/v1/issues/{id}/fix-code

POST   /api/v1/checkout/create-session
POST   /api/v1/portal/create-session
```

---

## 8. WordPress Plugin Architecture

### Plugin Structure
```
accessible-ai/
├── accessible-ai.php              # Main plugin file
├── includes/
│   ├── class-scanner.php         # Scanning logic
│   ├── class-fixer.php           # Auto-fix logic
│   ├── class-api-client.php      # Communication with SaaS
│   ├── class-admin.php           # Admin interface
│   └── class-dashboard.php       # Dashboard widget
├── assets/
│   ├── build/                    # Compiled JS/CSS
│   └── src/                      # Source React components
├── templates/
│   ├── dashboard.php
│   └── reports.php
└── package.json
```

### Key Features
1. **Real-time scanning** as admin navigates
2. **Quick fix buttons** in WordPress editor
3. **Dashboard widget** showing accessibility score
4. **Scheduled scans** (WP-Cron)
5. **One-click sync** with main SaaS platform

---

## 9. Security Considerations

### Authentication & Authorization
- JWT tokens with short expiry (15 minutes)
- Refresh tokens with longer expiry (7 days)
- API key authentication for WordPress plugins
- Rate limiting per user tier

### Data Protection
- Encrypt stored website data
- Sanitize all HTML before scanning
- GDPR compliance (right to deletion)
- SOC 2 Type II preparation for enterprise

### Payment Security
- Stripe handles all card data (PCI compliance)
- Store only customer ID and subscription ID
- Webhook signature verification

---

## 10. Scalability Plan

### Phase 1 (0-1000 users)
- Single VPS instance
- PostgreSQL + Redis on same host
- Celery with 2 workers

### Phase 2 (1000-10000 users)
- Separate database server
- Dedicated Redis instance
- Horizontal scaling of API workers
- CDN for static assets

### Phase 3 (10000+ users)
- Database read replicas
- Distributed task queue (Redis Cluster)
- Geographic distribution
- Enterprise features (SSO, custom domains)

---

## 11. Monitoring & Observability

### Metrics to Track
- Scan success rate
- Average scan duration
- API response times
- Error rates by endpoint
- User engagement (dashboard visits)
- Conversion funnel (signup → paid)
- Churn rate
- MRR/ARR growth

### Tools
- Sentry: Error tracking
- PostHog: Product analytics
- UptimeRobot: Service monitoring
- CloudWatch/Datadog: Infrastructure metrics

---

## 12. Success Metrics

### KPIs (Year 1)
- 500 paying customers
- $15K MRR
- 80% scan success rate
- 70% free-to-paid conversion
- <5% monthly churn
- 4.5/5 customer satisfaction

### Year 2 Targets
- 2,000 paying customers
- $60K MRR
- Shopify integration launched
- Enterprise features released
---

## 13. Development Phases

### Phase 1: MVP (8 weeks)
- Core scanning engine
- Web dashboard (Next.js)
- User auth + subscription management
- WordPress plugin beta
- Basic reporting

### Phase 2: Launch (4 weeks)
- Landing page optimization
- Payment integration (Stripe)
- Email notifications
- Documentation
- Beta testing with 50 users

### Phase 3: Growth (ongoing)
- Shopify integration
- AI fix improvements
- Advanced reporting
- Team collaboration features
- API for developers

---

## 14. Risk Mitigation

### Technical Risks
| Risk | Mitigation |
|------|------------|
| Scanning accuracy | Combine axe-core with AI, validate against manual audits |
| Performance at scale | Queue-based scanning, caching, CDN |
| WordPress compatibility | Test on multiple versions, use standard APIs |

### Business Risks
| Risk | Mitigation |
|------|------------|
| Competition | Focus on affordability + actually fixing code |
| Legal challenges | Clear disclaimers, attorney consultations |
| Low conversion | Free tier with value, strong CTAs, case studies |

---

**Design Status:** ✅ Approved for implementation
**Next Step:** Create detailed implementation plan
