import pandas as pd
from datetime import datetime, timedelta
from database import get_db_connection

def update_rolling_averages():
    print(f"[{datetime.now()}] Memulai Pricing Engine (30-Day Rolling Average)...")
    conn = get_db_connection()
    
    # Get all items
    df_items = pd.read_sql_query("SELECT id, nama_item, kategori FROM harga_lokal", conn)
    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    cursor = conn.cursor()
    
    for _, item in df_items.iterrows():
        # Get price history for the last 30 days
        df_hist = pd.read_sql_query(
            "SELECT harga_baru, sumber FROM price_history WHERE harga_lokal_id = ? AND tanggal >= ?",
            conn, params=(item['id'], thirty_days_ago)
        )
        
        if not df_hist.empty and len(df_hist) >= 1: # We have data to update
            # Terapkan Indeks Kalsel (0.85) jika harga asalnya adalah standar Jakarta
            KALSEL_INDEX = 0.85
            if 'Konsultansi' in str(item.get('kategori', '')) and 'Jakarta' in df_hist['sumber'].iloc[0]:
                df_hist['harga_baru'] = df_hist['harga_baru'] * KALSEL_INDEX
                
            harga_min = df_hist['harga_baru'].min()
            harga_max = df_hist['harga_baru'].max()
            harga_rek = df_hist['harga_baru'].mean() # Rolling average as recommendation
            
            # Update database
            cursor.execute('''
                UPDATE harga_lokal 
                SET harga_min = ?, harga_max = ?, harga_rekomendasi = ?, update_terakhir = date('now')
                WHERE id = ?
            ''', (harga_min, harga_max, harga_rek, item['id']))
            
            print(f"Update AI Pricing: {item['nama_item']} -> Rec: Rp {harga_rek:,.0f} (Min: {harga_min}, Max: {harga_max})")
            
    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] Selesai Pricing Engine.")

if __name__ == '__main__':
    update_rolling_averages()
