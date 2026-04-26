import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Mock data for MVP Dashboard before connecting to FastAPI OSINT DB
MOCK_NEWS_ALERTS = [
    {"tanggal": "2026-04-23", "kategori": "Tender Baru", "judul": "Proyek Jalan Tambang Tabalong", "sumber": "LPSE Tabalong", "skor": 95, "urgensi": "High"},
    {"tanggal": "2026-04-23", "kategori": "Regulasi", "judul": "Aturan Baru Royalti Batubara Kalsel", "sumber": "CNBC Energy", "skor": 88, "urgensi": "High"},
    {"tanggal": "2026-04-22", "kategori": "Harga Solar", "judul": "Harga Solar Industri Merangkak Naik 3%", "sumber": "Bisnis.com", "skor": 75, "urgensi": "Medium"},
    {"tanggal": "2026-04-22", "kategori": "Vendor", "judul": "Konsolidasi Vendor Drone Pemetaan Regional Kalimantan", "sumber": "Mining.com", "skor": 60, "urgensi": "Low"}
]

st.set_page_config(page_title="Intelligence Command Center", page_icon="📡", layout="wide")

st.markdown("""
<style>
    .header-box { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    .alert-high { background-color: #FEE2E2; color: #991B1B; padding: 5px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; }
    .alert-medium { background-color: #FEF3C7; color: #92400E; padding: 5px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; }
    .alert-low { background-color: #E0F2FE; color: #075985; padding: 5px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><h2>📡 Intelligence Command Center</h2><p>Real-Time Procurement & Market Radar Kalsel</p></div>', unsafe_allow_html=True)

# Top Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Active Sources", "12", "+3 Today")
col2.metric("Articles Analyzed (24h)", "245", "+15%")
col3.metric("High Risk Alerts", "2", "-1")
col4.metric("Market Sentiment", "Positive", "Tender +12%")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔴 Live Alerts", "🗺️ Tender Radar", "⚙️ Watchlist Settings"])

with tab1:
    st.subheader("Breaking Intelligence & AI Analysis")
    df_alerts = pd.DataFrame(MOCK_NEWS_ALERTS)
    
    # Display styling for urgency
    for idx, row in df_alerts.iterrows():
        with st.container():
            col_u, col_c = st.columns([1, 8])
            with col_u:
                if row['urgensi'] == 'High':
                    st.markdown('<span class="alert-high">HIGH RISK</span>', unsafe_allow_html=True)
                elif row['urgensi'] == 'Medium':
                    st.markdown('<span class="alert-medium">MEDIUM</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="alert-low">LOW</span>', unsafe_allow_html=True)
            with col_c:
                st.markdown(f"**{row['judul']}**")
                st.caption(f"{row['tanggal']} | Sumber: {row['sumber']} | Kategori: {row['kategori']} | AI Score: {row['skor']}/100")
            st.divider()

with tab2:
    st.subheader("Kalimantan Active Tender Heatmap (Mockup)")
    # Mock data for map
    map_data = pd.DataFrame({
        'lat': [-3.316694, -3.440263, -2.174246, -1.265386],
        'lon': [114.590111, 114.830064, 115.399564, 116.831200],
        'city': ['Banjarmasin', 'Banjarbaru', 'Tabalong', 'Balikpapan'],
        'tenders': [15, 8, 24, 12]
    })
    
    fig = px.scatter_mapbox(map_data, lat="lat", lon="lon", size="tenders", hover_name="city", 
                            color_discrete_sequence=["#EF4444"], zoom=5, height=400)
    fig.update_layout(mapbox_style="carto-positron")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Alert Watchlist Filters")
    st.info("Klien Enterprise dapat mengatur kata kunci spesifik untuk dikirim ke Telegram/WA.")
    
    with st.form("watchlist_form"):
        keyword = st.text_input("Watchlist Keyword (e.g. 'Tabalong', 'Drone', 'Solar')")
        category = st.selectbox("Category Filter", ["All", "Tender Baru", "Regulasi", "Harga Material"])
        send_to = st.multiselect("Deliver Alert To:", ["Dashboard", "Telegram", "WhatsApp", "Email"])
        
        submitted = st.form_submit_button("Add to Watchlist")
        if submitted:
            st.success(f"Keyword '{keyword}' ditambahkan ke Watchlist Engine!")
