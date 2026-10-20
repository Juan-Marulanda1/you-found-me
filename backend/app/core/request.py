from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Devuelve la dirección del cliente resuelta por el middleware confiable.

    No leas X-Forwarded-For aquí: el servidor ASGI primero debe validar que
    la conexión procede de una dirección incluida en FORWARDED_ALLOW_IPS.
    """
    return request.client.host if request.client else "unknown"
