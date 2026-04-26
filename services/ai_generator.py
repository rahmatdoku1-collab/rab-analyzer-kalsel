import openai
import json
import requests
from core.config import settings

# ==========================================
# MODEL ROUTING
# ==========================================
MODEL_MAP = {
    "rab_fast": "openai/gpt-4o-mini",
    "rab_pro": "anthropic/claude-sonnet-4",
    "war_mode": "anthropic/claude-opus-4"
}

# ==========================================
# MAIN FUNCTION
# ==========================================
def generate_rab_from_prompt(prompt_text: str, mode="rab_fast") -> dict:
    """
    mode:
    - rab_fast  = murah & cepat
    - rab_pro   = lebih pintar
    - war_mode  = premium reasoning
    """

    if not settings.OPENROUTER_API_KEY:
        return {"error": "API Key OpenRouter tidak ditemukan"}

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )

    selected_model = MODEL_MAP.get(mode, "openai/gpt-4o-mini")

    # ==========================================
    # BASE SYSTEM PROMPT
    # ==========================================
    system_prompt = """
Anda adalah Chief Procurement Officer, Quantity Surveyor, dan Estimator Senior Indonesia.

Tugas:
Buat RAB profesional dari prompt user.

Gunakan harga pasar Indonesia / referensi lokal / estimasi realistis.

WAJIB output JSON valid:

{
    "project_name": "Nama Proyek",
    "estimated_duration_days": 30,
    "items": [
        {
            "kategori": "Bahan",
            "nama_item": "Semen",
            "volume": 100,
            "satuan": "Zak",
            "harga_satuan_estimasi": 75000,
            "alasan": "Harga pasar rata-rata"
        }
    ],
    "total_estimated_budget": 0,
    "risk_factors": ["Risiko 1"]
}
"""

    # ==========================================
    # Learning memory sementara dimatikan

    # ==========================================
    # AI REQUEST
    # ==========================================
    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Buatkan RAB untuk: {prompt_text}"}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        rab_data = json.loads(content)

        # Hitung total real
        total = sum(
            item.get("volume", 0) * item.get("harga_satuan_estimasi", 0)
            for item in rab_data.get("items", [])
        )

        rab_data["total_estimated_budget"] = total
        rab_data["model_used"] = selected_model

        return rab_data

    except Exception as e:
        return {"error": str(e)}


# ==========================================
# VENDOR WAR MODE
# ==========================================
def analyze_vendor_negotiation(vendor_bid_data: dict, baseline_prices: dict) -> dict:
    return {
        "status": "ready",
        "message": "Vendor War Mode siap dikembangkan"
    }