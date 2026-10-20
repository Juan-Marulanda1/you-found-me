from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PublicationInvitation(Base):
    """Allowlist of email addresses approved by the shared invite key."""

    __tablename__ = "publication_invitations"

    email: Mapped[str] = mapped_column(String(254), primary_key=True)
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
