from pydantic import BaseModel


class DataResponse[T](BaseModel):
    success: bool = True
    message: str
    data: T | None = None
