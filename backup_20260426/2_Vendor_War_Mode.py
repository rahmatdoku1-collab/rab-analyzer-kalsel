import streamlit as st
import pandas as pd
import io, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings

st.set_page_config(page_title="Vendor War Mode", page_icon="⚔️", layout="wide")
st.markdown("""<style>
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
.kpi-card{background:#1A1A1D;padding:16px;border-radius:8px;border:1px solid #333;color:white;text-align:center;}
.kpi-val{font-size:1.8rem;font-weight:700;}
.green{color:#00E676;}.red{color:#FF1744;}.yellow{color:#FFEA00;}.blue{color:#1E90FF;}
</style>""", unsafe_allow_html=True)

MASTER_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "master_harga.db")

# ── helpers ─────────────────────────────────────────────────────────────────

def load_master() -> dict:
    if not os.path.exists(MASTER_DB):
        return {}
    import sqlite3
    conn = sqlite3.connect(MASTER_DB)
    rows = conn.execute(
        "SELECT nama_item, harga_pasar, harga_median FROM master_harga WHERE harga_median > 0"
    ).fetchall()
    conn.close()
    result = {}
    for nama, pasar, median in rows:
        result[nama.lower()] = {"pasar": pasar or median, "rab": median}
    return result


def detect_col(df, kws):
    for c in df.columns:
        if any(k in c.lower() for k in kws):
            return c
    return None


def parse_num(val):
    try:
        return float(str(val).replace(",", "").replace(".", "").replace("Rp", "").replace(" ", "").strip())
    except Exception:
        return 0


def match_master(item_name: str, master: dict):
    name_low = item_name.lower()
    best, best_score = None, 0
    for key, val in master.items():
        words = [w for w in key.split() if len(w) > 3]
        score = sum(1 for w in words if w in name_low)
        if score > best_score:
            best_score = score
            best = val
    return best if best_score > 0 else None


def ai_analyze_items(df_items: pd.DataFrame) -> list:
    """Call OpenRouter untuk strategic per-item analysis. Returns list of dicts."""
    import openai
    if not settings.OPENROUTER_API_KEY:
        return []

    items_text = []
    for _, row in df_items.iterrows():
        items_text.append(
            f"- {row['Item']} | Submit: Rp{int(row['Harga Submit']):,} "
            f"| Ref Pasar: Rp{int(row['Harga Ref']):,} | Qty: {row['Qty']} {row['Satuan']}"
        )

    prompt_items = "\n".join(items_text[:40])  # max 40 item per call

    system = """Anda adalah Senior Tender Strategist CV/Vendor di Kalimantan Selatan.
Posisi Anda: VENDOR yang ingin menang tender dengan PROFIT MAKSIMAL sekaligus lolos evaluasi.

Untuk setiap item RAB yang diberikan, analisa dari sudut pandang vendor:
- Berapa harga submit ideal (kompetitif tapi tetap profit)
- Range markup aman (%)
- Markup agresif maksimal (%)
- Margin estimasi realistis (%)
- Risiko kalah tender jika harga terlalu tinggi
- Apakah evaluator akan curiga dengan harga ini
- Alasan kenapa item ini bisa di-markup atau harus tipis
- Kategori: "tebal" (margin besar aman), "tipis" (harus kompetitif), "rawan" (evaluator sorot)

Output HARUS JSON array:
[{
  "item": "nama item",
  "harga_submit_ideal": 0,
  "markup_aman_pct": 0,
  "markup_agresif_pct": 0,
  "margin_estimasi_pct": 0,
  "risiko_kalah": "Rendah|Sedang|Tinggi",
  "curiga_evaluator": "Ya|Tidak",
  "alasan": "penjelasan singkat strategi",
  "kategori": "tebal|tipis|rawan"
}]"""

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Analisa item RAB berikut:\n{prompt_items}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=3000,
        )
        content = resp.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        for v in parsed.values():
            if isinstance(v, list):
                return v
        return []
    except Exception as e:
        st.warning(f"AI analysis partial error: {e}")
        return []


