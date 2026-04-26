import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="History & Tender Compare", page_icon="📚", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

st.title("📚 History, Analytics & Tender Compare")
st.caption("Evaluasi performa tender historis dan komparasi head-to-head dengan rival Anda.")

tab1, tab2, tab3 = st.tabs(["⚖️ Tender Compare (Head-to-Head)", "📂 History & Revenue", "🧠 Learning Analytics"])

with tab1:
    st.markdown("### ⚖️ Multi-Vendor Tender Compare")
    st.caption("Bandingkan penawaran Anda vs Kompetitor untuk mencari titik kelemahan harga.")
    
    st.dataframe(pd.DataFrame({
        "Komponen Pekerjaan": ["Mobilisasi & Demobilisasi", "Pekerjaan Galian & Timbunan", "Struktur Beton K-250", "Pekerjaan Baja WF", "Finishing & Arsitektur", "Pajak & Overhead"],
        "Penawaran KITA": ["Rp 250 Jt", "Rp 500 Jt", "Rp 2.0 M", "Rp 1.5 M", "Rp 800 Jt", "15%"],
        "PT Bangun Jaya (Rival 1)": ["Rp 150 Jt", "Rp 600 Jt", "Rp 2.1 M", "Rp 1.4 M", "Rp 900 Jt", "12%"],
        "CV Sinar Makmur (Rival 2)": ["Rp 300 Jt", "Rp 450 Jt", "Rp 1.9 M", "Rp 1.6 M", "Rp 700 Jt", "10%"]
    }), hide_index=True, use_container_width=True)
    
    st.info("💡 **Analisa:** Rival 1 memotong harga mobilisasi secara ekstrem, namun membebankannya pada item tanah (Galian). Anda memiliki keunggulan kompetitif pada harga Baja WF dibanding Rival 2.")

with tab2:
    st.markdown("### 📂 Arsip Tender & Realisasi Revenue")
    st.dataframe(pd.DataFrame({
        "Nama Proyek": ["Rehab Jalan (Konstruksi)", "Penyediaan BBM (Umum)", "Sewa Excavator (Tambang)", "Pembangunan Mess (Konstruksi)"],
        "Nilai Proyek": ["Rp 5 M", "Rp 2 M", "Rp 1.5 M", "Rp 8 M"],
        "Status": ["Menang", "Kalah (Harga Tinggi)", "Menang", "Kalah (Gugur Admin)"],
        "Margin Estimasi": ["15%", "10%", "20%", "18%"],
        "Margin Aktual (Realisasi)": ["12%", "-", "22%", "-"]
    }), hide_index=True, use_container_width=True)

with tab3:
    st.markdown("### 🧠 AI Learning Analytics")
    st.markdown("AI telah menganalisa 24 tender terakhir Anda dan menemukan pola berikut:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.error("🔴 **Pola Kekalahan (Weakness)**")
        st.markdown("- **Sering kalah di proyek konstruksi gedung (>Rp 5M)** akibat harga penawaran rata-rata 8% lebih tinggi dari pemenang.")
        st.markdown("- **Gugur Administrasi:** Sering terjadi masalah pada masa berlaku Surat Dukungan Pabrikan.")
    with col2:
        st.success("🟢 **Pola Kemenangan (Strength)**")
        st.markdown("- **Sangat dominan di sektor Penyewaan Alat Berat & Logistik.** Margin aktual seringkali lebih tinggi dari estimasi (Cuan berlebih).")
        st.markdown("- **Win Rate tinggi pada proyek dengan HPS < Rp 2 Miliar.**")
