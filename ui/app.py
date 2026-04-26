import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import streamlit_authenticator as stauth
from database import create_db, get_db_connection
from scheduler import start_scheduler
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Procurement Intelligence Kalsel", page_icon="🏢", layout="wide")

@st.cache_resource
def init_system():
    create_db()
    start_scheduler()
    return True

init_system()

def get_auth_config():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    
    credentials = {"usernames": {}}
    for u in users:
        credentials["usernames"][u['username']] = {
            "email": u['email'],
            "name": u['name'],
            "password": u['password_hash'],
            "company_id": u['company_id'],
            "role": u['role']
        }
    return credentials

credentials = get_auth_config()

authenticator = stauth.Authenticate(
    credentials,
    'rab_analyzer_cookie',
    'secret_key_123',
    cookie_expiry_days=30
)

# Login Form
name, authentication_status, username = authenticator.login(location='main')

if authentication_status:
    st.sidebar.markdown(f"**Welcome, {name}**")
    
    # Get current user details from db to set company_id
    user_info = credentials["usernames"][username]
    st.session_state["company_id"] = user_info["company_id"]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigasi SaaS")
    st.sidebar.page_link("pages/1_Smart_RAB_Audit.py", label="📊 Smart RAB Audit")
    st.sidebar.page_link("pages/2_Master_Data.py", label="🗄️ Master Harga Lokal")
    st.sidebar.page_link("pages/3_Tender_Compare.py", label="⚖️ Tender Comparison")
    st.sidebar.page_link("pages/4_History.py", label="📂 Histori Proyek")
    st.sidebar.page_link("pages/5_Market_Intelligence.py", label="📈 Market Intelligence")
    st.sidebar.page_link("pages/6_News_Alerts.py", label="📰 News & Regulation")
    st.sidebar.page_link("pages/7_Auto_RAB_Generator.py", label="🤖 Auto RAB Generator")
    st.sidebar.page_link("pages/8_Vendor_Intelligence.py", label="🛡️ Vendor Intelligence")
    st.sidebar.markdown("---")
    
    st.markdown("""
        ## AI Procurement Intelligence Kalsel 🚀
        Pilih menu di sidebar sebelah kiri untuk mulai melakukan audit cerdas, melihat intelijen pasar, atau memantau regulasi pengadaan terbaru.
    """)
    
    authenticator.logout('Logout', 'sidebar')
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Silakan masukkan username dan password')
    st.info("Demo Account -> Username: **admin**, Password: **admin123**")
