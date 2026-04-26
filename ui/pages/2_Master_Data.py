import streamlit as st
import pandas as pd
from database import get_db_connection, delete_item, update_item

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login dari halaman utama terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem; letter-spacing: -0.5px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Master Data Harga Lokal</p>', unsafe_allow_html=True)
st.write("Database Harga Acuan ini bersifat Global dan dapat digunakan di semua proyek.")

conn = get_db_connection()
df_db = pd.read_sql_query("SELECT id, kategori, nama_item, satuan, harga_min, harga_max, harga_rekomendasi, sumber_1, update_terakhir FROM harga_lokal", conn)
conn.close()

tab_view, tab_add, tab_bulk = st.tabs(["👁️ Lihat & Edit Data", "➕ Tambah Manual", "📥 Import Massal (Excel)"])

with tab_view:
    search_query = st.text_input("🔍 Cari Item:")
    filtered_db = df_db.copy()
    if search_query:
        filtered_db = filtered_db[filtered_db['nama_item'].str.contains(search_query, case=False)]
        
    st.info("💡 Tips: Anda bisa double-click pada tabel di bawah untuk mengedit harga secara langsung!")
    edited_df = st.data_editor(filtered_db, use_container_width=True, hide_index=True, disabled=["id", "update_terakhir"])
    
    if st.button("💾 Simpan Perubahan Harga (Live Edit)"):
        import sqlite3
        conn = sqlite3.connect('data/harga_lokal.db')
        cursor = conn.cursor()
        for idx, row in edited_df.iterrows():
            cursor.execute('''
                UPDATE harga_lokal 
                SET kategori=?, nama_item=?, satuan=?, harga_min=?, harga_max=?, harga_rekomendasi=?, sumber_1=?, update_terakhir=date('now')
                WHERE id=?
            ''', (row['kategori'], row['nama_item'], row['satuan'], row['harga_min'], row['harga_max'], row['harga_rekomendasi'], row['sumber_1'], row['id']))
        conn.commit()
        conn.close()
        st.success("Perubahan harga berhasil diperbarui di Database Kalsel!")
        st.rerun()
    st.markdown("#### Hapus Item")
    del_id = st.number_input("Masukkan ID Item yang ingin dihapus:", min_value=0, step=1)
    if st.button("🗑️ Hapus ID tersebut"):
        if del_id in df_db['id'].values:
            delete_item(del_id)
            st.success(f"Item ID {del_id} berhasil dihapus!")
            st.rerun()
        else:
            st.error("ID tidak ditemukan.")
            
with tab_add:
    with st.form("add_form"):
        new_kat = st.selectbox("Kategori", df_db['kategori'].unique().tolist() + ["Kategori Baru"])
        if new_kat == "Kategori Baru":
            new_kat = st.text_input("Nama Kategori Baru")
        col1, col2 = st.columns(2)
        with col1:
            new_nama = st.text_input("Nama Item (Misal: Sewa Alat)")
            new_satuan = st.text_input("Satuan (M2, LS, dll)")
        with col2:
            new_hmin = st.number_input("Harga Minimum", min_value=0)
            new_hmax = st.number_input("Harga Maximum", min_value=0)
            new_hrek = st.number_input("Harga Tengah/Wajar", min_value=0)
        new_sumber = st.text_input("Sumber (Contoh: E-Katalog, Vendor X)")
        
        if st.form_submit_button("Simpan ke Database"):
            if new_nama:
                import sqlite3
                conn = sqlite3.connect('data/harga_lokal.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO harga_lokal (kategori, nama_item, satuan, harga_min, harga_max, harga_rekomendasi, sumber_1, update_terakhir) VALUES (?,?,?,?,?,?,?,date('now'))", (new_kat, new_nama, new_satuan, new_hmin, new_hmax, new_hrek, new_sumber))
                conn.commit()
                conn.close()
                st.success("Tersimpan!")
                st.rerun()
                
with tab_bulk:
    st.info("Upload file Excel dengan kolom: kategori, nama_item, satuan, harga_min, harga_max, harga_rekomendasi, sumber_1")
    bulk_file = st.file_uploader("Upload Excel Master Harga", type=['xlsx'])
    if bulk_file:
        if st.button("Proses Import Massal"):
            try:
                bulk_df = pd.read_excel(bulk_file)
                import sqlite3
                conn = sqlite3.connect('data/harga_lokal.db')
                bulk_df['update_terakhir'] = pd.Timestamp('today').strftime('%Y-%m-%d')
                bulk_df[['kategori', 'nama_item', 'satuan', 'harga_min', 'harga_max', 'harga_rekomendasi', 'sumber_1', 'update_terakhir']].to_sql('harga_lokal', conn, if_exists='append', index=False)
                conn.close()
                st.success(f"{len(bulk_df)} item berhasil diimport massal!")
            except Exception as e:
                st.error(f"Error saat import massal: {e}. Pastikan nama kolom Excel sesuai instruksi.")
