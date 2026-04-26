"""
Rolling average pricing engine.
Reads recent price_snapshots from intel.db and updates master_harga.db medians.
"""
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.intel_db import init_intel_db, INTEL_DB

ROOT      = os.path.dirname(os.path.abspath(__file__))
MASTER_DB = os.path.join(ROOT, "data", "master_harga.db")


def update_rolling_averages():
    print(f"[{datetime.now()}] Pricing Engine — mulai...")
    init_intel_db()

    if not os.path.exists(MASTER_DB) or not os.path.exists(INTEL_DB):
        print("[pricing_engine] DB tidak ditemukan, skip.")
        return

    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    conn_intel  = sqlite3.connect(INTEL_DB)
    conn_master = sqlite3.connect(MASTER_DB)

    df_snaps = pd.read_sql_query(
        "SELECT nama_item, harga FROM price_snapshots "
        "WHERE harga > 0 AND tanggal >= ?",
        conn_intel, params=(cutoff,)
    )
    conn_intel.close()

    if df_snaps.empty:
        print("[pricing_engine] Tidak ada snapshot baru, skip.")
        conn_master.close()
        return

    updated = 0
    for nama, group in df_snaps.groupby("nama_item"):
        row = conn_master.execute(
            "SELECT id FROM master_harga WHERE nama_item LIKE ?",
            (f"%{nama.split()[0]}%",)
        ).fetchone()
        if not row:
            continue
        harga_list = group["harga"].tolist()
        h_med = sum(harga_list) / len(harga_list)
        h_min = min(harga_list)
        h_max = max(harga_list)
        conn_master.execute(
            "UPDATE master_harga SET harga_median=?, harga_min=?, harga_max=?, updated_at=date('now') WHERE id=?",
            (h_med, h_min, h_max, row[0])
        )
        updated += 1

    conn_master.commit()
    conn_master.close()
    print(f"[{datetime.now()}] Pricing Engine — {updated} item diperbarui.")


if __name__ == "__main__":
    update_rolling_averages()
