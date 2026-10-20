from app.core.config import settings
from app.core.exceptions import (
    AnnouncementImageLimitExceededError,
    AnnouncementImageNotFoundError,
    AnnouncementImageUploadPendingError,
    AnnouncementImageValidationError,
)
from app.integrations.supabase_storage import SupabaseStorage
from app.modules.publication.image_service import PublicationImageService

from .image_model import AnnouncementImage
from .image_repository import AnnouncementImageRepository
from .image_schemas import (
    AnnouncementImageManagementResponse,
    AnnouncementImageResponse,
    AnnouncementImageUploadResponse,
)


class AnnouncementImageService(PublicationImageService[AnnouncementImage]):
    def __init__(
        self,
        repository: AnnouncementImageRepository,
        storage: SupabaseStorage,
        *,
        bucket: str,
        max_bytes: int,
        max_count: int,
    ):
        super().__init__(
            repository,
            storage,
            bucket=bucket,
            max_bytes=max_bytes,
            max_count=max_count,
            image_model=AnnouncementImage,
            owner_field="announcement_id",
            storage_prefix="announcements",
            not_found_error=AnnouncementImageNotFoundError,
            limit_error=AnnouncementImageLimitExceededError,
            pending_error=AnnouncementImageUploadPendingError,
            validation_error=AnnouncementImageValidationError,
            upload_response_model=AnnouncementImageUploadResponse,
            image_response_model=AnnouncementImageResponse,
            management_response_model=AnnouncementImageManagementResponse,
        )


def build_announcement_image_service(
    repository: AnnouncementImageRepository,
) -> AnnouncementImageService:
    """Crea el adaptador de Storage y el servicio con los límites configurados."""
    storage = SupabaseStorage(
        project_url=settings.SUPABASE_URL,
        api_key=settings.supabase_admin_key,
        bucket=settings.SUPABASE_PRODUCT_IMAGES_BUCKET,
    )
    return AnnouncementImageService(
        repository,
        storage,
        bucket=settings.SUPABASE_PRODUCT_IMAGES_BUCKET,
        max_bytes=settings.PRODUCT_IMAGE_MAX_BYTES,
        max_count=settings.ANNOUNCEMENT_IMAGE_MAX_COUNT,
    )