def ai_war_report(df_analysis: pd.DataFrame, ai_items: list) -> dict:
    """Generate final war report narrative via AI."""
    import openai
    if not settings.OPENROUTER_API_KEY:
        return {}

    total_submit = df_analysis["Subtotal"].sum()
    tebal = [x for x in ai_items if x.get("kategori") == "tebal"]
    tipis = [x for x in ai_items if x.get("kategori") == "tipis"]
    rawan = [x for x in ai_items if x.get("kategori") == "rawan"]
    avg_margin = sum(x.get("margin_estimasi_pct", 0) for x in ai_items) / max(len(ai_items), 1)

    summary = (
        f"Total nilai submit: Rp{int(total_submit):,}. "
        f"Item tebal margin: {len(tebal)}. Item tipis: {len(tipis)}. Item rawan evaluator: {len(rawan)}. "
        f"Rata-rata margin estimasi: {avg_margin:.1f}%."
    )
    if tebal:
        summary += f" Item tebal: {', '.join(x['item'][:20] for x in tebal[:3])}."
    if rawan:
        summary += f" Item rawan: {', '.join(x['item'][:20] for x in rawan[:3])}."

    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "Anda adalah Senior Tender Strategist. Berikan war report ringkas untuk vendor/CV "
                    "yang akan submit tender. Output JSON: {"
                    '"strategi_submit": "...", '
                    '"taktik_utama": "...", '
                    '"item_profit_tertinggi": "...", '
                    '"item_paling_rawan": "...", '
                    '"peluang_menang_pct": 0, '
                    '"suspicious_score_pct": 0, '
                    '"verdict": "GO|REVISI|NO GO", '
                    '"alasan_verdict": "..."}'
                )},
                {"role": "user", "content": summary}
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {}


def build_pdf_report(df_raw, df_analysis, ai_items, war_report, filename="") -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import cm
    from datetime import datetime

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    bold_red = ParagraphStyle("br", parent=styles["Normal"], textColor=colors.red, fontName="Helvetica-Bold")
    bold_grn = ParagraphStyle("bg", parent=styles["Normal"], textColor=colors.HexColor("#006400"), fontName="Helvetica-Bold")
    story = []

    # Header
    story.append(Paragraph("VENDOR WAR REPORT — ANALISA STRATEGIS TENDER", styles["Title"]))
    story.append(Paragraph(f"File: {filename} | {datetime.now().strftime('%d %B %Y %H:%M')} | AI OpenRouter", styles["Normal"]))
    story.append(Spacer(1, 0.3*cm))

    # Summary KPI
    total = df_analysis["Subtotal"].sum()
    avg_margin = sum(x.get("margin_estimasi_pct", 0) for x in ai_items) / max(len(ai_items), 1) if ai_items else 0
    verdict = war_report.get("verdict", "—")
    peluang = war_report.get("peluang_menang_pct", "—")

    kpi_data = [["Total Nilai Submit","Margin Est.","Peluang Menang","Verdict"],
                [f"Rp {int(total):,}", f"{avg_margin:.1f}%", f"{peluang}%", verdict]]
    kt = Table(kpi_data, colWidths=[5.5*cm]*4)
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
    story.append(Spacer(1, 0.4*cm))

    # Strategi
    if war_report.get("strategi_submit"):
        story.append(Paragraph("STRATEGI SUBMIT", styles["Heading2"]))
        story.append(Paragraph(war_report["strategi_submit"], styles["Normal"]))
        if war_report.get("taktik_utama"):
            story.append(Paragraph(f"Taktik: {war_report['taktik_utama']}", styles["Normal"]))
        story.append(Spacer(1, 0.3*cm))

    # Per-item AI table
    if ai_items:
        story.append(Paragraph("ANALISA STRATEGIS PER ITEM (AI)", styles["Heading2"]))
        ai_tbl = [["Item", "Submit Ideal", "Markup Aman%", "Markup Agresif%", "Margin%", "Risiko", "Curiga?", "Kategori"]]
        for x in ai_items:
            ai_tbl.append([
                str(x.get("item",""))[:35],
                f"Rp {int(x.get('harga_submit_ideal',0)):,}" if x.get("harga_submit_ideal") else "—",
                f"{x.get('markup_aman_pct',0)}%",
                f"{x.get('markup_agresif_pct',0)}%",
                f"{x.get('margin_estimasi_pct',0)}%",
                str(x.get("risiko_kalah","—")),
                str(x.get("curiga_evaluator","—")),
                str(x.get("kategori","—")),
            ])
        cw = [7*cm,3*cm,2.5*cm,2.5*cm,2*cm,2*cm,2*cm,2*cm]
        at = Table(ai_tbl, colWidths=cw, repeatRows=1)
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
        story.append(Spacer(1, 0.3*cm))

    # Verdict
    if war_report.get("alasan_verdict"):
        vstyle = bold_grn if verdict == "GO" else bold_red
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
    "📊 4. Final War Report"
])

