import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Konfigurasi Keamanan Enterprise
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-enterprise-key-kalsel-ai-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 Hari

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dummy Rate Limiter In-Memory (Untuk Skala Awal) ---
# Di produksi, gunakan Redis.
rate_limit_db = {}
MAX_REQUESTS_PER_MINUTE = 30

def check_rate_limit(client_ip: str):
    current_time = datetime.utcnow()
    minute_key = current_time.strftime("%Y-%m-%d %H:%M")
    key = f"{client_ip}:{minute_key}"
    
    count = rate_limit_db.get(key, 0)
    if count >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate Limit Exceeded. Terlalu banyak request.")
    
    rate_limit_db[key] = count + 1
    return True
