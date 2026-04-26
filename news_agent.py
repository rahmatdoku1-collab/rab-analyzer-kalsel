import feedparser
import os
import sys
import openai
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.intel_db import init_intel_db, get_conn, INTEL_DB
from dotenv import load_dotenv

load_dotenv()


RSS_URL = (
    "https://news.google.com/rss/search?"
    "q=infrastruktur+kalimantan+selatan+OR+LKPP+OR+pengadaan+pemerintah"
    "+OR+harga+material+konstruksi+OR+PMK+pajak+konstruksi"
    "&hl=id&gl=ID&ceid=ID:id"
)

BBM_RSS_URL = (
    "https://news.google.com/rss/search?"
    "q=harga+solar+pertalite+pertamax+2025+terbaru"
    "&hl=id&gl=ID&ceid=ID:id"
)


def fetch_rss_news(url, limit=12):
    try:
        feed = feedparser.parse(url)
        entries = []
        for e in feed.entries[:limit]:
            entries.append({
                "title": e.get("title", ""),
                "link":  e.get("link", ""),
                "pub_date": e.get("published", ""),
            })
        return entries
    except Exception as ex:
        print(f"[news_agent] RSS fetch error: {ex}")
        return []


def analyze_news(title: str, api_key: str):
    if not api_key:
        return "API key belum diatur.", "Low", "Set OPENROUTER_API_KEY di .env"
    try:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        prompt = (
            "Anda adalah analis pengadaan barang/jasa pemerintah Indonesia.\n"
            f"Berita: {title}\n\n"
            "Jawab persis format ini (tanpa markdown):\n"
            "IMPACT: <1 kalimat dampak terhadap harga RAB atau proyek pemerintah>\n"
            "URGENCY: <High / Medium / Low>\n"
            "ACTION: <1 kalimat saran untuk kontraktor/PPK>"
        )
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        text = resp.choices[0].message.content
        impact = urgency = action = ""
        for line in text.split("\n"):
            if line.startswith("IMPACT:"):
                impact = line.replace("IMPACT:", "").strip()
            elif line.startswith("URGENCY:"):
                urgency = line.replace("URGENCY:", "").strip()
            elif line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
        return impact or "—", urgency or "Low", action or "Pantau."
    except Exception as ex:
        print(f"[news_agent] AI error: {ex}")
        return "Gagal analisis.", "Low", "-"


def run_news_agent():
    print(f"[{datetime.now()}] News Agent — mulai...")
    init_intel_db()
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    conn = get_conn()

    entries = fetch_rss_news(RSS_URL, 12) + fetch_rss_news(BBM_RSS_URL, 5)
    saved = 0
    for item in entries:
        if not item["title"]:
            continue
        exists = conn.execute(
            "SELECT id FROM market_news WHERE title = ?", (item["title"],)
        ).fetchone()
        if exists:
            continue
        impact, urgency, action = analyze_news(item["title"], api_key)
        conn.execute(
            """INSERT OR IGNORE INTO market_news
               (title, link, pub_date, impact, urgency, action)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item["title"], item["link"], item["pub_date"], impact, urgency, action),
        )
        saved += 1

    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] News Agent — {saved} berita baru disimpan.")
    return saved


if __name__ == "__main__":
    run_news_agent()
