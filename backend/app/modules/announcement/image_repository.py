from sqlalchemy.orm import Session

from app.modules.publication.image_repository import PublicationImageRepository

from .image_model import AnnouncementImage


class AnnouncementImageRepository(PublicationImageRepository[AnnouncementImage]):
    def __init__(self, db: Session):
        super().__init__(db, AnnouncementImage, "announcement_id")
