import streamlit as st
import pandas as pd
from database import get_db_connection

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login dari halaman utama terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem; letter-spacing: -0.5px;}
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 2rem; font-weight: 400;}
    .news-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 16px; border-left: 5px solid #3B82F6;}
    .news-card.High { border-left-color: #EF4444; background-color: #FEF2F2;}
    .news-card.Medium { border-left-color: #F59E0B; background-color: #FFFBEB;}
    .news-title { font-size: 1.1rem; font-weight: 700; color: #1E293B; margin-bottom: 8px;}
    .news-meta { font-size: 0.8rem; color: #64748B; margin-bottom: 12px;}
    .news-impact { font-weight: 600; color: #334155;}
    .news-action { margin-top: 8px; padding: 8px; background-color: #FFFFFF; border-radius: 4px; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📰 News & Regulation Alerts</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Pemindaian Berita Otomatis 24 Jam dengan OpenRouter LLM</p>', unsafe_allow_html=True)

conn = get_db_connection()
df_news = pd.read_sql_query("SELECT * FROM market_news ORDER BY id DESC LIMIT 50", conn)
conn.close()

if df_news.empty:
    st.info("Belum ada berita yang dipindai. Scheduler sedang mengumpulkan data...")
    if st.button("🔄 Paksa Scan Sekarang"):
        with st.spinner("Memindai berita..."):
            from news_agent import run_news_agent
            run_news_agent()
            st.rerun()
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Menampilkan {len(df_news)} berita terakhir yang dipindai.")
    with col2:
        if st.button("🔄 Refresh Data"):
            st.rerun()
            
    st.markdown("---")
    
    for _, row in df_news.iterrows():
        urgency = row['urgency'] if row['urgency'] in ['High', 'Medium', 'Low'] else 'Low'
        
        st.markdown(f"""
        <div class="news-card {urgency}">
            <div class="news-title"><a href="{row['link']}" target="_blank" style="text-decoration:none; color:inherit;">{row['title']}</a></div>
            <div class="news-meta">📅 Dipublikasikan: {row['published_date']} | ⚠️ Urgency: {urgency}</div>
            <div class="news-impact">📈 Impact: {row['impact_summary']}</div>
            <div class="news-action">💡 <b>Rekomendasi Aksi:</b> {row['recommended_action']}</div>
        </div>
        """, unsafe_allow_html=True)
