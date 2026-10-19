from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import PublicationContactMixin, TimestampMixin, UUIDMixin

from .enums import AnnouncementStatus


class Announcement(Base, UUIDMixin, TimestampMixin, PublicationContactMixin):
    __tablename__ = "announcements"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'PAUSED', 'CLOSED')",
            name="ck_announcements_status",
        ),
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    category: Mapped[str] = mapped_column(String(80), nullable=False)

    business_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    status: Mapped[AnnouncementStatus] = mapped_column(
        String(20),
        nullable=False,
        default=AnnouncementStatus.ACTIVE,
    )
