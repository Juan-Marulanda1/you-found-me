import logging
from uuid import UUID

from app.core.exceptions import AnnouncementNotFoundError, InvalidAdminPinError

from .model import Announcement
from .repository import AnnouncementRepository
from .schemas import AnnouncementCreate, AnnouncementUpdate

logger = logging.getLogger(__name__)


class AnnouncementService:
    def __init__(self, repository: AnnouncementRepository):
        self.repository = repository

    def create(self, data: AnnouncementCreate) -> Announcement:
        logger.info(
            "Creating announcement: title='%s', city='%s'",
            data.title,
            data.city,
        )
        announcement = Announcement(**data.model_dump())

        return self.repository.create(announcement)

    def get_by_id(self, announcement_id: UUID) -> Announcement:
        logger.info("Getting announcement %s", announcement_id)
        announcement = self.repository.get_by_id(announcement_id)

        if announcement is None:
            logger.warning("announcement %s not found", announcement_id)
            raise AnnouncementNotFoundError()

        return announcement

    def update(self, announcement_id: UUID, data: AnnouncementUpdate) -> Announcement:

        logger.info("Updating announcement %s", announcement_id)

        announcement = self.get_by_id(announcement_id)

        self._validate_admin_pin(
            announcement,
            data.admin_pin,
        )

        updates = data.model_dump(
            exclude_unset=True,
            exclude={"admin_pin"},
        )

        logger.info(
            "Updating announcement %s with fields: %s",
            announcement_id,
            list(updates.keys()),
        )

        for field, value in updates.items():
            setattr(announcement, field, value)

        updated_announcement = self.repository.update(announcement)

        logger.info(
            "Announcement %s updated successfully",
            announcement_id,
        )

        return updated_announcement

    def list(self) -> list[Announcement]:
        logger.info("Listing announcements")
        return self.repository.list()

    def delete(self, announcement_id: UUID, admin_pin: str) -> None:
        logger.info("Deleting announcement %s", announcement_id)
        announcement = self.get_by_id(announcement_id)

        self._validate_admin_pin(announcement, admin_pin)

        self.repository.delete(announcement)

        logger.info(
            "Announcement %s deleted successfully",
            announcement_id,
        )

    def _validate_admin_pin(
        self,
        announcement: Announcement,
        admin_pin: str,
    ) -> None:

        if announcement.admin_pin != admin_pin:
            logger.warning(
                "Invalid admin PIN for announcement %s",
                announcement.id,
            )

            raise InvalidAdminPinError
