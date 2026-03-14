"""Database base configuration."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower() + "s"


class TimestampMixin:
    """Add created_at and updated_at timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class UUIDMixin:
    """Add UUID primary key to models."""

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
