from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.vendor import Vendor

router = APIRouter()

@router.get("/", summary="Get all vendors")
def get_vendors(db: Session = Depends(get_db)):
    """
    Vendor Intelligence: List all vendors with their reliability scores.
    """
    vendors = db.query(Vendor).all()
    return vendors

@router.post("/", summary="Create new vendor")
def create_vendor(name: str, specialty_niche: str, db: Session = Depends(get_db)):
    """
    Register a new vendor in the system.
    """
    vendor = db.query(Vendor).filter(Vendor.name == name).first()
    if vendor:
        raise HTTPException(status_code=400, detail="Vendor already exists")
        
    new_vendor = Vendor(name=name, contact_email=f"info@{name.lower().replace(' ', '')}.com")
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor
