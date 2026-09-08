# Standard Library
from uuid import UUID

# Third Party
from fastapi import APIRouter, Depends, status

# Local
from app.core.responses import DataResponse

from .dependencies import get_service
from .schemas import (
    AnnouncementCreate,
    AnnouncementDelete,
    AnnouncementResponse,
)
from .service import AnnouncementService

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post("", response_model=DataResponse[AnnouncementResponse], status_code=201)
def create_announcement(
    data: AnnouncementCreate, service: AnnouncementService = Depends(get_service)
):
    return DataResponse[AnnouncementResponse](
        message="Announcement created successfully.", data=service.create(data)
    )


@router.get("/{announcement_id}", response_model=DataResponse[AnnouncementResponse])
def get_announcement(
    announcement_id: UUID, service: AnnouncementService = Depends(get_service)
):
    return DataResponse[AnnouncementResponse](
        message="Announcement retrieved successfully.",
        data=service.get_by_id(announcement_id),
    )


@router.get("", response_model=DataResponse[list[AnnouncementResponse]])
def list_announcements(service: AnnouncementService = Depends(get_service)):
    return DataResponse[list[AnnouncementResponse]](
        message="Announcements retrieved successfully.", data=service.list()
    )


@router.delete(
    "/{announcement_id}",
    response_model=DataResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_announcement(
    announcement_id: UUID,
    data: AnnouncementDelete,
    service: AnnouncementService = Depends(get_service),
):

    service.delete(
        announcement_id,
        data.admin_pin,
    )

    return DataResponse[None](message="Announcement deleted successfully.")
