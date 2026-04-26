import logging
import feedparser
from typing import List, Dict
from app.services.osint.source_registry import get_active_sources

logger = logging.getLogger(__name__)

class CrawlerManager:
    def __init__(self):
        self.sources = get_active_sources()
        
    def fetch_rss_feed(self, url: str) -> List[Dict]:
        """Fetch and parse RSS feed"""
        try:
            feed = feedparser.parse(url)
            articles = []
            for entry in feed.entries[:5]: # Take top 5 for MVP to save time
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "published_date": getattr(entry, 'published', None),
                    "summary": getattr(entry, 'summary', '')[:200]
                })
            return articles
        except Exception as e:
            logger.error(f"Failed to fetch RSS {url}: {e}")
            return []

    def fetch_html_scraper(self, url: str) -> List[Dict]:
        """Placeholder for BeautifulSoup / Selenium scraper for LPSE"""
        logger.info(f"Mocking HTML Scrape for LPSE: {url}")
        return [{
            "title": f"Tender Baru Terdeteksi di {url.split('//')[1].split('.')[0]}",
            "link": url,
            "published_date": None,
            "summary": "Mock data tender pengadaan barang dan jasa."
        }]

    def run_all(self) -> List[Dict]:
        """Execute all active crawlers"""
        all_news = []
        for source in self.sources:
            logger.info(f"Crawling source: {source['name']} ({source['type']})")
            if source['type'] == 'RSS':
                all_news.extend(self.fetch_rss_feed(source['url']))
            elif source['type'] == 'HTML_SCRAPER':
                all_news.extend(self.fetch_html_scraper(source['url']))
                
        return all_news

# Singleton instance
crawler_manager = CrawlerManager()
