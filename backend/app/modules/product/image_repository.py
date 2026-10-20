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
