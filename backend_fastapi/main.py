import sys
import os

# Menambahkan parent directory ke PYTHONPATH agar bisa import folder 'core' dan 'backend_fastapi'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from core.models_learning import init_learning_db
from backend_fastapi.routers import learning
import uvicorn
import threading

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request
from backend_fastapi.core.security import check_rate_limit

# Inisialisasi Database (PostgreSQL)
init_learning_db()

app = FastAPI(title="AI Procurement Backend API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    try:
        check_rate_limit(client_ip)
    except Exception as e:
        return JSONResponse(status_code=429, content={"detail": str(e)})
    return await call_next(request)

# Register Routers
from backend_fastapi.routers import intelligence

app.include_router(learning.router, prefix="/api/v1/learning", tags=["Self-Learning"])
app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["Intelligence Engines"])

@app.get("/")
def read_root():
    return {"message": "Enterprise API is running. Ready to learn!"}

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    run_server()
