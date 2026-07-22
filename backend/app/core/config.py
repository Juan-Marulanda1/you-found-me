from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "You Found Me API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    database_url: str 
    class Config:
        env_file = ".env"
        extra = "ignore"
        

settings = Settings()