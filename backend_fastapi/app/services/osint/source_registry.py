from typing import List, Dict

# Registry Statis (Ini nantinya disinkronkan dengan tabel NewsSource di Database)
OSINT_SOURCES: List[Dict] = [
    # --- PORTAL PEMERINTAH ---
    {"name": "LPSE Kalsel", "url": "https://lpse.kalselprov.go.id/eproc4", "type": "HTML_SCRAPER", "category": "Government", "region": "Kalsel"},
    {"name": "LPSE Banjarmasin", "url": "https://lpse.banjarmasinkota.go.id/eproc4", "type": "HTML_SCRAPER", "category": "Government", "region": "Banjarmasin"},
    {"name": "LPSE Banjarbaru", "url": "https://lpse.banjarbarukota.go.id/eproc4", "type": "HTML_SCRAPER", "category": "Government", "region": "Banjarbaru"},
    {"name": "LPSE Tabalong", "url": "https://lpse.tabalongkab.go.id/eproc4", "type": "HTML_SCRAPER", "category": "Government", "region": "Tabalong"},
    
    # --- MEDIA NASIONAL & INDUSTRI ---
    {"name": "CNBC Indonesia Energy", "url": "https://www.cnbcindonesia.com/news/energi/rss", "type": "RSS", "category": "Industry", "region": "Nasional"},
    {"name": "Bisnis.com Tambang", "url": "https://ekonomi.bisnis.com/rss", "type": "RSS", "category": "Industry", "region": "Nasional"},
    {"name": "Mining.com", "url": "https://www.mining.com/feed/", "type": "RSS", "category": "Industry", "region": "Global"},
    
    # --- MEDIA LOKAL KALIMANTAN ---
    {"name": "Banjarmasin Post", "url": "https://banjarmasin.tribunnews.com/rss", "type": "RSS", "category": "Local Media", "region": "Kalsel"},
    {"name": "Radar Banjarmasin", "url": "https://radarbanjarmasin.jawapos.com/rss", "type": "RSS", "category": "Local Media", "region": "Kalsel"}
]

def get_active_sources() -> List[Dict]:
    """Retrieve all active sources from the registry"""
    return OSINT_SOURCES
