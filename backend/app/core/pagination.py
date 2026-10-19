from math import ceil

from pydantic import BaseModel


class PageData[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int


def build_page[T](
    items: list[T], *, page: int, page_size: int, total: int
) -> PageData[T]:
    return PageData[T](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=ceil(total / page_size) if total else 0,
    )
