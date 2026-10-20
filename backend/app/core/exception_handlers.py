import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.problems import (
    problem_response,
    validation_field_errors,
    validation_summary,
)

logger = logging.getLogger(__name__)

# Errores que el propio framework genera (ruta inexistente, método no admitido,
# cuerpo ilegible...). Su texto original está en inglés, así que se reemplaza.
_FRAMEWORK_ERRORS = {
    400: ("bad_request", "La solicitud no tiene un formato válido."),
    404: ("not_found", "La ruta solicitada no existe."),
    405: ("method_not_allowed", "El método HTTP no está permitido en esta ruta."),
    413: ("payload_too_large", "El contenido enviado es demasiado grande."),
    415: ("unsupported_media_type", "El tipo de contenido no es compatible."),
}
_FRAMEWORK_DEFAULT = ("http_error", "No pudimos procesar la solicitud.")


def register_exception_handlers(app: FastAPI):
    """Convierte cualquier error en una respuesta Problem Details (RFC 9457)."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        # Errores del dominio: ya traen código y mensaje en español.
        return problem_response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            detail=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Cubre también fastapi.HTTPException, que hereda de la de Starlette.
        code, detail = _FRAMEWORK_ERRORS.get(exc.status_code, _FRAMEWORK_DEFAULT)
        return problem_response(
            request,
            status_code=exc.status_code,
            code=code,
            detail=detail,
            # Conserva encabezados como Allow (405) o WWW-Authenticate (401).
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request, exc: RequestValidationError
    ):
        field_errors = validation_field_errors(exc.errors())
        return problem_response(
            request,
            status_code=422,
            code="validation_error",
            detail=validation_summary(field_errors),
            errors=field_errors,
        )

    # Último recurso: registra el detalle técnico y devuelve un mensaje genérico
    # para no exponer información interna.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Error no controlado al procesar %s", request.url.path)
        return problem_response(
            request,
            status_code=500,
            code="internal_error",
            detail="Ocurrió un error inesperado. Inténtalo de nuevo más tarde.",
        )
