import streamlit as st
import pandas as pd
import io, os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.intel_db import save_scan_history

from core.config import settings

st.set_page_config(page_title="Vendor War Mode", page_icon="⚔️", layout="wide")
st.markdown("""<style>
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
.kpi-card{background:#1A1A1D;padding:16px;border-radius:8px;border-left:4px solid;color:white;text-align:center;}
.kpi-val{font-size:1.8rem;font-weight:700;}
</style>""", unsafe_allow_html=True)

MASTER_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "master_harga.db")

# ── FIXED parse_num: cek tipe dulu sebelum string ops ───────────────────────
def parse_num(val):
    """Parse angka dari Excel/CSV. Fix: nilai float dari pandas (1.0, 50.0) jangan diubah ke string dulu."""
    if val is None:
        return 0
    if isinstance(val, bool):
        return 0
    if isinstance(val, (int, float)):
        return 0 if math.isnan(float(val)) else float(val)
    s = str(val).strip().replace("Rp", "").replace(" ", "").replace("\xa0", "")
    if not s or s.lower() in ("nan", "none", "-", ""):
        return 0
    # Indonesian format: titik = ribuan, koma = desimal
    if s.count(".") > 1:          # "1.234.567" → hapus titik
        s = s.replace(".", "")
    elif "," in s and "." in s:   # "1.234,56" → hapus titik, koma jadi titik
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        parts = s.split(",")
        s = s.replace(",", "") if len(parts[-1]) == 3 else s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0


def load_master() -> dict:
    if not os.path.exists(MASTER_DB):
        return {}
    import sqlite3
    conn = sqlite3.connect(MASTER_DB)
    rows = conn.execute(
        "SELECT nama_item, harga_pasar, harga_median, sektor FROM master_harga WHERE harga_median > 0"
    ).fetchall()
    conn.close()
    return {r[0].lower(): {"pasar": r[1] or r[2], "rab": r[2], "sektor": r[3]} for r in rows}


def detect_col(df, kws):
    for c in df.columns:
        cl = c.lower().strip()
        if any(k == cl for k in kws):  # exact match dulu
            return c
    for c in df.columns:
        cl = c.lower().strip()
        if any(k in cl for k in kws):  # partial match
            return c
    return None


def fuzzy_match(item_name: str, master: dict):
    """Gunakan rapidfuzz untuk fuzzy match nama item ke master data."""
    from rapidfuzz import process, fuzz
    if not item_name or not master:
        return None
    keys = list(master.keys())
    result = process.extractOne(item_name.lower(), keys, scorer=fuzz.partial_ratio, score_cutoff=45)
    if result:
        return master[result[0]]
    # Fallback: keyword pertama
    words = [w for w in item_name.lower().split() if len(w) > 3]
    for w in words:
        for k, v in master.items():
            if w in k:
                return v
    return None


def ai_analyze_items(df_items: pd.DataFrame) -> list:
    import openai
    if not settings.OPENROUTER_API_KEY:
        return []
    items_text = []
    for _, row in df_items.iterrows():
        items_text.append(
            f"- {row['Item']} | Submit: Rp{int(row['Harga Submit']):,} "
            f"| Ref: Rp{int(row['Harga Ref']):,} | Qty: {row['Qty']} {row['Satuan']}"
        )
    prompt_items = "\n".join(items_text[:40])
    system = """Anda adalah Senior Tender Strategist CV/Vendor di Kalimantan Selatan.
Posisi: VENDOR ingin menang tender dengan PROFIT MAKSIMAL, lolos evaluasi.
Untuk tiap item, output JSON array:
[{"item":"nama","harga_submit_ideal":0,"markup_aman_pct":0,"markup_agresif_pct":0,
"margin_estimasi_pct":0,"risiko_kalah":"Rendah|Sedang|Tinggi","curiga_evaluator":"Ya|Tidak",
"alasan":"singkat","kategori":"tebal|tipis|rawan"}]"""
    client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role":"system","content":system},
                      {"role":"user","content":f"Analisa:\n{prompt_items}"}],
            temperature=0.3, response_format={"type":"json_object"}, max_tokens=3000,
        )
        parsed = json.loads(resp.choices[0].message.content)
        if isinstance(parsed, list): return parsed
        for v in parsed.values():
            if isinstance(v, list): return v
        return []
    except Exception as e:
        st.warning(f"AI error: {e}"); return []


