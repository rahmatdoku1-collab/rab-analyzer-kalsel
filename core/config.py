import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Procurement Intelligence Kalsel"
    VERSION: str = "2.0.0"
    
    # Database
    # Secara default menggunakan SQLite lokal untuk memudahkan development
    # Ubah di .env menjadi: DATABASE_URL=postgresql://user:password@localhost/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/harga_lokal_v2.db")
    
    # API Keys
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # Regional Config
    KALSEL_INDEX: float = 0.85

settings = Settings()
