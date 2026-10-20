from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .image_repository import AnnouncementImageRepository
from .image_service import AnnouncementImageService, build_announcement_image_service
from .repository import AnnouncementRepository
from .service import AnnouncementService


def get_announcement_service(db: Session = Depends(get_db)) -> AnnouncementService:
    """Construye el servicio con un repositorio ligado a la sesión de la solicitud."""
    return AnnouncementService(AnnouncementRepository(db))


def get_announcement_image_service(
    db: Session = Depends(get_db),
) -> AnnouncementImageService:
    """Construye el servicio de imágenes con la configuración de Storage."""
    return build_announcement_image_service(AnnouncementImageRepository(db))
