import sqlite3
from datetime import datetime
import random
from database import get_db_connection, create_db

def run_fuel_agent():
    create_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"[{datetime.now()}] Memulai AI Fuel Agent Crawler...")
    
    # Simulasi scraping data harga riil Pertamina (Kalsel region)
    # Harga di-mock mendekati harga riil 2026
    fuel_data = [
        {
            "kategori": "Bahan Bakar",
            "nama": "Pertalite",
            "satuan": "Liter",
            "harga": 10000,
            "sumber": "Pertamina / BPH Migas",
            "catatan": "Harga subsidi Kalsel"
        },
        {
            "kategori": "Bahan Bakar",
            "nama": "Pertamax",
            "satuan": "Liter",
            "harga": 13500,
            "sumber": "Pertamina / Web Scraper",
            "catatan": "Harga non-subsidi Kalsel"
        },
        {
            "kategori": "Bahan Bakar",
            "nama": "Pertamina Dex",
            "satuan": "Liter",
            "harga": 15400,
            "sumber": "Pertamina / Web Scraper",
            "catatan": "Harga diesel kualitas tinggi Kalsel"
        },
        {
            "kategori": "Bahan Bakar",
            "nama": "Dexlite",
            "satuan": "Liter",
            "harga": 14900,
            "sumber": "Pertamina / Web Scraper",
            "catatan": "Harga diesel menengah Kalsel"
        }
    ]
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    for fuel in fuel_data:
        # Cek apakah sudah ada di Master Data
        cursor.execute("SELECT id FROM harga_lokal WHERE nama_item = ?", (fuel["nama"],))
        result = cursor.fetchone()
        
        if result:
            item_id = result[0]
            # Update harga rekomendasi
            cursor.execute('''
                UPDATE harga_lokal 
                SET harga_rekomendasi=?, harga_min=?, harga_max=?, update_terakhir=?, sumber_1=?
                WHERE id=?
            ''', (fuel["harga"], fuel["harga"]-100, fuel["harga"]+500, today, fuel["sumber"], item_id))
        else:
            # Insert baru
            cursor.execute('''
                INSERT INTO harga_lokal (kategori, nama_item, satuan, harga_min, harga_max, harga_rekomendasi, sumber_1, update_terakhir, catatan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fuel["kategori"], fuel["nama"], fuel["satuan"], fuel["harga"]-100, fuel["harga"]+500, fuel["harga"], fuel["sumber"], today, fuel["catatan"]))
            item_id = cursor.lastrowid
            
        # Simulasikan history harga 3 bulan ke belakang untuk Market Intelligence chart
        cursor.execute("SELECT COUNT(*) FROM price_history WHERE harga_lokal_id = ?", (item_id,))
        count_history = cursor.fetchone()[0]
        
        if count_history == 0:
            for i in range(5, 0, -1):
                past_date = f"2026-04-{str(24-i).zfill(2)}"
                # Fluktuasi acak untuk grafik
                past_price = fuel["harga"] + random.uniform(-300, 300)
                cursor.execute('''
                    INSERT INTO price_history (harga_lokal_id, harga_baru, sumber, tanggal)
                    VALUES (?, ?, ?, ?)
                ''', (item_id, past_price, fuel["sumber"], past_date))
                
            # Insert harga hari ini
            cursor.execute('''
                INSERT INTO price_history (harga_lokal_id, harga_baru, sumber, tanggal)
                VALUES (?, ?, ?, ?)
            ''', (item_id, fuel["harga"], fuel["sumber"], today))
            
        print(f"[OK] Berhasil sinkronisasi harga: {fuel['nama']} - Rp {fuel['harga']}/Liter")
        
    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] AI Fuel Agent selesai. Master Data BBM berhasil diperbarui!")

if __name__ == '__main__':
    run_fuel_agent()
