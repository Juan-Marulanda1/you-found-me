from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.pagination import PageData, build_page
from app.core.publication_access import require_publication_creation_key
from app.core.request import get_client_ip
from app.core.responses import DataResponse

from .dependencies import get_announcement_image_service, get_announcement_service
from .enums import AnnouncementStatus
from .image_schemas import (
    AnnouncementImageCompleteRequest,
    AnnouncementImageDeleteRequest,
    AnnouncementImageManagementResponse,
    AnnouncementImageResponse,
    AnnouncementImageUploadRequest,
    AnnouncementImageUploadResponse,
)
from .image_service import AnnouncementImageService
from .schemas import (
    AnnouncementCreate,
    AnnouncementDelete,
    AnnouncementManagementResponse,
    AnnouncementManageRequest,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from .service import AnnouncementService

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post(
    "",
    response_model=DataResponse[AnnouncementResponse],
    status_code=201,
    dependencies=[Depends(require_publication_creation_key)],
)
def create_announcement(
    data: AnnouncementCreate,
    service: AnnouncementService = Depends(get_announcement_service),
):
    return DataResponse[AnnouncementResponse](
        message="Announcement created successfully.", data=service.create(data)
    )


@router.get("", response_model=DataResponse[PageData[AnnouncementResponse]])
def list_announcements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city: str | None = Query(default=None, min_length=2, max_length=100),
    category: str | None = Query(default=None, min_length=2, max_length=80),
    search: str | None = Query(default=None, min_length=2, max_length=150),
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    result = service.list(
        page=page,
        page_size=page_size,
        city=city,
        category=category,
        status=AnnouncementStatus.ACTIVE,
        search=search,
    )
    cover_images = image_service.list_cover_images(
        [announcement.id for announcement in result.items]
    )
    items = [
        AnnouncementResponse.model_validate(announcement).model_copy(
            update={"cover_image": cover_images.get(announcement.id)}
        )
        for announcement in result.items
    ]
    return DataResponse[PageData[AnnouncementResponse]](
        message="Announcements retrieved successfully.",
        data=build_page(items, page=page, page_size=page_size, total=result.total),
    )


@router.get("/{announcement_id}", response_model=DataResponse[AnnouncementResponse])
def get_announcement(
    announcement_id: UUID,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    announcement = service.get_public_by_id(announcement_id)
    cover_image = image_service.list_cover_images([announcement.id]).get(
        announcement.id
    )
    return DataResponse[AnnouncementResponse](
        message="Announcement retrieved successfully.",
        data=AnnouncementResponse.model_validate(announcement).model_copy(
            update={"cover_image": cover_image}
        ),
    )


@router.post(
    "/{announcement_id}/manage",
    response_model=DataResponse[AnnouncementManagementResponse],
)
def get_announcement_for_management(
    announcement_id: UUID,
    data: AnnouncementManageRequest,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
):
    return DataResponse[AnnouncementManagementResponse](
        message="Announcement management access granted.",
        data=service.get_for_management(
            announcement_id, data.admin_pin, get_client_ip(request)
        ),
    )


@router.patch(
    "/{announcement_id}",
    response_model=DataResponse[AnnouncementManagementResponse],
)
def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
):
    return DataResponse[AnnouncementManagementResponse](
        message="Announcement updated successfully.",
        data=service.update(announcement_id, data, get_client_ip(request)),
    )


@router.delete(
    "/{announcement_id}",
    response_model=DataResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_announcement(
    announcement_id: UUID,
    data: AnnouncementDelete,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    service.delete(
        announcement_id,
        data.admin_pin,
        get_client_ip(request),
        before_delete=image_service.remove_announcement_files,
    )
    return DataResponse[None](message="Announcement deleted successfully.")


@router.post(
    "/{announcement_id}/images/upload-url",
    response_model=DataResponse[AnnouncementImageUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_announcement_image_upload(
    announcement_id: UUID,
    data: AnnouncementImageUploadRequest,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    announcement = service.get_for_management(
        announcement_id, data.admin_pin, get_client_ip(request)
    )
    upload = image_service.create_upload(announcement, data)
    return DataResponse[AnnouncementImageUploadResponse](
        message="Signed announcement image upload created.", data=upload
    )


@router.post(
    "/{announcement_id}/images/{image_id}/complete",
    response_model=DataResponse[AnnouncementImageResponse],
)
def complete_announcement_image_upload(
    announcement_id: UUID,
    image_id: UUID,
    data: AnnouncementImageCompleteRequest,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    service.get_for_management(announcement_id, data.admin_pin, get_client_ip(request))
    image = image_service.complete(announcement_id, image_id)
    return DataResponse[AnnouncementImageResponse](
        message="Announcement image is ready.", data=image
    )


@router.get(
    "/{announcement_id}/images",
    response_model=DataResponse[list[AnnouncementImageResponse]],
)
def list_announcement_images(
    announcement_id: UUID,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    service.get_public_by_id(announcement_id)
    return DataResponse[list[AnnouncementImageResponse]](
        message="Announcement images retrieved successfully.",
        data=image_service.list_public(announcement_id),
    )


@router.post(
    "/{announcement_id}/images/manage",
    response_model=DataResponse[list[AnnouncementImageManagementResponse]],
)
def list_announcement_images_for_management(
    announcement_id: UUID,
    data: AnnouncementImageCompleteRequest,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    service.get_for_management(announcement_id, data.admin_pin, get_client_ip(request))
    return DataResponse[list[AnnouncementImageManagementResponse]](
        message="Announcement images retrieved for management.",
        data=image_service.list_management(announcement_id),
    )


@router.delete(
    "/{announcement_id}/images/{image_id}",
    response_model=DataResponse[None],
)
def delete_announcement_image(
    announcement_id: UUID,
    image_id: UUID,
    data: AnnouncementImageDeleteRequest,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    service.get_for_management(announcement_id, data.admin_pin, get_client_ip(request))
    image_service.delete(announcement_id, image_id)
    return DataResponse[None](message="Announcement image deleted successfully.")
