import json
from typing import Dict
from app.core.config import settings

def analyze_article_with_ai(title: str, summary: str) -> Dict:
    """
    Connects to OpenRouter (LLM) to extract structured insights.
    Returns categorized data: impact, urgency, score, etc.
    """
    # Mocking for Phase 7.2 - In production, this calls OpenRouter API with a structured JSON Prompt
    # Prompt would be: "Analyze this news: {title}. Return JSON with: kategori, wilayah, dampak_biaya, urgensi(High/Med/Low), skor_penting(1-100)"
    
    mock_response = {
        "kategori": "Tender Baru" if "Tender" in title else "Regulasi/Industri",
        "wilayah": "Kalimantan Selatan",
        "dampak_biaya": "Berpotensi menaikkan harga material 5%",
        "dampak_tender": "Peluang proyek baru senilai di atas 1 Miliar",
        "urgensi": "High" if "Tender" in title else "Medium",
        "sentimen": "Positive",
        "skor_penting": 85 if "Tender" in title else 60,
        "aksi_saran": "Segera siapkan dokumen kualifikasi vendor."
    }
    
    return mock_response
