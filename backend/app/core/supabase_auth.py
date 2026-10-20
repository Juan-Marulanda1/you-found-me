import json
import logging
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.invitation import PublicationInvitation
from app.database.owner import PublicationOwner
from app.database.session import get_db

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identidad verificada por Supabase Auth para la solicitud actual."""

    id: UUID
    email: str


def _auth_url(path: str) -> str:
    """Construye la URL de Supabase Auth o responde 503 si no está configurado."""
    base_url = settings.SUPABASE_URL.rstrip("/")
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account authentication is not configured.",
        )
    return f"{base_url}/auth/v1/{path.lstrip('/')}"


def get_authenticated_user(access_token: str) -> AuthenticatedUser:
    """Valida el token con Supabase Auth y exige un correo confirmado y no anónimo."""
    publishable_key = settings.SUPABASE_PUBLISHABLE_KEY.get_secret_value()
    if not publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account authentication is not configured.",
        )

    # Supabase valida el token; no se confía en datos decodificados por el cliente.
    request = Request(
        _auth_url("user"),
        headers={
            "apikey": publishable_key,
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=5) as response:
            data = json.loads(response.read())
    except HTTPError as error:
        if error.code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sign in with a verified account to continue.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        logger.warning("Supabase Auth user verification failed (%s)", error.code)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account authentication is temporarily unavailable.",
        ) from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        logger.warning("Supabase Auth is unavailable during token verification")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account authentication is temporarily unavailable.",
        ) from error

    try:
        user_id = UUID(data["id"])
        email = str(data["email"]).strip().lower()
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A verified account is required.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    if (
        not email
        or data.get("is_anonymous")
        or not (data.get("email_confirmed_at") or data.get("confirmed_at"))
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirm your email before managing publications.",
        )
    return AuthenticatedUser(id=user_id, email=email)


def require_authenticated_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Dependencia para rutas privadas: sesión válida y correo invitado."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in with a verified account to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in with a verified account to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_authenticated_user(token)
    # La sesión válida también debe pertenecer a un correo que recibió invitación.
    if db.get(PublicationInvitation, user.email) is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account was not invited to publish.",
        )
    # Crea el registro local solo una vez, al primer acceso autenticado.
    if db.get(PublicationOwner, user.id) is None:
        db.add(PublicationOwner(id=user.id))
        try:
            db.commit()
        except Exception as error:
            db.rollback()
            logger.exception("Failed to register an invited publication account")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Account authentication is temporarily unavailable.",
            ) from error
    return user


def optional_authenticated_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> AuthenticatedUser | None:
    """Igual que require_authenticated_user, pero admite solicitudes sin sesión."""
    if authorization is None:
        return None
    return require_authenticated_user(authorization, db)


def invite_account(email: str) -> None:
    """Pide a Supabase Auth el correo de invitación y traduce sus errores a HTTP."""
    admin_key = settings.supabase_admin_key
    if not admin_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account invitations are not configured.",
        )

    # El enlace de Supabase debe volver a una URL autorizada del frontend.
    query = urlencode(
        {"redirect_to": settings.SUPABASE_AUTH_REDIRECT_URL}
        if settings.SUPABASE_AUTH_REDIRECT_URL
        else {}
    )
    path = "invite" + (f"?{query}" if query else "")
    request = Request(
        _auth_url(path),
        data=json.dumps({"email": email}).encode(),
        headers={
            "apikey": admin_key,
            "Authorization": f"Bearer {admin_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:
            response.read()
    except HTTPError as error:
        if error.code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many account invitations. Try again later.",
            ) from error
        if error.code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "An account already exists for this email. Request a sign-in link."
                ),
            ) from error
        if error.code in (400, 422):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="This email address cannot be invited.",
            ) from error
        logger.error("Supabase Auth invite request failed (%s)", error.code)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account invitations are temporarily unavailable.",
        ) from error
    except (URLError, TimeoutError) as error:
        logger.warning("Supabase Auth is unavailable during account invitation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account invitations are temporarily unavailable.",
        ) from error
