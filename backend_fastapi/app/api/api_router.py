from fastapi import APIRouter
from app.api.endpoints import auth, vendor, rab

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(vendor.router, prefix="/vendors", tags=["Vendor Intelligence"])
api_router.include_router(rab.router, prefix="/rab", tags=["RAB Generator"])
