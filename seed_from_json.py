"""Seed master_harga.db dengan data INKINDO 2025/PMK 32/2025/HSPK Banjarbaru."""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "master_harga.db")

# Format: (sektor, nama_item, satuan, harga_pasar_riil, harga_rab_disarankan, sumber, confidence)
DATA = [
    # ── PERSONIL SEMUA BIDANG ───────────────────────────────────────────────
    ("Jasa Personil","Ketua Tim / Team Leader (S1 ≥10th)","OH",1831410,2450000,"INKINDO 2025 Kalsel idx 0.918",95),
    ("Jasa Personil","Ahli Senior (S1 ≥8th)","OH",1671999,2250000,"INKINDO 2025",95),
    ("Jasa Personil","Ahli Madya (S1 ≥5th)","OH",1477980,2000000,"INKINDO 2025",95),
    ("Jasa Personil","Ahli Muda (S1 ≥2th)","OH",1264545,1700000,"INKINDO 2025",95),
    ("Jasa Personil","Ahli Pertama / Fresh Graduate S1","OH",1193400,1600000,"INKINDO 2025",95),
    ("Jasa Personil","Ahli S2 (≥5th)","OH",1907145,2550000,"INKINDO 2025",95),
    ("Jasa Personil","Ahli S2 (≥10th)","OH",2343195,3150000,"INKINDO 2025",95),
    ("Jasa Personil","Ahli S3 / Doktor","OH",2464830,3350000,"INKINDO 2025",95),
    ("Jasa Personil","Analis / Asisten Ahli (D3/S1)","OH",504900,700000,"INKINDO 2025 Sub-Prof",90),
    ("Jasa Personil","Teknisi Senior (D3/S1 ≥5th)","OH",619650,850000,"INKINDO 2025 Sub-Prof",90),
    ("Jasa Personil","Surveyor Lapangan (D3/S1)","OH",436050,600000,"INKINDO 2025 Sub-Prof",90),
    ("Jasa Personil","Operator GIS / Drafter (D3/S1)","OH",481950,650000,"INKINDO 2025 Sub-Prof",90),
    ("Jasa Personil","Enumerator / Asisten Lapangan","OH",353430,500000,"INKINDO 2025 Sub-Prof",90),
    ("Jasa Personil","Sekretaris (D3/S1)","OH",378675,500000,"INKINDO 2025 Pendukung",90),
    ("Jasa Personil","Operator Komputer","OH",353430,500000,"INKINDO 2025 Pendukung",90),
    ("Jasa Personil","Administrasi Keuangan","OH",403920,550000,"INKINDO 2025 Pendukung",90),
    ("Jasa Personil","Office Boy / Helper","OH",160650,200000,"INKINDO 2025 Pendukung",90),
    ("Jasa Personil","Driver / Pengemudi","OH",252450,350000,"INKINDO 2025 Pendukung",90),

    # ── KEHUTANAN — PERSONIL ────────────────────────────────────────────────
    ("Kehutanan","Ahli Kehutanan Senior (S1 ≥8th)","OH",1450000,2000000,"INKINDO 2025 Kalsel",92),
    ("Kehutanan","Ahli Kehutanan Madya (S1 ≥5th)","OH",1250000,1700000,"INKINDO 2025",92),
    ("Kehutanan","Ahli Lingkungan Hidup (S1 ≥5th)","OH",1300000,1750000,"INKINDO 2025",92),
    ("Kehutanan","Ahli Inventarisasi Hutan (S1 ≥3th)","OH",1100000,1500000,"INKINDO 2025",90),
    ("Kehutanan","Ahli GIS/Pemetaan Kehutanan (S1 ≥3th)","OH",1050000,1450000,"INKINDO 2025",90),
    ("Kehutanan","Ahli Silvikultur (S1 ≥5th)","OH",1200000,1650000,"INKINDO 2025",90),
    ("Kehutanan","Ahli Hidrologi Hutan (S1 ≥5th)","OH",1250000,1700000,"INKINDO 2025",90),
    ("Kehutanan","Analis Data Kehutanan (D3/S1 ≥2th)","OH",550000,800000,"INKINDO Sub-Prof",88),
    ("Kehutanan","Enumerator Lapangan Hutan","OH",330000,450000,"Standar Lapangan Kalsel",80),
    # ── KEHUTANAN — ALAT ────────────────────────────────────────────────────
    ("Kehutanan","GPS Garmin / Trimble (sewa)","Hari",250000,450000,"Harga Pasar Banjarmasin 2026",85),
    ("Kehutanan","Kompas + Klinometer (sewa)","Hari",75000,150000,"Harga Pasar",80),
    ("Kehutanan","Drone DJI Mavic (sewa + operator)","Hari",1000000,1500000,"Harga Pasar Banjarmasin 2026",85),
    ("Kehutanan","Current Meter TH-02 (sewa)","Hari",500000,800000,"Harga Pasar",85),
    ("Kehutanan","Chainsaw (sewa)","Hari",300000,500000,"Harga Pasar",80),
    ("Kehutanan","Alat Ukur Diameter Pohon (Phi-band)","Unit",150000,250000,"Toko Alat Ukur Bjm",80),
    ("Kehutanan","Kamera DSLR (sewa)","Hari",200000,350000,"Harga Pasar",80),
    ("Kehutanan","Kendaraan Roda 4 (sewa+BBM+driver)","Hari",800000,1200000,"INKINDO 2025 Kalsel",90),
    ("Kehutanan","Motor Trail Lapangan (sewa)","Hari",200000,350000,"Harga Pasar",80),
    ("Kehutanan","Tenda / Camping Gear (sewa)","Set/Hari",150000,250000,"Harga Pasar",75),
    # ── KEHUTANAN — ATK ─────────────────────────────────────────────────────
    ("Kehutanan","Cetak Laporan A4 Softcover","Eksemplar",50000,100000,"Percetakan Banjarmasin",90),
    ("Kehutanan","Cetak Laporan Hardcover","Eksemplar",100000,200000,"Percetakan Banjarmasin",90),
    ("Kehutanan","Cetak Peta A3 Full Color","Lembar",20000,35000,"Percetakan Banjarmasin",90),
    ("Kehutanan","Flashdisk 64GB (dokumentasi)","Unit",65000,125000,"Toko Komputer Banjarmasin",85),
    ("Kehutanan","ATK & Bahan Pendukung Lapangan","Paket",300000,500000,"Estimasi",75),

    # ── PERTANIAN — PERSONIL ────────────────────────────────────────────────
    ("Pertanian","Ahli Agronomi Senior (S1 ≥8th)","OH",1400000,1900000,"INKINDO 2025 Kalsel",92),
    ("Pertanian","Ahli Tanah / Kesuburan Lahan (S1 ≥5th)","OH",1200000,1650000,"INKINDO 2025",90),
    ("Pertanian","Ahli Irigasi & Pengairan (S1 ≥5th)","OH",1250000,1700000,"INKINDO 2025",90),
    ("Pertanian","Ahli Perlindungan Tanaman (S1 ≥5th)","OH",1200000,1650000,"INKINDO 2025",90),
    ("Pertanian","Ahli Pangan / Teknologi Pangan (S1 ≥3th)","OH",1050000,1450000,"INKINDO 2025",88),
    ("Pertanian","Ahli Pemetaan Pertanian / GIS (S1 ≥3th)","OH",1050000,1450000,"INKINDO 2025",88),
    ("Pertanian","Ahli Sosek Pertanian (S1 ≥5th)","OH",1150000,1600000,"INKINDO 2025",88),
    ("Pertanian","Penyuluh Pertanian Lapangan","OH",450000,650000,"Standar Dinas Pertanian",80),
    ("Pertanian","Enumerator / Pencacah Data Pertanian","OH",330000,430000,"Standar BPS/Bappeda",80),
    # ── PERTANIAN — ALAT ────────────────────────────────────────────────────
    ("Pertanian","Soil Tester / pH Meter (sewa)","Hari",150000,280000,"Harga Pasar",80),
    ("Pertanian","GPS Lapangan (sewa)","Hari",250000,400000,"Harga Pasar Banjarmasin",85),
    ("Pertanian","Drone Pertanian (sewa + operator)","Hari",1000000,1500000,"Harga Pasar 2026",85),
    ("Pertanian","Kendaraan Roda 4 (sewa+BBM+driver)","Hari",800000,1200000,"INKINDO 2025 Kalsel",90),
    ("Pertanian","Kamera Dokumentasi (sewa)","Hari",150000,250000,"Harga Pasar",80),
    ("Pertanian","Timbangan Digital Lapangan","Unit",200000,350000,"Toko Alat Banjarmasin",80),
    ("Pertanian","Kit Analisis Tanah NPK","Paket",500000,800000,"Lab/Toko Pertanian",82),
    ("Pertanian","Botol Sampel Tanah","Unit",5000,10000,"Toko Kimia",85),
    ("Pertanian","Media Tanam / Sampel Benih","Paket",200000,400000,"Toko Pertanian",75),

    # ── KONSTRUKSI & SIPIL — PERSONIL ───────────────────────────────────────
    ("Konstruksi","Ahli Teknik Sipil Senior (S1 ≥10th)","OH",1500000,2100000,"INKINDO 2025 / Kepmen 33/2025",93),
    ("Konstruksi","Ahli Struktur Bangunan (S1 ≥8th)","OH",1400000,1950000,"INKINDO 2025",92),
    ("Konstruksi","Ahli Geoteknik (S1 ≥8th)","OH",1450000,2000000,"INKINDO 2025",92),
    ("Konstruksi","Ahli Hidrologi & SDA (S1 ≥8th)","OH",1400000,1950000,"INKINDO 2025",92),
    ("Konstruksi","Ahli Jalan & Jembatan (S1 ≥5th)","OH",1250000,1750000,"INKINDO 2025",90),
    ("Konstruksi","Ahli Pengairan / Irigasi (S1 ≥5th)","OH",1200000,1700000,"INKINDO 2025",90),
    ("Konstruksi","Ahli Quantity Surveyor (S1 ≥5th)","OH",1200000,1700000,"INKINDO 2025",90),
    ("Konstruksi","Ahli K3 Konstruksi (S1 ≥3th)","OH",1050000,1500000,"INKINDO 2025",88),
    ("Konstruksi","Drafter / Operator AutoCAD","OH",550000,800000,"INKINDO Sub-Prof",88),
    ("Konstruksi","Surveyor / Juru Ukur","OH",500000,750000,"INKINDO Sub-Prof",88),
    ("Konstruksi","Mandor Lapangan","OH",350000,550000,"SNI/HSPK 2025",85),
    ("Konstruksi","Tenaga Ahli K3 Lapangan","OH",400000,600000,"INKINDO Sub-Prof",85),
    # ── KONSTRUKSI — ALAT ───────────────────────────────────────────────────
    ("Konstruksi","Total Station (sewa)","Hari",500000,850000,"Harga Pasar Banjarmasin",85),
    ("Konstruksi","Waterpass (sewa)","Hari",200000,350000,"Harga Pasar",82),
    ("Konstruksi","Theodolit Digital (sewa)","Hari",350000,600000,"Harga Pasar",82),
    ("Konstruksi","GPS RTK Geodetik (sewa)","Hari",800000,1500000,"Harga Pasar",85),
    ("Konstruksi","Sondir / Cone Penetrometer (sewa)","Hari",1000000,1800000,"Harga Pasar",80),
    ("Konstruksi","Mesin Bor Tanah (sewa)","Hari",1500000,2500000,"Harga Pasar",80),
    ("Konstruksi","Concrete Mixer (sewa)","Hari",300000,500000,"Harga Pasar",82),
    ("Alat Berat","Excavator PC-200/300 (sewa)","Jam",350000,550000,"HSPK Banjarbaru 2025",90),
    ("Alat Berat","Dump Truck 10T (sewa)","Hari",700000,1100000,"HSPK Banjarbaru 2025",90),
    ("Konstruksi","Compactor Plate (sewa)","Hari",250000,450000,"Harga Pasar",80),
    ("Konstruksi","Concrete Vibrator (sewa)","Hari",150000,280000,"Harga Pasar",80),
    ("Konstruksi","Generator 5 KVA (sewa)","Hari",300000,500000,"Harga Pasar",82),
    # ── KONSTRUKSI — MATERIAL ───────────────────────────────────────────────
    ("Konstruksi","Semen Portland 40kg","Sak",75000,90000,"HSPK Banjarbaru 2025",93),
    ("Konstruksi","Pasir Beton","m3",250000,350000,"HSPK Banjarbaru 2025",90),
    ("Konstruksi","Batu Pecah / Split","m3",350000,500000,"HSPK Banjarbaru 2025",90),
    ("Konstruksi","Batu Bata Merah (per 100 buah)","Buah",120000,160000,"Toko Material Lokal",88),
    ("Konstruksi","Besi Beton Ø10mm","Kg",14500,18000,"Toko Besi Banjarmasin",90),
    ("Konstruksi","Besi Beton Ø12mm","Kg",14000,17500,"Toko Besi Banjarmasin",90),
    ("Konstruksi","Kawat Bendrat","Kg",25000,35000,"Toko Besi",85),
    ("Konstruksi","Papan Bekisting","m2",85000,120000,"Toko Kayu",82),
    ("Konstruksi","Cat Tembok (per kg)","Kg",35000,55000,"Toko Bangunan",85),
    ("Konstruksi","Keramik Lantai 40x40","m2",65000,95000,"Toko Bangunan",85),
    ("Konstruksi","Pipa PVC 4 inch / batang","Batang",85000,130000,"Toko Bangunan",85),
    ("Konstruksi","Kayu Kalimantan Kelas II","m3",4000000,5500000,"Toko Kayu Banjarmasin",88),

    # ── PERIKANAN — PERSONIL ────────────────────────────────────────────────
    ("Perikanan","Ahli Perikanan Senior (S1 ≥8th)","OH",1400000,1900000,"INKINDO 2025 Kalsel",90),
    ("Perikanan","Ahli Budidaya Perairan (S1 ≥5th)","OH",1200000,1650000,"INKINDO 2025",88),
    ("Perikanan","Ahli Kualitas Air (S1 ≥5th)","OH",1250000,1700000,"INKINDO 2025",88),
    ("Perikanan","Ahli Oseanografi (S1 ≥5th)","OH",1200000,1650000,"INKINDO 2025",88),
    ("Perikanan","Ahli Biologi Perairan (S1 ≥3th)","OH",1050000,1450000,"INKINDO 2025",88),
    ("Perikanan","Ahli Sosek Perikanan (S1 ≥5th)","OH",1150000,1600000,"INKINDO 2025",88),
    ("Perikanan","Ahli Teknologi Hasil Perikanan (S1 ≥3th)","OH",1050000,1450000,"INKINDO 2025",88),
    ("Perikanan","Analis Data Perikanan (D3/S1 ≥2th)","OH",550000,800000,"INKINDO Sub-Prof",85),
    ("Perikanan","Enumerator / Pencacah Lapangan","OH",330000,430000,"Standar BPS/Bappeda",80),
    # ── PERIKANAN — ALAT ────────────────────────────────────────────────────
    ("Perikanan","Water Quality Checker DO/pH/Suhu (sewa)","Hari",350000,600000,"Harga Pasar",82),
    ("Perikanan","Jaring Plankton / Bentos","Hari",200000,350000,"Harga Pasar",78),
    ("Perikanan","Secchi Disk","Hari",75000,150000,"Harga Pasar",75),
    ("Perikanan","Perahu Motor (sewa + BBM)","Hari",500000,900000,"Harga Pasar Kalsel",82),
    ("Perikanan","Echosounder / Fish Finder (sewa)","Hari",400000,700000,"Harga Pasar",80),
    ("Perikanan","Coolbox / Wadah Sampel","Hari",100000,200000,"Harga Pasar",78),
    ("Perikanan","Reagen Analisis Kualitas Air","Paket",500000,900000,"Lab/Toko Kimia",80),
    ("Perikanan","Botol Sampel Air","Lusin",120000,200000,"Toko Kimia",85),
    ("Perikanan","Formaldehyde 40% (fiksasi)","Liter",150000,250000,"Toko Kimia",85),

    # ── NON-PERSONIL UMUM — TRANSPORT ───────────────────────────────────────
    ("Logistik","Sewa Kendaraan Roda 4 (O&M, tanpa driver)","Hari",800000,1200000,"INKINDO 2025 Kalsel idx 0.924",92),
    ("Logistik","Sewa Kendaraan Roda 4 (full driver)","Hari",900000,1350000,"Harga Pasar 2026",88),
    ("BBM & Logistik","BBM Operasional Lapangan (Pertalite)","Liter",10200,12500,"SPBU Pertamina Apr 2026",95),
    ("Logistik","Sewa Motor Trail Lapangan","Hari",200000,350000,"Harga Pasar",80),
    ("Logistik","Tiket Pesawat Bjm–Jakarta PP","Orang",1800000,2500000,"Estimasi Pasar Apr 2026",75),
    ("Logistik","Uang Harian Perjalanan Dinas (Dalam Kota)","OH",150000,250000,"PMK 32/2025 SBM",95),
    ("Logistik","Uang Harian Perjalanan Dinas (Luar Kota)","OH",400000,600000,"PMK 32/2025 SBM",95),
    # ── NON-PERSONIL — AKOMODASI ────────────────────────────────────────────
    ("Akomodasi","Hotel Bintang 2 (Banjarmasin)","Malam",250000,350000,"Harga Pasar",85),
    ("Akomodasi","Hotel Bintang 3 (Banjarmasin)","Malam",450000,650000,"Harga Pasar",85),
    ("Akomodasi","Uang Makan Harian Lapangan","OH",75000,125000,"Estimasi",80),
    ("Akomodasi","Konsumsi Rapat (Snack + Makan)","Orang",50000,100000,"PMK 32/2025 SBM",90),
    # ── NON-PERSONIL — ATK ──────────────────────────────────────────────────
    ("ATK & Cetak","Kertas HVS A4 70gr","Rim",55000,80000,"Toko Palm Banjarmasin",90),
    ("ATK & Cetak","Kertas HVS F4 70gr","Rim",60000,90000,"Toko Palm Banjarmasin",90),
    ("ATK & Cetak","Tinta Printer (Set CMYK)","Set",350000,500000,"Toko Komputer",85),
    ("ATK & Cetak","Materai Rp 10.000","Lembar",10000,12000,"Kantor Pos",95),
    ("ATK & Cetak","Flashdisk 32GB","Unit",65000,125000,"Toko Komputer Banjarmasin",88),
    ("ATK & Cetak","Flashdisk 64GB","Unit",90000,175000,"Toko Komputer Banjarmasin",88),
    ("ATK & Cetak","HDD Eksternal 1TB","Unit",500000,750000,"Toko Komputer Banjarmasin",88),
    ("ATK & Cetak","HDD Eksternal 2TB","Unit",800000,1100000,"Toko Komputer Banjarmasin",88),
    # ── NON-PERSONIL — CETAK ────────────────────────────────────────────────
    ("ATK & Cetak","Cetak Laporan A4 B/W (per lembar)","Lembar",500,1500,"Percetakan Banjarmasin",90),
    ("ATK & Cetak","Cetak Laporan A4 Warna (per lembar)","Lembar",1500,3000,"Percetakan Banjarmasin",90),
    ("ATK & Cetak","Cetak Peta A3 Full Color Art Paper","Lembar",20000,35000,"Percetakan Banjarmasin",90),
    ("ATK & Cetak","Laminasi Peta A3 (Doff/Gloss)","Lembar",8000,15000,"Percetakan Banjarmasin",88),
    ("ATK & Cetak","Jilid Softcover + Spiral","Eksemplar",20000,45000,"Percetakan Banjarmasin",90),
    ("ATK & Cetak","Hardcover / Jilid Eksklusif","Eksemplar",80000,175000,"Percetakan Banjarmasin",88),
    ("ATK & Cetak","CD/DVD Dokumentasi","Keping",5000,15000,"Toko Komputer",85),
    ("ATK & Cetak","Banner / Backdrop (per m2)","m2",50000,90000,"Percetakan Banjarmasin",88),
    # ── NON-PERSONIL — KOMUNIKASI ───────────────────────────────────────────
    ("Teknologi","Paket Data Internet (per bulan)","Bulan",100000,200000,"Provider Lokal",85),
    ("Teknologi","Pulsa / Komunikasi Lapangan","Bulan",50000,150000,"Estimasi",78),
    ("Teknologi","Hosting Website / WebGIS (per bulan)","Bulan",100000,350000,"Penyedia Hosting",80),
    ("Teknologi","Lisensi ArcGIS Pro (alokasi per proyek)","LS",2500000,8500000,"Esri Indonesia",85),
    ("Teknologi","Software HEC-HMS/RAS (alokasi)","LS",500000,1500000,"Estimasi",75),
    # ── NON-PERSONIL — ALAT SURVEI UMUM ────────────────────────────────────
    ("Alat Survei","GPS Handheld Garmin / Trimble","Hari",250000,450000,"Harga Pasar Banjarmasin",88),
    ("Alat Survei","GPS RTK Geodetik","Hari",800000,1500000,"Harga Pasar",85),
    ("Alat Survei","Drone DJI Mavic 2 Zoom (+ operator)","Hari",1000000,1500000,"Harga Pasar 2026",88),
    ("Alat Survei","Kamera DSLR (sewa)","Hari",200000,350000,"Harga Pasar",85),
    ("Alat Survei","Tenda Lapangan + Perlengkapan","Set/Hari",150000,300000,"Harga Pasar",78),
]

