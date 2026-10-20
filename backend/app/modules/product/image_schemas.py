from app.modules.publication.image_schemas import (
    PublicationImageCompleteRequest,
    PublicationImageContentType,
    PublicationImageDeleteRequest,
    PublicationImageManagementResponse,
    PublicationImageResponse,
    PublicationImageUploadRequest,
    PublicationImageUploadResponse,
)

ProductImageContentType = PublicationImageContentType


class ProductImageUploadRequest(PublicationImageUploadRequest):
    pass


class ProductImageUploadResponse(PublicationImageUploadResponse):
    pass


class ProductImageCompleteRequest(PublicationImageCompleteRequest):
    pass


class ProductImageDeleteRequest(PublicationImageDeleteRequest):
    pass


class ProductImageResponse(PublicationImageResponse):
    pass


class ProductImageManagementResponse(PublicationImageManagementResponse):
    pass
