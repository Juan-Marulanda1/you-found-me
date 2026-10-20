from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.publication.schemas import AdminPinAuthSchema

ProductImageContentType = Literal["image/jpeg", "image/png", "image/webp"]


class ProductImageUploadRequest(AdminPinAuthSchema):
    content_type: ProductImageContentType
    size_bytes: int = Field(gt=0)
    alt_text: str | None = Field(default=None, max_length=200)


class ProductImageUploadResponse(BaseModel):
    id: UUID
    bucket: str
    path: str
    token: str
    signed_upload_url: str
    expires_in_seconds: int = 7200


class ProductImageCompleteRequest(AdminPinAuthSchema):
    pass


class ProductImageDeleteRequest(AdminPinAuthSchema):
    pass


class ProductImageResponse(BaseModel):
    id: UUID
    url: str
    content_type: ProductImageContentType
    size_bytes: int
    alt_text: str | None
    position: int


class ProductImageManagementResponse(ProductImageResponse):
    status: Literal["PENDING", "READY"]
