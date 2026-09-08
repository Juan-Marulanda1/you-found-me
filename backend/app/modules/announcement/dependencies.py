from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .repository import AnnouncementRepository
from .service import AnnouncementService


def get_service(db: Session = Depends(get_db)) -> AnnouncementService:
    repository = AnnouncementRepository(db)

    return AnnouncementService(repository)
