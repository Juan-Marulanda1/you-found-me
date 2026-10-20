from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, TypeVar
from uuid import UUID

Entity = TypeVar("Entity")


@dataclass(frozen=True)
class PageResult[Entity]:
    items: list[Entity]
    total: int


class PublicationRepository(Protocol[Entity]):
    def create(self, publication: Entity) -> Entity: ...

    def get_by_id(self, publication_id: UUID) -> Entity | None: ...

    def list_by_owner(self, owner_id: UUID) -> list[Entity]: ...

    def list_claimable_by_email(self, email: str) -> list[Entity]: ...

    def assign_owner(self, publication_id: UUID, owner_id: UUID) -> Entity | None: ...

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
    ) -> PageResult[Entity]: ...

    def update(self, publication: Entity) -> Entity: ...

    def delete(self, publication: Entity) -> None: ...
