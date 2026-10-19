from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.modules.publication.repository import PageResult


class SQLAlchemyPublicationRepository[Entity: Base]:
    """SQLAlchemy adapter shared by the product and announcement modules."""

    def __init__(self, db: Session, model: type[Entity]):
        self.db = db
        self.model = model

    def create(self, publication: Entity) -> Entity:
        self.db.add(publication)
        try:
            self.db.commit()
            self.db.refresh(publication)
        except Exception:
            self.db.rollback()
            raise
        return publication

    def get_by_id(self, publication_id: UUID) -> Entity | None:
        return self.db.scalar(
            select(self.model).where(self.model.id == publication_id)  # type: ignore[attr-defined]
        )

    def list(
        self,
        *,
        page: int,
        page_size: int,
        city: str | None = None,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> PageResult[Entity]:
        statement = select(self.model)
        filters: list[Any] = []
        if city:
            filters.append(self.model.city.ilike(f"%{city}%"))  # type: ignore[attr-defined]
        if category:
            filters.append(self.model.category == category)  # type: ignore[attr-defined]
        if status:
            filters.append(self.model.status == status)  # type: ignore[attr-defined]
        if search:
            search_pattern = f"%{search}%"
            search_fields = [
                self.model.title.ilike(search_pattern),  # type: ignore[attr-defined]
                self.model.description.ilike(search_pattern),  # type: ignore[attr-defined]
            ]
            business_name = getattr(self.model, "business_name", None)
            if business_name is not None:
                search_fields.append(business_name.ilike(search_pattern))
            filters.append(or_(*search_fields))
        if min_price is not None:
            filters.append(self.model.price >= min_price)  # type: ignore[attr-defined]
        if max_price is not None:
            filters.append(self.model.price <= max_price)  # type: ignore[attr-defined]
        if filters:
            statement = statement.where(*filters)

        total = (
            self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        )
        items = list(
            self.db.scalars(
                statement.order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return PageResult(items=items, total=total)

    def update(self, publication: Entity) -> Entity:
        try:
            self.db.commit()
            self.db.refresh(publication)
        except Exception:
            self.db.rollback()
            raise
        return publication

    def delete(self, publication: Entity) -> None:
        self.db.delete(publication)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
