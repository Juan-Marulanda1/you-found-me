from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .repository import AnnouncementRepository
from .service import AnnouncementService


def get_announcement_service(db: Session = Depends(get_db)) -> AnnouncementService:
    return AnnouncementService(AnnouncementRepository(db))


get_service = get_announcement_service
