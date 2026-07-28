# this is the main file of the app, it is the entry point of the application

from fastapi import FastAPI

##import the main router
from app.api.router import router as api_router
##import the settings for the app, manage info of .env
from app.core.config import settings

from app.core.exception_handlers import register_exception_handlers

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)

register_exception_handlers(app)
app.include_router(api_router)