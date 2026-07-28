from uuid import UUID

from sqlalchemy.orm import Session

from .model import Announcement
from .schemas import AnnouncementCreate

class AnnouncementRepository:
    
    def __init__(self, db: Session):
        self.db = db
        
    def create(self, announcement: Announcement ) -> Announcement:

        self.db.add(announcement)
        self.db.commit()
        self.db.refresh(announcement)

        return announcement
    
    def get_by_id(self, announcement_id: UUID) -> Announcement | None:
        
        announcement  = self.db.query(Announcement).filter(Announcement.id == announcement_id).first()
        
        return announcement 
    
    def list(self) -> list[Announcement]:
        
        list = self.db.query(Announcement).order_by(Announcement.created_at.desc()).all()
        
        return list
    
    def update(self, announcement: Announcement) -> Announcement:
        
        self.db.commit()
        self.db.refresh(announcement)
        
        return announcement