from sqlalchemy.orm import Session
from models.vendor_models import Vendor
from models.rab_models import Tender

def calculate_vendor_score(vendor_id: int, db: Session) -> float:
    """
    Vendor Intelligence: Menghitung ulang Reliability Score berdasarkan:
    - Sejarah menang/kalah tender
    - Tendensi markup harga (Overpriced tendency)
    - Respons speed
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        return 0.0
        
    tenders = db.query(Tender).filter(Tender.vendor_name == vendor.name).all()
    
    # Logic scoring algoritmik sederhana
    base_score = 100.0
    
    # Kurangi skor jika overpriced tendency tinggi
    penalty = vendor.overpriced_tendency * 100  # Jika tendency 0.1 (10%), kurangi 10 poin
    
    # Bonus jika history tender bagus (risk score low)
    bonus = 0
    for t in tenders:
        if t.risk_score == "Low": bonus += 2
        elif t.risk_score == "High": penalty += 5
        
    final_score = base_score + bonus - penalty
    
    # Cap between 0 and 100
    final_score = max(0.0, min(100.0, final_score))
    
    vendor.reliability_score = final_score
    db.commit()
    
    return final_score

def scan_lpse_tender_radar():
    """
    Tender Radar: Simulasi scanning LPSE/Tender baru di Kalsel.
    """
    # Di masa depan, ini akan scrape lpse.kalselprov.go.id
    return [
        {"title": "Pemetaan DAS Barito", "lokasi": "Banjarmasin", "nilai_pagu": 250000000},
        {"title": "Pengadaan Drone RTK Kehutanan", "lokasi": "Banjarbaru", "nilai_pagu": 150000000}
    ]
