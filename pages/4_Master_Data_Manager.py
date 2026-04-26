import streamlit as st
import pandas as pd
import sqlite3, os, io, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Master Data Manager", page_icon="🏭", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "master_harga.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS master_harga (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sektor TEXT NOT NULL,
            nama_item TEXT NOT NULL,
            satuan TEXT,
            harga_min REAL DEFAULT 0,
            harga_max REAL DEFAULT 0,
            harga_median REAL DEFAULT 0,
            sumber TEXT DEFAULT 'Input Manual',
            lokasi TEXT DEFAULT 'Kalsel',
            catatan TEXT,
            updated_at TEXT DEFAULT CURRENT_DATE
        )
    """)
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM master_harga").fetchone()[0]
    if count == 0:
        seeds = [
            ("Konstruksi","Semen Portland 50kg","Sak",82000,90000,86000,"Supplier Lokal","Banjarmasin",""),
            ("Konstruksi","Besi Beton Polos 10mm","Kg",11500,13500,12500,"AHSP 2024","Kalsel",""),
            ("Konstruksi","Pasir Urug","m3",120000,180000,150000,"Supplier Lokal","Kalsel",""),
            ("Konstruksi","Batu Split 2/3","m3",200000,260000,230000,"Supplier Lokal","Kalsel",""),
            ("Konstruksi","Cat Tembok 20 liter","Kaleng",350000,420000,385000,"Toko Material","Banjarmasin",""),
            ("Konstruksi","Upah Tukang Batu","OH",130000,160000,145000,"INKINDO 2024","Kalsel",""),
            ("Konstruksi","Upah Mandor","OH",180000,220000,200000,"INKINDO 2024","Kalsel",""),
            ("Konstruksi","Kayu Ulin Kelas II","m3",3500000,5000000,4200000,"Supplier Lokal","Kalsel",""),
            ("Konstruksi","Baja WF 200","Kg",14000,17000,15500,"Supplier Baja","Kalsel",""),
            ("Konstruksi","Beton Ready Mix K-250","m3",850000,950000,900000,"Batching Plant","Kalsel",""),
            ("Alat Berat","Sewa Excavator PC-200","Jam",300000,400000,350000,"Kontraktor Lokal","Kalsel",""),
            ("Alat Berat","Sewa Excavator PC-300","Jam",400000,520000,450000,"Kontraktor Lokal","Kalsel",""),
            ("Alat Berat","Sewa Dump Truck 10T","Rit",350000,500000,420000,"Kontraktor Lokal","Kalsel",""),
            ("Alat Berat","Sewa Bulldozer D85","Jam",450000,600000,500000,"Kontraktor Lokal","Kalsel",""),
            ("Alat Berat","Sewa Motor Grader","Jam",380000,480000,420000,"Kontraktor Lokal","Kalsel",""),
            ("Alat Berat","Sewa Vibro Roller","Jam",280000,380000,320000,"Kontraktor Lokal","Kalsel",""),
            ("BBM & Logistik","Solar Industri","Liter",14500,16500,15500,"LKPP / Pertamina","Kalsel",""),
            ("BBM & Logistik","Bensin Pertalite","Liter",10000,10000,10000,"Pertamina","Kalsel",""),
            ("BBM & Logistik","Trucking 10T Lokal","Trip",1200000,2000000,1500000,"Jasa Angkut","Kalsel",""),
            ("BBM & Logistik","Kontainer 20ft","Trip",8000000,12000000,10000000,"Ekspedisi","Kalsel",""),
            ("Tambang","Operator Excavator","OH",250000,350000,300000,"INKINDO 2024","Kalsel",""),
            ("Tambang","Hauling Fee Per Ton","Ton",15000,35000,25000,"Kontrak Hauling","Kalsel",""),
            ("Tambang","Wearpart Bucket PC-200","Unit",8000000,15000000,11000000,"Supplier Parts","Kalsel",""),
            ("Tambang","Blasting Service","m3",45000,65000,55000,"Jasa Peledak","Kalsel",""),
            ("Tambang","Sewa Crusher","Jam",600000,800000,700000,"Kontraktor","Kalsel",""),
            ("Kehutanan","Bibit Akasia 1 Tahun","Batang",3500,5000,4200,"Supplier Bibit","Kalsel",""),
            ("Kehutanan","Bibit Sawit Bersertifikat","Batang",35000,50000,42000,"PPKS / Supplier","Kalsel",""),
            ("Kehutanan","Pupuk NPK","Kg",12000,16000,14000,"Distributor Resmi","Kalsel",""),
            ("Kehutanan","Tenaga Tanam Manual","OH",80000,110000,95000,"INKINDO 2024","Kalsel",""),
            ("Kehutanan","Herbisida Roundup 1L","Liter",60000,80000,70000,"Toko Pertanian","Kalsel",""),
            ("Kehutanan","Pemeliharaan Tanaman/Ha","Ha",2500000,4000000,3200000,"INKINDO 2024","Kalsel",""),
            ("Pertanian","Pupuk Urea 50kg","Sak",115000,135000,125000,"Distributor Pupuk","Kalsel",""),
            ("Pertanian","Pestisida Cair 1L","Liter",55000,90000,70000,"Toko Pertanian","Kalsel",""),
            ("Pertanian","Benih Padi per Kg","Kg",12000,18000,15000,"Balai Benih","Kalsel",""),
            ("Pertanian","Traktor Roda 4 per Jam","Jam",150000,200000,175000,"Penyewaan Alsin","Kalsel",""),
            ("Katering / Konsumsi","Paket Makan Siang Proyek","Pax",22000,35000,28000,"Katering Lokal","Kalsel",""),
            ("Katering / Konsumsi","Beras per Kg","Kg",12000,15000,13500,"Pasar Lokal","Kalsel",""),
            ("Katering / Konsumsi","Air Galon 19L","Galon",6000,8000,7000,"Depot Air","Kalsel",""),
            ("Katering / Konsumsi","Paket Konsumsi Rapat","Pax",35000,55000,45000,"Katering Lokal","Kalsel",""),
            ("Jasa Umum","Security / Satpam","OH",120000,160000,140000,"INKINDO 2024","Kalsel",""),
            ("Jasa Umum","Operator Genset","OH",130000,170000,150000,"INKINDO 2024","Kalsel",""),
            ("Jasa Umum","Surveyor Lapangan","OH",200000,300000,250000,"INKINDO 2024","Kalsel",""),
            ("Jasa Umum","Helper / Buruh Harian","OH",75000,100000,87500,"Pasar Kerja","Kalsel",""),
        ]
        conn.executemany("""
            INSERT INTO master_harga (sektor, nama_item, satuan, harga_min, harga_max, harga_median, sumber, lokasi, catatan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seeds)
        conn.commit()
    conn.close()


