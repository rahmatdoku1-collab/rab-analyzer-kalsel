from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.base import AuditMixin

class NewsSource(Base, AuditMixin):
    __tablename__ = "news_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    url = Column(String, unique=True, nullable=False)
    source_type = Column(String) # RSS, HTML, API
    category = Column(String) # Government, Local Media, Industry
    region = Column(String) # Nasional, Kalsel, Tabalong, dll
    is_active = Column(Boolean, default=True)
    last_crawled_at = Column(DateTime, nullable=True)
    health_score = Column(Float, default=100.0) # Turun jika gagal crawling berulang kali

    articles = relationship("NewsArticle", back_populates="source", cascade="all, delete-orphan")

class NewsArticle(Base, AuditMixin):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("news_sources.id"))
    title = Column(String, unique=True, index=True, nullable=False)
    link = Column(String, unique=True, nullable=False)
    published_date = Column(DateTime)
    
    # AI Understanding Fields
    kategori = Column(String, index=True) # Tender Baru, Harga Solar, Regulasi, dll
    wilayah = Column(String, index=True)
    dampak_biaya = Column(Text)
    dampak_tender = Column(Text)
    urgensi = Column(String) # High, Medium, Low
    sentimen = Column(String) # Positive, Negative, Neutral
    skor_penting = Column(Integer) # 1-100
    aksi_saran = Column(Text)
    sektor_industri = Column(String)
    deadline_date = Column(DateTime, nullable=True)

    source = relationship("NewsSource", back_populates="articles")

class Watchlist(Base, AuditMixin):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    keyword = Column(String, nullable=False) # e.g. "Tabalong", "Drone", "Solar"
    category_filter = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class NewsAlert(Base, AuditMixin):
    __tablename__ = "news_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    article_id = Column(Integer, ForeignKey("news_articles.id"))
    delivery_method = Column(String) # Telegram, WA, Email
    status = Column(String) # Sent, Failed, Pending
    sent_at = Column(DateTime, nullable=True)
