from decimal import Decimal

from sqlalchemy import CheckConstraint, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import PublicationContactMixin, TimestampMixin, UUIDMixin

from .enums import ProductStatus


class Product(Base, UUIDMixin, TimestampMixin, PublicationContactMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'SOLD', 'CLOSED')", name="ck_products_status"
        ),
        CheckConstraint("price > 0", name="ck_products_price_positive"),
        CheckConstraint(
            "quantity IS NULL OR quantity >= 0",
            name="ck_products_quantity_nonnegative",
        ),
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[ProductStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ProductStatus.ACTIVE,
    )
