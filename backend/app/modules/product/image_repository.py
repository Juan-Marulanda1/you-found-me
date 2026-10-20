from sqlalchemy.orm import Session

from app.modules.publication.image_repository import PublicationImageRepository

from .image_model import ProductImage


class ProductImageRepository(PublicationImageRepository[ProductImage]):
    """Repositorio de imágenes de productos, enlazado por product_id."""

    def __init__(self, db: Session):
        super().__init__(db, ProductImage, "product_id")
