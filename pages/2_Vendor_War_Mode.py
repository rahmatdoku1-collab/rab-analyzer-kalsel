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
        "SELECT nama_item, harga_min, harga_median, sektor FROM master_harga WHERE harga_median > 0"
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


def build_pdf_report(df_items, ai_items, war_report, filename="", legal_score=None,
                     legal_missing=None, legal_critical=None) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.units import cm
    from datetime import datetime

    legal_missing  = legal_missing  or []
    legal_critical = legal_critical or []

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    S   = getSampleStyleSheet()

    # Custom styles
    def ps(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=S[parent], **kw)

    sTitle   = ps("sTitle",   "Title",   fontSize=18, spaceAfter=4, textColor=colors.HexColor("#1E3A5F"))
    sSub     = ps("sSub",     "Normal",  fontSize=9,  textColor=colors.grey, spaceAfter=12)
    sH       = ps("sH",       "Heading2",fontSize=12, textColor=colors.HexColor("#1E3A5F"),
                  spaceBefore=14, spaceAfter=6, borderPad=2)
    sBody    = ps("sBody",    "Normal",  fontSize=9,  leading=14, spaceAfter=4)
    sBold    = ps("sBold",    "Normal",  fontSize=9,  fontName="Helvetica-Bold", spaceAfter=4)
    sGO      = ps("sGO",      "Normal",  fontSize=13, fontName="Helvetica-Bold",
                  textColor=colors.HexColor("#00875A"), spaceAfter=6)
    sNOGO    = ps("sNOGO",    "Normal",  fontSize=13, fontName="Helvetica-Bold",
                  textColor=colors.HexColor("#D32F2F"), spaceAfter=6)
    sREVISI  = ps("sREVISI",  "Normal",  fontSize=13, fontName="Helvetica-Bold",
                  textColor=colors.HexColor("#E65100"), spaceAfter=6)
    sBullet  = ps("sBullet",  "Normal",  fontSize=9,  leading=14, leftIndent=12, spaceAfter=2)

    def tbl_style(header_bg="#1E3A5F"):
        return TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor(header_bg)),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,0), 8),
            ("FONTSIZE",    (0,1), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F4F7FB"), colors.white]),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
            ("ALIGN",       (1,0), (-1,-1), "CENTER"),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ])

    def section_divider():
        return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC"), spaceAfter=6)

    total   = df_items["Subtotal"].sum()
    avg_m   = sum(x.get("margin_estimasi_pct",0) for x in ai_items)/max(len(ai_items),1) if ai_items else 0
    verdict = war_report.get("verdict","—")
    tebal   = [x for x in ai_items if x.get("kategori")=="tebal"]
    rawan   = [x for x in ai_items if x.get("kategori")=="rawan"]
    tipis   = [x for x in ai_items if x.get("kategori")=="tipis"]
    peluang = war_report.get("peluang_menang_pct","—")

    story = []

    # ── HEADER ──────────────────────────────────────────────────────────────────
    story.append(Paragraph("VENDOR WAR EXECUTIVE REPORT", sTitle))
    story.append(Paragraph(
        f"File: {filename} &nbsp;|&nbsp; Diterbitkan: {datetime.now().strftime('%d %B %Y %H:%M')} WITA"
        f" &nbsp;|&nbsp; Confidential", sSub))
    story.append(section_divider())

    # ── SECTION 1 — Executive Summary ───────────────────────────────────────────
    story.append(Paragraph("SECTION 1 — Executive Summary", sH))
    kpi_data = [
        ["Keterangan", "Nilai"],
        ["Nama File Tender",       filename],
        ["Total Penawaran Submit",  f"Rp {int(total):,}"],
        ["Jumlah Item Dianalisa",  f"{len(df_items)} item"],
        ["Margin Estimasi Rata",   f"{avg_m:.1f}%"],
        ["Peluang Menang (AI)",    f"{peluang}%"],
        ["Suspicious Score",       f"{war_report.get('suspicious_score_pct','—')}%"],
    ]
    t_kpi = Table(kpi_data, colWidths=[7*cm, 9*cm])
    t_kpi.setStyle(tbl_style())
    story.append(t_kpi)
    story.append(Spacer(1, 0.3*cm))

    verdict_style = sGO if verdict=="GO" else (sNOGO if verdict=="NO GO" else sREVISI)
    story.append(Paragraph(f"VERDICT: {verdict}", verdict_style))
    if war_report.get("alasan_verdict"):
        story.append(Paragraph(war_report["alasan_verdict"], sBody))
    story.append(section_divider())

    # ── SECTION 2 — Pricing Analysis ────────────────────────────────────────────
    story.append(Paragraph("SECTION 2 — Pricing Analysis", sH))

    if war_report.get("strategi_submit"):
        story.append(Paragraph(f"<b>Strategi Submit:</b> {war_report['strategi_submit']}", sBody))
    if war_report.get("taktik_utama"):
        story.append(Paragraph(f"<b>Taktik Utama:</b> {war_report['taktik_utama']}", sBody))
    story.append(Spacer(1, 0.2*cm))

    # Item table
    if ai_items:
        item_tbl = [["Item Pekerjaan", "Submit (Rp)", "Submit Ideal (Rp)", "Markup%", "Margin%", "Risiko", "Kategori"]]
        for x in ai_items[:20]:
            item_row = df_items[df_items["Item"].str.lower() == x.get("item","").lower()]
            sub = int(item_row["Subtotal"].values[0]) if not item_row.empty else 0
            item_tbl.append([
                str(x.get("item",""))[:38],
                f"Rp {sub:,}" if sub else "—",
                f"Rp {int(x.get('harga_submit_ideal',0)):,}" if x.get("harga_submit_ideal") else "—",
                f"{x.get('markup_aman_pct',0)}%",
                f"{x.get('margin_estimasi_pct',0)}%",
                str(x.get("risiko_kalah","—")),
                str(x.get("kategori","—")),
            ])
        t_item = Table(item_tbl, colWidths=[5.5*cm,3*cm,3*cm,1.8*cm,1.8*cm,2*cm,2*cm], repeatRows=1)
        ts = tbl_style()
        # Color rawan rows red, tebal rows green
        for i, x in enumerate(ai_items[:20], start=1):
            kat = x.get("kategori","")
            if kat == "rawan":
                ts.add("BACKGROUND", (0,i), (-1,i), colors.HexColor("#FFF0F0"))
            elif kat == "tebal":
                ts.add("BACKGROUND", (0,i), (-1,i), colors.HexColor("#F0FFF4"))
        t_item.setStyle(ts)
        story.append(t_item)
        story.append(Spacer(1, 0.2*cm))

    # Top overpriced / underpriced
    if rawan:
        story.append(Paragraph("<b>Item Rawan / Overpriced (perlu review):</b>", sBold))
        for x in rawan[:5]:
            story.append(Paragraph(
                f"• {x.get('item','')} — markup agresif {x.get('markup_agresif_pct',0)}%, "
                f"alasan: {x.get('alasan','')[:80]}",
                sBullet))
    if tebal:
        story.append(Paragraph("<b>Item Profit Tebal (keunggulan harga):</b>", sBold))
        for x in tebal[:5]:
            story.append(Paragraph(
                f"• {x.get('item','')} — margin {x.get('margin_estimasi_pct',0)}%,"
                f" markup aman {x.get('markup_aman_pct',0)}%",
                sBullet))

    story.append(section_divider())

    # ── SECTION 3 — Legal & Compliance ──────────────────────────────────────────
    story.append(Paragraph("SECTION 3 — Legal & Compliance", sH))

    if legal_score is not None:
        admin_pass = "TINGGI" if legal_score >= 90 else ("SEDANG" if legal_score >= 75 else "RENDAH")
        legal_color = "#00875A" if legal_score >= 90 else ("#E65100" if legal_score >= 75 else "#D32F2F")
        legal_tbl = [
            ["Indikator", "Status"],
            ["Legal Compliance Score", f"{legal_score}%"],
            ["Admin Pass Probability", admin_pass],
            ["Dokumen Kritis Kurang",  str(len(legal_critical))],
            ["Total Dokumen Belum Siap", str(len(legal_missing))],
        ]
        tl = Table(legal_tbl, colWidths=[8*cm, 8*cm])
        tl.setStyle(tbl_style())
        story.append(tl)
        story.append(Spacer(1, 0.2*cm))
        if legal_critical:
            story.append(Paragraph(
                f"<b>⛔ RISIKO GUGUR ADMINISTRASI</b> — dokumen kritis belum ada:",
                ps("warn","Normal",fontSize=9,fontName="Helvetica-Bold",
                   textColor=colors.HexColor("#D32F2F"),spaceAfter=4)))
            for d in legal_critical:
                story.append(Paragraph(f"• {d}", sBullet))
        if legal_missing and not legal_critical:
            story.append(Paragraph("<b>Dokumen Pelengkap Belum Siap:</b>", sBold))
            for d in legal_missing[:8]:
                story.append(Paragraph(f"• {d}", sBullet))
        if not legal_missing:
            story.append(Paragraph("✅ Semua dokumen lengkap — risiko gugur admin sangat rendah.", sBody))
    else:
        story.append(Paragraph(
            "Data legalitas tidak tersedia. Isi Tab 3 (Legal Checklist) sebelum generate PDF "
            "untuk mendapatkan analisis compliance lengkap.", sBody))

    story.append(section_divider())

    # ── SECTION 4 — AI Strategic Advice ─────────────────────────────────────────
    story.append(Paragraph("SECTION 4 — AI Strategic Advice", sH))

    story.append(Paragraph("<b>3 Langkah Meningkatkan Peluang Menang:</b>", sBold))
    steps = []
    if war_report.get("strategi_submit"):
        steps.append(war_report["strategi_submit"])
    if war_report.get("taktik_utama"):
        steps.append(war_report["taktik_utama"])
    if war_report.get("item_profit_tertinggi"):
        steps.append(f"Optimalkan item profit tertinggi: {war_report['item_profit_tertinggi']}")
    if not steps:
        steps = ["Sesuaikan markup berdasarkan kategori item (tebal/tipis/rawan)",
                 "Pastikan item rawan tidak melebihi batas wajar evaluator",
                 "Perkuat posisi di item tebal untuk buffer profit"]
    for i, s in enumerate(steps[:3], 1):
        story.append(Paragraph(f"{i}. {s}", sBullet))

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("<b>3 Risiko Utama:</b>", sBold))
    risks = []
    if rawan:
        risks.append(f"Item rawan evaluator: {', '.join(x['item'] for x in rawan[:3])}")
    if legal_critical:
        risks.append(f"Dokumen kritis belum ada: {', '.join(legal_critical[:3])}")
    if war_report.get("suspicious_score_pct") and str(war_report.get("suspicious_score_pct","0")) != "0":
        try:
            if float(str(war_report["suspicious_score_pct"])) > 30:
                risks.append(f"Suspicious score tinggi ({war_report['suspicious_score_pct']}%) — beberapa item mungkin dicurigai evaluator")
        except Exception:
            pass
    if not risks:
        risks = ["Harga terlalu rendah pada item tipis bisa merugi di pelaksanaan",
                 "Perubahan HPS oleh panitia bisa menggeser posisi penawaran",
                 "Dokumen administrasi harus 100% lengkap untuk lolos evaluasi"]
    for i, r in enumerate(risks[:3], 1):
        story.append(Paragraph(f"{i}. {r}", sBullet))

    story.append(Spacer(1, 0.2*cm))
    if war_report.get("item_profit_tertinggi"):
        story.append(Paragraph(
            f"<b>Harga Submit Optimal:</b> Fokus profit di item "
            f"{war_report['item_profit_tertinggi']}. "
            f"Jaga markup item rawan &lt;10% di atas referensi pasar.", sBody))
    story.append(Paragraph(
        "<b>Negosiasi Jika Kalah Tipis:</b> Siapkan skenario revisi dengan menurunkan "
        "item tebal 3-5% dan mempertahankan item tipis untuk menjaga floor profit.", sBody))

    story.append(section_divider())

    # ── SECTION 5 — Final Recommendation ────────────────────────────────────────
    story.append(Paragraph("SECTION 5 — Final Recommendation", sH))

    rec_map = {
        "GO":     ("SUBMIT SEKARANG", "#00875A",
                   "Profil harga kompetitif dan margin mencukupi. Pastikan seluruh dokumen "
                   "administrasi lengkap sebelum batas upload."),
        "REVISI": ("REVISI DULU",     "#E65100",
                   "Ada beberapa item yang perlu disesuaikan sebelum submit. "
                   "Review item rawan dan perkuat kelengkapan dokumen."),
        "NO GO":  ("JANGAN IKUT",     "#D32F2F",
                   "Profil harga atau kelengkapan dokumen tidak memadai untuk tender ini. "
                   "Pertimbangkan untuk skip dan fokus pada tender lain yang lebih sesuai kapasitas."),
    }
    rec_title, rec_color, rec_desc = rec_map.get(verdict, ("EVALUASI ULANG", "#555555",
                                                            war_report.get("alasan_verdict","")))

    rec_style = ps("rFinal","Normal", fontSize=14, fontName="Helvetica-Bold",
                   textColor=colors.HexColor(rec_color), spaceAfter=6)
    story.append(Paragraph(f"▶ {rec_title}", rec_style))
    story.append(Paragraph(rec_desc, sBody))

    if war_report.get("alasan_verdict"):
        story.append(Paragraph(f"<i>Alasan AI: {war_report['alasan_verdict']}</i>",
                                ps("rItalic","Normal",fontSize=8.5,textColor=colors.grey,spaceAfter=4)))

    # Summary box
    box_data = [
        ["Metrik", "Nilai", "Indikator"],
        ["Total Submit",      f"Rp {int(total):,}",    "—"],
        ["Margin Estimasi",   f"{avg_m:.1f}%",          "✅" if avg_m >= 12 else "⚠️"],
        ["Peluang Menang",    f"{peluang}%",            "✅" if str(peluang).isdigit() and int(str(peluang))>=60 else "⚠️"],
        ["Legal Score",       f"{legal_score}%" if legal_score is not None else "N/A",
                              "✅" if legal_score and legal_score>=90 else ("⚠️" if legal_score and legal_score>=75 else "❌")],
        ["Docs Kritis Kurang",str(len(legal_critical)), "✅" if not legal_critical else "❌"],
    ]
    tb = Table(box_data, colWidths=[6*cm, 5*cm, 5*cm])
    tb.setStyle(tbl_style("#2E4057"))
    story.append(Spacer(1, 0.3*cm))
    story.append(tb)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Laporan ini dihasilkan secara otomatis oleh AI Procurement Intelligence Kalsel. "
        "Gunakan sebagai referensi strategis — keputusan akhir tetap di tangan manajemen.",
        ps("footer","Normal",fontSize=7.5,textColor=colors.grey)))

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
                pdf_b = build_pdf_report(df_items, ai_items, war_report, fname,
                                     legal_score=legal_score,
                                     legal_missing=legal_missing,
                                     legal_critical=legal_critical)
                st.download_button("📑 PDF War Report", pdf_b, "war_report.pdf",
                                   "application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"PDF: {e}")
