from app.modules.publication.image_schemas import (
    PublicationImageCompleteRequest,
    PublicationImageDeleteRequest,
    PublicationImageManagementResponse,
    PublicationImageResponse,
    PublicationImageUploadRequest,
    PublicationImageUploadResponse,
)


class AnnouncementImageUploadRequest(PublicationImageUploadRequest):
    pass


class AnnouncementImageUploadResponse(PublicationImageUploadResponse):
    pass


class AnnouncementImageCompleteRequest(PublicationImageCompleteRequest):
    pass


class AnnouncementImageDeleteRequest(PublicationImageDeleteRequest):
    pass


class AnnouncementImageResponse(PublicationImageResponse):
    pass


class AnnouncementImageManagementResponse(PublicationImageManagementResponse):
    pass
