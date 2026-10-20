from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers

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
)
