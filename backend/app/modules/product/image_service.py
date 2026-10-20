from app.core.config import settings
from app.core.exceptions import (
    ProductImageLimitExceededError,
    ProductImageNotFoundError,
    ProductImageUploadPendingError,
    ProductImageValidationError,
)
from app.integrations.supabase_storage import SupabaseStorage
from app.modules.publication.image_service import PublicationImageService

from .image_model import ProductImage
from .image_repository import ProductImageRepository
from .image_schemas import (
    ProductImageManagementResponse,
    ProductImageResponse,
    ProductImageUploadResponse,
)


class ProductImageService(PublicationImageService[ProductImage]):
    def __init__(
        self,
        repository: ProductImageRepository,
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
            image_model=ProductImage,
            owner_field="product_id",
            storage_prefix="products",
            not_found_error=ProductImageNotFoundError,
            limit_error=ProductImageLimitExceededError,
            pending_error=ProductImageUploadPendingError,
            validation_error=ProductImageValidationError,
            upload_response_model=ProductImageUploadResponse,
            image_response_model=ProductImageResponse,
            management_response_model=ProductImageManagementResponse,
        )


def build_product_image_service(
    repository: ProductImageRepository,
) -> ProductImageService:
    """Crea el adaptador de Storage y el servicio con los límites configurados."""
    storage = SupabaseStorage(
        project_url=settings.SUPABASE_URL,
        api_key=settings.supabase_admin_key,
        bucket=settings.SUPABASE_PRODUCT_IMAGES_BUCKET,
    )
    return ProductImageService(
        repository,
        storage,
        bucket=settings.SUPABASE_PRODUCT_IMAGES_BUCKET,
        max_bytes=settings.PRODUCT_IMAGE_MAX_BYTES,
        max_count=settings.PRODUCT_IMAGE_MAX_COUNT,
    )
