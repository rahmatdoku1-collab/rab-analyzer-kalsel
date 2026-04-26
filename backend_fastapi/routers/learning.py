import json
import logging
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from core.models_learning import PromptLog, UserFeedback, EditLearning, get_db

# Mocking OpenAI for embedding if needed, or use actual API
import openai

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Pydantic Schemas ---
class PromptLogCreate(BaseModel):
    user_id: str
    company_id: str
    module_name: str
    prompt_text: str
    output_result: str
    api_key: Optional[str] = None # Untuk generate embedding

class FeedbackCreate(BaseModel):
    prompt_log_id: int
    rating: str
    comment: Optional[str] = None

class EditLearningCreate(BaseModel):
    prompt_log_id: int
    item_name: str
    old_value: float
    new_value: float
    change_type: str
    region: Optional[str] = None

# --- Helper Functions ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity

import openai
import os
from pgvector.sqlalchemy import Vector

def get_embedding(text: str, api_key: str):
    # Gunakan kunci API OpenAI asli (Bukan OpenRouter) karena OpenRouter tidak mendukung embedding secara native.
    actual_api_key = os.getenv("OPENAI_API_KEY", api_key)
    try:
        client = openai.OpenAI(api_key=actual_api_key)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Gagal mendapatkan embedding: {e}. Pastikan OPENAI_API_KEY di .env valid.")
        return [0.0] * 1536

# --- Endpoints ---

@router.post("/log_prompt")
def log_prompt(log_data: PromptLogCreate, db: Session = Depends(get_db)):
    """Menyimpan aktivitas AI user dan membuat embedding untuk self-learning (pgvector)"""
    embedding_vector = []
    if log_data.api_key or os.getenv("OPENAI_API_KEY"):
        embedding_vector = get_embedding(log_data.prompt_text, log_data.api_key)
        
    db_log = PromptLog(
        user_id=log_data.user_id,
        company_id=log_data.company_id,
        module_name=log_data.module_name,
        prompt_text=log_data.prompt_text,
        output_result=log_data.output_result,
        embedding=embedding_vector
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return {"status": "success", "log_id": db_log.id}

@router.post("/submit_feedback")
def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Menyimpan feedback dari tombol (Akurat / Tidak Akurat)"""
    db_feedback = UserFeedback(
        prompt_log_id=feedback.prompt_log_id,
        rating=feedback.rating,
        comment=feedback.comment
    )
    db.add(db_feedback)
    db.commit()
    return {"status": "success"}

@router.post("/submit_edit")
def submit_edit(edit: EditLearningCreate, db: Session = Depends(get_db)):
    """Menyimpan data jika user melakukan edit manual pada tabel"""
    db_edit = EditLearning(
        prompt_log_id=edit.prompt_log_id,
        item_name=edit.item_name,
        old_value=edit.old_value,
        new_value=edit.new_value,
        change_type=edit.change_type,
        region=edit.region
    )
    db.add(db_edit)
    db.commit()
    return {"status": "success"}

@router.get("/similar_prompts")
def get_similar_prompts(query: str, api_key: str = "", limit: int = 3, db: Session = Depends(get_db)):
    """Mencari riwayat prompt lama menggunakan pgvector Semantic Search (Enterprise Grade)"""
    query_embedding = get_embedding(query, api_key)
    if sum(query_embedding) == 0:
        return {"similar_prompts": []}
        
    # pgvector magic: Order by cosine distance (<=> operator in SQL)
    # Cosine distance = 1 - Cosine Similarity. Similarity > 0.7 means Distance < 0.3
    similar_logs = db.query(PromptLog).filter(
        PromptLog.embedding.cosine_distance(query_embedding) < 0.3
    ).order_by(
        PromptLog.embedding.cosine_distance(query_embedding)
    ).limit(limit).all()
    
    results = []
    for log in similar_logs:
        # Kalkulasi manual untuk mengembalikan 'similarity' (1 - distance)
        # Tapi karena SQLAlchemy ORM mengembalikan objek, kita hitung ulang atau asumsikan dari threshold
        # Kita hanya butuh data untuk context, exact similarity number tidak terlalu penting di Frontend saat ini.
        
        feedbacks = [f.rating for f in log.feedbacks]
        final_rating = feedbacks[-1] if feedbacks else "Belum Dinilai"
        revisions = [{"item": e.item_name, "old": e.old_value, "new": e.new_value} for e in log.edits]
        
        # HANYA masukkan ke context jika prompt ini pernah dinilai atau direvisi user
        if final_rating != "Belum Dinilai" or len(revisions) > 0:
            results.append({
                "id": log.id,
                "prompt": log.prompt_text,
                "result": log.output_result,
                "rating": final_rating,
                "revisions": revisions
            })
            
    return {"similar_prompts": results}
