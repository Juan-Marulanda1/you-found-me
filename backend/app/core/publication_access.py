import hmac

from fastapi import Header, HTTPException

from app.core.config import settings


def require_publication_creation_key(
    x_publication_key: str | None = Header(default=None, alias="X-Publication-Key"),
) -> None:
    configured_key = settings.PUBLICATION_CREATION_KEY.get_secret_value()
    if not configured_key:
        raise HTTPException(
            status_code=503,
            detail="Publication creation is not configured.",
        )

    if not x_publication_key or not hmac.compare_digest(
        x_publication_key, configured_key
    ):
        raise HTTPException(status_code=403, detail="Invalid publication access key.")
