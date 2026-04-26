import sqlite3
import pandas as pd
from datetime import datetime
import os
import streamlit_authenticator as stauth

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'harga_lokal.db')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_db():
    if not os.path.exists('data'):
        os.makedirs('data')
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Existing Master Data Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS harga_lokal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategori TEXT,
        nama_item TEXT,
        satuan TEXT,
        harga_min REAL,
        harga_max REAL,
        harga_rekomendasi REAL,
        sumber_1 TEXT,
        sumber_2 TEXT,
        sumber_3 TEXT,
        metode_perhitungan TEXT,
        lokasi TEXT,
        confidence_score INTEGER,
        update_terakhir TEXT,
        catatan TEXT
    )
    ''')
    
    # 1. Companies Table (Multi-tenant)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        subscription_tier TEXT DEFAULT 'Free',
        created_at TEXT
    )
    ''')
    
    # 2. Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        name TEXT,
        email TEXT UNIQUE,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT DEFAULT 'user',
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )
    ''')
    
    # 3. Projects Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        name TEXT,
        total_budget REAL,
        status TEXT DEFAULT 'Draft',
        created_at TEXT,
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )
    ''')
    
    # 4. Project Items Table (History)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        item_name TEXT,
        kategori TEXT,
        volume REAL,
        satuan TEXT,
        harga_satuan REAL,
        total_harga REAL,
        status TEXT,
        harga_rekomendasi REAL,
        potensi_penghematan REAL,
        match_score REAL,
        sumber_referensi TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    ''')
    
    # 5. Tenders Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tenders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        vendor_name TEXT,
        total_bid_amount REAL,
        risk_score TEXT,
        created_at TEXT,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
    )
    ''')
    
    # 6. Market News Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS market_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT,
        published_date TEXT,
        category TEXT,
        impact_summary TEXT,
        urgency TEXT,
        recommended_action TEXT,
        created_at TEXT
    )
    ''')
    
    # 7. Price History Table (For Rolling Average)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        harga_lokal_id INTEGER,
        harga_baru REAL,
        sumber TEXT,
        tanggal TEXT,
        FOREIGN KEY (harga_lokal_id) REFERENCES harga_lokal (id) ON DELETE CASCADE
    )
    ''')
    
    # 8. Vendors Intelligence Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendors_intelligence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_vendor TEXT UNIQUE,
        spesialisasi TEXT,
        reliability_score REAL,
        overpriced_tendency REAL,
        response_speed TEXT,
        menang_tender INTEGER,
        created_at TEXT,
        updated_at TEXT
    )
    ''')
    
    # Seed default SaaS Data
    cursor.execute('SELECT COUNT(*) FROM companies')
    if cursor.fetchone()[0] == 0:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Create default Demo Company
        cursor.execute("INSERT INTO companies (name, subscription_tier, created_at) VALUES ('PT Demo Kalsel', 'Enterprise', ?)", (today,))
        comp_id = cursor.lastrowid
        
        # Create Default Admin User using streamlit-authenticator built-in context hash
        # We will use stauth.Hasher to hash 'admin123'
        from streamlit_authenticator.utilities.hasher import Hasher
        hashed_pw = Hasher(['admin123']).generate()[0]
        
        cursor.execute("INSERT INTO users (company_id, name, email, username, password_hash, role) VALUES (?, 'Admin Demo', 'admin@demokalsel.co.id', 'admin', ?, 'admin')", (comp_id, hashed_pw))
        
    conn.commit()
    conn.close()

# Existing CRUD
def delete_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM harga_lokal WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def update_item(item_id, kat, nama, sat, hmin, hmax, hrek, sumber):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE harga_lokal 
        SET kategori=?, nama_item=?, satuan=?, harga_min=?, harga_max=?, harga_rekomendasi=?, sumber_1=?, update_terakhir=date('now')
        WHERE id=?
    ''', (kat, nama, sat, hmin, hmax, hrek, sumber, item_id))
    conn.commit()
    conn.close()

# New SaaS CRUD
def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user

def save_project(company_id, name, total_budget, df_items):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("INSERT INTO projects (company_id, name, total_budget, status, created_at) VALUES (?, ?, ?, 'Saved', ?)", 
                   (company_id, name, total_budget, today))
    proj_id = cursor.lastrowid
    
    items_to_insert = []
    for _, row in df_items.iterrows():
        items_to_insert.append((
            proj_id, row['Item Pekerjaan'], row['Kategori'], row['Volume'], row['Satuan'],
            row['Harga Satuan (Rp)'], row['Total Harga (Rp)'], row['Status'],
            row['Harga Rekomendasi (Rp)'], row['Potensi Penghematan (Rp)'],
            row['Match Score (%)'], row['Sumber Referensi']
        ))
        
    cursor.executemany('''
        INSERT INTO project_items (project_id, item_name, kategori, volume, satuan, 
        harga_satuan, total_harga, status, harga_rekomendasi, potensi_penghematan, 
        match_score, sumber_referensi) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', items_to_insert)
    
    conn.commit()
    conn.close()
    return proj_id

def get_company_projects(company_id):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM projects WHERE company_id = ? ORDER BY id DESC", conn, params=(company_id,))
    conn.close()
    return df

def get_project_items(project_id):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM project_items WHERE project_id = ?", conn, params=(project_id,))
    conn.close()
    return df

if __name__ == '__main__':
    create_db()
    print("Database lokal diperbarui ke skema SaaS.")
