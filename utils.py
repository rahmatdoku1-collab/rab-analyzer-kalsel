import logging
import os
import openai
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.piecharts import Pie

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_ai_summary(df_results, api_key):
    """Generate Executive Summary using OpenRouter API"""
    if not api_key:
        logger.warning("API Key OpenRouter tidak ditemukan saat generate AI summary.")
        return "⚠️ API Key OpenRouter belum dimasukkan. Masukkan di sidebar untuk mengaktifkan AI Executive Summary."
        
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    total_anggaran = df_results['Total Harga (Rp)'].sum()
    total_hemat = df_results['Potensi Penghematan (Rp)'].sum()
    overpriced_items = df_results[df_results['Status'] == 'MAHAL (OVERPRICED)']
    
    top_overpriced = overpriced_items.nlargest(3, 'Potensi Penghematan (Rp)')[['Item Pekerjaan', 'Potensi Penghematan (Rp)']]
    top_overpriced_str = top_overpriced.to_string(index=False) if len(overpriced_items) > 0 else "Tidak ada item overpriced yang dominan."
    
    prompt = f"""
    Anda adalah auditor finansial proyek senior, spesialis procurement, dan analis risiko. 
    Buatkan Ringkasan Eksekutif & Analisis Risiko (maksimal 4 paragraf padat) untuk hasil audit kewajaran Rencana Anggaran Biaya (RAB) berikut:
    
    - Total Anggaran Diajukan: Rp {total_anggaran:,.0f}
    - Total Potensi Penghematan: Rp {total_hemat:,.0f}
    - Jumlah Item Overpriced: {len(overpriced_items)}
    
    Top Item Overpriced (berpotensi Front-loading atau Markup tinggi):
    {top_overpriced_str}
    
    Instruksi:
    1. Berikan analisa objektif tentang efisiensi anggaran ini.
    2. Lakukan Analisis Risiko Procurement: Deteksi indikasi "Front-loading" (markup pada item pekerjaan awal) atau "Predatory Pricing" jika ada indikasi harga tidak wajar.
    3. Berikan rekomendasi langkah negosiasi/taktis konkrit untuk memitigasi risiko kerugian perusahaan.
    4. Gunakan bahasa Indonesia bisnis enterprise yang modern dan profesional.
    """
    
    try:
        logger.info("Menghubungi OpenRouter API untuk generate summary...")
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("Berhasil generate summary dari AI.")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Gagal menghubungi server AI OpenRouter: {str(e)}")
        return f"Gagal menghubungi server AI OpenRouter: {str(e)}"

