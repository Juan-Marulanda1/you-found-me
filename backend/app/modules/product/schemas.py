from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.publication.schemas import (
    AdminPinAuthSchema,
    PublicationCreateSchema,
    PublicationUpdateSchema,
)

from .enums import ProductStatus
from .image_schemas import ProductImageResponse


class ProductCreate(PublicationCreateSchema):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=10, max_length=10_000)
    category: str = Field(min_length=2, max_length=80)
    price: Decimal = Field(ge=1000, max_digits=12, decimal_places=2)
    currency: str = Field(
        default="COP", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$"
    )
    quantity: int | None = Field(default=None, ge=0)
    contact_name: str = Field(min_length=2, max_length=100)
    contact_phone: str = Field(min_length=7, max_length=20)
    contact_email: str | None = Field(default=None, max_length=254)
    city: str = Field(min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)


class ProductUpdate(PublicationUpdateSchema):
    nullable_fields = {"quantity", "contact_email", "address"}

    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=10_000)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    price: Decimal | None = Field(default=None, ge=1000, max_digits=12, decimal_places=2)
    currency: str | None = Field(
        default=None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$"
    )
    quantity: int | None = Field(default=None, ge=0)
    contact_phone_public: bool | None = None
    status: ProductStatus | None = None
    contact_name: str | None = Field(default=None, min_length=2, max_length=100)
    contact_phone: str | None = Field(default=None, min_length=7, max_length=20)
    contact_email: str | None = Field(default=None, max_length=254)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)


class ProductResponse(BaseModel):
    """Vista pública: omite correo, dirección y el teléfono sin consentimiento."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    category: str
    price: Decimal
    currency: str
    quantity: int | None
    status: ProductStatus
    contact_name: str
    contact_phone: str | None = Field(validation_alias="public_contact_phone")
    city: str
    cover_image: ProductImageResponse | None = None
    created_at: datetime
    updated_at: datetime


class ProductManagementResponse(BaseModel):
    """Vista privada para quien administra la publicación."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    category: str
    price: Decimal
    currency: str
    quantity: int | None
    status: ProductStatus
    contact_name: str
    contact_phone: str
    contact_phone_public: bool
    contact_email: str | None
    city: str
    address: str | None
    created_at: datetime
    updated_at: datetime
    cover_image: ProductImageResponse | None = None


class ProductDelete(AdminPinAuthSchema):
    pass


class ProductManageRequest(AdminPinAuthSchema):
    pass
