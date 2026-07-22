from fastapi import APIRouter

### import the routers from modules
from app.modules.health.routes import router as helth_router
from app.modules.announcement.routes import router as announcement_router

##create main router
router = APIRouter()

## include the ther router from modules 
router.include_router(helth_router)
router.include_router(announcement_router)