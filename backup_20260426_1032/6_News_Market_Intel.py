import streamlit as st
import pandas as pd
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.intel_db import init_intel_db, INTEL_DB

st.set_page_config(page_title="News & Market Intel", page_icon="📡", layout="wide")
st.markdown("""<style>
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
.news-card{background:#1A1A1D;padding:14px 16px;border-radius:8px;margin-bottom:10px;border-left:4px solid;}
.high{border-color:#FF1744;}.medium{border-color:#FFEA00;}.low{border-color:#00E676;}
</style>""", unsafe_allow_html=True)

MASTER_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "master_harga.db")

init_intel_db()


def q_intel(sql, params=()):
    if not os.path.exists(INTEL_DB):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(INTEL_DB)
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def q_master(sql, params=()):
    if not os.path.exists(MASTER_DB):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(MASTER_DB)
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


# ── Header ────────────────────────────────────────────────────────────────────
st.title("📡 News & Market Intel")
st.caption("Berita regulasi pengadaan, pergerakan harga BBM & material — diperbarui otomatis tiap 2 jam.")

# ── Manual Refresh ────────────────────────────────────────────────────────────
col_r1, col_r2, col_r3 = st.columns([1, 1, 4])
refresh_news    = col_r1.button("🔄 Refresh Berita", use_container_width=True)
refresh_crawler = col_r2.button("⛽ Update Harga", use_container_width=True)

if refresh_news:
    with st.spinner("Mengambil berita terbaru dari RSS + AI..."):
        try:
            from news_agent import run_news_agent
            saved = run_news_agent()
            st.success(f"{saved} berita baru disimpan." if saved else "Tidak ada berita baru.")
        except Exception as e:
            st.error(f"Error: {e}")

if refresh_crawler:
    with st.spinner("Crawling harga BBM & material..."):
        try:
            from crawler import run_crawlers
            n = run_crawlers()
            st.success(f"Crawler selesai — {n} update." if n else "Tidak ada update harga baru.")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📰 Berita & Regulasi", "⛽ Harga BBM Terkini", "📈 Pergerakan Harga Material"])

