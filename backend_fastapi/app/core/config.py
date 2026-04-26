import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Procurement Enterprise API"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Database
    # Default to sqlite for local dev if Postgres URL is not provided
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise_data.db")
    
    # OpenRouter AI
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    class Config:
        case_sensitive = True

settings = Settings()
