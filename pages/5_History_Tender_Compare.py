import streamlit as st
import pandas as pd
import sqlite3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.intel_db import init_intel_db, INTEL_DB

st.set_page_config(page_title="History & Tender Compare", page_icon="📚", layout="wide")
st.markdown("""<style>
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
</style>""", unsafe_allow_html=True)

init_intel_db()

st.title("📚 History Scan & Analisa")
st.caption("Riwayat scan RAB dari Vendor War Mode — otomatis tersimpan setiap selesai scan.")


def load_history():
    if not os.path.exists(INTEL_DB):
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(INTEL_DB)
        df = pd.read_sql_query(
            "SELECT id, filename, scan_date, grand_total, item_count, avg_margin, "
            "peluang_pct, verdict, strategi, alasan "
            "FROM scan_history ORDER BY id DESC",
            conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


df = load_history()

if df.empty:
    st.markdown("---")
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;background:#1A1A1D;border-radius:12px;border:1px dashed #444;">
            <div style="font-size:3rem;">📂</div>
            <h3 style="color:#aaa;">Belum ada histori scan</h3>
            <p style="color:#666;">Buka <b>Vendor War Mode</b> → upload RAB → Scan & Analisa Sekarang<br/>
            Hasil scan akan otomatis tersimpan di sini.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⚔️ Buka Vendor War Mode", use_container_width=True):
            st.switch_page("pages/2_Vendor_War_Mode.py")
else:
    # KPI summary
    total_scans = len(df)
    go_count    = (df["verdict"] == "GO").sum()
    nogo_count  = (df["verdict"] == "NO GO").sum()
    avg_peluang = pd.to_numeric(df["peluang_pct"], errors="coerce").mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Scan", total_scans)
    k2.metric("GO", go_count)
    k3.metric("NO GO", nogo_count)
    k4.metric("Rata Peluang Menang", f"{avg_peluang:.0f}%" if not pd.isna(avg_peluang) else "—")

    st.markdown("---")

    # Format tampilan
    df_show = df.copy()
    df_show["Grand Total"] = df_show["grand_total"].apply(
        lambda x: f"Rp {int(x):,}" if pd.notna(x) and x > 0 else "—"
    )
    df_show["Margin Avg"] = df_show["avg_margin"].apply(
        lambda x: f"{x:.1f}%" if pd.notna(x) else "—"
    )
    df_show["Peluang"] = df_show["peluang_pct"].apply(
        lambda x: f"{x}%" if str(x) not in ("—", "nan", "") else "—"
    )
    df_show["Tanggal"] = pd.to_datetime(df_show["scan_date"], errors="coerce").dt.strftime("%d/%m/%Y %H:%M")

    cols_display = ["Tanggal", "filename", "Grand Total", "item_count", "Margin Avg", "Peluang", "verdict"]
    df_show = df_show[cols_display].rename(columns={
        "filename": "File", "item_count": "Item", "verdict": "Verdict"
    })

    # Color verdict
    def style_verdict(val):
        if val == "GO":      return "background-color:#0a3d0a;color:#00E676;font-weight:700"
        if val == "NO GO":   return "background-color:#3d0a0a;color:#FF1744;font-weight:700"
        if val == "REVISI":  return "background-color:#3d2a00;color:#FFEA00;font-weight:700"
        return ""

    try:
        styled = df_show.style.map(style_verdict, subset=["Verdict"])
    except AttributeError:
        styled = df_show.style.applymap(style_verdict, subset=["Verdict"])
    st.dataframe(styled, hide_index=True, use_container_width=True)

    # Detail per baris
    st.markdown("---")
    st.markdown("### Detail Strategi")
    sel_idx = st.selectbox(
        "Pilih scan untuk lihat detail strategi:",
        options=df.index,
        format_func=lambda i: f"{df.loc[i,'scan_date'][:16]} | {df.loc[i,'filename']} | {df.loc[i,'verdict']}"
    )
    row = df.loc[sel_idx]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**File:** {row['filename']}")
        st.markdown(f"**Grand Total:** Rp {int(row['grand_total']):,}" if row['grand_total'] else "—")
        st.markdown(f"**Margin Rata:** {row['avg_margin']:.1f}%")
        st.markdown(f"**Peluang Menang:** {row['peluang_pct']}%")
        vd = row['verdict']
        fn = st.success if vd == "GO" else (st.error if vd == "NO GO" else st.warning)
        fn(f"**Verdict: {vd}** — {row.get('alasan','')}")
    with c2:
        if row.get("strategi"):
            st.info(f"**Strategi:** {row['strategi']}")

    # Hapus histori
    st.markdown("---")
    if st.button("🗑️ Hapus Semua Histori", type="secondary"):
        try:
            conn = sqlite3.connect(INTEL_DB)
            conn.execute("DELETE FROM scan_history")
            conn.commit()
            conn.close()
            st.success("Histori dihapus.")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal: {e}")