def ai_war_report(df_items: pd.DataFrame, ai_items: list) -> dict:
    import openai
    if not settings.OPENROUTER_API_KEY:
        return {}
    total = df_items["Subtotal"].sum()
    tebal = [x for x in ai_items if x.get("kategori")=="tebal"]
    rawan = [x for x in ai_items if x.get("kategori")=="rawan"]
    avg_m = sum(x.get("margin_estimasi_pct",0) for x in ai_items)/max(len(ai_items),1)
    summary = (f"Total submit: Rp{int(total):,}. Margin rata: {avg_m:.1f}%. "
               f"Item tebal: {len(tebal)}. Item rawan: {len(rawan)}. "
               f"{'Tebal: '+', '.join(x['item'][:15] for x in tebal[:2]) if tebal else ''} "
               f"{'Rawan: '+', '.join(x['item'][:15] for x in rawan[:2]) if rawan else ''}")
    client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role":"system","content":'Tender strategist. Output JSON: {"strategi_submit":"...","taktik_utama":"...","item_profit_tertinggi":"...","item_paling_rawan":"...","peluang_menang_pct":0,"suspicious_score_pct":0,"verdict":"GO|REVISI|NO GO","alasan_verdict":"..."}'},
                {"role":"user","content":summary}
            ],
            temperature=0.4, response_format={"type":"json_object"}, max_tokens=600,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {}


def ai_scan_cv(text: str) -> dict:
    import openai
    if not settings.OPENROUTER_API_KEY:
        return {"error": "API key tidak ada"}
    client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role":"system","content":"""Anda adalah evaluator tender Indonesia. Analisa dokumen CV/Company Profile.
