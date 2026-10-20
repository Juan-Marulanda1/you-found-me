from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.pagination import PageData, build_page
from app.core.request import get_client_ip
from app.core.responses import DataResponse

from .dependencies import get_product_image_service, get_product_service
from .enums import ProductStatus
from .image_schemas import (
    ProductImageCompleteRequest,
    ProductImageDeleteRequest,
    ProductImageManagementResponse,
    ProductImageResponse,
    ProductImageUploadRequest,
    ProductImageUploadResponse,
)
from .image_service import ProductImageService
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
    image_service: ProductImageService = Depends(get_product_image_service),
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
    cover_images = image_service.list_cover_images(
        [product.id for product in result.items]
    )
    items = [
        ProductResponse.model_validate(product).model_copy(
            update={"cover_image": cover_images.get(product.id)}
        )
        for product in result.items
    ]
    return DataResponse[PageData[ProductResponse]](
        message="Products retrieved successfully.",
        data=build_page(items, page=page, page_size=page_size, total=result.total),
    )


@router.get("/{product_id}", response_model=DataResponse[ProductResponse])
def get_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
    image_service: ProductImageService = Depends(get_product_image_service),
):
    product = service.get_public_by_id(product_id)
    cover_image = image_service.list_cover_images([product.id]).get(product.id)
    return DataResponse[ProductResponse](
        message="Product retrieved successfully.",
        data=ProductResponse.model_validate(product).model_copy(
            update={"cover_image": cover_image}
        ),
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
    image_service: ProductImageService = Depends(get_product_image_service),
):
    service.delete(
        product_id,
        data.admin_pin,
        get_client_ip(request),
        before_delete=image_service.remove_product_files,
    )
    return DataResponse[None](message="Product deleted successfully.")


@router.post(
    "/{product_id}/images/upload-url",
    response_model=DataResponse[ProductImageUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_product_image_upload(
    product_id: UUID,
    data: ProductImageUploadRequest,
    request: Request,
    product_service: ProductService = Depends(get_product_service),
    image_service: ProductImageService = Depends(get_product_image_service),
):
    product = product_service.get_for_management(
        product_id, data.admin_pin, get_client_ip(request)
    )
    upload = image_service.create_upload(product, data)
    return DataResponse[ProductImageUploadResponse](
        message="Signed image upload created.", data=upload
    )


@router.post(
    "/{product_id}/images/{image_id}/complete",
    response_model=DataResponse[ProductImageResponse],
)
def complete_product_image_upload(
    product_id: UUID,
    image_id: UUID,
    data: ProductImageCompleteRequest,
    request: Request,
    product_service: ProductService = Depends(get_product_service),
    image_service: ProductImageService = Depends(get_product_image_service),
):
    product_service.get_for_management(
        product_id, data.admin_pin, get_client_ip(request)
    )
    image = image_service.complete(product_id, image_id)
    return DataResponse[ProductImageResponse](
        message="Product image is ready.", data=image
    )


@router.get(
    "/{product_id}/images",
    response_model=DataResponse[list[ProductImageResponse]],
)
def list_product_images(
    product_id: UUID,
    product_service: ProductService = Depends(get_product_service),
    image_service: ProductImageService = Depends(get_product_image_service),
):
    product_service.get_public_by_id(product_id)
    return DataResponse[list[ProductImageResponse]](
        message="Product images retrieved successfully.",
        data=image_service.list_public(product_id),
    )


@router.post(
    "/{product_id}/images/manage",
    response_model=DataResponse[list[ProductImageManagementResponse]],
)
def list_product_images_for_management(
    product_id: UUID,
    data: ProductImageCompleteRequest,
    request: Request,
    product_service: ProductService = Depends(get_product_service),
    image_service: ProductImageService = Depends(get_product_image_service),
):
    product_service.get_for_management(
        product_id, data.admin_pin, get_client_ip(request)
    )
    return DataResponse[list[ProductImageManagementResponse]](
        message="Product images retrieved for management.",
        data=image_service.list_management(product_id),
    )


@router.delete(
    "/{product_id}/images/{image_id}",
    response_model=DataResponse[None],
)
def delete_product_image(
    product_id: UUID,
    image_id: UUID,
    data: ProductImageDeleteRequest,
    request: Request,
    product_service: ProductService = Depends(get_product_service),
    image_service: ProductImageService = Depends(get_product_image_service),
):
    product_service.get_for_management(
        product_id, data.admin_pin, get_client_ip(request)
    )
    image_service.delete(product_id, image_id)
    return DataResponse[None](message="Product image deleted successfully.")