def generate_pdf_report(df_results, filename, ai_summary_text="", api_key="", company_id="ENTERPRISE_TENANT_01"):
    """Membuat laporan PDF Enterprise Premium yang Tajam dan Detail (Sekarang dengan Visualisasi)"""
    try:
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        filepath = os.path.join('reports', filename)
        
        # Fungsi pembantu untuk membuat Header / Watermark di setiap halaman
        def add_header_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 10)
            canvas.setFillColor(colors.HexColor("#94A3B8"))
            canvas.drawString(40, A4[1] - 25, f"CONFIDENTIAL - {company_id}")
            canvas.drawString(A4[0] - 150, A4[1] - 25, "SaaS B2B Edition")
            canvas.line(40, A4[1] - 30, A4[0] - 40, A4[1] - 30)
            canvas.restoreState()

        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40)
        elements = []
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'EnterpriseTitle', 
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor("#0F172A"),
            alignment=1,
            spaceAfter=10,
            fontName="Helvetica-Bold"
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor("#64748B"),
            alignment=1,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#1E3A8A"),
            spaceBefore=15,
            spaceAfter=10,
            fontName="Helvetica-Bold",
            borderPadding=5,
            backColor=colors.HexColor("#F1F5F9")
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.leading = 14
        
        elements.append(Paragraph("EXECUTIVE AUDIT REPORT", title_style))
        elements.append(Paragraph("AI Procurement Intelligence Kalsel", subtitle_style))
        elements.append(Spacer(1, 10))
        
        # --- 1. METRIK FINANSIAL & RINGKASAN ---
        total_anggaran = df_results['Total Harga (Rp)'].sum()
        potensi_hemat = df_results['Potensi Penghematan (Rp)'].sum()
        efisiensi_pct = (potensi_hemat / total_anggaran) * 100 if total_anggaran > 0 else 0
        
        overpriced = df_results[df_results['Status'] == 'MAHAL (OVERPRICED)']
        
        elements.append(Paragraph("1. METRIK FINANSIAL UTAMA", heading_style))
        metrics_text = f"""
        <b>Total Nilai Proyek (Diajukan):</b> Rp {total_anggaran:,.0f}<br/>
        <b>Total Potensi Pemborosan (Markup):</b> <font color="red">Rp {potensi_hemat:,.0f} ({efisiensi_pct:.1f}%)</font><br/>
        <b>Jumlah Item Pekerjaan Diperiksa:</b> {len(df_results)} item<br/>
        <b>Item Terdeteksi Overpriced:</b> {len(overpriced)} item
        """
        elements.append(Paragraph(metrics_text, normal_style))
        
        # --- GRAFIK PIE DINAMIS ---
        d = Drawing(400, 160)
        pc = Pie()
        pc.x = 150
        pc.y = 10
        pc.width = 120
        pc.height = 120
        anggaran_wajar = total_anggaran - potensi_hemat
        if anggaran_wajar < 0: anggaran_wajar = 0
        
        pc.data = [anggaran_wajar, potensi_hemat]
        pc.labels = ['Anggaran Wajar', 'Potensi Hemat']
        
        pc.slices[0].fillColor = colors.HexColor('#10B981') # Hijau
        pc.slices[1].fillColor = colors.HexColor('#EF4444') # Merah
        d.add(pc)
        elements.append(d)
        
        elements.append(Spacer(1, 10))
        
        # --- 2. ANALISIS TAJAM SISTEM PAKAR (Rule-based) ---
        elements.append(Paragraph("2. TEMUAN KRITIS & ANALISIS RISIKO", heading_style))
        temuan = []
        if efisiensi_pct > 20:
            temuan.append("⚠️ <b>RISIKO FATAL:</b> Indikasi markup sistematis sangat kuat (>20%). Proyek ini memerlukan re-evaluasi total atau lelang ulang.")
        elif efisiensi_pct > 5:
            temuan.append("⚠️ <b>RISIKO SEDANG:</b> Ditemukan beberapa item dengan harga di atas kewajaran pasar regional Kalsel. Negosiasi wajib dilakukan.")
        else:
            temuan.append("✅ <b>WAJAR:</b> Harga secara mayoritas berada di batas kewajaran, namun tetap cek detail untuk efisiensi mikro.")
            
        if len(overpriced) > 0:
            top_markup = overpriced.iloc[0]
            markup_pct = (top_markup['Harga Satuan (Rp)'] - top_markup['Harga Rekomendasi (Rp)']) / top_markup['Harga Rekomendasi (Rp)'] * 100 if top_markup['Harga Rekomendasi (Rp)'] > 0 else 0
            temuan.append(f"🔍 <b>ANOMALI TERTINGGI:</b> Item '{top_markup['Item Pekerjaan'][:40]}' memiliki markup fantastis sebesar <b>{markup_pct:,.0f}%</b> dari standar!")
            
        for t in temuan:
            elements.append(Paragraph(t, normal_style))
            elements.append(Spacer(1, 5))
            
        elements.append(Spacer(1, 15))
        
        # --- 3. AI EXECUTIVE SUMMARY ---
        if not ai_summary_text and api_key:
            ai_summary_text = generate_ai_summary(df_results, api_key)
            
        if ai_summary_text and not ai_summary_text.startswith('⚠️'):
            elements.append(Paragraph("3. OPINI AUDITOR AI (Kecerdasan Buatan)", heading_style))
            for p in ai_summary_text.split('\n\n'):
                elements.append(Paragraph(p, normal_style))
                elements.append(Spacer(1, 8))
            elements.append(Spacer(1, 15))
        
        # --- 4. TABEL PRIORITAS NEGOSIASI ---
        if not overpriced.empty:
            elements.append(Paragraph("4. PRIORITAS NEGOSIASI (TARGET PEMOTONGAN HARGA)", heading_style))
            elements.append(Paragraph("Fokuskan negosiasi pada item-item berikut untuk mengamankan anggaran perusahaan secara maksimal:", normal_style))
            elements.append(Spacer(1, 10))
            
            top_overpriced = overpriced.nlargest(15, 'Potensi Penghematan (Rp)')
            table_data = [['Item Pekerjaan', 'Harga Diajukan', 'Harga Standar AI', 'Potensi Hemat']]
            
            for _, row in top_overpriced.iterrows():
                item_name = str(row['Item Pekerjaan'])[:35] + "..." if len(str(row['Item Pekerjaan'])) > 35 else str(row['Item Pekerjaan'])
                table_data.append([
                    Paragraph(item_name, styles['Normal']),
                    f"Rp {row['Harga Satuan (Rp)']:,.0f}",
                    f"Rp {row['Harga Rekomendasi (Rp)']:,.0f}",
                    f"Rp {row['Potensi Penghematan (Rp)']:,.0f}"
                ])
                
            t = Table(table_data, colWidths=[200, 90, 90, 100])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('TOPPADDING', (0,0), (-1,0), 10),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(t)
        
        # Footer Note
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("<i>Dokumen ini di-generate secara otomatis oleh AI Procurement Intelligence Kalsel (SaaS Version).</i>", styles['Italic']))
        
        doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        logger.info(f"Berhasil membuat laporan PDF Enterprise: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Gagal membuat laporan PDF: {e}")
        raise