def load_data(sektor_filter="Semua", search=""):
    conn = get_conn()
    q = "SELECT * FROM master_harga WHERE 1=1"
    params = []
    if sektor_filter != "Semua":
        q += " AND sektor = ?"
        params.append(sektor_filter)
    if search.strip():
        q += " AND (nama_item LIKE ? OR catatan LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    q += " ORDER BY sektor, nama_item"
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


def insert_item(sektor, nama, satuan, hmin, hmax, hmed, sumber, lokasi, catatan):
    conn = get_conn()
    conn.execute("""
        INSERT INTO master_harga (sektor, nama_item, satuan, harga_min, harga_max, harga_median, sumber, lokasi, catatan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sektor, nama, satuan, hmin, hmax, hmed, sumber, lokasi, catatan))
    conn.commit()
    conn.close()


def delete_items(ids: list):
    if not ids:
        return
    conn = get_conn()
    conn.execute(f"DELETE FROM master_harga WHERE id IN ({','.join('?'*len(ids))})", ids)
    conn.commit()
    conn.close()


def import_from_df(df_import: pd.DataFrame):
    conn = get_conn()
    count = 0
    df_import.columns = df_import.columns.str.lower().str.strip()
    for _, row in df_import.iterrows():
        try:
            nama = str(row.get("nama_item", row.get("item", ""))).strip()
            if not nama:
                continue
            conn.execute("""
                INSERT INTO master_harga (sektor, nama_item, satuan, harga_min, harga_max, harga_median, sumber, lokasi, catatan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get("sektor", "Umum")),
                nama,
                str(row.get("satuan", "")),
                float(row.get("harga_min", row.get("harga", 0)) or 0),
                float(row.get("harga_max", row.get("harga", 0)) or 0),
                float(row.get("harga_median", row.get("harga_rekomendasi", row.get("harga", 0))) or 0),
                str(row.get("sumber", "Import")),
                str(row.get("lokasi", "Kalsel")),
                str(row.get("catatan", "")),
            ))
            count += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return count


init_db()

SEKTORS = ["Semua", "Konstruksi", "Alat Berat", "BBM & Logistik", "Tambang",
           "Kehutanan", "Pertanian", "Katering / Konsumsi", "Jasa Umum"]

