from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    contact_info = Column(String)
    specialty_niche = Column(String) # e.g., GIS, Survey, Alat Berat
    reliability_score = Column(Float, default=100.0) # 0-100 rating
    overpriced_tendency = Column(Float, default=0.0) # percentage
    response_speed = Column(String, default="Medium")
    created_at = Column(DateTime, default=datetime.utcnow)

    # In future, can link to Tenders to track win/loss history
