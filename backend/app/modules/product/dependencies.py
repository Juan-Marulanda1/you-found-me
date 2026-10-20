from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from .image_repository import ProductImageRepository
from .image_service import ProductImageService, build_product_image_service
from .repository import ProductRepository
from .service import ProductService


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Construye el servicio con un repositorio ligado a la sesión de la solicitud."""
    return ProductService(ProductRepository(db))


def get_product_image_service(db: Session = Depends(get_db)) -> ProductImageService:
    """Construye el servicio de imágenes con la configuración de Storage."""
    return build_product_image_service(ProductImageRepository(db))
