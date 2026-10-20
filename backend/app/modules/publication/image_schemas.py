from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from .schemas import AdminPinAuthSchema

PublicationImageContentType = Literal["image/jpeg", "image/png", "image/webp"]


class PublicationImageUploadRequest(AdminPinAuthSchema):
    content_type: PublicationImageContentType
    size_bytes: int = Field(gt=0)
    alt_text: str | None = Field(default=None, max_length=200)


class PublicationImageUploadResponse(BaseModel):
    id: UUID
    bucket: str
    path: str
    token: str
    signed_upload_url: str
    expires_in_seconds: int = 7200


class PublicationImageCompleteRequest(AdminPinAuthSchema):
    pass


class PublicationImageDeleteRequest(AdminPinAuthSchema):
    pass


class PublicationImageResponse(BaseModel):
    id: UUID
    url: str
    content_type: PublicationImageContentType
    size_bytes: int
    alt_text: str | None
    position: int


class PublicationImageManagementResponse(PublicationImageResponse):
    status: Literal["PENDING", "READY"]
