from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, date
from core.database import Base

class HargaLokal(Base):
    __tablename__ = "harga_lokal"

    id = Column(Integer, primary_key=True, index=True)
    kategori = Column(String, index=True)
    nama_item = Column(String, index=True)
    satuan = Column(String)
    harga_min = Column(Float)
    harga_max = Column(Float)
    harga_rekomendasi = Column(Float)
    sumber_1 = Column(String)
    sumber_2 = Column(String)
    sumber_3 = Column(String)
    metode_perhitungan = Column(String)
    lokasi = Column(String)
    confidence_score = Column(Integer)
    update_terakhir = Column(String, default=lambda: date.today().isoformat())
    catatan = Column(Text)

    price_history = relationship("PriceHistory", back_populates="harga_lokal", cascade="all, delete")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    harga_lokal_id = Column(Integer, ForeignKey("harga_lokal.id"))
    harga_baru = Column(Float)
    sumber = Column(String)
    tanggal = Column(String, default=lambda: date.today().isoformat())

    harga_lokal = relationship("HargaLokal", back_populates="price_history")

class MarketNews(Base):
    __tablename__ = "market_news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    link = Column(String)
    published_date = Column(String)
    category = Column(String)
    impact_summary = Column(Text)
    urgency = Column(String)
    recommended_action = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
