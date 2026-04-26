import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Vendor War Mode", page_icon="⚔️", layout="wide")

st.markdown("""
    <style>
    .war-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .war-subheader {
        font-size: 1.2rem;
        color: #FAFAFA;
        text-align: center;
        margin-top: 0;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .premium-badge {
        background: linear-gradient(90deg, #FFD700 0%, #FFA500 100%);
        color: #000;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .mode-card {
        background-color: #1E1E1E;
        border-left: 5px solid #FF4B4B;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .highlight-red { color: #FF4B4B; font-weight: bold; }
    .highlight-green { color: #00FF00; font-weight: bold; }
    .highlight-yellow { color: #FFD700; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div style='text-align: center;'><span class='premium-badge'>👑 PREMIUM FEATURE</span></div>", unsafe_allow_html=True)
st.markdown("<h1 class='war-header'>⚔️ VENDOR WAR MODE ⚔️</h1>", unsafe_allow_html=True)
st.markdown("<p class='war-subheader'>Win Tenders. Maximize Profit. Stay Under the Radar.</p>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Smart Markup Engine", "🕵️ Hidden Markup Mode", "🛡️ Tender Defense", "📊 Final War Strategy"])

# ==========================================
# TAB 1: SMART MARKUP ENGINE
# ==========================================
with tab1:
    st.markdown("### 🎯 Smart Markup Engine")
    st.caption("Upload BOQ/RAB untuk analisis strategi harga optimal per item.")
    
    uploaded_file = st.file_uploader("Upload File Tender (Excel/CSV)", type=['xlsx', 'csv'], key="war_upload")
    
    if uploaded_file or st.button("Simulasi Dummy Data", key="sim_smart"):
        with st.spinner("Menganalisa struktur harga dan pola evaluator..."):
            time.sleep(1.5)
            
            # Dummy Data Generation
            items = ["Beton Bertulang K-250", "Pekerjaan Galian Tanah", "Sewa Scaffolding", "Instalasi Kabel NYM 3x2.5", "Cat Dinding Interior", "Mobilisasi & Demobilisasi"]
            pasar = [1200000, 85000, 45000, 25000, 35000, 5000000]
            
            data = []
            for i, item in enumerate(items):
                p = pasar[i]
                if "Beton" in item:
                    strat = "Pemanis (Margin Tipis)"
                    markup = 3
                    ideal = p * 1.03
                    risk = "Low"
                    catatan = "Item mayor. Evaluator pasti cek detail. Margin tipis agar total kompetitif."
                elif "Sewa" in item or "Mobilisasi" in item:
                    strat = "Margin Tebal (Jarang disorot)"
                    markup = 35
                    ideal = p * 1.35
                    risk = "Low"
                    catatan = "Sulit dibenchmark evaluator. Bebas markup tinggi."
                elif "Kabel" in item:
                    strat = "Balancing Item"
                    markup = 15
                    ideal = p * 1.15
                    risk = "Med"
                    catatan = "Markup wajar, volume rentan berubah. Ambil untung di volume."
                else:
                    strat = "Standar"
                    markup = 10
                    ideal = p * 1.10
                    risk = "Low"
                    catatan = "Harga pasar standar."
                
                margin_val = ideal - p
                
                data.append({
                    "Item Pekerjaan": item,
                    "Harga Pasar (Est)": f"Rp {p:,.0f}",
                    "Strategi Markup": strat,
                    "Markup Aman (%)": f"{markup}%",
                    "Harga Submit Ideal": f"Rp {ideal:,.0f}",
                    "Est. Margin/Unit": f"Rp {margin_val:,.0f}",
                    "Risiko Kalah/Curiga": risk,
                    "Catatan Evaluator": catatan
                })
                
            df_smart = pd.DataFrame(data)
            
            st.success("Analisis Smart Markup Selesai!")
            st.dataframe(df_smart, use_container_width=True)
            
            st.info("**Strategi Makro:** Gunakan item beton/baja sebagai pemanis untuk memenangkan harga total, lalu subsidi silang margin dari item persiapan, mobilisasi, dan aksesoris minor.")

# ==========================================
# TAB 2: HIDDEN MARKUP MODE
# ==========================================
with tab2:
    st.markdown("### 🕵️ Hidden Markup Mode")
    st.caption("Pola markup tersembunyi yang REALISTIS untuk membaca pergerakan kompetitor atau menyusun buffer profit yang masuk akal.")
    st.warning("⚠️ Disclaimer: Mode ini ditujukan untuk edukasi bisnis, strategi penetapan harga yang cerdas, dan mitigasi risiko. Bukan untuk praktik fraud/ilegal.")
    
    hidden_categories = [
        {"kategori": "Mobilisasi & Demobilisasi", "alasan": "Sangat subjektif, sulit dibenchmark. Tidak ada standar baku.", "markup": "30% - 50%", "risiko": "Low", "deteksi": "Evaluator cek rincian sewa alat.", "counter": "Pecah jadi item detail: 'Asuransi alat', 'Biaya pengawalan', 'Loading fee' agar terlihat riil."},
        {"kategori": "Consumable / Alat Bantu Kecil", "alasan": "Sering diabaikan karena nilainya kecil, tapi frekuensi/volumenya banyak.", "markup": "40% - 80%", "risiko": "Low", "deteksi": "Jarang dicek kecuali persentase total anomali.", "counter": "Gabungkan dalam Lumpsum (LS) agar volume tidak bisa didebat."},
        {"kategori": "Pekerjaan Tanah / Galian", "alasan": "Volume lapangan sangat sering berubah (Change Order Potential).", "markup": "15% - 25%", "risiko": "Med", "deteksi": "Opname lapangan.", "counter": "Naikkan harga satuan, karena kemungkinan volume bengkak di lapangan tinggi."},
        {"kategori": "Overtime / Lembur / Cuaca", "alasan": "Kontinjensi risiko murni dari vendor, susah disalahkan.", "markup": "20% - 40%", "risiko": "Low", "deteksi": "Evaluator memotong item kontinjensi.", "counter": "Ganti nama menjadi 'Percepatan Jadwal Khusus' atau 'Safety Weather Protocol'."},
        {"kategori": "Spare Factor Material / Waste", "alasan": "Tiap material punya waste factor. Pemborong bisa klaim waste 10% padahal aslinya 5%.", "markup": "5% - 10%", "risiko": "Med", "deteksi": "Pembandingan dengan koefisien SNI.", "counter": "Gunakan spesifikasi merk yang tidak ada di SNI, klaim bahwa material ini butuh handling khusus."}
    ]
    
    for hc in hidden_categories:
        with st.expander(f"💼 {hc['kategori']}"):
            st.markdown(f"**Kenapa Realistis:** {hc['alasan']}")
            st.markdown(f"**Range Markup Lazim:** <span class='highlight-green'>{hc['markup']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Risiko Ketahuan:** {hc['risiko']}")
            st.markdown(f"**Cara Evaluator Mendeteksi:** {hc['deteksi']}")
            st.markdown(f"**Cara Vendor Cerdas (Counter-Strategy):** {hc['counter']}")

# ==========================================
# TAB 3: TENDER DEFENSE / IZIN MODE
# ==========================================
with tab3:
    st.markdown("### 🛡️ Tender Defense & Administrasi")
    st.caption("Checklist peluru administrasi untuk memastikan lolos fase kualifikasi tanpa gugur konyol.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔴 Dokumen WAJIB (Fatal Jika Salah)")
        st.checkbox("NIB (Nomor Induk Berusaha) - Aktif & KBLI Sesuai")
        st.checkbox("NPWP Perusahaan - Status Valid")
        st.checkbox("SPT Tahunan (Tahun Terakhir)")
        st.checkbox("SBU / Izin Usaha Konstruksi/Pengadaan (Relevan)")
        st.checkbox("Jaminan Penawaran (Asli, Nilai & Masa Berlaku Tepat)")
        st.checkbox("Surat Penawaran Bermaterai & Bertanggal Sesuai Dokumen")
    
    with col2:
        st.markdown("#### 🟡 Dokumen NILAI TAMBAH (Pembeda)")
        st.checkbox("SKK/SKA Tenaga Ahli (Kualifikasi di atas syarat)")
        st.checkbox("Laporan Keuangan Audited (KAP Terdaftar)")
        st.checkbox("ISO 9001 / ISO 14001 / OHSAS 45001")
        st.checkbox("Surat Dukungan Pabrikan (Resmi & Eksklusif)")
        st.checkbox("Bukti Pengalaman Kerja Serupa (Nilai Terbesar/Kompleks)")
    
    st.info("**Risiko Gugur Administrasi Terbesar:** Kesalahan penulisan masa berlaku jaminan penawaran dan KBLI pada NIB yang tidak match dengan syarat tender. Selalu double check 2 item ini!")

# ==========================================
# TAB 4: FINAL WAR STRATEGY
# ==========================================
with tab4:
    st.markdown("### 📊 Laporan Intelijen: Rekomendasi Final")
    
    if st.button("Generate Final Strategy", type="primary"):
        with st.spinner("Merangkum taktik perang..."):
            time.sleep(2)
            
            st.markdown("""
            <div class='mode-card'>
                <h4>🏆 Peluang Menang Tender: <span class='highlight-green'>78%</span></h4>
                <h4>💰 Margin Sehat Estimasi: <span class='highlight-green'>18.5% - 22.0%</span></h4>
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### ⚠️ Titik Rawan Kalah")
                st.markdown("- Harga beton struktural terlalu tinggi (kompetitor sering banting harga di sini).")
                st.markdown("- Pengalaman kerja tidak spesifik menyebutkan jenis pekerjaan yang disyaratkan.")
            with col_b:
                st.markdown("#### 🕵️ Titik Rawan Ketahuan Overpriced")
                st.markdown("- Item sewa alat berat jika di-breakdown per jam (sebaiknya gunakan lumpsum atau per bulan).")
                st.markdown("- Biaya manajemen/K3 yang melebihi 5% dari nilai proyek.")
            
            st.divider()
            
            st.markdown("#### 🎯 Strategi Submit Terbaik")
            st.markdown("> **Gunakan taktik 'Front-Loading' Halus.** Taruh profit di pekerjaan awal (persiapan, tanah, pondasi) untuk memperkuat cashflow. Turunkan harga di pekerjaan akhir (finishing, MEP) agar total tetap kompetitif. Kompetitor yang kesulitan cashflow akan mati perlahan.")
            
            st.markdown("#### 🤝 5 Langkah Negosiasi (Bila Kalah Tipis)")
            st.markdown("1. **Tawarkan Value Engineering:** 'Kami bisa turunkan harga 5% jika spesifikasi cat/keramik diganti ke merk ekuivalen X.'")
            st.markdown("2. **Jaminan Waktu:** 'Kami jamin selesai 2 minggu lebih cepat. Ada denda keterlambatan jika kami gagal.'")
            st.markdown("3. **Skema Pembayaran Fleksibel:** 'Kami siap terima DP lebih kecil jika harga disepakati.'")
            st.markdown("4. **Free Extended Warranty:** 'Kami beri garansi maintenance 6 bulan ekstra gratis.'")
            st.markdown("5. **Buka Buku (Open Book):** 'Mari bedah RAB kami. Kami transparan margin kami hanya X%, sisanya murni biaya kualitas.'")
            
            st.markdown("#### 🏁 Rekomendasi Final")
            st.success("**SUBMIT.** Lakukan pemotongan 2% dari total RAB awal dengan memangkas item finishing, amankan margin di item pondasi & mobilisasi. Ajukan dukungan pabrikan tier-1 untuk menjustifikasi harga jika dipanggil klarifikasi.")
""")
