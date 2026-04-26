import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add backend to path to import tender_monster
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend_fastapi'))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.services.tender_monster import analyze_vendor_submissions, generate_forensic_summary
from database import get_company_projects

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("Silakan login dari halaman utama terlebih dahulu.")
    st.stop()

st.markdown("""
<style>
    .main-header { font-size: 2.8rem; font-weight: 900; color: #0F172A; margin-bottom: 0rem; letter-spacing: -1px;}
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 2rem; font-weight: 400;}
    .kpi-card { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: center; }
    .kpi-title { font-size: 0.9rem; color: #64748B; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;}
    .kpi-value { font-size: 2rem; color: #0F172A; font-weight: 800; margin-top: 5px;}
    .winner-box { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: white; padding: 30px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-left: 5px solid #10B981;}
    .warning-box { background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 15px 20px; margin-bottom: 20px; border-radius: 0 8px 8px 0;}
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px; color: #475569; font-weight: 600; font-size: 1rem; }
    .stTabs [aria-selected="true"] { color: #2563EB !important; border-bottom: 3px solid #2563EB !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">⚡ TENDER COMPARE MONSTER MODE</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI Best Value Procurement Engine untuk Kontraktor, EPC, dan Private Owner</p>', unsafe_allow_html=True)

company_id = st.session_state['company_id']
projects = get_company_projects(company_id)

if projects.empty:
    st.error("⚠️ Belum ada proyek yang disimpan sebagai Pagu Acuan. Harap buat di menu Smart RAB Audit.")
    st.stop()

# ==================== CONTROLS ====================
with st.container():
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        selected_project_name = st.selectbox("🎯 Proyek (HPS Acuan)", projects['name'].tolist())
        project_budget = projects[projects['name'] == selected_project_name]['total_budget'].values[0]
        st.caption(f"Pagu HPS: **Rp {project_budget:,.0f}**")
    with col2:
        industry = st.selectbox("🏭 Industri (Algorithm Weight)", ["Sipil", "Tambang", "EPC", "Umum"])
    with col3:
        uploaded_files = st.file_uploader("📂 Upload RAB Vendor (Excel/CSV)", type=['xlsx', 'csv'], accept_multiple_files=True)

# ==================== EXECUTION ====================
if uploaded_files and st.button("🚀 EXECUTE MONSTER ENGINE", type="primary", use_container_width=True):
    with st.spinner("Mengaktifkan Oracle Procurement + McKinsey AI Engine..."):
        dfs = []
        vendor_names = []
        for file in uploaded_files:
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Check required columns
                required = ['Item', 'Volume', 'Harga Satuan', 'Total Harga']
                missing = [c for c in required if c not in df.columns]
                if missing:
                    st.error(f"File {file.name} kekurangan kolom: {', '.join(missing)}")
                    continue
                
                dfs.append(df)
                vendor_names.append(file.name.split('.')[0])
            except Exception as e:
                st.error(f"Gagal membaca file {file.name}: {e}")
                
        if len(dfs) > 0:
            # RUN ENGINE
            analysis = analyze_vendor_submissions(dfs, vendor_names, project_budget, industry)
            
            if "error" in analysis:
                st.error(analysis["error"])
                st.stop()
                
            vendor_scores = analysis["vendor_scoring"]
            df_vendors = pd.DataFrame(vendor_scores)
            df_items = pd.DataFrame(analysis["item_analysis"])
            collusion_flags = analysis["collusion_flags"]
            
            best_vendor = vendor_scores[0]
            
            st.success("Analisis Selesai! Memuat Executive Dashboard...")
            
            # ==================== KPI CARDS ====================
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Vendor</div><div class="kpi-value">{len(vendor_names)}</div></div>', unsafe_allow_html=True)
            
            lowest_bid = df_vendors["Total_Bid"].min()
            k2.markdown(f'<div class="kpi-card"><div class="kpi-title">Lowest Bid</div><div class="kpi-value" style="font-size:1.5rem; margin-top:10px;">Rp {lowest_bid/1e6:,.0f}M</div></div>', unsafe_allow_html=True)
            
            saving_opp = max(0, project_budget - best_vendor["Total_Bid"])
            k3.markdown(f'<div class="kpi-card"><div class="kpi-title">Target Saving</div><div class="kpi-value" style="color:#10B981; font-size:1.5rem; margin-top:10px;">Rp {saving_opp/1e6:,.0f}M</div></div>', unsafe_allow_html=True)
            
            k4.markdown(f'<div class="kpi-card"><div class="kpi-title">Collusion Risk</div><div class="kpi-value" style="color:{"#EF4444" if len(collusion_flags) > 0 else "#10B981"};">{len(collusion_flags)}</div></div>', unsafe_allow_html=True)
            
            risk_vendors = len(df_vendors[df_vendors["Hidden_Markups"] > 0])
            k5.markdown(f'<div class="kpi-card"><div class="kpi-title">Markup Detected</div><div class="kpi-value" style="color:#F59E0B;">{risk_vendors} Vendor</div></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ==================== TABS ====================
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏆 Recommended Winner", 
                "📊 Executive Dashboard", 
                "🕵️ Forensic Radar", 
                "🤝 AI Negotiation", 
                "🗄️ Item Intelligence"
            ])
            
            with tab1:
                # Winner Logic
                if best_vendor["Total_Bid"] > project_budget and len(df_vendors[df_vendors["Total_Bid"] <= project_budget]) == 0:
                    st.markdown("""
                    <div class="warning-box">
                        <h3 style="margin-top:0;">🛑 NEGOTIATION REQUIRED</h3>
                        <p>Semua penawaran melebihi HPS. Pemenang tidak dapat diputuskan tanpa negosiasi (BAFO).</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="winner-box">
                        <h2 style="margin-top:0; color:#10B981;">🥇 {best_vendor['Vendor']}</h2>
                        <h4 style="color:#94A3B8; font-weight:400;">Final Score: {best_vendor['Final_Score']:.1f} / 100</h4>
                        <hr style="border-color:#334155; margin:15px 0;">
                        <div style="display:flex; justify-content:space-between;">
                            <div>
                                <p style="margin:0; color:#94A3B8; font-size:0.9rem;">Total Penawaran</p>
                                <h3 style="margin:0;">Rp {best_vendor['Total_Bid']:,.0f}</h3>
                            </div>
                            <div>
                                <p style="margin:0; color:#94A3B8; font-size:0.9rem;">Reliability Score</p>
                                <h3 style="margin:0;">{best_vendor['Reliability']:.1f}%</h3>
                            </div>
                            <div>
                                <p style="margin:0; color:#94A3B8; font-size:0.9rem;">Anomaly Risk</p>
                                <h3 style="margin:0;">{best_vendor['Risk_Score']}/100</h3>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("### Vendor Rankings")
                st.dataframe(df_vendors.style.format({"Total_Bid": "Rp {:,.0f}", "Final_Score": "{:.1f}", "Reliability": "{:.1f}%"}), use_container_width=True)
                
            with tab2:
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.markdown("#### Market Positioning (Harga vs Keandalan)")
                    fig_bubble = px.scatter(
                        df_vendors, x="Total_Bid", y="Reliability", size="Risk_Score", color="Final_Score",
                        hover_name="Vendor", text="Vendor", size_max=40, color_continuous_scale="Viridis",
                        labels={"Total_Bid": "Total Penawaran (Rp)", "Reliability": "Keandalan (%)"}
                    )
                    fig_bubble.update_traces(textposition='top center')
                    fig_bubble.add_vline(x=project_budget, line_dash="dash", line_color="red", annotation_text="HPS Budget")
                    st.plotly_chart(fig_bubble, use_container_width=True)
                    
                with col_chart2:
                    st.markdown("#### Savings Waterfall")
                    fig_waterfall = go.Figure(go.Waterfall(
                        name="20", orientation="v",
                        measure=["relative", "relative", "total", "relative", "total"],
                        x=["HPS Budget", "Vendor Terendah", "Current Bidding", "Target Negosiasi (-5%)", "Final Target"],
                        textposition="outside",
                        y=[project_budget, -(project_budget - lowest_bid), lowest_bid, -(lowest_bid * 0.05), lowest_bid * 0.95],
                        connector={"line":{"color":"rgb(63, 63, 63)"}},
                    ))
                    fig_waterfall.update_layout(showlegend=False)
                    st.plotly_chart(fig_waterfall, use_container_width=True)
                    
            with tab3:
                st.markdown("### 🚨 Collusion & Fraud Detector")
                if len(collusion_flags) > 0:
                    for flag in collusion_flags:
                        st.error(f"**{flag['Risk_Level']} RISK:** {flag['Vendor_1']} & {flag['Vendor_2']} - {flag['Reason']}")
                else:
                    st.success("Tidak terdeteksi adanya indikasi harga kongkalikong yang persis.")
                
                st.markdown("### 🕸️ Risk Radar")
                radar_data = pd.DataFrame(dict(
                    r=[best_vendor['Price_Score'], best_vendor['Reliability'], 100-best_vendor['Risk_Score'], 80, 90],
                    theta=['Price Fairness', 'Reliability', 'Anomaly Safety', 'Delivery Speed', 'Legal Safety']
                ))
                fig_radar = px.line_polar(radar_data, r='r', theta='theta', line_close=True)
                fig_radar.update_traces(fill='toself')
                st.plotly_chart(fig_radar, use_container_width=True)
                
            with tab4:
                st.markdown("### 🤖 AI Procurement Negotiator")
                st.caption("Skrip negosiasi berbasis Forensic Data (dijenerasi otomatis oleh LLM).")
                with st.spinner("AI sedang merangkum strategi negosiasi..."):
                    ai_summary = generate_forensic_summary(analysis)
                    st.markdown(f"> {ai_summary}")
                
            with tab5:
                st.markdown("### 🔥 Hidden Markup Heatmap")
                st.caption("Baris merah menunjukkan harga item jauh di atas median market.")
                
                pivot_markup = df_items.pivot_table(index="Vendor", columns="Item", values="Markup_Pct").fillna(0)
                fig_heat = px.imshow(pivot_markup, text_auto=".1f", aspect="auto", color_continuous_scale="RdYlGn_r",
                                     labels=dict(color="Markup %"))
                st.plotly_chart(fig_heat, use_container_width=True)
                
                st.markdown("### Detail Raw Data")
                st.dataframe(df_items)