def seed():
    conn = sqlite3.connect(DB)

    # Add columns if not exist
    existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(master_harga)").fetchall()]
    if "harga_pasar" not in existing_cols:
        conn.execute("ALTER TABLE master_harga ADD COLUMN harga_pasar REAL DEFAULT 0")
    if "confidence_score" not in existing_cols:
        conn.execute("ALTER TABLE master_harga ADD COLUMN confidence_score INTEGER DEFAULT 80")
    conn.commit()

    inserted = 0
    skipped = 0
    for sektor, nama, sat, pasar, rab, sumber, conf in DATA:
        exists = conn.execute(
            "SELECT id FROM master_harga WHERE nama_item=? AND sektor=?", (nama, sektor)
        ).fetchone()
        if exists:
            skipped += 1
            continue
        conn.execute("""
            INSERT INTO master_harga
            (sektor, nama_item, satuan, harga_min, harga_max, harga_median, harga_pasar, sumber, lokasi, confidence_score, updated_at)
            VALUES (?,?,?,?,?,?,?,?,'Kalsel',?,CURRENT_DATE)
        """, (sektor, nama, sat, pasar, rab, rab, pasar, sumber, conf))
        inserted += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM master_harga").fetchone()[0]
    conn.close()
    print(f"Inserted: {inserted} | Skipped (duplicate): {skipped} | Total DB: {total}")

if __name__ == "__main__":
    seed()
