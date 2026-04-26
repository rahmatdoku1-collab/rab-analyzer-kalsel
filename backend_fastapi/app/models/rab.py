from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import AuditMixin

class ApprovalState(str, enum.Enum):
    DRAFT = "Draft"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class Project(Base, AuditMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    total_budget = Column(Float, default=0.0)
    approval_state = Column(String, default=ApprovalState.DRAFT.value)
    risk_score = Column(String, nullable=True) # AI Generated Risk
    
    company = relationship("Company", back_populates="projects")
    items = relationship("ProjectItem", back_populates="project", cascade="all, delete-orphan")
    tenders = relationship("Tender", back_populates="project", cascade="all, delete-orphan")

class ProjectItem(Base, AuditMixin):
    __tablename__ = "project_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    item_name = Column(String, index=True, nullable=False)
    volume = Column(Float, default=1.0)
    satuan = Column(String)
    harga_satuan = Column(Float)
    total_harga = Column(Float)
    
    # Audit Analysis Data
    status_harga = Column(String) # OVERPRICED, NORMAL, UNDERBUDGET
    harga_rekomendasi_ai = Column(Float)
    potensi_penghematan = Column(Float)

    project = relationship("Project", back_populates="items")

class Tender(Base, AuditMixin):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    total_bid_amount = Column(Float)
    approval_state = Column(String, default=ApprovalState.DRAFT.value)
    
    project = relationship("Project", back_populates="tenders")
    vendor = relationship("Vendor")

class VendorSubmission(Base, AuditMixin):
    __tablename__ = "vendor_submissions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    round_number = Column(Integer, default=1)
    total_bid = Column(Float)
    final_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    is_winner = Column(Boolean, default=False)
    
    items = relationship("SubmissionItem", back_populates="submission", cascade="all, delete-orphan")

class SubmissionItem(Base, AuditMixin):
    __tablename__ = "submission_items"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("vendor_submissions.id"), nullable=False)
    item_name = Column(String, index=True)
    volume = Column(Float)
    satuan = Column(String)
    harga_satuan = Column(Float)
    total_harga = Column(Float)
    
    # Analysis fields
    is_anomalous = Column(Boolean, default=False)
    markup_percentage = Column(Float, default=0.0)
    fraud_signal = Column(String, nullable=True) # e.g. "HIDDEN_MARKUP"

    submission = relationship("VendorSubmission", back_populates="items")

class CollusionFlag(Base, AuditMixin):
    __tablename__ = "collusion_flags"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    vendor_1_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    vendor_2_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    risk_level = Column(String) # LOW, MEDIUM, HIGH
    reason = Column(Text) # "Identical pricing in 80% items"

class NegotiationLog(Base, AuditMixin):
    __tablename__ = "negotiation_logs"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("vendor_submissions.id"), nullable=False)
    target_savings = Column(Float)
    ai_script = Column(Text)
    status = Column(String, default="DRAFT") # SENT, ACCEPTED, REJECTED

class ApprovalLog(Base, AuditMixin):
    __tablename__ = "approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    approver_role = Column(String) # Staff, Manager, Director
    status = Column(String) # PENDING, APPROVED, REJECTED
    comments = Column(Text)