Output JSON: {
"nama_perusahaan":"...", "bidang_usaha":"...",
"skor_legalitas":0, "skor_pengalaman":0, "skor_kemampuan_teknis":0, "skor_keuangan":0,
"skor_total":0, "peluang_lolos_tender_pct":0,
"kekuatan":["..."], "kelemahan":["..."],
"dokumen_lengkap":["..."], "dokumen_kurang":["..."],
"rekomendasi":"...", "verdict":"KUAT|CUKUP|LEMAH"
}
Skor 0-100. skor_total = rata-rata 4 skor."""},
                {"role":"user","content":f"Analisa dokumen berikut:\n\n{text[:4000]}"}
            ],
            temperature=0.3, response_format={"type":"json_object"}, max_tokens=1200,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


def build_pdf_report(df_items, ai_items, war_report, filename="") -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import cm
    from datetime import datetime
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("VENDOR WAR REPORT", styles["Title"]))
    story.append(Paragraph(f"File: {filename} | {datetime.now().strftime('%d %B %Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 0.3*cm))

    total = df_items["Subtotal"].sum()
    avg_m = sum(x.get("margin_estimasi_pct",0) for x in ai_items)/max(len(ai_items),1) if ai_items else 0
    verdict = war_report.get("verdict","—")
    kpi = [["Total Submit","Margin Est.","Peluang Menang","Verdict"],
           [f"Rp {int(total):,}", f"{avg_m:.1f}%", f"{war_report.get('peluang_menang_pct','—')}%", verdict]]
    kt = Table(kpi, colWidths=[5*cm]*4)
    kt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.4,colors.grey),
        ("BACKGROUND",(0,1),(-1,1),colors.HexColor("#EEF3FF")),
    ]))
    story.append(kt)
    story.append(Spacer(1, 0.3*cm))

    if war_report.get("strategi_submit"):
        story.append(Paragraph("STRATEGI: " + war_report["strategi_submit"], styles["Normal"]))
        story.append(Spacer(1, 0.2*cm))

    if ai_items:
        story.append(Paragraph("ANALISA PER ITEM (AI)", styles["Heading2"]))
        ai_tbl = [["Item","Submit Ideal","Markup Aman%","Markup Agresif%","Margin%","Risiko","Curiga","Kategori"]]
        for x in ai_items:
            ai_tbl.append([str(x.get("item",""))[:35],
                f"Rp {int(x.get('harga_submit_ideal',0)):,}" if x.get("harga_submit_ideal") else "—",
                f"{x.get('markup_aman_pct',0)}%", f"{x.get('markup_agresif_pct',0)}%",
                f"{x.get('margin_estimasi_pct',0)}%", str(x.get("risiko_kalah","—")),
                str(x.get("curiga_evaluator","—")), str(x.get("kategori","—"))])
        at = Table(ai_tbl, colWidths=[7*cm,3*cm,2.5*cm,2.5*cm,2*cm,2*cm,2*cm,2*cm], repeatRows=1)
        at.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1E3A5F")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),7),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#F5F5FF"),colors.white]),
            ("GRID",(0,0),(-1,-1),0.25,colors.grey),
            ("ALIGN",(1,0),(-1,-1),"CENTER"),
        ]))
        story.append(at)

    if war_report.get("alasan_verdict"):
        story.append(Spacer(1,0.3*cm))
        vstyle = ParagraphStyle("v", parent=styles["Normal"],
            textColor=colors.green if verdict=="GO" else colors.red, fontName="Helvetica-Bold")
        story.append(Paragraph(f"VERDICT: {verdict} — {war_report['alasan_verdict']}", vstyle))

    doc.build(story)
    return buf.getvalue()


# ── UI ───────────────────────────────────────────────────────────────────────
st.title("⚔️ Vendor War Mode")
st.caption("Upload RAB/BOQ → AI bedah per item → strategi markup & profit → War Report PDF")

tab1, tab2, tab3, tab4 = st.tabs([
    "📂 1. Upload & Scan",
    "🔍 2. Analisa AI per Item",
    "🛡️ 3. Legal & Checklist",
    "📊 4. Final War Report",
])

# ── TAB 1 ────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Upload Dokumen RAB / BOQ / Tender")
    uploaded = st.file_uploader("Format: Excel (.xlsx/.xls) atau CSV", type=["xlsx","xls","csv"])

    if uploaded:
        col1, col2 = st.columns(2)
        use_ai = col1.checkbox("Aktifkan AI Analysis (OpenRouter)", value=True)
        col2.caption(f"API Key: {'✅' if settings.OPENROUTER_API_KEY else '❌ Tidak ada'}")

        if st.button("🚀 Scan & Analisa Sekarang", type="primary", use_container_width=True):
            try:
                df_raw = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            except Exception as e:
                st.error(f"Gagal baca file: {e}"); st.stop()

            # Deteksi kolom
            item_col  = detect_col(df_raw, ["uraian pekerjaan","uraian","item","pekerjaan","description","nama"])
            price_col = detect_col(df_raw, ["harga satuan","harga_satuan","unit price","price satuan"])
            qty_col   = detect_col(df_raw, ["qty","volume","kuantitas","jumlah","vol"])
            sat_col   = detect_col(df_raw, ["satuan","unit","sat"])

            master = load_master()
            rows = []
            for _, row in df_raw.iterrows():
                item = str(row.get(item_col,"")).strip() if item_col else ""
                if not item or item.lower() in ["nan","none","","-"]: continue
                # Skip baris total/subtotal
                if any(k in item.lower() for k in ["total","subtotal","ppn","grand","pajak"]): continue

                hs  = parse_num(row.get(price_col, 0)) if price_col else 0
                qty = parse_num(row.get(qty_col, 1))   if qty_col  else 1
                if qty == 0: qty = 1
                sat = str(row.get(sat_col,"")).strip()  if sat_col  else ""

                ref = fuzzy_match(item, master)
                harga_ref = ref["pasar"] if ref else 0
                harga_rab = ref["rab"]   if ref else 0
                selisih   = hs - harga_ref if harga_ref > 0 else 0
                pct       = selisih/harga_ref*100 if harga_ref > 0 else 0

                rows.append({
                    "Item": item, "Qty": qty, "Satuan": sat,
                    "Harga Submit": hs,
                    "Harga Ref": harga_ref,
                    "Harga RAB Std": harga_rab,
                    "Selisih (%)": round(pct,1),
                    "Subtotal": hs * qty,
                })

            df_items = pd.DataFrame(rows)
            st.session_state.update({
                "wm_df_raw": df_raw, "wm_df_items": df_items,
                "wm_filename": uploaded.name,
                "wm_ai_items": [], "wm_war_report": {}, "wm_ai_done": False,
            })

            # Validasi total vs Excel
            total_calc  = df_items["Subtotal"].sum()
            # Cari grand total di file asli (baris GRAND TOTAL / TOTAL)
            gt_row = df_raw[df_raw.apply(
                lambda r: any("grand total" in str(v).lower() or ("total" == str(v).lower()) for v in r), axis=1
            )]

            st.success(f"✅ {len(df_items)} item diparsing | Total dihitung: **Rp {int(total_calc):,}**")
            if not gt_row.empty:
                st.info(f"Grand Total dari file: lihat baris → {gt_row.iloc[0].tolist()}")
            st.dataframe(df_items, hide_index=True, use_container_width=True)

            if use_ai and len(df_items) > 0:
                with st.spinner(f"AI menganalisa {min(len(df_items),40)} item..."):
                    ai_items = ai_analyze_items(df_items)
                    st.session_state["wm_ai_items"] = ai_items
                    st.session_state["wm_ai_done"]  = True
                if ai_items:
                    with st.spinner("Membuat War Report..."):
                        wr = ai_war_report(df_items, ai_items)
                        st.session_state["wm_war_report"] = wr
                    st.success(f"AI selesai: {len(ai_items)} item. Buka Tab 2 & 4.")
                    avg_m = sum(x.get("margin_estimasi_pct",0) for x in ai_items)/max(len(ai_items),1)
                    try:
                        save_scan_history(
                            filename=uploaded.name,
                            grand_total=df_items["Subtotal"].sum(),
                            item_count=len(df_items),
                            avg_margin=round(avg_m,1),
                            peluang_pct=wr.get("peluang_menang_pct","—"),
                            verdict=wr.get("verdict","—"),
                            strategi=wr.get("strategi_submit",""),
                            alasan=wr.get("alasan_verdict",""),
                        )
                    except Exception:
                        pass
    else:
        st.info("Upload file RAB/BOQ/Excel untuk mulai.")

# ── TAB 2 ────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Analisa Strategis per Item (AI + Master Data)")
    if "wm_df_items" not in st.session_state:
        st.warning("Upload file di Tab 1 dulu.")
    else:
        df_items = st.session_state["wm_df_items"]
        ai_items = st.session_state.get("wm_ai_items", [])

        if df_items.empty:
            st.warning("Tidak ada item. Cek format file.")
        else:
            ai_map = {x.get("item","").lower(): x for x in ai_items}
            df_d = df_items.copy()
            df_d["Submit Ideal (AI)"]     = df_d["Item"].apply(lambda x: ai_map.get(x.lower(),{}).get("harga_submit_ideal","—"))
            df_d["Markup Aman % (AI)"]    = df_d["Item"].apply(lambda x: ai_map.get(x.lower(),{}).get("markup_aman_pct","—"))
            df_d["Markup Agresif % (AI)"] = df_d["Item"].apply(lambda x: ai_map.get(x.lower(),{}).get("markup_agresif_pct","—"))
            df_d["Margin Est. % (AI)"]    = df_d["Item"].apply(lambda x: ai_map.get(x.lower(),{}).get("margin_estimasi_pct","—"))
            df_d["Risiko Kalah"]          = df_d["Item"].apply(lambda x: ai_map.get(x.lower(),{}).get("risiko_kalah","—"))
            df_d["Curiga Evaluator"]      = df_d["Item"].apply(lambda x: ai_map.get(x.lower(),{}).get("curiga_evaluator","—"))
            df_d["Kategori (AI)"]         = df_d["Item"].apply(lambda x: ai_map.get(x.lower(),{}).get("kategori","—"))

            flt = st.selectbox("Filter Kategori", ["Semua","tebal","tipis","rawan"])
            df_show = df_d if flt == "Semua" else df_d[df_d["Kategori (AI)"].str.lower() == flt]
            st.dataframe(df_show, hide_index=True, use_container_width=True)

            if ai_items:
                with st.expander("📋 Detail Alasan Strategi"):
                    for x in ai_items:
                        kat = x.get("kategori","—")
                        ic  = {"tebal":"🟢","tipis":"🟡","rawan":"🔴"}.get(kat,"⚪")
                        st.markdown(
                            f"**{ic} {x.get('item','')}** | "
                            f"Markup aman: **{x.get('markup_aman_pct',0)}%** | "
                            f"Agresif: **{x.get('markup_agresif_pct',0)}%** | "
                            f"Margin: **{x.get('margin_estimasi_pct',0)}%** | "
                            f"Risiko: {x.get('risiko_kalah','—')} | Curiga: {x.get('curiga_evaluator','—')}"
                        )
                        if x.get("alasan"):
                            st.caption(f"↳ {x['alasan']}")

            st.download_button("📄 Export CSV", df_d.to_csv(index=False).encode("utf-8"),
                               "war_analisa.csv", "text/csv")

# ── TAB 3 ────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Checklist Kelengkapan Dokumen Tender")
    c1, c2 = st.columns(2)
    checks = {}
    with c1:
        st.markdown("**Legalitas Utama**")
        checks["NIB (KBLI Tepat)"]           = st.checkbox("NIB (KBLI Tepat)")
        checks["NPWP Aktif"]                 = st.checkbox("NPWP Aktif")
        checks["PKP (jika wajib)"]           = st.checkbox("PKP (jika wajib)")
        checks["OSS Valid"]                  = st.checkbox("OSS Valid")
        checks["SBU / IUJP sesuai bidang"]   = st.checkbox("SBU / IUJP sesuai bidang")
        checks["SKK Tenaga Ahli"]            = st.checkbox("SKK Tenaga Ahli")
        checks["SPT Tahunan 2 th terakhir"]  = st.checkbox("SPT Tahunan 2 th terakhir")
        checks["Laporan Keuangan"]           = st.checkbox("Laporan Keuangan (2 th)")
    with c2:
        st.markdown("**Teknis & Keuangan**")
        checks["Kontrak Pengalaman Serupa"]  = st.checkbox("Kontrak Pengalaman Serupa ≥1")
        checks["Referensi Bank"]             = st.checkbox("Referensi Bank")
        checks["Jaminan Penawaran"]          = st.checkbox("Jaminan Penawaran (Asli)")
        checks["Jaminan Pelaksanaan (siap)"] = st.checkbox("Jaminan Pelaksanaan (siap)")
        checks["Surat Dukungan Pabrikan"]    = st.checkbox("Surat Dukungan Pabrikan")
        checks["Dokumen Custom Panitia"]     = st.checkbox("Dokumen Custom Panitia")
        checks["BPJS (bukti iuran terbaru)"] = st.checkbox("BPJS (bukti iuran terbaru)")
        checks["Akta + SK Kemenkumham"]      = st.checkbox("Akta + SK Kemenkumham")

    ready = sum(checks.values())
    total = len(checks)
    pct   = ready/total*100
    CRITICAL = ["NIB (KBLI Tepat)", "NPWP Aktif", "SBU / IUJP sesuai bidang", "SKK Tenaga Ahli"]
    missing  = [k for k,v in checks.items() if not v]
    missing_critical = [k for k in missing if k in CRITICAL]
    # Simpan ke session state untuk dipakai Tab 4
    st.session_state["wm_legal_score"]    = round(pct)
    st.session_state["wm_legal_missing"]  = missing
    st.session_state["wm_legal_critical"] = missing_critical

    st.markdown("---")
    st.progress(pct/100, text=f"Kesiapan: {ready}/{total} ({pct:.0f}%)")
    if missing_critical:
        st.error("⛔ Dokumen KRITIS belum ada: " + " | ".join(missing_critical))
    if missing and not missing_critical:
        st.warning("Belum siap: " + " | ".join(missing))
    if not missing:
        st.success("Semua dokumen siap! Legal compliance 100%")

# ── TAB 4 ────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Final War Report — Keputusan Submit Tender")
    if "wm_df_items" not in st.session_state:
        st.warning("Upload file di Tab 1 dulu.")
    else:
        df_items   = st.session_state["wm_df_items"]
        ai_items   = st.session_state.get("wm_ai_items", [])
        war_report = st.session_state.get("wm_war_report", {})
        df_raw     = st.session_state.get("wm_df_raw", pd.DataFrame())
        fname      = st.session_state.get("wm_filename", "RAB")

        # Legal data dari Tab 3
        legal_score    = st.session_state.get("wm_legal_score", None)
        legal_missing  = st.session_state.get("wm_legal_missing", [])
        legal_critical = st.session_state.get("wm_legal_critical", [])

        total_submit = df_items["Subtotal"].sum()
        avg_margin   = sum(x.get("margin_estimasi_pct",0) for x in ai_items)/max(len(ai_items),1) if ai_items else 0
        tebal = [x for x in ai_items if x.get("kategori")=="tebal"]
        rawan = [x for x in ai_items if x.get("kategori")=="rawan"]
        peluang_raw  = war_report.get("peluang_menang_pct", "—")
        suspicious   = war_report.get("suspicious_score_pct","—")
        verdict      = war_report.get("verdict","—")

        # Kalkulasi peluang yang sudah dikoreksi legal
        try:
            p_base = float(peluang_raw)
            if legal_score is not None:
                if legal_critical:
                    p_adj = max(0, p_base - 25)
                elif legal_score < 75:
                    p_adj = max(0, p_base - 15)
                elif legal_score >= 90:
                    p_adj = min(100, p_base + 5)
                else:
                    p_adj = p_base
            else:
                p_adj = p_base
            peluang_display = f"{p_adj:.0f}"
        except Exception:
            peluang_display = str(peluang_raw)

        k1,k2,k3,k4 = st.columns(4)
        k1.markdown(f'<div class="kpi-card" style="border-color:#00E676"><b>Total Harga Submit</b><br/>'
                    f'<span class="kpi-val" style="color:#00E676">Rp {int(total_submit):,}</span></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card" style="border-color:#{"00E676" if avg_margin>=15 else "FFEA00"}"><b>Margin Est.</b><br/>'
                    f'<span class="kpi-val" style="color:#FFEA00">{avg_margin:.1f}%</span></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card" style="border-color:#1E90FF"><b>Peluang Menang</b><br/>'
                    f'<span class="kpi-val" style="color:#1E90FF">{peluang_display}%</span><br/>'
                    f'<small style="color:#aaa;">{"(disesuaikan legal)" if legal_score is not None else ""}</small></div>',
                    unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-card" style="border-color:#FF6D00"><b>Suspicious Score</b><br/>'
                    f'<span class="kpi-val" style="color:#FF6D00">{suspicious}%</span></div>', unsafe_allow_html=True)

        st.markdown("---")
        if verdict == "GO":
            st.success(f"**VERDICT: {verdict}** — {war_report.get('alasan_verdict','')}")
        elif verdict == "NO GO":
            st.error(f"**VERDICT: {verdict}** — {war_report.get('alasan_verdict','')}")
        elif verdict:
            st.warning(f"**VERDICT: {verdict}** — {war_report.get('alasan_verdict','')}")

        if war_report.get("strategi_submit"):
            st.info(f"**Strategi Submit:** {war_report['strategi_submit']}")
        if war_report.get("taktik_utama"):
            st.markdown(f"**Taktik Utama:** {war_report['taktik_utama']}")

        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### Item Profit Tebal 🟢")
            for x in tebal[:5]:
                st.success(f"**{x['item']}** — markup {x.get('markup_aman_pct',0)}%, margin {x.get('margin_estimasi_pct',0)}%")
            if not tebal and war_report.get("item_profit_tertinggi"):
                st.success(war_report["item_profit_tertinggi"])
        with cr:
            st.markdown("#### Item Rawan Evaluator 🔴")
            for x in rawan[:5]:
                st.error(f"**{x['item']}** — {x.get('alasan','')[:80]}")
            if not rawan and war_report.get("item_paling_rawan"):
                st.error(war_report["item_paling_rawan"])

        # ── Legal Compliance Block (P4) ──────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🛡️ Legal Compliance")
        if legal_score is None:
            st.info("Isi Tab 3 (Legal Checklist) untuk melihat Legal Compliance Score.")
        else:
            admin_pass = "TINGGI" if legal_score >= 90 else ("SEDANG" if legal_score >= 75 else "RENDAH")
            acolor     = "success" if admin_pass == "TINGGI" else ("warning" if admin_pass == "SEDANG" else "error")
            lc1, lc2, lc3 = st.columns(3)
            lc1.metric("Legal Compliance Score", f"{legal_score}%")
            lc2.metric("Admin Pass Probability", admin_pass)
            lc3.metric("Missing Critical Docs",  len(legal_critical))
            if legal_critical:
                st.error("⛔ **Risiko GUGUR ADMINISTRASI** — dokumen kritis belum ada: " + ", ".join(legal_critical))
            elif legal_missing:
                st.warning("⚠️ Dokumen pelengkap belum lengkap: " + ", ".join(legal_missing))
            else:
                st.success("✅ Legal compliance penuh — risiko gugur admin sangat rendah.")

        st.markdown("---")
        e1,e2,e3 = st.columns(3)
        with e1:
            st.download_button("📄 CSV", df_items.to_csv(index=False).encode("utf-8"),
                               "war_report.csv","text/csv", use_container_width=True)
        with e2:
            buf_xl = io.BytesIO()
            with pd.ExcelWriter(buf_xl, engine="xlsxwriter") as wr:
                df_raw.to_excel(wr, sheet_name="Data Asli", index=False)
                df_items.to_excel(wr, sheet_name="Analisa Harga", index=False)
                if ai_items: pd.DataFrame(ai_items).to_excel(wr, sheet_name="AI Strategy", index=False)
            st.download_button("📊 Excel", buf_xl.getvalue(), "war_report.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        with e3:
            try:
                pdf_b = build_pdf_report(df_items, ai_items, war_report, fname)
                st.download_button("📑 PDF War Report", pdf_b, "war_report.pdf",
                                   "application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"PDF: {e}")
