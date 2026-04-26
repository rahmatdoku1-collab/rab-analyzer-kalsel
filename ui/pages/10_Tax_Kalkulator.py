import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem;}
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 2rem; font-weight: 400;}
    .tax-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 24px; margin-bottom: 16px; border-left: 5px solid #10B981;}
    .tax-value { font-size: 1.8rem; font-weight: 800; color: #1E293B; margin-top: 8px;}
    .tax-label { font-size: 0.9rem; color: #64748B; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🧾 Tax & Regulation Center</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Kalkulator PPN 12% & Referensi Pajak Konstruksi</p>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🧮 Kalkulator PPN Termin (Include)", "📖 Referensi Aturan PPh"])

with tab1:
    st.markdown("### Kalkulator Ekstraksi DPP & PPN (Tarif 12%)")
    st.info("💡 Rumus ini diadaptasi langsung dari referensi resmi pajak: `DPP = Harga / 1.12` dan `PPN = DPP * 12%`.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("Masukkan Harga/Nilai Termin yang sudah **Termasuk (Include) PPN 12%**:")
        harga_include = st.number_input("Harga Include PPN (Rp)", min_value=0, value=306526500, step=1000000, format="%d")
        
        # Kalkulasi
        dpp = harga_include / 1.12
        ppn = dpp * 0.12
        
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<div class="tax-card"><div class="tax-label">Dasar Pengenaan Pajak (DPP)</div><div class="tax-value">Rp {dpp:,.2f}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tax-card" style="border-left-color: #EF4444;"><div class="tax-label">PPN Keluaran (12%)</div><div class="tax-value">Rp {ppn:,.2f}</div></div>', unsafe_allow_html=True)
        
    st.success(f"**Verifikasi Silang:** Rp {dpp:,.2f} (DPP) + Rp {ppn:,.2f} (PPN) = **Rp {dpp + ppn:,.2f}** (Harga Include)")

with tab2:
    st.markdown("### Referensi PPh Pasal 4 Ayat (2) Jasa Konstruksi")
    st.markdown("Berikut adalah tarif Pajak Penghasilan Final untuk jasa konstruksi yang berlaku terbaru:")
    
    data_pph = {
        "Jenis Pekerjaan": [
            "Pekerjaan Konstruksi (Pelaksana) - Kualifikasi Kecil",
            "Pekerjaan Konstruksi (Pelaksana) - Kualifikasi Menengah/Besar",
            "Pekerjaan Konstruksi (Pelaksana) - Tanpa Sertifikat",
            "Konsultansi Konstruksi (Perencana/Pengawas) - Memiliki Sertifikat",
            "Konsultansi Konstruksi (Perencana/Pengawas) - Tanpa Sertifikat",
            "Pekerjaan Konstruksi Terintegrasi (EPC) - Memiliki Sertifikat",
            "Pekerjaan Konstruksi Terintegrasi (EPC) - Tanpa Sertifikat"
        ],
        "Tarif PPh Final": ["1.75%", "2.65%", "4.00%", "3.50%", "6.00%", "2.65%", "4.00%"]
    }
    
    st.dataframe(pd.DataFrame(data_pph), use_container_width=True, hide_index=True)
    st.caption("Sumber: Peraturan Pemerintah (PP) Nomor 9 Tahun 2022.")
