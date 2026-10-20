from app.modules.publication.image_schemas import (
    PublicationImageCompleteRequest,
    PublicationImageDeleteRequest,
    PublicationImageManagementResponse,
    PublicationImageResponse,
    PublicationImageUploadRequest,
    PublicationImageUploadResponse,
)


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
