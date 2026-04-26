import streamlit as st
import pandas as pd
import plotly.express as px
from utils import analyze_rab, generate_pdf_report, generate_ai_summary
from database import save_project
import os

# Check Auth
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login dari halaman utama terlebih dahulu.")
    st.stop()

# --- UI/UX Modern CSS ---
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem; letter-spacing: -0.5px;}
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 2rem; font-weight: 400;}
    .metric-card { background-color: #FFFFFF; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border-left: 6px solid #3B82F6; transition: transform 0.2s;}
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .metric-value { font-size: 2rem; font-weight: 800; color: #0F172A; margin-top: 8px;}
    .metric-label { font-size: 0.85rem; color: #64748B; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600;}
    .stButton>button { background-color: #0F172A; color: white; border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem; border: none;}
    .stButton>button:hover { background-color: #1E293B; color: white;}
    .ai-summary-box { background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); border: 1px solid #BAE6FD; border-radius: 12px; padding: 24px; margin-top: 20px;}
    .ai-summary-title { font-weight: 800; color: #0369A1; font-size: 1.2rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">RAB Analyzer Enterprise</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated Cost Analysis & AI Auditing</p>', unsafe_allow_html=True)

# Add API Key input locally if not provided
if 'api_key' not in st.session_state:
    # Membaca dari environment jika ada, jika tidak kosong
    st.session_state['api_key'] = os.environ.get("OPENROUTER_API_KEY", "")

with st.sidebar:
    st.markdown("### 🔑 API Key (OpenRouter)")
    def update_api_key():
        st.session_state['api_key'] = st.session_state['api_key_input']
    
    st.text_input("API Key (Untuk Fitur AI)", type="password", value=st.session_state['api_key'], key="api_key_input", on_change=update_api_key)
    st.caption("API Key Anda otomatis tersimpan selama sesi berjalan.")

uploaded_file = st.file_uploader("Upload RAB Vendor (Excel/CSV)", type=['xlsx', 'csv'])

if uploaded_file is not None:
    try:
        # Pengecekan agar tidak memproses ulang file yang sama persis
        if 'uploaded_filename' not in st.session_state or st.session_state['uploaded_filename'] != uploaded_file.name:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                xls = pd.ExcelFile(uploaded_file)
                if len(xls.sheet_names) > 1:
                    sheet_name = st.selectbox("Pilih Sheet (Tab Excel) RAB Utama:", xls.sheet_names)
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                else:
                    df = pd.read_excel(xls)
                
            with st.spinner("Mengaudit RAB dengan Database Perusahaan & RapidFuzz..."):
                df_results = analyze_rab(df)
                # Simpan ke session state agar tidak hilang saat pindah halaman
                st.session_state['df_results'] = df_results
                st.session_state['uploaded_filename'] = uploaded_file.name
                if 'ai_summary' in st.session_state:
                    del st.session_state['ai_summary']
    except Exception as e:
        st.error(f"Gagal memproses file: {str(e)}")

# Tampilkan data dari session state (mencegah data hilang)
if 'df_results' in st.session_state:
    df_results = st.session_state['df_results']
    st.success(f"🟢 Data aktif: **{st.session_state['uploaded_filename']}** (Data tersimpan sementara, tidak akan hilang saat pindah menu).")
    
    try:
        # Metrics
        total_anggaran = df_results['Total Harga (Rp)'].sum()
        total_hemat = df_results['Potensi Penghematan (Rp)'].sum()
        persentase_hemat = (total_hemat / total_anggaran * 100) if total_anggaran > 0 else 0
        overpriced_count = len(df_results[df_results['Status'] == 'MAHAL (OVERPRICED)'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown(f'<div class="metric-card" style="border-left-color: #3B82F6;"><div class="metric-label">Total RAB Diajukan</div><div class="metric-value">Rp {total_anggaran/1000000:,.1f}M</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card" style="border-left-color: #10B981;"><div class="metric-label">Potensi Hemat</div><div class="metric-value">Rp {total_hemat/1000000:,.1f}M</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card" style="border-left-color: #F59E0B;"><div class="metric-label">Efisiensi</div><div class="metric-value">{persentase_hemat:.1f}%</div></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="metric-card" style="border-left-color: #EF4444;"><div class="metric-label">Item Overpriced</div><div class="metric-value">{overpriced_count}</div></div>', unsafe_allow_html=True)
        
        # Project Saving
        col_save1, col_save2 = st.columns([3, 1])
        with col_save1:
            project_name = st.text_input("Nama Proyek untuk disimpan ke Histori:")
        with col_save2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Save Project", type="secondary", use_container_width=True):
                if project_name:
                    save_project(st.session_state['company_id'], project_name, total_anggaran, df_results)
                    st.success("Project Saved!")
                else:
                    st.error("Nama Proyek Wajib Diisi")

        # AI Summary
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ Generate AI Risk Analysis & Summary", type="primary"):
            with st.spinner("AI sedang melakukan analisis risiko (Procurement Risk)..."):
                ai_summary = generate_ai_summary(df_results, st.session_state['api_key'])
                st.session_state['ai_summary'] = ai_summary
                
        if 'ai_summary' in st.session_state:
            st.markdown(f"""
            <div class="ai-summary-box">
                <div class="ai-summary-title">🤖 AI Procurement Risk Analysis</div>
                <div>{st.session_state['ai_summary'].replace(chr(10), '<br>')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📋 Tabel Audit Detail", "📈 Analisis Visual", "📥 Export Premium Report"])
        
        with tab1:
            st.markdown("#### Detail Audit Harga per Item")
            filter_status = st.multiselect("Filter Status:", options=df_results['Status'].unique(), default=df_results['Status'].unique())
            filtered_df = df_results[df_results['Status'].isin(filter_status)]
            styled_df = filtered_df.copy()
            for col in ['Harga Satuan (Rp)', 'Total Harga (Rp)', 'Harga Rekomendasi (Rp)', 'Potensi Penghematan (Rp)']:
                styled_df[col] = styled_df[col].apply(lambda x: f"Rp {x:,.0f}")
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
        with tab2:
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                status_counts = df_results['Status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Jumlah']
                fig_pie = px.pie(status_counts, values='Jumlah', names='Status', color='Status', hole=0.5,
                                color_discrete_map={'NORMAL (WAJAR)': '#10B981', 'MAHAL (OVERPRICED)': '#EF4444', 'MURAH (UNDERBUDGET)': '#3B82F6', 'REVIEW MANUAL': '#CBD5E1'})
                fig_pie.update_layout(title="Proporsi Status Harga")
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_chart2:
                top_items = df_results.nlargest(5, 'Total Harga (Rp)').copy()
                top_items['Item Pekerjaan'] = top_items['Item Pekerjaan'].apply(lambda x: (str(x)[:45] + '...') if len(str(x)) > 45 else str(x))
                fig_top = px.bar(top_items, x='Total Harga (Rp)', y='Item Pekerjaan', orientation='h', color='Status',
                               color_discrete_map={'NORMAL (WAJAR)': '#10B981', 'MAHAL (OVERPRICED)': '#EF4444', 'MURAH (UNDERBUDGET)': '#3B82F6', 'REVIEW MANUAL': '#CBD5E1'})
                fig_top.update_layout(
                    yaxis={'categoryorder':'total ascending', 'tickfont': {'size': 14}}, 
                    xaxis={'tickfont': {'size': 13}},
                    title="Top 5 Item Terbesar (Pareto)",
                    font=dict(size=14),
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig_top, use_container_width=True)
                
        with tab3:
            st.markdown("#### Export Executive Report (PDF)")
            st.write("Unduh laporan premium untuk dibagikan ke manajemen, PPK, atau Klien.")
            
            if st.button("📄 Buat Dokumen PDF"):
                with st.spinner("Merender PDF resolusi tinggi..."):
                    summary_to_pass = st.session_state.get('ai_summary', '')
                    pdf_path = generate_pdf_report(df_results, "Audit_RAB_Premium.pdf", summary_to_pass)
                    with open(pdf_path, "rb") as file:
                        st.download_button(label="⬇️ Download Premium PDF", data=file, file_name="RAB_Audit_Report.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Gagal memproses visualisasi: {str(e)}")
