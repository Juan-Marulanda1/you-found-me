# this is the main file of the app, it is the entry point of the application

from fastapi import FastAPI

##import the main router
from app.api.router import router as api_router
##import the settings for the app, manage info of .env
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)

app.include_router(api_router)