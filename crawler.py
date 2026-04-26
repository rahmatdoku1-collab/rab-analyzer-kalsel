"""
Market Price Crawler
- Fetches BBM price news from RSS and extracts prices via AI
- Updates master_harga.db for BBM/material items
- Logs snapshots to intel.db
"""
import os
import sys
import re
import sqlite3
import openai
import feedparser
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.intel_db import init_intel_db, get_conn as intel_conn

load_dotenv()

ROOT       = os.path.dirname(os.path.abspath(__file__))
MASTER_DB  = os.path.join(ROOT, "data", "master_harga.db")

BBM_ITEMS = {
    "Solar Industri":   {"sektor": "BBM & Logistik", "satuan": "Liter", "keywords": ["solar industri", "solar non subsidi"]},
    "Bensin Pertalite": {"sektor": "BBM & Logistik", "satuan": "Liter", "keywords": ["pertalite"]},
    "Bensin Pertamax":  {"sektor": "BBM & Logistik", "satuan": "Liter", "keywords": ["pertamax"]},
}

BBM_RSS = (
    "https://news.google.com/rss/search?"
    "q=harga+solar+pertalite+pertamax+Pertamina+2025&hl=id&gl=ID&ceid=ID:id"
)

MATERIAL_RSS = (
    "https://news.google.com/rss/search?"
    "q=harga+semen+besi+beton+pasir+konstruksi+2025+naik+turun&hl=id&gl=ID&ceid=ID:id"
)


def extract_price_from_text(text: str, item_name: str, api_key: str):
    """Use AI to extract a numeric price from a news headline."""
    if not api_key:
        return None
    try:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        prompt = (
            f"Dari kalimat berikut, ekstrak harga terbaru untuk '{item_name}' dalam Rupiah per satuan.\n"
            f"Teks: {text}\n\n"
            "Jawab HANYA angka bulat tanpa titik/koma/Rp (contoh: 14500). "
            "Jika tidak ada harga spesifik, jawab: TIDAK_ADA"
        )
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=20,
        )
        raw = resp.choices[0].message.content.strip().replace(",", "").replace(".", "")
        if raw == "TIDAK_ADA" or not raw.isdigit():
            return None
        return float(raw)
    except Exception:
        return None


def update_master_harga(nama_item: str, sektor: str, satuan: str, harga: float, sumber: str):
    """Update harga_median in master_harga.db for the matched item."""
    if not os.path.exists(MASTER_DB):
        return
    try:
        conn = sqlite3.connect(MASTER_DB)
        row = conn.execute(
            "SELECT id, harga_min, harga_max FROM master_harga WHERE nama_item LIKE ? AND sektor = ?",
            (f"%{nama_item.split()[0]}%", sektor)
        ).fetchone()
        if row:
            new_min = min(row[1], harga) if row[1] else harga * 0.95
            new_max = max(row[2], harga) if row[2] else harga * 1.05
            conn.execute(
                """UPDATE master_harga
                   SET harga_median=?, harga_min=?, harga_max=?, sumber=?, updated_at=date('now')
                   WHERE id=?""",
                (harga, new_min, new_max, sumber, row[0])
            )
            print(f"[crawler] Updated '{nama_item}' → Rp {harga:,.0f}")
        else:
            conn.execute(
                """INSERT INTO master_harga
                   (sektor, nama_item, satuan, harga_min, harga_max, harga_median, sumber, lokasi)
                   VALUES (?,?,?,?,?,?,?,'Kalsel')""",
                (sektor, nama_item, satuan, harga * 0.95, harga * 1.05, harga, sumber)
            )
            print(f"[crawler] Inserted new '{nama_item}' → Rp {harga:,.0f}")
        conn.commit()
        conn.close()
    except Exception as ex:
        print(f"[crawler] master_harga update error: {ex}")


def save_snapshot(nama_item: str, sektor: str, satuan: str, harga: float, sumber: str):
    conn = intel_conn()
    conn.execute(
        """INSERT INTO price_snapshots (nama_item, sektor, satuan, harga, sumber, tanggal)
           VALUES (?,?,?,?,?,date('now'))""",
        (nama_item, sektor, satuan, harga, sumber)
    )
    conn.commit()
    conn.close()


def crawl_bbm_prices():
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    try:
        feed = feedparser.parse(BBM_RSS)
    except Exception:
        return 0

    updated = 0
    for entry in feed.entries[:8]:
        title = entry.get("title", "")
        for item_name, meta in BBM_ITEMS.items():
            if any(kw in title.lower() for kw in meta["keywords"]):
                harga = extract_price_from_text(title, item_name, api_key)
                if harga and 5000 < harga < 50000:  # sanity check Rp/liter range
                    save_snapshot(item_name, meta["sektor"], meta["satuan"], harga, f"Google News: {title[:60]}")
                    update_master_harga(item_name, meta["sektor"], meta["satuan"], harga, "Auto-Crawl RSS")
                    updated += 1
    return updated


def crawl_material_news():
    """Log material price movement headlines as snapshots (no price extraction — just awareness)."""
    try:
        feed = feedparser.parse(MATERIAL_RSS)
    except Exception:
        return 0

    conn = intel_conn()
    saved = 0
    for entry in feed.entries[:6]:
        title = entry.get("title", "")
        if not title:
            continue
        exists = conn.execute(
            "SELECT id FROM price_snapshots WHERE catatan = ?", (title,)
        ).fetchone()
        if not exists:
            conn.execute(
                """INSERT INTO price_snapshots (nama_item, sektor, satuan, harga, sumber, tanggal, catatan)
                   VALUES ('Material Konstruksi','Konstruksi','—',0,'RSS Berita',date('now'),?)""",
                (title,)
            )
            saved += 1
    conn.commit()
    conn.close()
    return saved


def run_crawlers():
    print(f"[{datetime.now()}] Crawler — mulai...")
    init_intel_db()
    bbm = crawl_bbm_prices()
    mat = crawl_material_news()
    print(f"[{datetime.now()}] Crawler — BBM: {bbm} update, Material news: {mat} disimpan.")
    return bbm + mat


if __name__ == "__main__":
    run_crawlers()
