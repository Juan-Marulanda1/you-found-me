from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.announcement.enums import AnnouncementStatus
from app.modules.publication.schemas import (
    AdminPinAuthSchema,
    PublicationCreateSchema,
    PublicationUpdateSchema,
)


class AnnouncementCreate(PublicationCreateSchema):
    title: str = Field(min_length=5, max_length=150)
    description: str = Field(min_length=10, max_length=10_000)
    category: str = Field(min_length=2, max_length=80)
    business_name: str | None = Field(default=None, max_length=150)
    website_url: str | None = Field(default=None, max_length=2048)
    contact_name: str = Field(min_length=2, max_length=100)
    contact_phone: str = Field(min_length=7, max_length=20)
    contact_email: str | None = Field(default=None, max_length=254)
    city: str = Field(min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)


class AnnouncementUpdate(PublicationUpdateSchema):
    nullable_fields = {"business_name", "website_url", "contact_email", "address"}

    title: str | None = Field(default=None, min_length=5, max_length=150)
    description: str | None = Field(default=None, min_length=10, max_length=10_000)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    business_name: str | None = Field(default=None, max_length=150)
    website_url: str | None = Field(default=None, max_length=2048)
    contact_phone_public: bool | None = None
    status: AnnouncementStatus | None = None
    contact_name: str | None = Field(default=None, min_length=2, max_length=100)
    contact_phone: str | None = Field(default=None, min_length=7, max_length=20)
    contact_email: str | None = Field(default=None, max_length=254)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)


class AnnouncementDelete(AdminPinAuthSchema):
    pass


class AnnouncementManageRequest(AdminPinAuthSchema):
    pass


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    category: str
    business_name: str | None
    website_url: str | None
    status: AnnouncementStatus
    contact_name: str
    contact_phone: str | None = Field(validation_alias="public_contact_phone")
    city: str
    created_at: datetime
    updated_at: datetime


class AnnouncementManagementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    category: str
    business_name: str | None
    website_url: str | None
    status: AnnouncementStatus
    contact_name: str
    contact_phone: str
    contact_phone_public: bool
    contact_email: str | None
    city: str
    address: str | None
    created_at: datetime
    updated_at: datetime
