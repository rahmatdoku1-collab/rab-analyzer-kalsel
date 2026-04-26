from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.models_learning import get_db, EditLearning, PromptLog

router = APIRouter()

@router.get("/vendor_markup_analysis")
def vendor_markup_analysis(item_name: str, db: Session = Depends(get_db)):
    """
    Engine untuk menganalisa secara historis, seberapa sering harga sebuah item di-markup tinggi,
    dan bagaimana tren revisi/koreksi user terhadap item tersebut.
    """
    edits = db.query(EditLearning).filter(EditLearning.item_name.ilike(f"%{item_name}%")).all()
    
    if not edits:
        return {"status": "no_data", "message": f"Belum ada histori markup/revisi untuk {item_name}"}
        
    total_revisions = len(edits)
    total_markup_detected = sum(1 for e in edits if e.old_value > e.new_value)
    
    avg_old = sum(e.old_value for e in edits) / total_revisions
    avg_new = sum(e.new_value for e in edits) / total_revisions
    
    markup_percentage = ((avg_old - avg_new) / avg_new) * 100 if avg_new > 0 else 0
    
    return {
        "status": "success",
        "item_name": item_name,
        "total_historical_revisions": total_revisions,
        "markup_frequency": f"{total_markup_detected} dari {total_revisions} pengajuan",
        "average_system_estimate": avg_old,
        "average_user_corrected_price": avg_new,
        "average_markup_percentage": f"{markup_percentage:.2f}%",
        "recommendation": "Gunakan harga koreksi user sebagai patokan karena sistem AI terbukti sering di-mark-down oleh user." if markup_percentage > 10 else "Harga AI cukup stabil."
    }

@router.post("/trigger_auto_correction")
def auto_correct_master_db(db: Session = Depends(get_db)):
    """
    Cron-job endpoint: Mencari pola item yang direvisi >3 kali oleh user berbeda,
    lalu secara otomatis menyarankan atau langsung meng-update database Master lokal.
    """
    # Mencari item yang sering direvisi
    frequent_edits = db.query(
        EditLearning.item_name,
        func.count(EditLearning.id).label('edit_count'),
        func.avg(EditLearning.new_value).label('avg_new_price')
    ).group_by(EditLearning.item_name).having(func.count(EditLearning.id) >= 3).all()
    
    corrections_made = []
    for edit in frequent_edits:
        item = edit.item_name
        new_price = float(edit.avg_new_price)
        
        # Di sini logika untuk UPDATE sqlite data/rab_database.db
        # Karena kita menggunakan SQLAlchemy di backend, kita bisa melakukan koneksi terpisah
        # ke rab_database lokal dan melakukan update harga master.
        # Untuk MVP SaaS, kita log sarannya dulu:
        corrections_made.append({
            "item": item,
            "suggested_master_price": new_price,
            "trigger": f"Direvisi {edit.edit_count} kali oleh komunitas user"
        })
        
    return {
        "status": "success",
        "corrections_pending_approval": corrections_made
    }
