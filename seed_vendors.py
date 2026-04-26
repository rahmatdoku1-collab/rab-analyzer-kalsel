import sqlite3
from datetime import datetime
from database import get_db_connection, create_db

def seed_vendors():
    # Ensure DB and tables exist
    create_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    vendors_data = [
        ("PT. Kalimantan Konstruksindo Utama", "Infrastruktur Jalan & Jembatan", 96.5, 3.5, "Fast", 24),
        ("PT. Sapta Jasa Konstruksi", "Gedung Komersial", 92.0, 6.0, "Fast", 15),
        ("PT. Bangun Banua Kalsel", "Proyek Pemerintah & BUMD", 88.5, 8.5, "Medium", 32),
        ("PT. Bimasuta Primatama Karya", "Sipil & Tata Air", 75.0, 18.0, "Slow", 5),
        ("Bimo Laksana Group, PT.", "Konstruksi Menengah", 81.0, 12.0, "Medium", 8)
    ]
    
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for v in vendors_data:
        try:
            cursor.execute('''
                INSERT INTO vendors_intelligence 
                (nama_vendor, spesialisasi, reliability_score, overpriced_tendency, response_speed, menang_tender, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (v[0], v[1], v[2], v[3], v[4], v[5], today, today))
        except sqlite3.IntegrityError:
            # If already exists, update it to refresh data
            cursor.execute('''
                UPDATE vendors_intelligence
                SET spesialisasi=?, reliability_score=?, overpriced_tendency=?, response_speed=?, menang_tender=?, updated_at=?
                WHERE nama_vendor=?
            ''', (v[1], v[2], v[3], v[4], v[5], today, v[0]))
            
    conn.commit()
    conn.close()
    print("Database vendors_intelligence berhasil di-seed dengan data riil.")

if __name__ == "__main__":
    seed_vendors()
