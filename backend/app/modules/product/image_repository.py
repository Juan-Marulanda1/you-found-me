from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.publication.image_repository import PublicationImageRepository

from .image_model import ProductImage


class ProductImageRepository(PublicationImageRepository[ProductImage]):
    def __init__(self, db: Session):
        super().__init__(db, ProductImage, "product_id")

    def count_for_product(self, product_id: UUID) -> int:
        return self.count_for_publication(product_id)

    def list_for_product(
        self, product_id: UUID, *, ready_only: bool = False
    ) -> list[ProductImage]:
        return self.list_for_publication(product_id, ready_only=ready_only)

    def delete_for_product(self, product_id: UUID) -> None:
        self.delete_for_publication(product_id)
