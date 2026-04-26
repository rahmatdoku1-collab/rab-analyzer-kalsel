from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import add_or_update_user, get_user_preferences, update_preference

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # Registrasi user otomatis
    add_or_update_user(chat_id, username, first_name)
    
    welcome_text = (
        f"🏢 *Selamat datang di Kalsel Procurement Intelligence Bot, {first_name}!*\n\n"
        "Saya adalah asisten AI 24/7 Anda untuk memantau pergerakan harga lokal, tender terbaru, aturan pajak, dan risiko vendor.\n\n"
        "Gunakan perintah /menu untuk mengatur preferensi notifikasi Anda atau ketik /help untuk bantuan."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🛠 *Pusat Bantuan RAB Analyzer Bot*\n\n"
        "Berikut adalah daftar perintah yang bisa Anda gunakan:\n"
        "🔹 /start - Memulai ulang bot dan registrasi akun.\n"
        "🔹 /menu - Membuka panel pengaturan notifikasi personal Anda.\n"
        "🔹 /help - Menampilkan pesan bantuan ini.\n\n"
        "👑 *Khusus Admin:*\n"
        "🔹 /broadcast [pesan] - Mengirim pesan ke semua pengguna terdaftar.\n\n"
        "💡 _Bot ini berjalan 24/7 memantau Database Kalsel Procurement._"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    prefs = get_user_preferences(chat_id)
    
    if not prefs:
        await update.message.reply_text("Ketik /start terlebih dahulu.")
        return
        
    # Membangun tombol interaktif berdasarkan preferensi saat ini
    keyboard = [
        [
            InlineKeyboardButton(f"Tender Alert {'✅' if prefs['alert_tender'] else '❌'}", callback_data="toggle_tender"),
            InlineKeyboardButton(f"Tax Update {'✅' if prefs['alert_tax'] else '❌'}", callback_data="toggle_tax")
        ],
        [
            InlineKeyboardButton(f"Market Price {'✅' if prefs['alert_market'] else '❌'}", callback_data="toggle_market"),
            InlineKeyboardButton(f"Vendor Risk {'✅' if prefs['alert_vendor'] else '❌'}", callback_data="toggle_vendor")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ *Pengaturan Notifikasi Personal*\nSilakan klik tombol di bawah untuk menghidupkan/mematikan peringatan:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    chat_id = query.message.chat_id
    data = query.data
    
    prefs = get_user_preferences(chat_id)
    pesan_notifikasi = ""
    
    if data == "toggle_tender":
        status_baru = not prefs['alert_tender']
        update_preference(chat_id, 'alert_tender', status_baru)
        pesan_notifikasi = "Tender Alert AKTIF ✅" if status_baru else "Tender Alert NONAKTIF ❌"
    elif data == "toggle_tax":
        status_baru = not prefs['alert_tax']
        update_preference(chat_id, 'alert_tax', status_baru)
        pesan_notifikasi = "Tax Update AKTIF ✅" if status_baru else "Tax Update NONAKTIF ❌"
    elif data == "toggle_market":
        status_baru = not prefs['alert_market']
        update_preference(chat_id, 'alert_market', status_baru)
        pesan_notifikasi = "Market Price AKTIF ✅" if status_baru else "Market Price NONAKTIF ❌"
    elif data == "toggle_vendor":
        status_baru = not prefs['alert_vendor']
        update_preference(chat_id, 'alert_vendor', status_baru)
        pesan_notifikasi = "Vendor Risk AKTIF ✅" if status_baru else "Vendor Risk NONAKTIF ❌"
        
    # Tampilkan pesan popup (toast) di layar pengguna
    await query.answer(text=pesan_notifikasi, show_alert=False)
        
    # Edit pesan untuk memperbarui ikon ✅/❌
    prefs = get_user_preferences(chat_id)
    keyboard = [
        [
            InlineKeyboardButton(f"Tender Alert {'✅' if prefs['alert_tender'] else '❌'}", callback_data="toggle_tender"),
            InlineKeyboardButton(f"Tax Update {'✅' if prefs['alert_tax'] else '❌'}", callback_data="toggle_tax")
        ],
        [
            InlineKeyboardButton(f"Market Price {'✅' if prefs['alert_market'] else '❌'}", callback_data="toggle_market"),
            InlineKeyboardButton(f"Vendor Risk {'✅' if prefs['alert_vendor'] else '❌'}", callback_data="toggle_vendor")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_reply_markup(reply_markup=reply_markup)
