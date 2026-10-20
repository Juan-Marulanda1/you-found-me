import logging
from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.core.publication_access import require_publication_creation_key
from app.core.request import get_client_ip
from app.core.responses import DataResponse
from app.core.supabase_auth import (
    AuthenticatedUser,
    invite_account,
    require_authenticated_user,
)
from app.database.invitation import PublicationInvitation
from app.database.session import get_db
from app.modules.announcement.dependencies import (
    get_announcement_image_service,
    get_announcement_service,
)
from app.modules.announcement.image_service import AnnouncementImageService
from app.modules.announcement.schemas import AnnouncementManagementResponse
from app.modules.announcement.service import AnnouncementService
from app.modules.product.dependencies import (
    get_product_image_service,
    get_product_service,
)
from app.modules.product.image_service import ProductImageService
from app.modules.product.schemas import ProductManagementResponse
from app.modules.product.service import ProductService
from app.modules.publication.image_schemas import PublicationImageResponse

router = APIRouter(prefix="/account-access", tags=["Account access"])
logger = logging.getLogger(__name__)


class AccountInvitationRequest(BaseModel):
    """Correo a invitar; se normaliza en minúsculas."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        local, separator, domain = email.rpartition("@")
        if (
            not separator
            or not local
            or "." not in domain
            or any(c.isspace() for c in email)
        ):
            raise ValueError("Enter a valid email address.")
        return email


class LegacyPublicationCandidate(BaseModel):
    """Resumen de una publicación antigua que la cuenta puede reclamar."""

    kind: Literal["product", "announcement"]
    id: UUID
    title: str
    category: str
    description: str
    city: str
    status: str
    created_at: datetime
    cover_image: PublicationImageResponse | None = None


class OwnedPublicationsResponse(BaseModel):
    """Publicaciones propias y reclamables de la cuenta."""

    products: list[ProductManagementResponse]
    announcements: list[AnnouncementManagementResponse]
    claimable: list[LegacyPublicationCandidate]


class ClaimPublicationRequest(BaseModel):
    """Datos para reclamar una publicación antigua con su PIN."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["product", "announcement"]
    publication_id: UUID
    admin_pin: str = Field(min_length=4, max_length=12, pattern=r"^\d{4,12}$")


@router.post(
    "/invite",
    response_model=DataResponse[bool],
    dependencies=[Depends(require_publication_creation_key)],
    status_code=status.HTTP_202_ACCEPTED,
)
def request_account_invitation(
    data: AccountInvitationRequest,
    db: Session = Depends(get_db),
):
    """Valida la clave de invitación y autoriza el correo para publicar."""
    # El correo se autoriza aunque Supabase indique que la cuenta ya existía.
    try:
        invite_account(data.email)
    except HTTPException as error:
        if error.status_code != status.HTTP_409_CONFLICT:
            raise

    if db.get(PublicationInvitation, data.email) is None:
        db.add(PublicationInvitation(email=data.email))
        try:
            db.commit()
        except Exception as error:
            db.rollback()
            logger.exception("Failed to register an approved account invitation")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Account invitations are temporarily unavailable.",
            ) from error
    return DataResponse[bool](
        message="Invitation request accepted. Check your email or sign in.", data=True
    )


@router.get("/me/publications", response_model=DataResponse[OwnedPublicationsResponse])
def get_my_publications(
    user: AuthenticatedUser = Depends(require_authenticated_user),
    product_service: ProductService = Depends(get_product_service),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
    product_image_service: ProductImageService = Depends(get_product_image_service),
    announcement_image_service: AnnouncementImageService = Depends(
        get_announcement_image_service
    ),
):
    """Lista las publicaciones de la cuenta y las antiguas que puede reclamar."""
    # Combina publicaciones propias y antiguas sin dueño cuyo correo coincide.
    products = product_service.list_by_owner(user.id)
    announcements = announcement_service.list_by_owner(user.id)
    legacy_products = product_service.list_claimable_by_email(user.email)
    legacy_announcements = announcement_service.list_claimable_by_email(user.email)
    product_covers = product_image_service.list_cover_images(
        [item.id for item in [*products, *legacy_products]]
    )
    announcement_covers = announcement_image_service.list_cover_images(
        [item.id for item in [*announcements, *legacy_announcements]]
    )
    claimable = []
    for item in legacy_products:
        claimable.append(
            LegacyPublicationCandidate(
                kind="product",
                id=item.id,
                title=item.title,
                category=item.category,
                description=item.description,
                city=item.city,
                status=item.status,
                created_at=item.created_at,
                cover_image=product_covers.get(item.id),
            )
        )
    for item in legacy_announcements:
        claimable.append(
            LegacyPublicationCandidate(
                kind="announcement",
                id=item.id,
                title=item.title,
                category=item.category,
                description=item.description,
                city=item.city,
                status=item.status,
                created_at=item.created_at,
                cover_image=announcement_covers.get(item.id),
            )
        )
    return DataResponse[OwnedPublicationsResponse](
        message="Your publications were retrieved.",
        data=OwnedPublicationsResponse(
            products=[
                ProductManagementResponse.model_validate(item).model_copy(
                    update={"cover_image": product_covers.get(item.id)}
                )
                for item in products
            ],
            announcements=[
                AnnouncementManagementResponse.model_validate(item).model_copy(
                    update={"cover_image": announcement_covers.get(item.id)}
                )
                for item in announcements
            ],
            claimable=claimable,
        ),
    )


@router.post("/me/claim", response_model=DataResponse[bool])
def claim_legacy_publication(
    data: ClaimPublicationRequest,
    request: Request,
    user: AuthenticatedUser = Depends(require_authenticated_user),
    product_service: ProductService = Depends(get_product_service),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    """Vincula una publicación antigua a la cuenta tras validar su PIN."""
    if data.kind == "product":
        product_service.claim(
            data.publication_id,
            data.admin_pin,
            user.id,
            get_client_ip(request),
        )
    else:
        announcement_service.claim(
            data.publication_id,
            data.admin_pin,
            user.id,
            get_client_ip(request),
        )
    return DataResponse[bool](message="Publication claimed successfully.", data=True)