def generate_tender_pdf_report(winner, res_df, project_budget, target_nego, company_id="ENTERPRISE_TENANT_01"):
    """Membuat Surat Rekomendasi Pemenang Tender (Tender Intelligence)"""
    try:
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        filename = f"Tender_Recommendation_{winner['Vendor']}.pdf"
        filepath = os.path.join('reports', filename)
        
        def add_header_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 10)
            canvas.setFillColor(colors.HexColor("#94A3B8"))
            canvas.drawString(40, A4[1] - 25, f"CONFIDENTIAL TENDER REPORT - {company_id}")
            canvas.drawString(A4[0] - 150, A4[1] - 25, "AI Intelligence Engine")
            canvas.line(40, A4[1] - 30, A4[0] - 40, A4[1] - 30)
            canvas.restoreState()

        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40)
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'EnterpriseTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor("#0F172A"), alignment=1, spaceAfter=10, fontName="Helvetica-Bold"
        )
        heading_style = ParagraphStyle(
            'SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#1E3A8A"), spaceBefore=15, spaceAfter=10, fontName="Helvetica-Bold", borderPadding=5, backColor=colors.HexColor("#F1F5F9")
        )
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.leading = 14
        
        elements.append(Paragraph("TENDER INTELLIGENCE & VENDOR RECOMMENDATION", title_style))
        elements.append(Spacer(1, 10))
        
        # --- 1. REKOMENDASI PEMENANG ---
        elements.append(Paragraph("1. KEPUTUSAN & REKOMENDASI AI", heading_style))
        
        keputusan_text = f"""
        Berdasarkan analisis algoritma <b>Weighted Ranking (Harga 60% : Keandalan 40%)</b> terhadap {len(res_df)} penawaran vendor, 
        sistem merekomendasikan: <br/><br/>
        <b>Pemenang Tender:</b> {winner['Vendor']} <br/>
        <b>Skor Akhir (Out of 100):</b> {winner['Final Score']:.1f} <br/>
        <b>Total Penawaran:</b> Rp {winner['Total Penawaran']:,.0f} <br/>
        <b>Keandalan Historis:</b> {winner['Keandalan (%)']}% <br/>
        """
        elements.append(Paragraph(keputusan_text, normal_style))
        
        # --- 2. STRATEGI NEGOSIASI ---
        elements.append(Paragraph("2. STRATEGI & TARGET NEGOSIASI", heading_style))
        nego_text = f"""
        Walaupun {winner['Vendor']} merupakan penawaran terbaik secara <i>Value for Money</i>, sistem menyarankan tim pengadaan 
        untuk melakukan negosiasi lanjutan dengan target <i>Deal Price</i> di angka: <br/><br/>
        <b>🎯 Rp {target_nego:,.0f}</b> <br/><br/>
        <i>Dasar Pengambilan Keputusan (AI Insight): Target negosiasi ini diambil menggunakan nilai tengah (Median) dari seluruh penawaran vendor yang wajar di pasar. Sistem menghindari penggunaan rerata (Average) untuk mencegah distorsi harga dari vendor yang melakukan Predatory Pricing (banting harga ekstrim).</i>
        """
        elements.append(Paragraph(nego_text, normal_style))
        
        # --- 3. KOMPARASI VENDOR ---
        elements.append(Paragraph("3. TABEL KOMPARASI SELURUH VENDOR", heading_style))
        elements.append(Spacer(1, 10))
        
        table_data = [['Peringkat', 'Nama Vendor', 'Skor Akhir', 'Penawaran (Rp)', 'Status Risiko']]
        for idx, row in res_df.iterrows():
            table_data.append([
                str(idx + 1),
                row['Vendor'],
                f"{row['Final Score']:.1f}",
                f"Rp {row['Total Penawaran']:,.0f}",
                row['Status Risiko']
            ])
            
        t = Table(table_data, colWidths=[60, 150, 70, 100, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,0), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('TOPPADDING', (0,0), (-1,0), 10),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(t)
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("<i>Dokumen ini di-generate secara otomatis oleh sistem AI Procurement Intelligence - Tender Module.</i>", styles['Italic']))
        
        doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        return filepath
    except Exception as e:
        logger.error(f"Gagal membuat Tender PDF: {e}")
        raise
