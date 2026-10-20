from pydantic import BaseModel


class DataResponse[T](BaseModel):
    """Envoltura común de todas las respuestas: success, message y data."""

    success: bool = True
    message: str
    data: T | None = None