st.title("🏭 Master Data Manager")
st.caption("Database harga hidup — SQLite lokal. Data nyata, bukan dummy.")

col_s, col_f = st.columns([2, 1.5])
with col_s:
    search = st.text_input("Cari", placeholder="Cari nama item...", label_visibility="collapsed")
with col_f:
    sektor_sel = st.selectbox("Sektor", SEKTORS, label_visibility="collapsed")

col_add, col_imp, col_del = st.columns(3)
add_clicked = col_add.button("➕ Tambah Item", use_container_width=True)
imp_clicked = col_imp.button("📥 Import File", use_container_width=True)
del_clicked = col_del.button("🗑️ Hapus Terpilih", type="secondary", use_container_width=True)

st.markdown("---")

df_all = load_data()
df = load_data(sektor_sel, search)

c1, c2, c3 = st.columns(3)
c1.metric("Total Item DB", f"{len(df_all):,}")
c2.metric("Ditampilkan", f"{len(df):,}")
c3.metric("Sektor", len(SEKTORS) - 1)

if df.empty:
    st.info("Tidak ada data dengan filter ini.")
else:
    df_edit = df.copy()
    df_edit.insert(0, "Pilih", False)
    edited = st.data_editor(
        df_edit,
        column_config={
            "Pilih": st.column_config.CheckboxColumn("", default=False, width="small"),
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "sektor": st.column_config.SelectboxColumn("Sektor", options=SEKTORS[1:]),
            "harga_min": st.column_config.NumberColumn("Min (Rp)", format="Rp %d"),
            "harga_max": st.column_config.NumberColumn("Max (Rp)", format="Rp %d"),
            "harga_median": st.column_config.NumberColumn("Median (Rp)", format="Rp %d"),
            "updated_at": st.column_config.TextColumn("Update", disabled=True, width="small"),
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="master_editor"
    )

    if del_clicked:
        sel_ids = edited[edited["Pilih"] == True]["id"].tolist()
        if sel_ids:
            delete_items(sel_ids)
            st.success(f"{len(sel_ids)} item dihapus.")
            st.rerun()
        else:
            st.warning("Centang item yang ingin dihapus.")

    e1, e2 = st.columns(2)
    with e1:
        st.download_button("📄 Export CSV", df.to_csv(index=False).encode("utf-8"),
                           "master_harga.csv", "text/csv", use_container_width=True)
    with e2:
        buf = io.BytesIO()
        df.to_excel(buf, index=False, engine="xlsxwriter")
        st.download_button("📊 Export Excel", buf.getvalue(), "master_harga.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

if add_clicked:
    with st.expander("Tambah Item Baru", expanded=True):
        with st.form("add_form"):
            a1, a2 = st.columns(2)
            with a1:
                f_sektor = st.selectbox("Sektor *", SEKTORS[1:])
                f_nama = st.text_input("Nama Item *")
                f_satuan = st.text_input("Satuan")
                f_sumber = st.text_input("Sumber", value="Input Manual")
            with a2:
                f_hmin = st.number_input("Harga Min (Rp)", min_value=0, step=1000)
                f_hmax = st.number_input("Harga Max (Rp)", min_value=0, step=1000)
                f_hmed = st.number_input("Harga Median (Rp)", min_value=0, step=1000)
                f_lokasi = st.text_input("Lokasi", value="Kalsel")
            f_catatan = st.text_area("Catatan", height=60)
            if st.form_submit_button("Simpan", type="primary"):
                if not f_nama.strip():
                    st.error("Nama item wajib diisi.")
                else:
                    insert_item(f_sektor, f_nama, f_satuan, f_hmin, f_hmax, f_hmed,
                                f_sumber, f_lokasi, f_catatan)
                    st.success(f"'{f_nama}' disimpan.")
                    st.rerun()

if imp_clicked:
    with st.expander("Import dari Excel/CSV", expanded=True):
        st.caption("Kolom wajib: `nama_item`, `sektor`. Opsional: `satuan`, `harga_min`, `harga_max`, `harga_median`, `sumber`, `lokasi`, `catatan`")
        up = st.file_uploader("Upload", type=["xlsx", "csv"], key="imp_up")
        if up:
            try:
                df_imp = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
                st.dataframe(df_imp.head(10), use_container_width=True)
                if st.button("Konfirmasi Import", type="primary"):
                    n = import_from_df(df_imp)
                    st.success(f"{n} item berhasil diimport.")
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal baca file: {e}")
