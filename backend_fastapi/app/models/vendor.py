from sqlalchemy import Column, Integer, String, Float, Text
from app.core.database import Base
from app.models.base import AuditMixin

class Vendor(Base, AuditMixin):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    contact_email = Column(String)
    contact_phone = Column(String)
    reliability_score = Column(Float, default=100.0)
    overpriced_tendency = Column(Float, default=0.0)
    response_speed = Column(String, default="Medium")
    notes = Column(Text)