# ── Tab 1: News ───────────────────────────────────────────────────────────────
with tab1:
    df_news = q_intel(
        "SELECT title, link, pub_date, impact, urgency, action, created_at "
        "FROM market_news ORDER BY id DESC LIMIT 50"
    )

    if df_news.empty:
        st.info("Belum ada berita. Klik **Refresh Berita** untuk memulai.")
    else:
        # KPI row
        high_count   = (df_news["urgency"].str.upper() == "HIGH").sum()
        medium_count = (df_news["urgency"].str.upper() == "MEDIUM").sum()
        total_news   = len(df_news)

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Berita", total_news)
        k2.metric("🔴 High Urgency", high_count)
        k3.metric("🟡 Medium Urgency", medium_count)
        st.markdown("---")

        # Filter
        urgency_filter = st.selectbox("Filter Urgensi", ["Semua", "High", "Medium", "Low"], key="urg_filter")
        if urgency_filter != "Semua":
            df_news = df_news[df_news["urgency"].str.upper() == urgency_filter.upper()]

        for _, row in df_news.iterrows():
            urg = str(row.get("urgency", "Low")).lower()
            css_class = "high" if "high" in urg else ("medium" if "medium" in urg else "low")
            badge_color = "#FF1744" if "high" in urg else ("#FFEA00" if "medium" in urg else "#00E676")
            title_link = (
                f'<a href="{row["link"]}" target="_blank" style="color:white;text-decoration:none;">'
                f'{row["title"]}</a>'
                if row.get("link") else row["title"]
            )
            st.markdown(
                f'<div class="news-card {css_class}">'
                f'<span style="background:{badge_color};color:#000;padding:2px 8px;border-radius:4px;'
                f'font-size:0.75rem;font-weight:700;">{row.get("urgency","Low").upper()}</span>&nbsp;&nbsp;'
                f'{title_link}<br/>'
                f'<small style="color:#aaa;">📅 {str(row.get("pub_date",""))[:20]}</small><br/>'
                f'<small>💡 <b>Impact:</b> {row.get("impact","—")}</small><br/>'
                f'<small>✅ <b>Action:</b> {row.get("action","—")}</small>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── Tab 2: BBM Prices ─────────────────────────────────────────────────────────
with tab2:
    st.markdown("### ⛽ Harga BBM Terkini — Kalimantan Selatan")

    # From master_harga.db
    df_bbm = q_master(
        "SELECT nama_item, satuan, harga_min, harga_max, harga_median, sumber, updated_at "
        "FROM master_harga WHERE sektor = 'BBM & Logistik' ORDER BY nama_item"
    )

    if not df_bbm.empty:
        df_bbm.columns = ["Item", "Satuan", "Min (Rp)", "Max (Rp)", "Median (Rp)", "Sumber", "Update"]
        for col in ["Min (Rp)", "Max (Rp)", "Median (Rp)"]:
            df_bbm[col] = df_bbm[col].apply(lambda x: f"Rp {int(x):,}" if x else "—")
        st.dataframe(df_bbm, hide_index=True, use_container_width=True)
    else:
        st.info("Data BBM belum tersedia di master DB.")

    # Latest snapshots from intel.db
    df_snap = q_intel(
        "SELECT nama_item, harga, sumber, tanggal FROM price_snapshots "
        "WHERE sektor = 'BBM & Logistik' ORDER BY id DESC LIMIT 20"
    )
    if not df_snap.empty:
        st.markdown("#### Riwayat Update Harga BBM (Auto-Crawl)")
        df_snap.columns = ["Item", "Harga (Rp)", "Sumber", "Tanggal"]
        df_snap["Harga (Rp)"] = df_snap["Harga (Rp)"].apply(lambda x: f"Rp {int(x):,}" if x else "—")
        st.dataframe(df_snap, hide_index=True, use_container_width=True)

    st.info(
        "💡 Harga diperbarui otomatis tiap 6 jam dari Google News RSS. "
        "Untuk update manual klik **⛽ Update Harga** di atas."
    )

# ── Tab 3: Material Price Movement ────────────────────────────────────────────
with tab3:
    st.markdown("### 📈 Radar Pergerakan Harga Material")

    # BBM + konstruksi from master DB, ordered by most recently updated
    df_mat = q_master(
        "SELECT sektor, nama_item, satuan, harga_min, harga_max, harga_median, updated_at "
        "FROM master_harga "
        "WHERE sektor IN ('Konstruksi','Alat Berat','Tambang','BBM & Logistik') "
        "ORDER BY updated_at DESC LIMIT 40"
    )

    if not df_mat.empty:
        df_mat.columns = ["Sektor", "Item", "Satuan", "Min (Rp)", "Max (Rp)", "Median (Rp)", "Update"]
        for col in ["Min (Rp)", "Max (Rp)", "Median (Rp)"]:
            df_mat[col] = df_mat[col].apply(lambda x: f"Rp {int(x):,}" if x else "—")

        sektor_list = ["Semua"] + sorted(df_mat["Sektor"].unique().tolist())
        sel = st.selectbox("Filter Sektor", sektor_list, key="mat_sektor")
        if sel != "Semua":
            df_mat = df_mat[df_mat["Sektor"] == sel]

        st.dataframe(df_mat, hide_index=True, use_container_width=True)
    else:
        st.info("Buka Master Data Manager terlebih dahulu untuk mengisi data material.")

    # Material movement headlines from intel.db
    df_mat_news = q_intel(
        "SELECT catatan, tanggal FROM price_snapshots "
        "WHERE nama_item = 'Material Konstruksi' "
        "ORDER BY id DESC LIMIT 15"
    )
    if not df_mat_news.empty:
        st.markdown("#### 📰 Berita Pergerakan Harga Material Terbaru")
        for _, row in df_mat_news.iterrows():
            st.markdown(f"- {row['catatan']} *(crawled: {row['tanggal']})*")

    st.caption(
        "Data harga material bersumber dari master_harga.db. "
        "Crawler memantau berita kenaikan/penurunan harga tiap 6 jam."
    )
