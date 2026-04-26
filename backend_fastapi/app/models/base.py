from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime

class AuditMixin:
    """
    Mixin class to add Audit Trail fields to any SQLAlchemy model.
    Wajib untuk Enterprise Corporate Compliance.
    """
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def created_by_id(cls):
        return Column(Integer, nullable=True) # Will point to User.id

    @declared_attr
    def updated_by_id(cls):
        return Column(Integer, nullable=True) # Will point to User.id