# ── TAB 1: UPLOAD ────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Upload Dokumen RAB / BOQ / Tender")
    uploaded = st.file_uploader(
        "Format: Excel (.xlsx/.xls) atau CSV",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded:
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            use_ai = st.checkbox("Aktifkan AI Analysis (OpenRouter)", value=True,
                                 help="AI analisa markup strategy per item. ~5-15 detik, hemat token.")
        with col_opt2:
            st.caption(f"API Key: {'✅ Tersedia' if settings.OPENROUTER_API_KEY else '❌ Tidak ada'}")

        if st.button("🚀 Scan & Analisa Sekarang", type="primary", use_container_width=True):
            with st.spinner("Membaca file..."):
                try:
                    df_raw = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") \
                        else pd.read_excel(uploaded)
                except Exception as e:
                    st.error(f"Gagal baca file: {e}"); st.stop()

            item_col  = detect_col(df_raw, ["uraian","item","pekerjaan","description","nama","no"])
            price_col = detect_col(df_raw, ["harga satuan","harga_satuan","unit price","price","harga"])
            qty_col   = detect_col(df_raw, ["volume","qty","kuantitas","jumlah","vol"])
            sat_col   = detect_col(df_raw, ["satuan","unit","sat"])

            master = load_master()
            rows = []
            for _, row in df_raw.iterrows():
                item  = str(row.get(item_col,"")).strip() if item_col else ""
                hs    = parse_num(row.get(price_col,0)) if price_col else 0
                qty   = parse_num(row.get(qty_col,1)) if qty_col else 1
                sat   = str(row.get(sat_col,"")) if sat_col else ""
                if not item or item.lower() in ["nan","none",""]: continue

                ref_data = match_master(item, master)
                harga_ref  = ref_data["pasar"] if ref_data else 0
                harga_rab  = ref_data["rab"]   if ref_data else 0
                selisih    = hs - harga_ref if harga_ref > 0 else 0
                pct        = selisih / harga_ref * 100 if harga_ref > 0 else 0

                rows.append({
                    "Item": item,
                    "Qty": qty,
                    "Satuan": sat,
                    "Harga Submit": hs,
                    "Harga Ref": harga_ref,
                    "Harga RAB Std": harga_rab,
                    "Selisih (%)": round(pct, 1),
                    "Subtotal": hs * qty,
                })

            df_items = pd.DataFrame(rows)
            st.session_state["wm_df_raw"]   = df_raw
            st.session_state["wm_df_items"] = df_items
            st.session_state["wm_filename"] = uploaded.name
            st.session_state["wm_ai_done"]  = False
            st.session_state["wm_ai_items"] = []
            st.session_state["wm_war_report"] = {}

            n = len(df_items)
            st.success(f"File dibaca: {len(df_raw)} baris → {n} item valid")
            st.dataframe(df_items.head(10), hide_index=True, use_container_width=True)

            if use_ai and n > 0:
                with st.spinner(f"AI menganalisa {min(n,40)} item via OpenRouter..."):
                    ai_items = ai_analyze_items(df_items)
                    st.session_state["wm_ai_items"] = ai_items
                    st.session_state["wm_ai_done"]  = True

                if ai_items:
                    with st.spinner("Membuat War Report AI..."):
                        wr = ai_war_report(df_items, ai_items)
                        st.session_state["wm_war_report"] = wr

                    st.success(f"AI selesai: {len(ai_items)} item dianalisa. Buka Tab 2 & 4.")
                else:
                    st.warning("AI tidak mengembalikan hasil. Cek API key atau coba lagi.")
            else:
                st.info("Buka Tab 2 untuk analisa detail.")
    else:
        st.info("Upload file RAB/BOQ/Excel untuk mulai.")

# ── TAB 2: ANALISA PER ITEM ──────────────────────────────────────────────────
with tab2:
    st.markdown("### Analisa Strategis per Item (AI + Master Data)")
    if not st.session_state.get("wm_df_items") is not None and "wm_df_items" not in st.session_state:
        st.warning("Upload file di Tab 1 dulu."); st.stop()
    if "wm_df_items" not in st.session_state:
        st.warning("Upload file di Tab 1 dulu."); st.stop()

    df_items   = st.session_state["wm_df_items"]
    ai_items   = st.session_state.get("wm_ai_items", [])

    if df_items.empty:
        st.warning("Tidak ada item ditemukan di file."); st.stop()

    # Merge AI results
    ai_map = {x.get("item","").lower(): x for x in ai_items}
    df_display = df_items.copy()
    df_display["Submit Ideal (AI)"]    = df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("harga_submit_ideal", "—"))
    df_display["Markup Aman % (AI)"]   = df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("markup_aman_pct", "—"))
    df_display["Markup Agresif % (AI)"]= df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("markup_agresif_pct", "—"))
    df_display["Margin Est. % (AI)"]   = df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("margin_estimasi_pct", "—"))
    df_display["Risiko Kalah (AI)"]    = df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("risiko_kalah", "—"))
    df_display["Curiga Evaluator"]     = df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("curiga_evaluator", "—"))
    df_display["Kategori (AI)"]        = df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("kategori", "—"))
    df_display["Alasan Strategi"]      = df_display["Item"].apply(lambda x: ai_map.get(x.lower(), {}).get("alasan", ""))

    filter_kat = st.selectbox("Filter", ["Semua","tebal","tipis","rawan","—"])
    if filter_kat != "Semua":
        mask = df_display["Kategori (AI)"].str.lower() == filter_kat.lower()
        df_show = df_display[mask]
    else:
        df_show = df_display

    st.dataframe(df_show, hide_index=True, use_container_width=True)

    if ai_items:
        with st.expander("📋 Detail Alasan Strategi per Item"):
            for x in ai_items:
                kat = x.get("kategori","—")
                color = {"tebal":"🟢","tipis":"🟡","rawan":"🔴"}.get(kat,"⚪")
                st.markdown(
                    f"**{color} {x.get('item','')}** "
                    f"| Markup aman: {x.get('markup_aman_pct',0)}% "
                    f"| Agresif: {x.get('markup_agresif_pct',0)}% "
                    f"| Margin: {x.get('margin_estimasi_pct',0)}% "
                    f"| Risiko: {x.get('risiko_kalah','—')} "
                    f"| Curiga: {x.get('curiga_evaluator','—')}"
                )
                if x.get("alasan"):
                    st.caption(f"↳ {x['alasan']}")

    st.download_button("📄 Export CSV Analisa", df_display.to_csv(index=False).encode("utf-8"),
                       "war_mode_analisa.csv", "text/csv")

