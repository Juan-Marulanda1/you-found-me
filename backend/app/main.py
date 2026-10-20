from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.problems import PROBLEM_RESPONSES, use_problem_media_type

# Punto de entrada ASGI: configura metadatos, CORS, errores y rutas versionadas.
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.PROJECT_DESCRIPTION,
    debug=settings.DEBUG,
)

# Restringe las solicitudes de navegador a los orígenes configurados para esta API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Publication-Key", "Authorization"],
)

register_exception_handlers(app)

app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
    # Sustituye el 422 por defecto de FastAPI por el esquema Problem Details.
    responses=PROBLEM_RESPONSES,
)

_build_openapi = app.openapi


def openapi_with_problem_details() -> dict:
    """Genera OpenAPI declarando los errores con su media type real."""
    return use_problem_media_type(_build_openapi())


app.openapi = openapi_with_problem_details
