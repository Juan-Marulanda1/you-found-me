from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.owner import PublicationOwner
from app.modules.publication.repository import PageResult


class SQLAlchemyPublicationRepository[Entity: Base]:
    """SQLAlchemy adapter shared by the product and announcement modules."""

    def __init__(self, db: Session, model: type[Entity]):
        self.db = db
        self.model = model

    def create(self, publication: Entity) -> Entity:
        owner_id = getattr(publication, "owner_id", None)
        if owner_id is not None and self.db.get(PublicationOwner, owner_id) is None:
            self.db.add(PublicationOwner(id=owner_id))
            self.db.flush()
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

    def list_by_owner(self, owner_id: UUID) -> list[Entity]:
        return list(
            self.db.scalars(
                select(self.model)
                .where(self.model.owner_id == owner_id)  # type: ignore[attr-defined]
                .order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
            )
        )

    def list_claimable_by_email(self, email: str) -> list[Entity]:
        return list(
            self.db.scalars(
                select(self.model)
                .where(
                    self.model.owner_id.is_(None),  # type: ignore[attr-defined]
                    func.lower(self.model.contact_email) == email.lower(),  # type: ignore[attr-defined]
                )
                .order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
            )
        )

    def assign_owner(self, publication_id: UUID, owner_id: UUID) -> Entity | None:
        publication = self.get_by_id(publication_id)
        if publication is None:
            return None
        current_owner = getattr(publication, "owner_id", None)
        if current_owner is not None and current_owner != owner_id:
            return None
        if self.db.get(PublicationOwner, owner_id) is None:
            self.db.add(PublicationOwner(id=owner_id))
            self.db.flush()
        if current_owner is None:
            result = self.db.execute(
                update(self.model)
                .where(
                    self.model.id == publication_id,  # type: ignore[attr-defined]
                    self.model.owner_id.is_(None),  # type: ignore[attr-defined]
                )
                .values(owner_id=owner_id)
            )
            if result.rowcount != 1:
                self.db.rollback()
                return None
            self.db.commit()
            return self.get_by_id(publication_id)
        return publication

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
