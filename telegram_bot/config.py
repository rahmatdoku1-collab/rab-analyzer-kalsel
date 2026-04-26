import os
from dotenv import load_dotenv

# Muat file .env jika ada
load_dotenv()

# Konfigurasi Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

# Path ke Database Dashboard RAB Analyzer yang sudah ada
# Supaya bot membaca database yang sama dengan website
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DB_PATH = os.path.join(BASE_DIR, 'data', 'harga_lokal.db')
BOT_DB_PATH = os.path.join(BASE_DIR, 'data', 'telegram_bot.db')
