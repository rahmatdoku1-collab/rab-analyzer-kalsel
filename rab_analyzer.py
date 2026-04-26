import logging
import pandas as pd
from rapidfuzz import process, fuzz
from database import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def match_item_to_db(item_name, df_db, threshold=60.0):
    """Mencari item di database yang namanya mirip dengan item di RAB menggunakan RapidFuzz"""
    if df_db.empty:
        return None, 0
        
    choices = df_db['nama_item'].tolist()
    match = process.extractOne(str(item_name), choices, scorer=fuzz.WRatio)
    
    if match:
        best_match_str, best_score, best_idx = match
        if best_score >= threshold:
            return df_db.iloc[best_idx], best_score
    return None, 0

def analyze_rab(df_rab):
    """Menganalisis DataFrame RAB terhadap database lokal"""
    logger.info("Memulai analisis RAB...")
    try:
        conn = get_db_connection()
        df_db = pd.read_sql_query("SELECT * FROM harga_lokal", conn)
        conn.close()
    except Exception as e:
        logger.error(f"Gagal memuat database: {e}")
        raise
    
    # 1. Cleaning
    df_rab = df_rab.dropna(how='all').dropna(axis=1, how='all')
    df_rab = df_rab.reset_index(drop=True)
    
    # 2. Auto Header Search
    header_idx = 0
    keywords = ['uraian', 'pekerjaan', 'item', 'nama', 'harga', 'jumlah', 'total', 'vol', 'qty']
    
    cols_str = ' '.join([str(c).lower() for c in df_rab.columns])
    if sum(1 for kw in keywords if kw in cols_str) >= 2:
        header_idx = -1
    else:
        for idx, row in df_rab.iterrows():
            row_str = ' '.join([str(val).lower() for val in row.values])
            if sum(1 for kw in keywords if kw in row_str) >= 2:
                header_idx = idx
                break
                
    if header_idx >= 0:
        df_rab.columns = df_rab.iloc[header_idx].astype(str)
        df_rab = df_rab.iloc[header_idx+1:].reset_index(drop=True)
        
    df_rab.columns = [str(col).lower().strip().replace('\n', ' ') for col in df_rab.columns]
    
    # 3. Fuzzy Column Mapping
    col_mapping = {}
    nama_kws = ['nama', 'pekerjaan', 'uraian', 'item', 'jenis']
    for col in df_rab.columns:
        if any(kw in col for kw in nama_kws):
            col_mapping[col] = 'nama_item'
            break
            
    vol_kws = ['qty', 'kuantitas', 'vol', 'volume']
    for col in df_rab.columns:
        if any(kw in col for kw in vol_kws):
            col_mapping[col] = 'volume'
            break
            
    sat_kws = ['sat', 'unit', 'satuan']
    for col in df_rab.columns:
        if col not in col_mapping.values() and any(kw in col for kw in sat_kws):
            col_mapping[col] = 'satuan'
            break
            
    harga_kws = ['harga', 'biaya', 'satuan']
    for col in df_rab.columns:
        if col not in col_mapping.values() and 'total' not in col and 'jumlah' not in col and any(kw in col for kw in harga_kws):
            col_mapping[col] = 'harga_satuan'
            break
            
    df_rab.rename(columns=col_mapping, inplace=True)
    
    if 'nama_item' in df_rab.columns:
        df_rab = df_rab[df_rab['nama_item'].notna() & (df_rab['nama_item'] != '') & (df_rab['nama_item'] != 'nan')]
        
    required_cols = ['nama_item', 'volume', 'satuan', 'harga_satuan']
    missing_cols = [col for col in required_cols if col not in df_rab.columns]
    
    if missing_cols:
        logger.error("Kolom yang dibutuhkan tidak ditemukan di RAB.")
        raise ValueError("Sistem gagal mendeteksi tabel otomatis. Pastikan file memiliki tulisan kolom: 'Nama/Uraian', 'Volume', 'Satuan', 'Harga'.")
        
    def clean_number(x):
        if pd.isna(x): return 0
        s = str(x).lower().replace('rp', '').replace(' ', '').replace(',', '')
        if s.count('.') > 1 or (s.count('.') == 1 and len(s.split('.')[-1]) == 3):
            s = s.replace('.', '')
        try:
            return float(s)
        except:
            return 0
            
    df_rab['volume'] = df_rab['volume'].apply(clean_number)
    df_rab['harga_satuan'] = df_rab['harga_satuan'].apply(clean_number)
    df_rab = df_rab[(df_rab['volume'] > 0) & (df_rab['harga_satuan'] > 0)]
    df_rab['total_harga'] = df_rab['volume'] * df_rab['harga_satuan']
        
    results = []
    for _, row in df_rab.iterrows():
        item_name = str(row['nama_item']).strip()
        harga_satuan = float(row['harga_satuan'])
        volume = float(row['volume'])
        
        db_match, score = match_item_to_db(item_name, df_db)
        
        status = "REVIEW MANUAL"
        kategori = "Belum Terklasifikasi"
        harga_rekomendasi = 0
        efisiensi = 0
        sumber_referensi = "-"
        
        if db_match is not None:
            kategori = db_match['kategori']
            harga_min = db_match['harga_min']
            harga_max = db_match['harga_max']
            harga_rekomendasi = db_match['harga_rekomendasi']
            sumber_referensi = db_match.get('sumber_1', '-')
            
            if harga_satuan > harga_max:
                status = "MAHAL (OVERPRICED)"
                efisiensi = (harga_satuan - harga_rekomendasi) * volume
            elif harga_satuan < harga_min:
                status = "MURAH (UNDERBUDGET)"
            else:
                status = "NORMAL (WAJAR)"
                
        results.append({
            'Item Pekerjaan': item_name,
            'Kategori': kategori,
            'Volume': volume,
            'Satuan': row['satuan'],
            'Harga Satuan (Rp)': harga_satuan,
            'Total Harga (Rp)': row['total_harga'],
            'Status': status,
            'Harga Rekomendasi (Rp)': harga_rekomendasi,
            'Potensi Penghematan (Rp)': max(0, efisiensi),
            'Match Score (%)': round(score, 1),
            'Sumber Referensi': sumber_referensi
        })
        
    logger.info(f"Analisis RAB selesai. {len(results)} item diproses.")
    return pd.DataFrame(results)
