import logging
from collections.abc import Callable
from uuid import UUID

from app.core.exceptions import InvalidAdminPinError, PublicationNotFoundError
from app.core.pin_limiter import PinAttemptLimiter, pin_attempt_limiter
from app.core.security import hash_admin_pin, verify_admin_pin
from app.modules.publication.repository import PublicationRepository

from .enums import AnnouncementStatus
from .model import Announcement
from .schemas import AnnouncementCreate, AnnouncementUpdate

logger = logging.getLogger(__name__)


class AnnouncementService:
    def __init__(
        self,
        repository: PublicationRepository[Announcement],
        limiter: PinAttemptLimiter = pin_attempt_limiter,
    ):
        self.repository = repository
        self.limiter = limiter

    def create(
        self, data: AnnouncementCreate, owner_id: UUID | None = None
    ) -> Announcement:
        values = data.model_dump(exclude={"admin_pin"})
        announcement = Announcement(
            **values,
            admin_pin_hash=hash_admin_pin(data.admin_pin) if data.admin_pin else None,
            owner_id=owner_id,
            status=AnnouncementStatus.ACTIVE,
        )
        return self.repository.create(announcement)

    def get_by_id(self, announcement_id: UUID) -> Announcement:
        announcement = self.repository.get_by_id(announcement_id)
        if announcement is None:
            raise PublicationNotFoundError()
        return announcement

    def get_public_by_id(self, announcement_id: UUID) -> Announcement:
        announcement = self.get_by_id(announcement_id)
        if announcement.status != AnnouncementStatus.ACTIVE:
            raise PublicationNotFoundError()
        return announcement

    def get_for_management(
        self,
        announcement_id: UUID,
        admin_pin: str | None = None,
        client_ip: str = "unknown",
        owner_id: UUID | None = None,
    ) -> Announcement:
        announcement = self.get_by_id(announcement_id)
        self._authorize(announcement, admin_pin, client_ip, owner_id)
        return announcement

    def list_by_owner(self, owner_id: UUID) -> list[Announcement]:
        return self.repository.list_by_owner(owner_id)

    def list_claimable_by_email(self, email: str) -> list[Announcement]:
        return self.repository.list_claimable_by_email(email)

    def claim(
        self, announcement_id: UUID, admin_pin: str, owner_id: UUID, client_ip: str
    ) -> Announcement:
        announcement = self.get_by_id(announcement_id)
        if announcement.owner_id == owner_id:
            return announcement
        if announcement.owner_id is not None:
            raise PublicationNotFoundError()
        self._validate_pin(announcement, admin_pin, client_ip)
        claimed = self.repository.assign_owner(announcement_id, owner_id)
        if claimed is None:
            raise PublicationNotFoundError()
        return claimed

    def list(
        self,
        *,
        page: int,
        page_size: int,
        city: str | None,
        category: str | None,
        status: AnnouncementStatus | None,
        search: str | None,
    ):
        return self.repository.list(
            page=page,
            page_size=page_size,
            city=city,
            category=category,
            status=status,
            search=search,
        )

    def update(
        self,
        announcement_id: UUID,
        data: AnnouncementUpdate,
        client_ip: str = "unknown",
        owner_id: UUID | None = None,
    ) -> Announcement:
        announcement = self.get_by_id(announcement_id)
        self._authorize(announcement, data.admin_pin, client_ip, owner_id)

        updates = data.model_dump(
            exclude_unset=True, exclude={"admin_pin", "new_admin_pin"}
        )
        for field, value in updates.items():
            setattr(announcement, field, value)
        if data.new_admin_pin:
            announcement.admin_pin_hash = hash_admin_pin(data.new_admin_pin)
        return self.repository.update(announcement)

    def delete(
        self,
        announcement_id: UUID,
        admin_pin: str | None,
        client_ip: str = "unknown",
        before_delete: Callable[[UUID], None] | None = None,
        owner_id: UUID | None = None,
    ) -> None:
        announcement = self.get_by_id(announcement_id)
        self._authorize(announcement, admin_pin, client_ip, owner_id)
        if before_delete is not None:
            before_delete(announcement_id)
        self.repository.delete(announcement)

    def _validate_pin(
        self, announcement: Announcement, admin_pin: str, client_ip: str
    ) -> None:
        self.limiter.check("announcement", announcement.id, client_ip)
        if not announcement.admin_pin_hash or not verify_admin_pin(
            admin_pin, announcement.admin_pin_hash
        ):
            self.limiter.record_failure("announcement", announcement.id, client_ip)
            logger.warning(
                "Invalid management PIN for announcement %s", announcement.id
            )
            raise InvalidAdminPinError()
        self.limiter.record_success("announcement", announcement.id, client_ip)

    def _authorize(
        self,
        announcement: Announcement,
        admin_pin: str | None,
        client_ip: str,
        owner_id: UUID | None,
    ) -> None:
        if announcement.owner_id is not None:
            if announcement.owner_id != owner_id:
                raise PublicationNotFoundError()
            return
        if not admin_pin:
            raise InvalidAdminPinError()
        self._validate_pin(announcement, admin_pin, client_ip)
