import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def evaluate_and_send_alerts(article: Dict, watchlists: List[Dict]):
    """
    Evaluates an analyzed article against user watchlists.
    If match, triggers notification (Telegram/WA/Email).
    """
    for wl in watchlists:
        keyword = wl.get("keyword", "").lower()
        title = article.get("title", "").lower()
        kategori = article.get("ai_analysis", {}).get("kategori", "").lower()
        
        # Simple match logic
        if keyword in title or keyword in kategori:
            logger.info(f"🚨 ALERT TRIGGERED for User {wl.get('user_id')} - Keyword: {keyword}")
            _send_telegram_alert(wl.get("user_id"), article)
            
def _send_telegram_alert(user_id: int, article: Dict):
    """Mock sending Telegram alert"""
    logger.info(f"--> [Telegram API Mock] Sending to user {user_id}: {article.get('title')}")
    # Integration logic with python-telegram-bot or REST API goes here
