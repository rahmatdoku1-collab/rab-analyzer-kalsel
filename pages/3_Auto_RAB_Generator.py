import streamlit as st
import pandas as pd
import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_generator import generate_rab_from_prompt

st.set_page_config(page_title="Auto RAB Generator", page_icon="🤖", layout="wide")
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

st.title("🤖 Auto RAB Generator (AI Real)")
st.caption("Instruksi bebas → AI OpenRouter → RAB nyata. Tidak ada dummy data.")


def build_excel(df: pd.DataFrame, meta: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="RAB Detail", startrow=3)
        wb = writer.book
        ws = writer.sheets["RAB Detail"]

        bold = wb.add_format({"bold": True, "font_size": 12})
        money = wb.add_format({"num_format": "#,##0", "align": "right"})
        hdr = wb.add_format({"bold": True, "bg_color": "#1E3A5F", "font_color": "white"})

        ws.write("A1", meta.get("project_name", "RAB Project"), bold)
        ws.write("A2", f"Durasi: {meta.get('estimated_duration_days', '-')} hari")
        for col_num, col_name in enumerate(df.columns):
            ws.write(3, col_num, col_name, hdr)

        ws.set_column("A:A", 20)
        ws.set_column("B:B", 32)
        ws.set_column("C:E", 12)
        ws.set_column("F:G", 20)
        ws.set_column("H:H", 38)

        subtotal = df["Subtotal (Rp)"].sum()
        contingency = subtotal * 0.05
        ppn = (subtotal + contingency) * 0.11
        grand_total = subtotal + contingency + ppn

        last = len(df) + 5
        ws.write(last, 5, "Subtotal:", bold)
        ws.write(last, 6, subtotal, money)
        ws.write(last + 1, 5, "Contingency (5%):", bold)
        ws.write(last + 1, 6, contingency, money)
        ws.write(last + 2, 5, "PPN (11%):", bold)
        ws.write(last + 2, 6, ppn, money)
        ws.write(last + 3, 5, "GRAND TOTAL:", bold)
        ws.write(last + 3, 6, grand_total, money)

        if meta.get("risk_factors"):
            rws = wb.add_worksheet("Risiko")
            rws.write("A1", "Faktor Risiko", bold)
            for i, r in enumerate(meta["risk_factors"]):
                rws.write(i + 1, 0, r)
    return buf.getvalue()


def build_pdf(df: pd.DataFrame, meta: dict) -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import cm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"RAB: {meta.get('project_name', 'Proyek')}", styles["Title"]))
    story.append(Paragraph(
        f"Durasi: {meta.get('estimated_duration_days', '-')} hari | AI OpenRouter",
        styles["Normal"]))
    story.append(Spacer(1, 0.4*cm))

    subtotal = df["Subtotal (Rp)"].sum()
    contingency = subtotal * 0.05
    ppn = (subtotal + contingency) * 0.11
    grand_total = subtotal + contingency + ppn

    table_data = [["No", "Kategori", "Item Pekerjaan", "Vol", "Sat", "Harga Satuan", "Subtotal"]]
    for i, row in df.iterrows():
        table_data.append([
            str(i + 1),
            str(row["Kategori"])[:18],
            str(row["Item Pekerjaan"])[:42],
            str(row["Volume"]),
            str(row["Satuan"]),
            f"Rp {int(row['Harga Satuan (Rp)']):,}",
            f"Rp {int(row['Subtotal (Rp)']):,}",
        ])
    table_data.append(["", "", "", "", "", "Subtotal", f"Rp {int(subtotal):,}"])
    table_data.append(["", "", "", "", "", "Contingency (5%)", f"Rp {int(contingency):,}"])
    table_data.append(["", "", "", "", "", "PPN (11%)", f"Rp {int(ppn):,}"])
    table_data.append(["", "", "", "", "", "GRAND TOTAL", f"Rp {int(grand_total):,}"])

    col_widths = [1*cm, 3.5*cm, 9*cm, 1.5*cm, 1.5*cm, 4.5*cm, 5*cm]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -5), [colors.HexColor("#EEF3FF"), colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -4), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ALIGN", (5, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)

    if meta.get("risk_factors"):
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Faktor Risiko:", styles["Heading3"]))
        for r in meta["risk_factors"]:
            story.append(Paragraph(f"• {r}", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()


st.markdown("### Instruksi RAB")
prompt = st.text_area(
    "Ketik kebutuhan proyek:",
    placeholder=(
        "Contoh:\n"
        "- Bangun gudang baja 20x30 di Banjarmasin\n"
        "- Pengadaan bibit revegetasi 10 hektar Tabalong\n"
        "- Sewa alat berat tambang batu bara 3 bulan\n"
        "- Pembangunan mess karyawan 2 lantai 20 kamar"
    ),
    height=120
)

if st.button("🚀 Generate RAB Sekarang", type="primary", use_container_width=True):
    if not prompt.strip():
        st.warning("Masukkan instruksi RAB terlebih dahulu.")
        st.stop()

    with st.spinner("Menghubungi OpenRouter AI — harap tunggu..."):
        result = generate_rab_from_prompt(prompt)

    if "error" in result:
        st.error(f"Gagal: {result['error']}")
        st.stop()

    items = result.get("items", [])
    if not items:
        st.error("AI tidak mengembalikan item. Coba prompt lebih spesifik.")
        st.stop()

    df = pd.DataFrame([{
        "Kategori": it.get("kategori", "-"),
        "Item Pekerjaan": it.get("nama_item", "-"),
        "Volume": it.get("volume", 0),
        "Satuan": it.get("satuan", "-"),
        "Harga Satuan (Rp)": it.get("harga_satuan_estimasi", 0),
        "Subtotal (Rp)": it.get("volume", 0) * it.get("harga_satuan_estimasi", 0),
        "Keterangan": it.get("alasan", ""),
    } for it in items])

    subtotal = df["Subtotal (Rp)"].sum()
    contingency = subtotal * 0.05
    ppn = (subtotal + contingency) * 0.11
    grand_total = subtotal + contingency + ppn

    st.success(f"RAB selesai — {len(df)} item dari AI")
    st.dataframe(df, hide_index=True, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Subtotal", f"Rp {subtotal:,.0f}")
    c2.metric("Contingency + PPN", f"Rp {contingency + ppn:,.0f}")
    c3.metric("Grand Total", f"Rp {grand_total:,.0f}")

    if result.get("risk_factors"):
        with st.expander("Faktor Risiko"):
            for r in result["risk_factors"]:
                st.warning(r)

    st.markdown("---")
    st.markdown("### Export")
    d1, d2, d3 = st.columns(3)

    with d1:
        st.download_button("📄 CSV", df.to_csv(index=False).encode("utf-8"),
                           "RAB.csv", "text/csv", use_container_width=True)
    with d2:
        try:
            st.download_button("📊 Excel", build_excel(df, result), "RAB.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        except Exception as e:
            st.error(f"Excel: {e}")
    with d3:
        try:
            st.download_button("📑 PDF", build_pdf(df, result), "RAB.pdf",
                               "application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"PDF: {e}")
