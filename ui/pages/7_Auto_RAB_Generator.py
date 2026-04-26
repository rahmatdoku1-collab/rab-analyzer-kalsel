import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from services.ai_generator import generate_rab_from_prompt

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem;}
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 2rem; font-weight: 400;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🤖 Auto RAB Generator</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-Powered Cost Estimation (Kalsel Regional Index)</p>', unsafe_allow_html=True)

st.info("Ketikkan deskripsi proyek singkat, AI akan merakit struktur RAB lengkap beserta estimasi biaya berdasarkan harga pasar Kalsel (INKINDO x 0.85).")

prompt_text = st.text_area("Deskripsi Proyek:", placeholder="Contoh: Pemetaan DAS 5000 Ha Tabalong menggunakan drone RTK dan tenaga ahli GIS senior selama 1 bulan", height=100)

if st.button("Generate RAB Otomatis ✨", type="primary"):
    if len(prompt_text) < 10:
        st.error("Deskripsi terlalu singkat. Mohon lebih spesifik.")
    else:
        with st.spinner("AI sedang menghitung dan merakit RAB (Est. 10-15 detik)..."):
            result = generate_rab_from_prompt(prompt_text)
            
            if "error" in result:
                st.error(f"Gagal generate: {result['error']}")
            else:
                st.success(f"Berhasil! Proyek: **{result.get('project_name')}**")
                
                # Metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Estimasi Biaya", f"Rp {result.get('total_estimated_budget', 0):,.0f}")
                with col2:
                    st.metric("Estimasi Waktu", f"{result.get('estimated_duration_days', 0)} Hari")
                
                # Table
                st.markdown("### Rincian Item Pekerjaan")
                df_items = pd.DataFrame(result.get("items", []))
                
                # Format currency
                if not df_items.empty and 'harga_satuan_estimasi' in df_items.columns:
                    df_items['harga_satuan_estimasi'] = df_items['harga_satuan_estimasi'].apply(lambda x: f"Rp {x:,.0f}")
                    df_items['Total'] = df_items.apply(lambda row: f"Rp {row['volume'] * float(str(row['harga_satuan_estimasi']).replace('Rp', '').replace(',', '')):,.0f}", axis=1)
                
                st.dataframe(df_items, use_container_width=True)
                
                # Risks
                st.markdown("### ⚠️ Faktor Risiko Terdeteksi")
                for risk in result.get("risk_factors", []):
                    st.markdown(f"- {risk}")
                    
                st.download_button("Export as CSV", df_items.to_csv(index=False), file_name=f"{result.get('project_name', 'rab')}.csv", mime="text/csv")
