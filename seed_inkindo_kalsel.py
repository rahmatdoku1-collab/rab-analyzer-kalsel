import sqlite3
from datetime import datetime
from database import get_db_connection

KALSEL_INDEX = 0.85

def inject_regional_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Standar INKINDO 2025 (Asumsi Harga Dasar Jakarta)
    # Ahli GIS (S1 Pengalaman 5 Tahun): Rp 18.000.000 / Bulan (Jakarta)
    inkindo_ahli_gis_jkt = 18000000
    inkindo_ahli_gis_kalsel = inkindo_ahli_gis_jkt * KALSEL_INDEX
    
    # Surveyor / Asisten (S1 Pengalaman 1 Tahun): Rp 8.000.000 / Bulan (Jakarta)
    inkindo_surveyor_jkt = 8000000
    inkindo_surveyor_kalsel = inkindo_surveyor_jkt * KALSEL_INDEX
    
    # 2. Harga Pasar Riil Banjarmasin / Freelancer Lokal
    # Cetak Peta A0 Full Color Kertas Luster (Banjarmasin)
    cetak_a0_bjm = 180000
    
    # Sewa Alat GPS Geodetic RTK (Lokal Kalsel per Hari)
    sewa_rtk_bjm = 1200000

    seed_data = [
        {
            "kategori": "Jasa Konsultansi (INKINDO)",
            "nama_item": "Tenaga Ahli GIS (S1 - 5 Tahun)",
            "satuan": "Bulan",
            "harga_min": inkindo_ahli_gis_kalsel * 0.9,
            "harga_max": inkindo_ahli_gis_kalsel * 1.1,
            "harga_rek": inkindo_ahli_gis_kalsel,
            "sumber": "Standar INKINDO 2025 x Indeks Kalsel (0.85)",
            "lokasi": "Kalimantan Selatan",
            "confidence": 99
        },
        {
            "kategori": "Jasa Konsultansi (INKINDO)",
            "nama_item": "Surveyor Lapangan (S1 - 1 Tahun)",
            "satuan": "Bulan",
            "harga_min": inkindo_surveyor_kalsel * 0.9,
            "harga_max": inkindo_surveyor_kalsel * 1.1,
            "harga_rek": inkindo_surveyor_kalsel,
            "sumber": "Standar INKINDO 2025 x Indeks Kalsel (0.85)",
            "lokasi": "Kalimantan Selatan",
            "confidence": 99
        },
        {
            "kategori": "Percetakan Lokal",
            "nama_item": "Cetak Peta A0 Full Color (Luster/Glossy)",
            "satuan": "Lembar",
            "harga_min": 150000,
            "harga_max": 250000,
            "harga_rek": cetak_a0_bjm,
            "sumber": "Pasar Riil Banjarmasin",
            "lokasi": "Banjarmasin",
            "confidence": 95
        },
        {
            "kategori": "Sewa Alat",
            "nama_item": "Sewa GPS Geodetic RTK (Rover + Base)",
            "satuan": "Hari",
            "harga_min": 1000000,
            "harga_max": 1500000,
            "harga_rek": sewa_rtk_bjm,
            "sumber": "Vendor Alat Lokal Kalsel",
            "lokasi": "Kalimantan Selatan",
            "confidence": 90
        }
    ]

    for item in seed_data:
        # Check if already exists to avoid duplicates
        cursor.execute("SELECT id FROM harga_lokal WHERE nama_item = ?", (item["nama_item"],))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute('''
                INSERT INTO harga_lokal (kategori, nama_item, satuan, harga_min, harga_max, harga_rekomendasi, sumber_1, lokasi, confidence_score, update_terakhir, catatan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['kategori'], item['nama_item'], item['satuan'], item['harga_min'], item['harga_max'], item['harga_rek'], item['sumber'], item['lokasi'], item['confidence'], today, "Dikalibrasi Otomatis"))
            print(f"Berhasil menambahkan: {item['nama_item']} -> Rp {item['harga_rek']:,.0f}")
        else:
            # Update existing
            cursor.execute('''
                UPDATE harga_lokal 
                SET harga_min=?, harga_max=?, harga_rekomendasi=?, sumber_1=?, lokasi=?, confidence_score=?, update_terakhir=?, catatan=?
                WHERE id=?
            ''', (item['harga_min'], item['harga_max'], item['harga_rek'], item['sumber'], item['lokasi'], item['confidence'], today, "Dikalibrasi Otomatis", row['id']))
            print(f"Berhasil update: {item['nama_item']} -> Rp {item['harga_rek']:,.0f}")

    conn.commit()
    conn.close()
    print("Injeksi INKINDO 2025 & Pasar Kalsel Selesai!")

if __name__ == '__main__':
    inject_regional_data()