# ── TAB 3: LEGAL & CHECKLIST ─────────────────────────────────────────────────
with tab3:
    st.markdown("### Checklist Kelengkapan Dokumen Tender")
    st.caption("Centang item yang SUDAH siap. Item merah = harus diselesaikan sebelum submit.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Dokumen Legalitas Utama**")
        nib      = st.checkbox("NIB (Nomor Induk Berusaha) — KBLI Tepat")
        npwp     = st.checkbox("NPWP Perusahaan Aktif")
        pkp      = st.checkbox("PKP (Pengusaha Kena Pajak) — jika wajib")
        oss      = st.checkbox("Status OSS Valid & Tidak Kedaluwarsa")
        sbu      = st.checkbox("SBU / IUJP / SIUJK Sesuai Bidang Tender")
        skk      = st.checkbox("SKK Tenaga Ahli (sesuai jabatan & jenjang)")
        spt      = st.checkbox("SPT Tahunan 2 Tahun Terakhir (bukti setor)")
        lap_keu  = st.checkbox("Laporan Keuangan 2 Tahun (Audited/Non-Audited)")

    with c2:
        st.markdown("**Dokumen Teknis & Keuangan**")
        pengalam = st.checkbox("Kontrak / SPK Pengalaman Kerja Serupa (≥1 kontrak)")
        ref_bank = st.checkbox("Referensi Bank (atas nama perusahaan)")
        jamin_p  = st.checkbox("Jaminan Penawaran (Asli, masa berlaku cukup)")
        jamin_pl = st.checkbox("Jaminan Pelaksanaan (siap disiapkan jika menang)")
        duk_pab  = st.checkbox("Surat Dukungan Pabrikan / Distributor (jika ada item material)")
        dok_kus  = st.checkbox("Dokumen Custom Panitia (sesuai dokumen pengadaan)")
        bpjs     = st.checkbox("BPJS Ketenagakerjaan & Kesehatan (bukti iuran terbaru)")
        akta     = st.checkbox("Akta Perusahaan + SK Kemenkumham Terbaru")

    all_items = [nib, npwp, pkp, oss, sbu, skk, spt, lap_keu,
                 pengalam, ref_bank, jamin_p, jamin_pl, duk_pab, dok_kus, bpjs, akta]
    ready = sum(all_items)
    total_doc = len(all_items)
    pct_ready = ready / total_doc * 100

    st.markdown("---")
    st.progress(pct_ready / 100, text=f"Kesiapan Dokumen: {ready}/{total_doc} ({pct_ready:.0f}%)")
    if pct_ready == 100:
        st.success("Semua dokumen siap. Anda boleh submit!")
    elif pct_ready >= 75:
        st.warning(f"{total_doc - ready} dokumen belum siap. Segera lengkapi sebelum deadline.")
    else:
        st.error(f"PERINGATAN: {total_doc - ready} dokumen kritis belum ada. Risiko gugur administrasi TINGGI.")

