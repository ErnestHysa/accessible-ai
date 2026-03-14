"""API documentation for AccessibleAI.

This module provides enhanced OpenAPI documentation with examples.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.config import get_settings

settings = get_settings()


def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation."""
    if settings.app_name == "AccessibleAI":
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "AccessibleAI API",
                "description": "AI-powered accessibility compliance API for WCAG 2.1",
                "version": settings.app_version,
                "contact": {
                    "name": "AccessibleAI Support",
                    "email": "hello@accessibleai.com",
                    "url": "https://accessibleai.com/support",
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT",
                },
            },
            "servers": [
                {
                    "url": settings.base_url,
                    "description": "Production server",
                },
                {
                    "url": "http://localhost:8000",
                    "description": "Local development server",
                },
            ],
            "tags": [
                {
                    "name": "Authentication",
                    "description": "User authentication and token management",
                },
                {
                    "name": "Websites",
                    "description": "Website management and monitoring",
                },
                {
                    "name": "Scans",
                    "description": "Accessibility scanning and results",
                },
                {
                    "name": "Issues",
                    "description": "Accessibility issue tracking and fixes",
                },
                {
                    "name": "Subscriptions",
                    "description": "Billing and subscription management",
                },
            ],
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "Enter your JWT token (without 'Bearer ' prefix)",
                    },
                    "apiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key",
                        "description": "Enter your API key (starts with 'aai_')",
                    },
                },
                "schemas": {
                    "Error": {
                        "type": "object",
                        "properties": {
                            "error": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "code": {"type": "string"},
                                    "details": {"type": "object"},
                                },
                            },
                        },
                    },
                    "ScanStatus": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed", "cancelled"],
                        "description": "The current status of a scan",
                    },
                    "Severity": {
                        "type": "string",
                        "enum": ["critical", "serious", "moderate", "minor"],
                        "description": "The severity level of an accessibility issue",
                    },
                },
            },
        }
    return {}

# Example responses for documentation
EXAMPLES = {
    "UserCreate": {
        "summary": "Create a new user account",
        "value": {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "name": "John Doe",
        },
    },
    "ScanResponse": {
        "summary": "Scan response example",
        "value": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "website_id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "completed",
            "score": 85,
            "total_issues": 12,
            "critical_issues": 2,
            "serious_issues": 5,
            "moderate_issues": 3,
            "minor_issues": 2,
            "created_at": "2026-03-14T10:00:00Z",
        },
    },
}
