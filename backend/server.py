import argparse

import uvicorn

from app.core.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicia la API de You Found Me")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    # Uvicorn solo confía en encabezados reenviados de FORWARDED_ALLOW_IPS; así
    # get_client_ip obtiene la IP real para limitar intentos de PIN.
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=args.reload,
        proxy_headers=True,
        forwarded_allow_ips=settings.FORWARDED_ALLOW_IPS,
    )


if __name__ == "__main__":
    main()
