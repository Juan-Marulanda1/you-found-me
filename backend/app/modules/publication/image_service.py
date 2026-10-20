import logging
from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

from app.core.exceptions import (
    ImageStorageUnavailableError,
    PublicationImageLimitExceededError,
    PublicationImageNotFoundError,
    PublicationImageUploadPendingError,
    PublicationImageValidationError,
)
from app.integrations.supabase_storage import (
    SignedUpload,
    SupabaseStorage,
    SupabaseStorageError,
)

from .image_repository import PublicationImageRepository
from .image_schemas import (
    PublicationImageContentType,
    PublicationImageManagementResponse,
    PublicationImageResponse,
    PublicationImageUploadRequest,
    PublicationImageUploadResponse,
)

logger = logging.getLogger(__name__)

_CONTENT_TYPE_EXTENSIONS: dict[PublicationImageContentType, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class PublicationImageService[ImageModel]:
    """Valida cargas y coordina sus metadatos con Supabase Storage.

    Ciclo de una imagen: create_upload la registra como PENDING y firma la
    carga; el navegador sube el archivo a Storage; complete verifica el objeto
    real y la marca READY. Solo las imágenes READY aparecen en el catálogo.
    Cada dominio la especializa con su modelo, prefijo y errores propios.
    """

    def __init__(
        self,
        repository: PublicationImageRepository[ImageModel],
        storage: SupabaseStorage,
        *,
        bucket: str,
        max_bytes: int,
        max_count: int,
        image_model: type[ImageModel],
        owner_field: str,
        storage_prefix: str,
        not_found_error: type[Exception] = PublicationImageNotFoundError,
        limit_error: type[Exception] = PublicationImageLimitExceededError,
        pending_error: type[Exception] = PublicationImageUploadPendingError,
        validation_error: type[Exception] = PublicationImageValidationError,
        upload_response_model: type[
            PublicationImageUploadResponse
        ] = PublicationImageUploadResponse,
        image_response_model: type[PublicationImageResponse] = PublicationImageResponse,
        management_response_model: type[
            PublicationImageManagementResponse
        ] = PublicationImageManagementResponse,
    ):
        self.repository = repository
        self.storage = storage
        self.bucket = bucket
        self.max_bytes = max_bytes
        self.max_count = max_count
        self.image_model = image_model
        self.owner_field = owner_field
        self.storage_prefix = storage_prefix
        self.not_found_error = not_found_error
        self.limit_error = limit_error
        self.pending_error = pending_error
        self.validation_error = validation_error
        self.upload_response_model = upload_response_model
        self.image_response_model = image_response_model
        self.management_response_model = management_response_model

    def create_upload(
        self, publication: Any, data: PublicationImageUploadRequest
    ) -> PublicationImageUploadResponse:
        """Valida tamaño y cupo, registra la imagen pendiente y firma su carga."""
        if data.size_bytes > self.max_bytes:
            raise self.validation_error()

        # Las cargas pendientes también ocupan cupo para evitar exceder el límite.
        current_images = self.repository.list_for_publication(publication.id)
        if len(current_images) >= self.max_count:
            raise self.limit_error()

        position = max((image.position for image in current_images), default=-1) + 1
        extension = _CONTENT_TYPE_EXTENSIONS[data.content_type]
        path = f"{self.storage_prefix}/{publication.id}/{uuid4().hex}{extension}"
        image = self.image_model(
            **{
                self.owner_field: publication.id,
                "storage_path": path,
                "content_type": data.content_type,
                "size_bytes": data.size_bytes,
                "position": position,
                "alt_text": data.alt_text,
                "status": "PENDING",
            }
        )
        image = self.repository.create(image)

        try:
            signed_upload: SignedUpload = self.storage.create_signed_upload(path)
        except SupabaseStorageError:
            # Sin URL firmada el registro pendiente no sirve; se descarta.
            self.repository.delete(image)
            raise ImageStorageUnavailableError() from None

        return self.upload_response_model(
            id=image.id,
            bucket=self.bucket,
            path=path,
            token=signed_upload.token,
            signed_upload_url=signed_upload.url,
        )

    def complete(
        self, publication_id: UUID, image_id: UUID
    ) -> PublicationImageResponse:
        """Confirma una carga si el archivo en Storage coincide con lo declarado."""
        image = self._get_image(publication_id, image_id)
        if image.status == "READY":
            return self._as_response(image)

        try:
            metadata = self.storage.get_object_info(image.storage_path)
        except SupabaseStorageError as error:
            if error.not_found:
                raise self.pending_error() from None
            raise ImageStorageUnavailableError() from None

        # La URL firmada autoriza la carga, pero el servidor verifica el objeto real
        # antes de publicarlo.
        # Supabase expone estos datos con nombres distintos según la versión.
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
                    "Failed to clean up invalid publication image %s", image.id
                )
            raise self.validation_error()

        image.status = "READY"
        image = self.repository.update(image)
        return self._as_response(image)

    def list_public(self, publication_id: UUID) -> list[PublicationImageResponse]:
        """Imágenes listas para mostrar en el catálogo."""
        return [
            self._as_response(image)
            for image in self.repository.list_for_publication(
                publication_id, ready_only=True
            )
        ]

    def list_cover_images(
        self, publication_ids: Sequence[UUID]
    ) -> dict[UUID, PublicationImageResponse]:
        """Portada de cada publicación; vacío si Storage no está configurado."""
        if not self.storage.project_url:
            return {}
        return {
            publication_id: self._as_response(image)
            for publication_id, image in self.repository.list_cover_images(
                publication_ids
            ).items()
        }

    def list_management(
        self, publication_id: UUID
    ) -> list[PublicationImageManagementResponse]:
        """Todas las imágenes con su estado, para la pantalla de gestión."""
        return [
            self.management_response_model(
                **self._as_response(image).model_dump(), status=image.status
            )
            for image in self.repository.list_for_publication(publication_id)
        ]

    def delete(self, publication_id: UUID, image_id: UUID) -> None:
        """Borra el archivo en Storage y después su registro."""
        image = self._get_image(publication_id, image_id)
        try:
            self.storage.remove([image.storage_path])
        except SupabaseStorageError:
            raise ImageStorageUnavailableError() from None
        self.repository.delete(image)

    def remove_publication_files(self, publication_id: UUID) -> None:
        """Borra de Storage los archivos de una publicación antes de eliminarla."""
        images = self.repository.list_for_publication(publication_id)
        try:
            self.storage.remove([image.storage_path for image in images])
        except SupabaseStorageError:
            raise ImageStorageUnavailableError() from None

    def _get_image(self, publication_id: UUID, image_id: UUID) -> ImageModel:
        """Obtiene la imagen y comprueba que pertenezca a la publicación indicada."""
        image = self.repository.get_by_id(image_id)
        if image is None or getattr(image, self.owner_field) != publication_id:
            raise self.not_found_error()
        return image

    def _as_response(self, image: ImageModel) -> PublicationImageResponse:
        """Convierte el modelo en respuesta con su URL pública."""
        return self.image_response_model(
            id=image.id,
            url=self.storage.public_url(image.storage_path),
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            alt_text=image.alt_text,
            position=image.position,
        )