# ── TAB 4: FINAL WAR REPORT ──────────────────────────────────────────────────
with tab4:
    st.markdown("### Final War Report — Keputusan Submit Tender")

    if "wm_df_items" not in st.session_state:
        st.warning("Upload dan scan file di Tab 1 terlebih dahulu.")
        st.stop()

    df_items   = st.session_state["wm_df_items"]
    ai_items   = st.session_state.get("wm_ai_items", [])
    war_report = st.session_state.get("wm_war_report", {})
    df_raw     = st.session_state.get("wm_df_raw", pd.DataFrame())
    fname      = st.session_state.get("wm_filename", "RAB")

    total_submit = df_items["Subtotal"].sum()
    avg_margin   = sum(x.get("margin_estimasi_pct",0) for x in ai_items) / max(len(ai_items),1) if ai_items else 0
    tebal_items  = [x for x in ai_items if x.get("kategori") == "tebal"]
    rawan_items  = [x for x in ai_items if x.get("kategori") == "rawan"]
    tipis_items  = [x for x in ai_items if x.get("kategori") == "tipis"]
    peluang      = war_report.get("peluang_menang_pct", "—")
    suspicious   = war_report.get("suspicious_score_pct", "—")
    verdict      = war_report.get("verdict", "—")

    # KPI cards
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"""<div class="kpi-card"><div>Total Harga Submit</div>
        <div class="kpi-val green">Rp {int(total_submit):,}</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="kpi-card"><div>Margin Total Est.</div>
        <div class="kpi-val {'green' if avg_margin>=15 else 'yellow'}">{avg_margin:.1f}%</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="kpi-card"><div>Peluang Menang (AI)</div>
        <div class="kpi-val blue">{peluang}%</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="kpi-card"><div>Suspicious Score</div>
        <div class="kpi-val {'red' if str(suspicious).replace('%','').strip().isdigit() and int(str(suspicious).replace('%','').strip())>40 else 'yellow'}">{suspicious}%</div></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Verdict banner
    if verdict == "GO":
        st.success(f"**REKOMENDASI AI: {verdict}** — {war_report.get('alasan_verdict','')}")
    elif verdict == "NO GO":
        st.error(f"**REKOMENDASI AI: {verdict}** — {war_report.get('alasan_verdict','')}")
    elif verdict:
        st.warning(f"**REKOMENDASI AI: {verdict}** — {war_report.get('alasan_verdict','')}")

    if war_report.get("strategi_submit"):
        st.markdown("#### Strategi Submit Terbaik")
        st.info(war_report["strategi_submit"])
    if war_report.get("taktik_utama"):
        st.markdown(f"**Taktik Utama:** {war_report['taktik_utama']}")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Item Paling Profit (Tebal Margin)")
        if tebal_items:
            for x in tebal_items[:5]:
                st.success(f"🟢 **{x['item']}** — Markup aman {x.get('markup_aman_pct',0)}%, margin {x.get('margin_estimasi_pct',0)}%")
        elif war_report.get("item_profit_tertinggi"):
            st.success(f"🟢 {war_report['item_profit_tertinggi']}")
        else:
            st.info("Jalankan AI analysis di Tab 1 untuk insight ini.")

    with col_r:
        st.markdown("#### Item Paling Rawan Sorotan Evaluator")
        if rawan_items:
            for x in rawan_items[:5]:
                st.error(f"🔴 **{x['item']}** — Curiga: {x.get('curiga_evaluator','?')}, risiko: {x.get('risiko_kalah','?')}")
        elif war_report.get("item_paling_rawan"):
            st.error(f"🔴 {war_report['item_paling_rawan']}")
        else:
            st.info("Jalankan AI analysis di Tab 1 untuk insight ini.")

    st.markdown("---")
    st.markdown("### Export Report")
    e1, e2, e3 = st.columns(3)

    with e1:
        st.download_button("📄 CSV",
                           df_items.to_csv(index=False).encode("utf-8"),
                           "war_report.csv", "text/csv", use_container_width=True)
    with e2:
        buf_xl = io.BytesIO()
        with pd.ExcelWriter(buf_xl, engine="xlsxwriter") as wr:
            df_raw.to_excel(wr, sheet_name="Data Asli", index=False)
            df_items.to_excel(wr, sheet_name="Analisa Harga", index=False)
            if ai_items:
                pd.DataFrame(ai_items).to_excel(wr, sheet_name="AI Strategy", index=False)
        st.download_button("📊 Excel (3 Sheet)", buf_xl.getvalue(), "war_report.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with e3:
        try:
            pdf_b = build_pdf_report(df_raw, df_items, ai_items, war_report, fname)
            st.download_button("📑 PDF War Report", pdf_b, "war_report.pdf",
                               "application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"PDF error: {e}")
