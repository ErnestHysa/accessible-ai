# AccessibleAI

**AI-Powered Accessibility Compliance for Small Businesses**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)

---

## The Problem

- **98%** of websites fail ADA/WCAG compliance
- Accessibility lawsuits cost businesses **$50K+** per incident
- Current solutions cost **$500-$2000/month** (prohibitive for SMBs)
- Existing tools are just overlays that don't actually fix code

## Our Solution

AccessibleAI is an AI-powered accessibility compliance SaaS that:
- Scans websites for WCAG 2.1 violations
- Generates automated code fixes (not just overlays)
- Provides simple, non-technical user experience
- Integrates with WordPress, Shopify, and more
- Costs **$49-$249/month** (affordable for SMBs)

## Features

- 🔍 **Automated Scanning** - Comprehensive WCAG 2.1 compliance checks
- 🤖 **AI-Powered Fixes** - Generated code to fix accessibility issues
- 🔧 **WordPress Plugin** - One-click fixes for WordPress sites
- 📊 **Detailed Reports** - Clear insights and prioritized recommendations
- 💰 **Affordable Pricing** - Designed for small businesses
- 🔒 **Secure** - GDPR compliant, data encryption

## Tech Stack

### Backend
- FastAPI (Python)
- PostgreSQL
- Redis + Celery
- OpenAI API
- axe-core (accessibility engine)

### Frontend
- Next.js 14 (App Router)
- shadcn/ui
- Tailwind CSS
- Recharts

### WordPress Plugin
- PHP + React
- WordPress Block Editor integration

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/accessible-ai.git
cd accessible-ai
```

2. **Start services with Docker**
```bash
docker-compose up -d
```

3. **Backend setup**
```bash
cd backend
poetry install
alembic upgrade head
uvicorn app.main:app --reload
```

4. **Frontend setup**
```bash
cd frontend
npm install
npm run dev
```

5. **Access the application**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
accessible-ai/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Security, config
│   │   ├── db/       # Database models
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   └── tests/
├── frontend/         # Next.js dashboard
│   ├── src/
│   │   ├── app/      # Next.js app router
│   │   ├── components/
│   │   ├── lib/      # Utilities
│   │   └── types/
│   └── public/
├── shared/           # Shared types & constants
├── plugins/          # CMS plugins
│   ├── wordpress/
│   └── shopify/
├── docs/             # Documentation
└── docker/           # Docker configurations
```

## Development

### Running Tests
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test

# E2E tests
npm run test:e2e
```

### Code Quality
```bash
# Backend linting
cd backend && ruff check
cd backend && mypy .

# Frontend linting
cd frontend && npm run lint
```

## API Documentation

Interactive API documentation is available at `/docs` (Swagger) and `/redoc` when running the backend.

Key endpoints:
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Sign in
- `POST /api/v1/websites` - Add website to monitor
- `POST /api/v1/scans` - Trigger accessibility scan
- `GET /api/v1/scans/{id}` - Get scan results

## Pricing

| Tier | Price | Websites | Scans/Month | Features |
|------|-------|----------|-------------|----------|
| Free | $0 | 1 | 5 | Basic reports |
| Starter | $49/mo | 3 | Unlimited | WordPress plugin, email support |
| Pro | $99/mo | 10 | Unlimited | CMS integrations, priority support |
| Agency | $249/mo | Unlimited | Unlimited | White-label, API access |

## Roadmap

- [x] Market research
- [x] Design document
- [x] MVP (Backend + Frontend)
- [x] WordPress plugin
- [ ] Shopify integration
- [ ] Team collaboration features
- [ ] Public API access
- [ ] Mobile apps
- [ ] Advanced AI features (image alt text, PDF remediation)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Contact

- Website: https://accessibleai.com
- Email: hello@accessibleai.com
- Twitter: @accessibleai

---

**Built with ❤️ to make the web accessible for everyone**
