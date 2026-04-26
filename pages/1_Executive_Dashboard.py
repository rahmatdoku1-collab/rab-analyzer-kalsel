import streamlit as st
import pandas as pd
import sqlite3, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Executive Dashboard", page_icon="🏢", layout="wide")
st.markdown("""<style>
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
.kpi{background:#1A1A1D;padding:16px;border-radius:8px;border-left:4px solid;color:white;}
</style>""", unsafe_allow_html=True)

MASTER_DB  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "master_harga.db")
BACKEND_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "backend_fastapi", "enterprise_data.db")


def q(db_path, sql, params=()):
    if not os.path.exists(db_path):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def scalar(db_path, sql, params=(), default=0):
    if not os.path.exists(db_path):
        return default
    try:
        conn = sqlite3.connect(db_path)
        val = conn.execute(sql, params).fetchone()
        conn.close()
        return val[0] if val and val[0] is not None else default
    except Exception:
        return default


# ── Load real data ───────────────────────────────────────────────────────────
total_master   = scalar(MASTER_DB, "SELECT COUNT(*) FROM master_harga")
total_sektors  = scalar(MASTER_DB, "SELECT COUNT(DISTINCT sektor) FROM master_harga")
total_projects = scalar(BACKEND_DB, "SELECT COUNT(*) FROM projects")
total_vendors  = scalar(BACKEND_DB, "SELECT COUNT(*) FROM vendors")
total_users    = scalar(BACKEND_DB, "SELECT COUNT(*) FROM users")

df_projects = q(BACKEND_DB, "SELECT * FROM projects ORDER BY id DESC LIMIT 20")
df_vendors  = q(BACKEND_DB, "SELECT * FROM vendors ORDER BY id DESC LIMIT 20")
df_master_by_sektor = q(MASTER_DB,
    "SELECT sektor, COUNT(*) as jumlah, AVG(harga_median) as rata_median FROM master_harga GROUP BY sektor ORDER BY jumlah DESC")

# Session-based war mode data (from Vendor War Mode scans this session)
last_scan_items    = st.session_state.get("wm_df_items", pd.DataFrame())
last_war_report    = st.session_state.get("wm_war_report", {})
last_scan_filename = st.session_state.get("wm_filename", "")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🏢 Executive Dashboard")
st.caption("Data real dari database lokal. Refresh otomatis tiap interaksi.")

# ── KPI Row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.markdown(f"""<div class="kpi" style="border-color:#1E90FF">
    <b>Master Harga</b><br/><span style="font-size:1.8rem;font-weight:700;color:#1E90FF">{total_master:,}</span><br/>
    <small>{total_sektors} sektor</small></div>""", unsafe_allow_html=True)
k2.markdown(f"""<div class="kpi" style="border-color:#00E676">
    <b>Proyek Tersimpan</b><br/><span style="font-size:1.8rem;font-weight:700;color:#00E676">{total_projects}</span><br/>
    <small>di backend DB</small></div>""", unsafe_allow_html=True)
k3.markdown(f"""<div class="kpi" style="border-color:#FFEA00">
    <b>Vendor Terdaftar</b><br/><span style="font-size:1.8rem;font-weight:700;color:#FFEA00">{total_vendors}</span><br/>
    <small>intelligence DB</small></div>""", unsafe_allow_html=True)
k4.markdown(f"""<div class="kpi" style="border-color:#FF6D00">
    <b>User Aktif</b><br/><span style="font-size:1.8rem;font-weight:700;color:#FF6D00">{total_users}</span><br/>
    <small>terdaftar</small></div>""", unsafe_allow_html=True)

war_verdict = last_war_report.get("verdict", "—")
vcolor = "#00E676" if war_verdict == "GO" else ("#FF1744" if war_verdict == "NO GO" else "#FFEA00")
k5.markdown(f"""<div class="kpi" style="border-color:{vcolor}">
    <b>Last War Verdict</b><br/><span style="font-size:1.8rem;font-weight:700;color:{vcolor}">{war_verdict}</span><br/>
    <small>{last_scan_filename[:20] if last_scan_filename else 'Belum ada scan'}</small></div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Row 2: Master Data + Last Scan ───────────────────────────────────────────
col_l, col_r = st.columns([1.2, 1])

with col_l:
    st.markdown("### 📊 Master Harga — Distribusi per Sektor")
    if not df_master_by_sektor.empty:
        df_master_by_sektor.columns = ["Sektor", "Jumlah Item", "Rata-rata Median (Rp)"]
        df_master_by_sektor["Rata-rata Median (Rp)"] = df_master_by_sektor["Rata-rata Median (Rp)"].apply(
            lambda x: f"Rp {int(x):,}" if x else "—")
        st.dataframe(df_master_by_sektor, hide_index=True, use_container_width=True)
    else:
        st.info("Master data kosong. Buka Master Data Manager untuk mulai.")

with col_r:
    st.markdown("### ⚔️ Last War Mode Scan")
    if not last_scan_items.empty:
        total_val    = last_scan_items["Subtotal"].sum()
        avg_margin   = last_war_report.get("peluang_menang_pct", "—")
        suspicious   = last_war_report.get("suspicious_score_pct", "—")
        ai_items     = st.session_state.get("wm_ai_items", [])
        tebal_count  = sum(1 for x in ai_items if x.get("kategori") == "tebal")
        rawan_count  = sum(1 for x in ai_items if x.get("kategori") == "rawan")

        st.metric("Nilai RAB Ter-scan", f"Rp {int(total_val):,}")
        st.metric("Peluang Menang (AI)", f"{avg_margin}%")
        mc1, mc2 = st.columns(2)
        mc1.metric("Item Profit Tebal", tebal_count)
        mc2.metric("Item Rawan Evaluator", rawan_count)

        if last_war_report.get("strategi_submit"):
            st.info(f"**Strategi:** {last_war_report['strategi_submit'][:200]}...")
    else:
        st.info("Belum ada scan. Buka Vendor War Mode → upload RAB.")

# ── Row 3: Projects + Vendors ─────────────────────────────────────────────────
st.markdown("---")
col_p, col_v = st.columns(2)

with col_p:
    st.markdown("### 📁 Proyek Terbaru (Backend DB)")
    if not df_projects.empty:
        cols_show = [c for c in ["name","total_budget","status","created_at"] if c in df_projects.columns]
        st.dataframe(df_projects[cols_show].head(10), hide_index=True, use_container_width=True)
    else:
        st.info("Belum ada proyek tersimpan.")

with col_v:
    st.markdown("### 🏭 Vendor Intelligence")
    if not df_vendors.empty:
        cols_show = [c for c in ["nama_vendor","spesialisasi","reliability_score","menang_tender"] if c in df_vendors.columns]
        if cols_show:
            st.dataframe(df_vendors[cols_show].head(10), hide_index=True, use_container_width=True)
        else:
            st.dataframe(df_vendors.head(10), hide_index=True, use_container_width=True)
    else:
        st.info("Database vendor kosong.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"Data source: `master_harga.db` ({total_master} item) | "
    f"`enterprise_data.db` ({total_projects} proyek, {total_vendors} vendor) | "
    f"Refresh: buka ulang halaman"
)
