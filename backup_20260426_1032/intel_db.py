import sqlite3
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTEL_DB = os.path.join(ROOT, "data", "intel.db")


def get_conn():
    conn = sqlite3.connect(INTEL_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_intel_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS market_news (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            link       TEXT,
            pub_date   TEXT,
            category   TEXT DEFAULT 'Regulasi/Pasar',
            impact     TEXT,
            urgency    TEXT DEFAULT 'Low',
            action     TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title)
        );

        CREATE TABLE IF NOT EXISTS price_snapshots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_item  TEXT NOT NULL,
            sektor     TEXT,
            satuan     TEXT,
            harga      REAL,
            sumber     TEXT,
            lokasi     TEXT DEFAULT 'Kalsel',
            tanggal    TEXT DEFAULT CURRENT_DATE,
            catatan    TEXT
        );
    """)
    conn.commit()
    conn.close()
