from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDMixin

from .enums import AnnouncementStatus, AnnouncementType


class Announcement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(String(150), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False)

    type: Mapped[AnnouncementType] = mapped_column(
        Enum(
            AnnouncementType,
            name="announcement_type",
        ),
        nullable=False,
    )

    status: Mapped[AnnouncementStatus] = mapped_column(
        Enum(
            AnnouncementStatus,
            name="announcement_status",
            create_constraint=True,
        ),
        nullable=False,
        default=AnnouncementStatus.OPEN,
    )

    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)

    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    admin_pin: Mapped[str] = mapped_column(String(4), nullable=False)
