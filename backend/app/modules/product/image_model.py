from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .model import Product


class ProductImage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "product_images"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="ck_product_images_size_positive"),
        CheckConstraint("position >= 0", name="ck_product_images_position_nonnegative"),
        CheckConstraint(
            "status IN ('PENDING', 'READY')", name="ck_product_images_status"
        ),
    )

    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_path: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", server_default="PENDING"
    )

    product: Mapped["Product"] = relationship(back_populates="images")
