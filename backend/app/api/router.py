from fastapi import APIRouter, Depends

from app.core.publication_access import require_publication_creation_key
from app.core.responses import DataResponse
from app.modules.announcement.routes import router as announcement_router
from app.modules.product.routes import router as product_router

router = APIRouter()


@router.post(
    "/publication-access/verify",
    response_model=DataResponse[bool],
    dependencies=[Depends(require_publication_creation_key)],
)
def verify_publication_access():
    return DataResponse[bool](message="Publication access granted.", data=True)


router.include_router(announcement_router)
router.include_router(product_router)
