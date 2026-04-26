from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from app.core.database import engine, Base
# Import all models here to ensure they are registered with Base before create_all
from app.models import user, vendor, rab, osint

Base.metadata.create_all(bind=engine)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, change to specific origins like Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API. Access /docs for Swagger UI."}

from app.api.api_router import api_router

app.include_router(api_router, prefix=settings.API_V1_STR)
