from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.responses import DataResponse


def _build_error_response(message: str, status_code: int):
    return JSONResponse(
        status_code=status_code,
        content=DataResponse[None](success=False, message=message).model_dump(),
    )


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ):
        return _build_error_response(exc.detail, exc.status_code)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return _build_error_response(message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        message = (
            "; ".join(error["msg"] for error in exc.errors()) or "Validation error"
        )
        return _build_error_response(message, 422)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ):
        return _build_error_response("Internal server error", 500)
