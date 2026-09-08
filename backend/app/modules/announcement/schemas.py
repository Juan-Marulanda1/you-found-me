from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import AnnouncementStatus, AnnouncementType


class AdminPinSchema(BaseModel):
    admin_pin: str = Field(
        ...,
        min_length=4,
        max_length=4,
    )

    @field_validator("admin_pin")
    @classmethod
    def validate_pin(cls, value: str) -> str:

        if not value.isdigit():
            raise ValueError("The PIN must contain only digits.")

        return value


class AnnouncementCreate(AdminPinSchema):
    title: str = Field(..., min_length=5, max_length=150)

    description: str = Field(..., min_length=10)

    type: AnnouncementType

    contact_name: str = Field(..., min_length=2, max_length=100)

    contact_phone: str = Field(..., min_length=7, max_length=20)

    city: str = Field(..., min_length=2, max_length=100)

    address: str | None = Field(default=None, max_length=255)


class AnnouncementUpdate(AdminPinSchema):
    title: str | None = Field(default=None, min_length=5, max_length=150)
    description: str | None = Field(default=None, min_length=10)
    contact_name: str | None = Field(default=None, min_length=2, max_length=100)
    contact_phone: str | None = Field(default=None, min_length=7, max_length=20)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=255)


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    type: AnnouncementType
    status: AnnouncementStatus
    contact_name: str
    contact_phone: str
    city: str
    address: str | None
    created_at: datetime
    updated_at: datetime


class AnnouncementDelete(AdminPinSchema):
    pass
