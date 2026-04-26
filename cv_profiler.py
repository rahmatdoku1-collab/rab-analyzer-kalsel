import logging
import json
import PyPDF2
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_pdf_text(file_obj):
    try:
        reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        logger.info("Berhasil mengekstrak teks dari PDF.")
        return text
    except Exception as e:
        logger.error(f"Error membaca PDF: {str(e)}")
        return f"Error membaca PDF: {str(e)}"

def analyze_vendor_profile_with_ai(cv_text, api_key):
    if not api_key:
        logger.warning("API Key OpenRouter tidak ditemukan.")
        return {"error": "API Key OpenRouter belum diatur"}
        
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    prompt = f"""
    Anda adalah analis pengadaan (Procurement Auditor).
    Berikut adalah teks hasil ekstrak dari dokumen Profil Perusahaan (CV Vendor):
    
    \"\"\"{cv_text[:4000]}\"\"\"
    
    Tugas Anda:
    1. Identifikasi Nama Vendor/Perusahaan.
    2. Identifikasi Spesialisasi utama mereka.
    3. Simulasikan "Internet Background Check": Berdasarkan narasi profil dan standar industri, berikan penilaian (0-100) untuk Reliability Score (kemampuan teknis & pengalaman) dan Overpriced Tendency (kecenderungan harga mahal/markup, biasanya 0-30%).
    4. Hitung perkiraan berapa kali mereka Menang Tender berdasarkan pengalaman yang disebutkan.
    
    Keluarkan HASIL SAJA dalam format JSON murni tanpa markdown/penjelasan tambahan, persis seperti ini:
    {{
        "Nama Vendor": "PT/CV...",
        "Spesialisasi": "...",
        "Reliability Score": 85.0,
        "Overpriced Tendency": 10.0,
        "Response Speed": "Fast" atau "Medium" atau "Slow",
        "Menang Tender": 5,
        "Kesimpulan": "Alasan singkat..."
    }}
    """
    
    try:
        logger.info("Menghubungi OpenRouter API untuk analisa profil vendor...")
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        logger.info("Berhasil mendapatkan response dari AI.")
        return json.loads(content.strip())
    except Exception as e:
        logger.error(f"Gagal memproses dengan AI: {str(e)}")
        return {"error": f"Gagal memproses dengan AI: {str(e)}"}
