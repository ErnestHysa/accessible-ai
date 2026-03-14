"""API Keys module for WordPress and external integrations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.user import User
from app.models.website import Website
from app.error_handlers import NotFoundException
from core.security import generate_api_key

import secrets


class APIKeyService:
    """Service for managing API keys."""

    @staticmethod
    async def create_api_key(user_id: UUID, db: AsyncSession) -> str:
        """Create a new API key for a user."""
        # Check if user has an API key
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("User not found")

        # Generate unique API key
        api_key = generate_api_key()

        # Ensure uniqueness
        existing = await db.execute(
            select(Website).where(Website.api_key == api_key)
        )
        while existing.scalar_one_or_none():
            api_key = generate_api_key()
            existing = await db.execute(
                select(Website).where(Website.api_key == api_key)
            )

        # Update user's first website with the API key
        website_result = await db.execute(
            select(Website).where(Website.user_id == user_id).limit(1)
        )
        website = website_result.scalar_one_or_none()

        if website:
            website.api_key = api_key
            await db.commit()
            await db.refresh(website)

        return api_key

    @staticmethod
    async def rotate_api_key(api_key: str, db: AsyncSession) -> str:
        """Rotate an existing API key."""
        result = await db.execute(
            select(Website).where(Website.api_key == api_key)
        )
        website = result.scalar_one_or_none()

        if not website:
            raise NotFoundException("Invalid API key")

        new_key = generate_api_key()
        website.api_key = new_key
        await db.commit()
        await db.refresh(website)

        return new_key

    @staticmethod
    async def validate_api_key(api_key: str, db: AsyncSession) -> Optional[Website]:
        """Validate an API key and return the associated website."""
        if not api_key or not api_key.startswith("aai_"):
            return None

        result = await db.execute(
            select(Website).where(Website.api_key == api_key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_api_key(api_key: str, db: AsyncSession) -> bool:
        """Revoke an API key."""
        result = await db.execute(
            select(Website).where(Website.api_key == api_key)
        )
        website = result.scalar_one_or_none()

        if not website:
            return False

        website.api_key = None
        await db.commit()

        return True
