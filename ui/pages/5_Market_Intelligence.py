import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_db_connection

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login dari halaman utama terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #0F172A; margin-bottom: 0rem; letter-spacing: -0.5px;}
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 2rem; font-weight: 400;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📈 Market Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Pemantauan Tren Harga & Anomali Pasar Kalsel</p>', unsafe_allow_html=True)

conn = get_db_connection()

# Get Price History
df_history = pd.read_sql_query('''
    SELECT ph.tanggal, hl.nama_item, ph.harga_baru, hl.lokasi 
    FROM price_history ph
    JOIN harga_lokal hl ON ph.harga_lokal_id = hl.id
    ORDER BY ph.tanggal ASC
''', conn)
conn.close()

if df_history.empty:
    st.info("Belum ada histori harga. Sistem crawler otomatis akan segera mengumpulkan data.")
else:
    st.markdown("### Tren Harga Harian (30 Hari Terakhir)")
    
    selected_items = st.multiselect("Pilih Item untuk Dilihat:", df_history['nama_item'].unique(), default=df_history['nama_item'].unique()[:3])
    
    if selected_items:
        filtered_df = df_history[df_history['nama_item'].isin(selected_items)]
        fig = px.line(filtered_df, x='tanggal', y='harga_baru', color='nama_item', markers=True, title="Pergerakan Harga Otomatis")
        fig.update_layout(yaxis_title="Harga (Rp)", xaxis_title="Tanggal")
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Distribusi Wilayah Data")
        dist_df = df_history.groupby('lokasi').size().reset_index(name='jumlah')
        fig_pie = px.pie(dist_df, values='jumlah', names='lokasi', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        st.markdown("### Logs Crawler Terbaru")
        logs = df_history.sort_values(by='tanggal', ascending=False).head(10)
        logs['harga_baru'] = logs['harga_baru'].apply(lambda x: f"Rp {x:,.0f}")
        st.dataframe(logs[['tanggal', 'nama_item', 'harga_baru', 'lokasi']], use_container_width=True, hide_index=True)
