from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .image_model import ProductImage


class ProductImageRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_for_product(self, product_id: UUID) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(ProductImage)
                .where(ProductImage.product_id == product_id)
            )
            or 0
        )

    def list_for_product(
        self, product_id: UUID, *, ready_only: bool = False
    ) -> list[ProductImage]:
        statement = select(ProductImage).where(ProductImage.product_id == product_id)
        if ready_only:
            statement = statement.where(ProductImage.status == "READY")
        return list(self.db.scalars(statement.order_by(ProductImage.position)))

    def list_cover_images(
        self, product_ids: Sequence[UUID]
    ) -> dict[UUID, ProductImage]:
        if not product_ids:
            return {}

        statement = (
            select(ProductImage)
            .where(
                ProductImage.product_id.in_(product_ids),
                ProductImage.status == "READY",
            )
            .order_by(
                ProductImage.product_id,
                ProductImage.position,
                ProductImage.created_at,
                ProductImage.id,
            )
        )
        covers: dict[UUID, ProductImage] = {}
        for image in self.db.scalars(statement):
            covers.setdefault(image.product_id, image)
        return covers

    def get_by_id(self, image_id: UUID) -> ProductImage | None:
        return self.db.scalar(select(ProductImage).where(ProductImage.id == image_id))

    def create(self, image: ProductImage) -> ProductImage:
        self.db.add(image)
        try:
            self.db.commit()
            self.db.refresh(image)
        except Exception:
            self.db.rollback()
            raise
        return image

    def update(self, image: ProductImage) -> ProductImage:
        try:
            self.db.commit()
            self.db.refresh(image)
        except Exception:
            self.db.rollback()
            raise
        return image

    def delete(self, image: ProductImage) -> None:
        self.db.delete(image)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def delete_for_product(self, product_id: UUID) -> None:
        self.db.query(ProductImage).filter(
            ProductImage.product_id == product_id
        ).delete(synchronize_session=False)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
