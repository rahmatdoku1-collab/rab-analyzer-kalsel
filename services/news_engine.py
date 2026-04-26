import feedparser
import os
import openai
from datetime import datetime
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()

def fetch_rss_news():
    # Menggunakan Google News RSS feed untuk kata kunci infrastruktur Kalsel
    url = "https://news.google.com/rss/search?q=infrastruktur+kalimantan+selatan+OR+tender+pemerintah+OR+LKPP&hl=id&gl=ID&ceid=ID:id"
    feed = feedparser.parse(url)
    
    entries = []
    for entry in feed.entries[:3]: # Ambil 3 berita terbaru
        entries.append({
            "title": entry.title,
            "link": entry.link,
            "published_date": entry.published
        })
    return entries

def analyze_news_impact(news_item, api_key):
    if not api_key:
        return "ERROR: API Key OpenRouter belum diatur di .env", "Low", "Abaikan"
        
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    prompt = f"""
    Anda adalah analis pengadaan barang/jasa pemerintah (Procurement Analyst).
    Terdapat berita terbaru berikut:
    Judul: {news_item['title']}
    
    Tolong berikan respons terstruktur dengan format seperti ini persis (jangan gunakan markdown tambahan, langsung teks saja):
    IMPACT: (berikan 1 kalimat dampak berita ini terhadap harga RAB atau proyek, misalnya "Harga aspal berpotensi naik")
    URGENCY: (High / Medium / Low)
    ACTION: (berikan 1 kalimat saran untuk auditor/PPK)
    """
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        
        impact = "Tidak ada dampak terdeteksi."
        urgency = "Low"
        action = "Pantau perkembangan."
        
        for line in content.split('\\n'):
            if line.startswith('IMPACT:'): impact = line.replace('IMPACT:', '').strip()
            elif line.startswith('URGENCY:'): urgency = line.replace('URGENCY:', '').strip()
            elif line.startswith('ACTION:'): action = line.replace('ACTION:', '').strip()
            
        return impact, urgency, action
    except Exception as e:
        print(f"Error LLM: {e}")
        return "Gagal analisis", "Low", "-"

def run_news_agent():
    print(f"[{datetime.now()}] Memulai News & Regulation Scanner...")
    news_items = fetch_rss_news()
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for item in news_items:
        # Check if already exists
        cursor.execute("SELECT id FROM market_news WHERE title = ?", (item['title'],))
        if cursor.fetchone():
            continue # Skip jika sudah ada
            
        impact, urgency, action = analyze_news_impact(item, api_key)
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO market_news (title, link, published_date, category, impact_summary, urgency, recommended_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item['title'], item['link'], item['published_date'], "Regulasi/Pasar", impact, urgency, action, today))
        
        print(f"Berita Baru: {item['title']} | Urgency: {urgency}")
        
    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] Selesai News & Regulation Scanner.")

if __name__ == '__main__':
    run_news_agent()
