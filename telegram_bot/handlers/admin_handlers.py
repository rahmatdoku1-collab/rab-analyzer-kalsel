from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_CHAT_ID
from database import get_all_active_users

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("⛔ Anda tidak memiliki akses admin untuk fitur ini.")
        return
        
    if not context.args:
        await update.message.reply_text("Penggunaan: /broadcast [pesan Anda]")
        return
        
    pesan = " ".join(context.args)
    users = get_all_active_users()
    
    sukses = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 *BROADCAST DARI ADMIN*\n\n{pesan}", parse_mode='Markdown')
            sukses += 1
        except Exception:
            pass
            
    await update.message.reply_text(f"✅ Broadcast berhasil dikirim ke {sukses} pengguna.")
