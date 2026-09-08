from fastapi import APIRouter

### import the routers from modules
from app.modules.announcement.routes import router as announcement_router

##create main router
router = APIRouter()

## include the ther router from modules
router.include_router(announcement_router)
