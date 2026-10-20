from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """Primary key UUID generado por PostgreSQL."""

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Campos de auditoría."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PublicationContactMixin:
    """Shared contact and management fields for public listings."""

    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_phone_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin_pin_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    @property
    def public_contact_phone(self) -> str | None:
        """Expose the phone only when the publisher explicitly opted in."""
        return self.contact_phone if self.contact_phone_public else None
