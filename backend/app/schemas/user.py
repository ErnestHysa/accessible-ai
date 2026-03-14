"""User schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """User registration schema."""

    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login schema."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update schema."""

    name: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""

    id: UUID
    subscription_tier: str
    is_active: bool
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
