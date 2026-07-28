from uuid import UUID
from sqlalchemy.orm import session

from .model import Announcement
from .repository import AnnouncementRepository
from .schemas import (AnnouncementCreate, AnnouncementUpdate)
from app.core.exceptions import AnnouncementNotFoundError

class AnnouncementService:
    
    def __init__(self, repository: AnnouncementRepository):
        self.repository = repository
        
    def create(self, data: AnnouncementCreate) -> Announcement:
        announcement = Announcement(**data.model_dump())
        
        return self.repository.create(announcement)
    
    def get_by_id(self, announcement_id: UUID) -> Announcement:
        announcement = self.repository.get_by_id(announcement_id)
        
        if announcement is None:
            raise AnnouncementNotFoundError()
            
        return announcement
    
    def update(self, announment_id: UUID, data:AnnouncementUpdate) -> Announcement:
        announcement = self.get_by_id(announment_id)
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(announcement, field, value)
            
        return self.repository.update(announcement)
    
    def list(self) -> list[Announcement]:
        return self.repository.list()