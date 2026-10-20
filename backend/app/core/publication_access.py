import hmac

from fastapi import Header

from app.core.config import settings
from app.core.exceptions import (
    InvalidInvitationKeyError,
    InvitationKeyNotConfiguredError,
)


def require_publication_creation_key(
    x_publication_key: str | None = Header(default=None, alias="X-Publication-Key"),
) -> None:
    """Dependencia que exige X-Publication-Key igual a PUBLICATION_CREATION_KEY."""
    configured_key = settings.PUBLICATION_CREATION_KEY.get_secret_value()
    if not configured_key:
        raise InvitationKeyNotConfiguredError()

    # La comparación tarda lo mismo aunque coincida parcialmente el prefijo.
    if not x_publication_key or not hmac.compare_digest(
        x_publication_key, configured_key
    ):
        raise InvalidInvitationKeyError()
