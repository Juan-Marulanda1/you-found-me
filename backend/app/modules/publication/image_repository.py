from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session


class PublicationImageRepository[ImageModel]:
    """Persistence operations shared by image records for each publication type."""

    def __init__(self, db: Session, model: type[ImageModel], owner_field: str):
        self.db = db
        self.model = model
        self.owner_field = owner_field

    def count_for_publication(self, publication_id: UUID) -> int:
        owner_column = getattr(self.model, self.owner_field)
        return (
            self.db.scalar(
                select(func.count())
                .select_from(self.model)
                .where(owner_column == publication_id)
            )
            or 0
        )

    def list_for_publication(
        self, publication_id: UUID, *, ready_only: bool = False
    ) -> list[ImageModel]:
        owner_column = getattr(self.model, self.owner_field)
        statement = select(self.model).where(owner_column == publication_id)
        if ready_only:
            statement = statement.where(self.model.status == "READY")
        return list(self.db.scalars(statement.order_by(self.model.position)))

    def list_cover_images(
        self, publication_ids: Sequence[UUID]
    ) -> dict[UUID, ImageModel]:
        if not publication_ids:
            return {}

        owner_column = getattr(self.model, self.owner_field)
        statement = (
            select(self.model)
            .where(owner_column.in_(publication_ids), self.model.status == "READY")
            .order_by(
                owner_column,
                self.model.position,
                self.model.created_at,
                self.model.id,
            )
        )
        covers: dict[UUID, ImageModel] = {}
        for image in self.db.scalars(statement):
            covers.setdefault(getattr(image, self.owner_field), image)
        return covers

    def get_by_id(self, image_id: UUID) -> ImageModel | None:
        return self.db.scalar(select(self.model).where(self.model.id == image_id))

    def create(self, image: ImageModel) -> ImageModel:
        self.db.add(image)
        try:
            self.db.commit()
            self.db.refresh(image)
        except Exception:
            self.db.rollback()
            raise
        return image

    def update(self, image: ImageModel) -> ImageModel:
        try:
            self.db.commit()
            self.db.refresh(image)
        except Exception:
            self.db.rollback()
            raise
        return image

    def delete(self, image: ImageModel) -> None:
        self.db.delete(image)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def delete_for_publication(self, publication_id: UUID) -> None:
        owner_column = getattr(self.model, self.owner_field)
        self.db.query(self.model).filter(owner_column == publication_id).delete(
            synchronize_session=False
        )
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
