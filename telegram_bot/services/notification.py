def format_tender_alert(instansi, nilai, lokasi, deadline, skor, saran):
    """Format pesan premium untuk Tender Baru"""
    return (
        "🚨 *ALERT TENDER BARU*\n"
        "─────────────────\n"
        f"🏛 *Instansi:* {instansi}\n"
        f"💰 *Nilai:* Rp {nilai:,.0f}\n"
        f"📍 *Lokasi:* {lokasi}\n"
        f"⏳ *Deadline:* {deadline}\n"
        f"📊 *Skor Peluang:* {skor}/100\n\n"
        "📌 *Rekomendasi:*\n"
        f"_{saran}_\n"
        "─────────────────\n"
        "💡 _Dikirim oleh RAB Analyzer AI_"
    )

def format_price_alert(item, lokasi, status, persentase, dampak):
    """Format pesan premium untuk Perubahan Harga (Market Intelligence)"""
    icon = "📈" if status == "naik" else "📉"
    return (
        f"{icon} *UPDATE HARGA {item.upper()}*\n"
        "─────────────────\n"
        f"📍 *Lokasi:* {lokasi}\n"
        f"🔄 *Status:* {status.upper()} ({persentase}%)\n\n"
        "⚠️ *Dampak Bisnis:*\n"
        f"_{dampak}_\n"
        "─────────────────\n"
        "💡 _Cek Dashboard untuk grafik lengkap._"
    )
