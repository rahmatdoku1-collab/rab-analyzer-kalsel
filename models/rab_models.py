from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    name = Column(String, index=True)
    total_budget = Column(Float)
    status = Column(String, default="Draft")
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="projects")
    items = relationship("ProjectItem", back_populates="project", cascade="all, delete")
    tenders = relationship("Tender", back_populates="project", cascade="all, delete")

class ProjectItem(Base):
    __tablename__ = "project_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    item_name = Column(String, index=True)
    kategori = Column(String)
    volume = Column(Float)
    satuan = Column(String)
    harga_satuan = Column(Float)
    total_harga = Column(Float)
    status = Column(String)
    harga_rekomendasi = Column(Float)
    potensi_penghematan = Column(Float)
    match_score = Column(Float)
    sumber_referensi = Column(String)

    project = relationship("Project", back_populates="items")

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    vendor_name = Column(String, index=True)
    total_bid_amount = Column(Float)
    risk_score = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="tenders")
