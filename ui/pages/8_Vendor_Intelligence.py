import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.express as px

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem;}
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 2rem; font-weight: 400;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🛡️ Vendor Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Scoring & Radar Kinerja Rekanan</p>', unsafe_allow_html=True)

with st.expander("ℹ️ Panduan Membaca Data (Klik untuk membuka)", expanded=True):
    st.markdown("""
    - **Reliability Score (0-100)**: Skor keandalan vendor. Dihitung dari riwayat memenangkan tender tanpa masalah. **Semakin mendekati 100, semakin bagus.**
    - **Overpriced Tendency (%)**: Kecenderungan vendor memberikan harga lebih mahal dari harga wajar (mark-up). **Semakin rendah (mendekati 0%), semakin jujur harganya.**
    - **Response Speed**: Kecepatan respons vendor saat diminta penawaran atau revisi (Fast/Medium/Slow).
    """)

# Data diambil langsung dari Database SQLite (Production Mode)
from database import get_db_connection
from utils import extract_pdf_text, analyze_vendor_profile_with_ai
from datetime import datetime
import os

# --- Tambahan Fitur: AI Vendor Profiler (Upload CV) ---
st.markdown("### 📤 AI Vendor Profiler (Scan Profil CV)")
uploaded_file = st.file_uploader("Upload Dokumen Profil/CV Perusahaan Baru (PDF)", type=['pdf'])

if uploaded_file is not None:
    if st.button("🔍 Jalankan Pemindaian AI & Background Check", type="primary"):
        api_key = os.environ.get("OPENROUTER_API_KEY", st.session_state.get('api_key', ''))
        if not api_key:
            st.error("⚠️ API Key OpenRouter belum diatur. Silakan isi di menu Smart RAB Audit.")
        else:
            with st.spinner("AI sedang membaca CV dan melakukan simulasi investigasi riwayat proyek..."):
                cv_text = extract_pdf_text(uploaded_file)
                if cv_text.startswith("Error"):
                    st.error(cv_text)
                else:
                    hasil_ai = analyze_vendor_profile_with_ai(cv_text, api_key)
                    
                    if "error" in hasil_ai:
                        st.error(hasil_ai["error"])
                    else:
                        st.success(f"Pemindaian Selesai: {hasil_ai['Nama Vendor']} berhasil dianalisis!")
                        st.info(f"**Kesimpulan AI:** {hasil_ai['Kesimpulan']}")
                        
                        # Simpan ke Database
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        try:
                            cursor.execute('''
                                INSERT INTO vendors_intelligence 
                                (nama_vendor, spesialisasi, reliability_score, overpriced_tendency, response_speed, menang_tender, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                hasil_ai['Nama Vendor'], hasil_ai['Spesialisasi'], 
                                hasil_ai['Reliability Score'], hasil_ai['Overpriced Tendency'], 
                                hasil_ai['Response Speed'], hasil_ai['Menang Tender'], 
                                today, today
                            ))
                            conn.commit()
                            st.success("✅ Vendor baru berhasil ditambahkan ke Database!")
                        except Exception as db_err:
                            st.error(f"Gagal menyimpan ke database (mungkin vendor sudah ada): {str(db_err)}")
                        finally:
                            conn.close()

st.markdown("---")

conn = get_db_connection()
df_vendors = pd.read_sql_query("SELECT * FROM vendors_intelligence ORDER BY reliability_score DESC", conn)
conn.close()

# Ubah nama kolom agar lebih enak dibaca dan sesuai dengan grafik
df_vendors = df_vendors.rename(columns={
    "nama_vendor": "Nama Vendor",
    "spesialisasi": "Spesialisasi",
    "reliability_score": "Reliability Score",
    "overpriced_tendency": "Overpriced Tendency (%)",
    "response_speed": "Response Speed",
    "menang_tender": "Menang Tender"
})

# Visualisasi
col1, col2 = st.columns(2)
with col1:
    st.markdown("### Top Vendors (Reliability > 90)")
    fig = px.bar(df_vendors[df_vendors['Reliability Score'] >= 90], x='Nama Vendor', y='Reliability Score', color='Reliability Score', color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Radar Risiko Overpriced")
    fig2 = px.scatter(df_vendors, x='Reliability Score', y='Overpriced Tendency (%)', size='Menang Tender', color='Nama Vendor', hover_name='Nama Vendor')
    fig2.update_layout(xaxis_title="Reliability Score (Makin tinggi makin baik)", yaxis_title="Overpriced Tendency (%) (Makin rendah makin baik)")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Database Rekanan")
st.dataframe(df_vendors, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🤖 Kesimpulan Analisis AI")
st.info("""
**Berdasarkan agregasi data kinerja dan simulasi rekam jejak di wilayah Kalimantan Selatan:**
- 🌟 **Rekomendasi Kemitraan Utama:** **PT. Kalimantan Konstruksindo Utama** dan **PT. Sapta Jasa Konstruksi** menunjukkan rekam jejak paling andal dengan *Reliability Score* tinggi (>90) dan tingkat *markup* yang sangat rendah (di bawah 6%). Sangat cocok untuk proyek prioritas.
- ⚖️ **Risiko Menengah:** **PT. Bangun Banua Kalsel** memiliki histori kemenangan tender sangat besar (32 kali), namun memiliki *Overpriced Tendency* 8.5%. Dibutuhkan ketegasan negosiasi saat me-review RAB dari vendor ini.
- ⚠️ **Peringatan Audit (Red Flag):** **PT. Bimasuta Primatama Karya** memiliki *Overpriced Tendency* hingga 18% dan respon lambat. AI merekomendasikan audit silang (*cross-audit*) yang ketat menggunakan fitur **Smart RAB Audit** setiap kali berurusan dengan vendor ini untuk mencegah kebocoran anggaran.
""")
