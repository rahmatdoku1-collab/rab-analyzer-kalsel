from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json

# Menggunakan Supabase PostgreSQL (Production)
DATABASE_URL = "postgresql://postgres:eqMGCoarVb6uR1rJ@db.tqmumaplemfkjomodujb.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Security & Multi-Tenant Models ---
class Company(Base):
    __tablename__ = "companies"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    subscription_plan = Column(String, default="Starter")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="company")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    company_id = Column(String, ForeignKey("companies.id"))
    role = Column(String, default="user") # 'admin' or 'user'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="users")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    resource = Column(String)
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class RateLimit(Base):
    __tablename__ = "rate_limits"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    api_calls_count = Column(Integer, default=0)
    reset_time = Column(DateTime)

from pgvector.sqlalchemy import Vector
from sqlalchemy import text

# --- AI Intelligence Models ---
class PromptLog(Base):
    __tablename__ = "prompt_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    company_id = Column(String, index=True)
    module_name = Column(String, index=True)
    prompt_text = Column(Text)
    output_result = Column(Text)
    
    # Menggunakan tipe Vector dari pgvector (dimension = 1536 untuk OpenAI)
    embedding = Column(Vector(1536)) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    feedbacks = relationship("UserFeedback", back_populates="prompt_log")
    edits = relationship("EditLearning", back_populates="prompt_log")

class UserFeedback(Base):
    __tablename__ = "user_feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    prompt_log_id = Column(Integer, ForeignKey("prompt_logs.id"))
    rating = Column(String)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prompt_log = relationship("PromptLog", back_populates="feedbacks")

class EditLearning(Base):
    __tablename__ = "edit_learning"
    id = Column(Integer, primary_key=True, index=True)
    prompt_log_id = Column(Integer, ForeignKey("prompt_logs.id"))
    item_name = Column(String)
    old_value = Column(Float)
    new_value = Column(Float)
    change_type = Column(String)
    region = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prompt_log = relationship("PromptLog", back_populates="edits")

def init_learning_db():
    try:
        # Create vector extension
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            
        # Create all tables including vector column
        Base.metadata.create_all(bind=engine)
        print("Database Enterprise berhasil diinisialisasi (dengan pgvector)")
    except Exception as e:
        print(f"PostgreSQL Connection Error: Pastikan psycopg2-binary dan pgvector terinstall. Detail: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
