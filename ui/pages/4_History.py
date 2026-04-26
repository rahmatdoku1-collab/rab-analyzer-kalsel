import streamlit as st
import pandas as pd
from database import get_company_projects, get_project_items

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login dari halaman utama terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem; letter-spacing: -0.5px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Histori Proyek</p>', unsafe_allow_html=True)
st.write("Daftar RAB yang pernah diaudit dan disimpan oleh perusahaan Anda.")

company_id = st.session_state['company_id']
projects = get_company_projects(company_id)

if projects.empty:
    st.info("Belum ada proyek yang disimpan.")
else:
    display_proj = projects.copy()
    display_proj['total_budget'] = display_proj['total_budget'].apply(lambda x: f"Rp {x:,.0f}")
    st.dataframe(display_proj[['id', 'name', 'total_budget', 'status', 'created_at']], use_container_width=True, hide_index=True)
    
    st.markdown("### Detail Proyek")
    selected_id = st.selectbox("Pilih ID Proyek untuk melihat detail item:", projects['id'].tolist())
    
    if selected_id:
        items = get_project_items(selected_id)
        if not items.empty:
            styled_items = items.copy()
            for col in ['harga_satuan', 'total_harga', 'harga_rekomendasi', 'potensi_penghematan']:
                styled_items[col] = styled_items[col].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(styled_items[['item_name', 'volume', 'satuan', 'harga_satuan', 'total_harga', 'status', 'potensi_penghematan', 'sumber_referensi']], use_container_width=True, hide_index=True)
