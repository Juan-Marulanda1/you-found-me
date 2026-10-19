from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.pagination import PageData, build_page
from app.core.responses import DataResponse

from .dependencies import get_announcement_service
from .enums import AnnouncementStatus
from .schemas import (
    AnnouncementCreate,
    AnnouncementDelete,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from .service import AnnouncementService

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post("", response_model=DataResponse[AnnouncementResponse], status_code=201)
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
    listing_status: AnnouncementStatus | None = Query(default=None, alias="status"),
    service: AnnouncementService = Depends(get_announcement_service),
):
    result = service.list(
        page=page,
        page_size=page_size,
        city=city,
        category=category,
        status=listing_status,
        search=search,
    )
    return DataResponse[PageData[AnnouncementResponse]](
        message="Announcements retrieved successfully.",
        data=build_page(
            result.items, page=page, page_size=page_size, total=result.total
        ),
    )


@router.get("/{announcement_id}", response_model=DataResponse[AnnouncementResponse])
def get_announcement(
    announcement_id: UUID,
    service: AnnouncementService = Depends(get_announcement_service),
):
    return DataResponse[AnnouncementResponse](
        message="Announcement retrieved successfully.",
        data=service.get_by_id(announcement_id),
    )


@router.patch("/{announcement_id}", response_model=DataResponse[AnnouncementResponse])
def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    request: Request,
    service: AnnouncementService = Depends(get_announcement_service),
):
    return DataResponse[AnnouncementResponse](
        message="Announcement updated successfully.",
        data=service.update(
            announcement_id,
            data,
            request.client.host if request.client else "unknown",
        ),
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
):
    service.delete(
        announcement_id,
        data.admin_pin,
        request.client.host if request.client else "unknown",
    )
    return DataResponse[None](message="Announcement deleted successfully.")
