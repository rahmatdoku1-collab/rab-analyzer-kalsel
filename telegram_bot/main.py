import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import TELEGRAM_BOT_TOKEN
from database import init_db
from handlers.user_handlers import start_command, menu_command, button_callback, help_command
from handlers.admin_handlers import broadcast_command

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN belum diatur di .env! Bot tidak bisa berjalan.")
        return
        
    # Inisialisasi Database SQLite Bot
    init_db()
    
    # Menonaktifkan internal job_queue (menggunakan None) untuk mencegah bug 'weakref' di versi Python terbaru
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).job_queue(None).build()

    # Daftarkan Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # Daftarkan Callback Handler untuk tombol interaktif
    application.add_handler(CallbackQueryHandler(button_callback))

    # Mulai Bot
    logger.info("Bot berhasil dijalankan! Menunggu pesan masuk...")
    application.run_polling()

import asyncio
import sys

if __name__ == '__main__':
    # Fix untuk Windows & Python 3.14+ (Event loop policy workaround)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
        
    main()
