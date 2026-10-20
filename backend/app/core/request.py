from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Return the peer address resolved by Uvicorn's trusted proxy middleware.

    Do not read X-Forwarded-For here: the ASGI server must first validate that
    the connecting peer is in FORWARDED_ALLOW_IPS.
    """
    return request.client.host if request.client else "unknown"
