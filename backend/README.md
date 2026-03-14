# AccessibleAI Backend

AI-powered accessibility compliance scanning API.

## Features

- WCAG 2.1 accessibility scanning
- AI-generated fix suggestions
- Multi-platform CMS integration (WordPress, Shopify, etc.)
- Subscription-based access tiers
- Real-time scan results

## Installation

```bash
pip install -e .
```

## Development

```bash
# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Run migrations
alembic upgrade head
```

## Environment

See `.env.example` for required environment variables.
