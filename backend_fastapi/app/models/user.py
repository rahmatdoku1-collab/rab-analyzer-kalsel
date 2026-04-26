from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import AuditMixin

class SubscriptionTier(str, enum.Enum):
    FREE = "Free"
    STARTER = "Starter"
    GROWTH = "Growth"
    ENTERPRISE = "Enterprise"
    CUSTOM = "Custom"

class UserRole(str, enum.Enum):
    SUPERADMIN = "Superadmin"
    COMPANY_OWNER = "Company Owner"
    PROCUREMENT_MANAGER = "Procurement Manager"
    ANALYST = "Analyst"
    VIEWER = "Viewer"

class Company(Base, AuditMixin):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    subscription_tier = Column(String, default=SubscriptionTier.FREE.value)
    is_active = Column(Boolean, default=True)
    logo_url = Column(String, nullable=True) # For White-labeling
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")

class User(Base, AuditMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.VIEWER.value)
    is_active = Column(Boolean, default=True)
    
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    company = relationship("Company", back_populates="users")
