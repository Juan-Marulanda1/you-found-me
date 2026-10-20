from fastapi import APIRouter

from app.modules.account.routes import router as account_router
from app.modules.announcement.routes import router as announcement_router
from app.modules.product.routes import router as product_router

# Router raíz de la API. main.py lo monta bajo API_PREFIX (por defecto /api/v1).
# Para agregar un dominio, crea su módulo en app/modules e inclúyelo aquí.
router = APIRouter()

router.include_router(announcement_router)
router.include_router(product_router)
router.include_router(account_router)
