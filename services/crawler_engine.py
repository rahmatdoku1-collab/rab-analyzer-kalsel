import random
import time
from datetime import datetime
from database import get_db_connection

def fetch_solar_industri():
    """Dummy fetcher for Solar Industri in Kalsel"""
    # Simulate network delay
    time.sleep(1)
    
    # Simulate price fluctuation
    base_price = 14500
    fluctuation = random.uniform(-0.02, 0.05) # -2% to +5%
    current_price = base_price * (1 + fluctuation)
    
    return {
        "kategori": "Bahan Bakar",
        "nama_item": "Solar Industri (Non-Subsidi)",
        "satuan": "Liter",
        "harga": round(current_price, -2),
        "lokasi": "Kalimantan Selatan",
        "sumber": "Situs Resmi Pertamina (Simulasi)",
        "confidence_score": 95
    }

def fetch_drone_rental():
    """Dummy fetcher for Drone Mapping services"""
    time.sleep(1)
    
    base_price = 3500000
    fluctuation = random.uniform(-0.05, 0.10)
    current_price = base_price * (1 + fluctuation)
    
    return {
        "kategori": "Jasa Survei",
        "nama_item": "Sewa Drone Pemetaan (RTK) + Pilot",
        "satuan": "Hari",
        "harga": round(current_price, -4),
        "lokasi": "Banjarbaru",
        "sumber": "Marketplace Vendor Lokal (Simulasi)",
        "confidence_score": 85
    }

def run_crawlers():
    print(f"[{datetime.now()}] Memulai Market Price Crawler...")
    new_data = [
        fetch_solar_industri(),
        fetch_drone_rental()
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for item in new_data:
        # Check if item exists in harga_lokal
        cursor.execute("SELECT id FROM harga_lokal WHERE nama_item LIKE ?", (f"%{item['nama_item']}%",))
        row = cursor.fetchone()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if row:
            # Insert into price history
            cursor.execute('''
                INSERT INTO price_history (harga_lokal_id, harga_baru, sumber, tanggal)
                VALUES (?, ?, ?, ?)
            ''', (row['id'], item['harga'], item['sumber'], today))
            print(f"Update histori harga: {item['nama_item']} -> Rp {item['harga']}")
        else:
            # If not exist, add as new item
            cursor.execute('''
                INSERT INTO harga_lokal (kategori, nama_item, satuan, harga_min, harga_max, harga_rekomendasi, sumber_1, lokasi, confidence_score, update_terakhir)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['kategori'], item['nama_item'], item['satuan'], item['harga']*0.9, item['harga']*1.1, item['harga'], item['sumber'], item['lokasi'], item['confidence_score'], today))
            
            new_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO price_history (harga_lokal_id, harga_baru, sumber, tanggal)
                VALUES (?, ?, ?, ?)
            ''', (new_id, item['harga'], item['sumber'], today))
            
            print(f"Item baru ditambahkan: {item['nama_item']} -> Rp {item['harga']}")
            
    conn.commit()
    conn.close()
    print(f"[{datetime.now()}] Selesai Market Price Crawler.")

if __name__ == '__main__':
    run_crawlers()
