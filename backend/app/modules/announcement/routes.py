from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.pagination import PageData, build_page
from app.core.request import get_client_ip
from app.core.responses import DataResponse
from app.core.supabase_auth import (
    AuthenticatedUser,
    optional_authenticated_user,
    require_authenticated_user,
)

from .dependencies import get_announcement_image_service, get_announcement_service
from .enums import AnnouncementStatus
from .image_schemas import (
    AnnouncementImageCompleteRequest,
    AnnouncementImageDeleteRequest,
    AnnouncementImageManagementResponse,
    AnnouncementImageResponse,
    AnnouncementImageUploadRequest,
    AnnouncementImageUploadResponse,
)
from .image_service import AnnouncementImageService
from .schemas import (
    AnnouncementCreate,
    AnnouncementDelete,
    AnnouncementManagementResponse,
    AnnouncementManageRequest,
    AnnouncementResponse,
    AnnouncementUpdate,
)
from .service import AnnouncementService

# Las búsquedas son públicas; las escrituras y la administración delegan la
# autorización al servicio.
router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post(
    "",
    response_model=DataResponse[AnnouncementResponse],
    status_code=201,
)
def create_announcement(
    data: AnnouncementCreate,
    user: AuthenticatedUser = Depends(require_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
):
    """Crea un aviso asociado a la cuenta autenticada."""
    return DataResponse[AnnouncementResponse](
        message="Aviso creado correctamente.",
        data=service.create(data, user.id),
    )


@router.get("", response_model=DataResponse[PageData[AnnouncementResponse]])
def list_announcements(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city: str | None = Query(default=None, min_length=2, max_length=100),
    category: str | None = Query(default=None, min_length=2, max_length=80),
    search: str | None = Query(default=None, min_length=2, max_length=150),
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Lista avisos activos con filtros y paginación; ruta pública."""
    result = service.list(
        page=page,
        page_size=page_size,
        city=city,
        category=category,
        status=AnnouncementStatus.ACTIVE,
        search=search,
    )
    cover_images = image_service.list_cover_images(
        [announcement.id for announcement in result.items]
    )
    items = [
        AnnouncementResponse.model_validate(announcement).model_copy(
            update={"cover_image": cover_images.get(announcement.id)}
        )
        for announcement in result.items
    ]
    return DataResponse[PageData[AnnouncementResponse]](
        message="Avisos obtenidos correctamente.",
        data=build_page(items, page=page, page_size=page_size, total=result.total),
    )


@router.get("/{announcement_id}", response_model=DataResponse[AnnouncementResponse])
def get_announcement(
    announcement_id: UUID,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Devuelve un aviso activo con su imagen de portada."""
    announcement = service.get_public_by_id(announcement_id)
    cover_image = image_service.list_cover_images([announcement.id]).get(
        announcement.id
    )
    return DataResponse[AnnouncementResponse](
        message="Aviso obtenido correctamente.",
        data=AnnouncementResponse.model_validate(announcement).model_copy(
            update={"cover_image": cover_image}
        ),
    )


@router.post(
    "/{announcement_id}/manage",
    response_model=DataResponse[AnnouncementManagementResponse],
)
def get_announcement_for_management(
    announcement_id: UUID,
    data: AnnouncementManageRequest,
    request: Request,
    user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
):
    """Devuelve los datos privados del aviso al dueño o con el PIN heredado."""
    return DataResponse[AnnouncementManagementResponse](
        message="Acceso de administración concedido.",
        data=service.get_for_management(
            announcement_id,
            data.admin_pin,
            get_client_ip(request),
            user.id if user else None,
        ),
    )


@router.patch(
    "/{announcement_id}",
    response_model=DataResponse[AnnouncementManagementResponse],
)
def update_announcement(
    announcement_id: UUID,
    data: AnnouncementUpdate,
    request: Request,
    user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
):
    """Actualiza campos, estado o PIN de un aviso autorizado."""
    return DataResponse[AnnouncementManagementResponse](
        message="Aviso actualizado correctamente.",
        data=service.update(
            announcement_id, data, get_client_ip(request), user.id if user else None
        ),
    )


@router.delete(
    "/{announcement_id}",
    response_model=DataResponse[None],
    status_code=status.HTTP_200_OK,
)
def delete_announcement(
    announcement_id: UUID,
    data: AnnouncementDelete,
    request: Request,
    user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Borra el aviso, primero sus archivos en Storage y luego el registro."""
    service.delete(
        announcement_id,
        data.admin_pin,
        get_client_ip(request),
        before_delete=image_service.remove_publication_files,
        owner_id=user.id if user else None,
    )
    return DataResponse[None](message="Aviso eliminado correctamente.")


@router.post(
    "/{announcement_id}/images/upload-url",
    response_model=DataResponse[AnnouncementImageUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_announcement_image_upload(
    announcement_id: UUID,
    data: AnnouncementImageUploadRequest,
    request: Request,
    user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Registra una imagen pendiente y entrega la URL firmada de carga."""
    announcement = service.get_for_management(
        announcement_id,
        data.admin_pin,
        get_client_ip(request),
        user.id if user else None,
    )
    upload = image_service.create_upload(announcement, data)
    return DataResponse[AnnouncementImageUploadResponse](
        message="Carga de imagen autorizada.", data=upload
    )


@router.post(
    "/{announcement_id}/images/{image_id}/complete",
    response_model=DataResponse[AnnouncementImageResponse],
)
def complete_announcement_image_upload(
    announcement_id: UUID,
    image_id: UUID,
    data: AnnouncementImageCompleteRequest,
    request: Request,
    user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Verifica el archivo subido a Storage y marca la imagen como lista."""
    service.get_for_management(
        announcement_id,
        data.admin_pin,
        get_client_ip(request),
        user.id if user else None,
    )
    image = image_service.complete(announcement_id, image_id)
    return DataResponse[AnnouncementImageResponse](
        message="La imagen del aviso está lista.", data=image
    )


@router.get(
    "/{announcement_id}/images",
    response_model=DataResponse[list[AnnouncementImageResponse]],
)
def list_announcement_images(
    announcement_id: UUID,
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Lista las imágenes confirmadas de un aviso activo."""
    service.get_public_by_id(announcement_id)
    return DataResponse[list[AnnouncementImageResponse]](
        message="Imágenes del aviso obtenidas correctamente.",
        data=image_service.list_public(announcement_id),
    )


@router.post(
    "/{announcement_id}/images/manage",
    response_model=DataResponse[list[AnnouncementImageManagementResponse]],
)
def list_announcement_images_for_management(
    announcement_id: UUID,
    data: AnnouncementManageRequest,
    request: Request,
    user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Lista todas las imágenes del aviso, incluidas las pendientes."""
    service.get_for_management(
        announcement_id,
        data.admin_pin,
        get_client_ip(request),
        user.id if user else None,
    )
    return DataResponse[list[AnnouncementImageManagementResponse]](
        message="Imágenes del aviso obtenidas para administración.",
        data=image_service.list_management(announcement_id),
    )


@router.delete(
    "/{announcement_id}/images/{image_id}",
    response_model=DataResponse[None],
)
def delete_announcement_image(
    announcement_id: UUID,
    image_id: UUID,
    data: AnnouncementImageDeleteRequest,
    request: Request,
    user: AuthenticatedUser | None = Depends(optional_authenticated_user),
    service: AnnouncementService = Depends(get_announcement_service),
    image_service: AnnouncementImageService = Depends(get_announcement_image_service),
):
    """Borra una imagen del aviso en Storage y en la base de datos."""
    service.get_for_management(
        announcement_id,
        data.admin_pin,
        get_client_ip(request),
        user.id if user else None,
    )
    image_service.delete(announcement_id, image_id)
    return DataResponse[None](message="Imagen del aviso eliminada correctamente.")
