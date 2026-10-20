import logging
from collections.abc import Sequence
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.exceptions import (
    ImageStorageUnavailableError,
    ProductImageLimitExceededError,
    ProductImageNotFoundError,
    ProductImageUploadPendingError,
    ProductImageValidationError,
)
from app.integrations.supabase_storage import (
    SignedUpload,
    SupabaseStorage,
    SupabaseStorageError,
)
from app.modules.product.image_model import ProductImage
from app.modules.product.image_repository import ProductImageRepository
from app.modules.product.image_schemas import (
    ProductImageContentType,
    ProductImageManagementResponse,
    ProductImageResponse,
    ProductImageUploadRequest,
    ProductImageUploadResponse,
)
from app.modules.product.model import Product

logger = logging.getLogger(__name__)

_CONTENT_TYPE_EXTENSIONS: dict[ProductImageContentType, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class ProductImageService:
    def __init__(
        self,
        repository: ProductImageRepository,
        storage: SupabaseStorage,
        *,
        bucket: str,
        max_bytes: int,
        max_count: int,
    ):
        self.repository = repository
        self.storage = storage
        self.bucket = bucket
        self.max_bytes = max_bytes
        self.max_count = max_count

    def create_upload(
        self, product: Product, data: ProductImageUploadRequest
    ) -> ProductImageUploadResponse:
        if data.size_bytes > self.max_bytes:
            raise ProductImageValidationError()
        current_images = self.repository.list_for_product(product.id)
        if len(current_images) >= self.max_count:
            raise ProductImageLimitExceededError()

        position = max((image.position for image in current_images), default=-1) + 1
        extension = _CONTENT_TYPE_EXTENSIONS[data.content_type]
        path = f"products/{product.id}/{uuid4().hex}{extension}"
        image = self.repository.create(
            ProductImage(
                product_id=product.id,
                storage_path=path,
                content_type=data.content_type,
                size_bytes=data.size_bytes,
                position=position,
                alt_text=data.alt_text,
                status="PENDING",
            )
        )

        try:
            signed_upload: SignedUpload = self.storage.create_signed_upload(path)
        except SupabaseStorageError:
            self.repository.delete(image)
            raise ImageStorageUnavailableError() from None

        return ProductImageUploadResponse(
            id=image.id,
            bucket=self.bucket,
            path=path,
            token=signed_upload.token,
            signed_upload_url=signed_upload.url,
        )

    def complete(self, product_id: UUID, image_id: UUID) -> ProductImageResponse:
        image = self._get_image(product_id, image_id)
        if image.status == "READY":
            return self._as_response(image)

        try:
            metadata = self.storage.get_object_info(image.storage_path)
        except SupabaseStorageError as error:
            if error.not_found:
                raise ProductImageUploadPendingError() from None
            raise ImageStorageUnavailableError() from None

        object_metadata = metadata.get("metadata") or {}
        actual_size = (
            metadata.get("size")
            or metadata.get("contentLength")
            or object_metadata.get("size")
        )
        actual_type = (
            metadata.get("mimetype")
            or metadata.get("contentType")
            or object_metadata.get("mimetype")
            or object_metadata.get("contentType")
        )
        if (
            not isinstance(actual_size, (int, float))
            or actual_size != image.size_bytes
            or actual_size > self.max_bytes
            or actual_type != image.content_type
        ):
            try:
                self.storage.remove([image.storage_path])
                self.repository.delete(image)
            except SupabaseStorageError:
                logger.exception(
                    "Failed to clean up invalid product image %s", image.id
                )
            raise ProductImageValidationError()

        image.status = "READY"
        image = self.repository.update(image)
        return self._as_response(image)

    def list_public(self, product_id: UUID) -> list[ProductImageResponse]:
        return [
            self._as_response(image)
            for image in self.repository.list_for_product(product_id, ready_only=True)
        ]

    def list_cover_images(
        self, product_ids: Sequence[UUID]
    ) -> dict[UUID, ProductImageResponse]:
        if not self.storage.project_url:
            return {}
        return {
            product_id: self._as_response(image)
            for product_id, image in self.repository.list_cover_images(
                product_ids
            ).items()
        }

    def list_management(self, product_id: UUID) -> list[ProductImageManagementResponse]:
        return [
            ProductImageManagementResponse(
                **self._as_response(image).model_dump(), status=image.status
            )
            for image in self.repository.list_for_product(product_id)
        ]

    def delete(self, product_id: UUID, image_id: UUID) -> None:
        image = self._get_image(product_id, image_id)
        try:
            self.storage.remove([image.storage_path])
        except SupabaseStorageError:
            raise ImageStorageUnavailableError() from None
        self.repository.delete(image)

    def remove_product_files(self, product_id: UUID) -> None:
        images = self.repository.list_for_product(product_id)
        try:
            self.storage.remove([image.storage_path for image in images])
        except SupabaseStorageError:
            raise ImageStorageUnavailableError() from None

    def _get_image(self, product_id: UUID, image_id: UUID) -> ProductImage:
        image = self.repository.get_by_id(image_id)
        if image is None or image.product_id != product_id:
            raise ProductImageNotFoundError()
        return image

    def _as_response(self, image: ProductImage) -> ProductImageResponse:
        return ProductImageResponse(
            id=image.id,
            url=self.storage.public_url(image.storage_path),
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            alt_text=image.alt_text,
            position=image.position,
        )


def build_product_image_service(
    repository: ProductImageRepository,
) -> ProductImageService:
    storage = SupabaseStorage(
        project_url=settings.SUPABASE_URL,
        api_key=settings.supabase_storage_admin_key,
        bucket=settings.SUPABASE_PRODUCT_IMAGES_BUCKET,
    )
    return ProductImageService(
        repository,
        storage,
        bucket=settings.SUPABASE_PRODUCT_IMAGES_BUCKET,
        max_bytes=settings.PRODUCT_IMAGE_MAX_BYTES,
        max_count=settings.PRODUCT_IMAGE_MAX_COUNT,
    )
