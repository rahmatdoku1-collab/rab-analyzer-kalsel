import streamlit as st
import requests
import jwt
from scheduler import start_scheduler
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="AI Procurement Intelligence Kalsel", page_icon="🏢", layout="wide")

@st.cache_resource
def init_system():
    start_scheduler()
    return True

init_system()

API_URL = "http://localhost:8000/api/v1"

def login_user(username, password):
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.ConnectionError:
        st.error("Gagal terhubung ke FastAPI Backend. Pastikan uvicorn berjalan.")
        return None

if "jwt_token" not in st.session_state:
    st.session_state["jwt_token"] = None
    st.session_state["authentication_status"] = False

# DEMO MODE
DEMO_MODE = True
if DEMO_MODE:
    st.session_state["authentication_status"] = True
    st.session_state["username"] = "demo_reviewer"
    st.session_state["role"] = "SuperAdmin"
    st.session_state["company_id"] = "DEMO"
if not st.session_state["authentication_status"]:
    st.markdown('<h1 style="text-align: center;">🛡️ Enterprise SaaS Login</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">AI Procurement Intelligence Kalsel</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login to Command Center")
            
            if submit:
                if username and password:
                    with st.spinner("Authenticating via FastAPI..."):
                        token_data = login_user(username, password)
                        if token_data:
                            st.session_state["jwt_token"] = token_data["access_token"]
                            
                            # Decode JWT to get claims without verifying signature (Backend already verified it)
                            decoded = jwt.decode(token_data["access_token"], options={"verify_signature": False})
                            
                            st.session_state["authentication_status"] = True
                            st.session_state["company_id"] = decoded.get("company_id")
                            st.session_state["username"] = decoded.get("username", username)
                            st.session_state["role"] = decoded.get("role")
                            
                            st.rerun()
                        else:
                            st.error("Username atau Password salah!")
                else:
                    st.warning("Masukkan username dan password")
else:
    # User is logged in
    st.sidebar.markdown(f"**Welcome, {st.session_state['username']}**")
    st.sidebar.caption(f"Role: {st.session_state.get('role', 'Viewer')} | Company ID: {st.session_state.get('company_id')}")
    
    if st.sidebar.button("Logout"):
        st.session_state["jwt_token"] = None
        st.session_state["authentication_status"] = False
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Navigasi")
    st.sidebar.page_link("pages/1_Executive_Dashboard.py",   label="🏢 Executive Dashboard")
    st.sidebar.page_link("pages/2_Vendor_War_Mode.py",       label="⚔️ Vendor War Mode")
    st.sidebar.page_link("pages/3_Auto_RAB_Generator.py",    label="🤖 Auto RAB Generator")
    st.sidebar.page_link("pages/4_Master_Data_Manager.py",   label="🏭 Master Data Manager")
    st.sidebar.page_link("pages/5_History_Tender_Compare.py",label="📚 History & Compare")
    st.sidebar.page_link("pages/6_News_Market_Intel.py",     label="📡 News & Market Intel")
    st.sidebar.page_link("pages/7_CV_Profile_Scanner.py",    label="📄 CV & Profile Scanner")

    st.markdown("## Selamat Datang")
    st.markdown(f"Login sebagai **{st.session_state.get('username','')}** | Role: **{st.session_state.get('role','')}**")
    st.info("Pilih menu di sidebar untuk mulai.")
