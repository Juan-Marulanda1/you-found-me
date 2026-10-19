from fastapi import APIRouter

from app.modules.announcement.routes import router as announcement_router
from app.modules.product.routes import router as product_router

router = APIRouter()
router.include_router(announcement_router)
router.include_router(product_router)
