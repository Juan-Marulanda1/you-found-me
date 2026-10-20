from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.pagination import PageData, build_page
from app.core.request import get_client_ip
from app.core.responses import DataResponse

from .dependencies import get_product_service
from .enums import ProductStatus
from .schemas import (
    ProductCreate,
    ProductDelete,
    ProductManagementResponse,
    ProductManageRequest,
    ProductResponse,
    ProductUpdate,
)
from .service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=DataResponse[ProductResponse], status_code=201)
def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    return DataResponse[ProductResponse](
        message="Product created successfully.", data=service.create(data)
    )


@router.get("", response_model=DataResponse[PageData[ProductResponse]])
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city: str | None = Query(default=None, min_length=2, max_length=100),
    category: str | None = Query(default=None, min_length=2, max_length=80),
    search: str | None = Query(default=None, min_length=2, max_length=150),
    min_price: Decimal | None = Query(default=None, gt=0),
    max_price: Decimal | None = Query(default=None, gt=0),
    service: ProductService = Depends(get_product_service),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=422, detail="min_price cannot be greater than max_price"
        )

    result = service.list(
        page=page,
        page_size=page_size,
        city=city,
        category=category,
        status=ProductStatus.ACTIVE,
        search=search,
        min_price=min_price,
        max_price=max_price,
    )
    return DataResponse[PageData[ProductResponse]](
        message="Products retrieved successfully.",
        data=build_page(
            result.items, page=page, page_size=page_size, total=result.total
        ),
    )


@router.get("/{product_id}", response_model=DataResponse[ProductResponse])
def get_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
):
    return DataResponse[ProductResponse](
        message="Product retrieved successfully.",
        data=service.get_public_by_id(product_id),
    )


@router.post(
    "/{product_id}/manage",
    response_model=DataResponse[ProductManagementResponse],
)
def get_product_for_management(
    product_id: UUID,
    data: ProductManageRequest,
    request: Request,
    service: ProductService = Depends(get_product_service),
):
    return DataResponse[ProductManagementResponse](
        message="Product management access granted.",
        data=service.get_for_management(
            product_id, data.admin_pin, get_client_ip(request)
        ),
    )


@router.patch("/{product_id}", response_model=DataResponse[ProductManagementResponse])
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    request: Request,
    service: ProductService = Depends(get_product_service),
):
    return DataResponse[ProductManagementResponse](
        message="Product updated successfully.",
        data=service.update(
            product_id,
            data,
            get_client_ip(request),
        ),
    )


@router.delete(
    "/{product_id}", response_model=DataResponse[None], status_code=status.HTTP_200_OK
)
def delete_product(
    product_id: UUID,
    data: ProductDelete,
    request: Request,
    service: ProductService = Depends(get_product_service),
):
    service.delete(
        product_id,
        data.admin_pin,
        get_client_ip(request),
    )
    return DataResponse[None](message="Product deleted successfully.")
