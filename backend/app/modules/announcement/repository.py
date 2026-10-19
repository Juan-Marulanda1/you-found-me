from sqlalchemy.orm import Session

from app.database.repositories import SQLAlchemyPublicationRepository

from .model import Announcement


class AnnouncementRepository(SQLAlchemyPublicationRepository[Announcement]):
    def __init__(self, db: Session):
        super().__init__(db, Announcement)
