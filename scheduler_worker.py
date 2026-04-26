import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from services.crawler_engine import run_crawlers
from services.news_engine import run_news_agent

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def job_crawler():
    logger.info("Mulai mengeksekusi Auto Price Crawler...")
    try:
        run_crawlers()
        logger.info("Auto Price Crawler selesai.")
    except Exception as e:
        logger.error(f"Error pada Crawler: {e}")

def job_news():
    logger.info("Mulai mengeksekusi News & Regulation Scanner...")
    try:
        run_news_agent()
        logger.info("News Scanner selesai.")
    except Exception as e:
        logger.error(f"Error pada News Scanner: {e}")

if __name__ == "__main__":
    logger.info("Memulai AI Procurement Background Worker...")
    
    # Run once at startup
    job_crawler()
    job_news()
    
    # Initialize BlockingScheduler (Standalone Process)
    scheduler = BlockingScheduler()
    
    # Jadwalkan Crawler setiap 2 jam
    scheduler.add_job(job_crawler, 'interval', hours=2, id='crawler_job', replace_existing=True)
    
    # Jadwalkan News Scanner setiap 1 jam
    scheduler.add_job(job_news, 'interval', hours=1, id='news_job', replace_existing=True)
    
    try:
        logger.info("Scheduler berjalan (Tekan Ctrl+C untuk berhenti)")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Mematikan Background Worker...")
