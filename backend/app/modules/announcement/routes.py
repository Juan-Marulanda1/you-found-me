from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .repository import AnnouncementRepository
from .service import AnnouncementService

from .schemas import (AnnouncementCreate, AnnouncementResponse)

from uuid import UUID

router = APIRouter(prefix="/announcements", tags=["Announcements"])

def get_service(db:Session = Depends(get_db)) -> AnnouncementService:
    repository = AnnouncementRepository(db)
    
    return AnnouncementService(repository)

@router.post("", response_model=AnnouncementResponse, status_code=201)
def create_announcement(data: AnnouncementCreate, service: AnnouncementService = Depends(get_service)):
    announcement = service.create(data)
    return  announcement

@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(announcement_id: UUID, service: AnnouncementService = Depends(get_service)):
    announcement = service.get_by_id(announcement_id)
    return announcement

@router.get("", response_model=list[AnnouncementResponse])
def list_announcements(service: AnnouncementService = Depends(get_service)):

    return service.list()