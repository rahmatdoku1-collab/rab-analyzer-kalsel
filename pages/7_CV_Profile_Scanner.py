import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import settings

st.set_page_config(page_title="CV & Profile Scanner", page_icon="📄", layout="wide")
st.markdown("""<style>
#MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
</style>""", unsafe_allow_html=True)


def ai_scan_cv(text: str) -> dict:
    import openai
    if not settings.OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY belum diatur di .env"}
    client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Anda adalah evaluator tender Indonesia.
Analisa dokumen CV/Company Profile/legalitas yang diberikan.
Output JSON persis:
{
  "nama_perusahaan":"...", "bidang_usaha":"...",
  "skor_legalitas":0, "skor_pengalaman":0, "skor_kemampuan_teknis":0, "skor_keuangan":0,
  "skor_total":0, "peluang_lolos_tender_pct":0,
  "kekuatan":["..."], "kelemahan":["..."],
  "dokumen_lengkap":["..."], "dokumen_kurang":["..."],
  "rekomendasi":"...", "verdict":"KUAT|CUKUP|LEMAH"
}
Skor 0-100. skor_total = rata-rata 4 skor."""},
                {"role": "user", "content": f"Analisa dokumen berikut:\n\n{text[:4000]}"}
            ],
            temperature=0.3, response_format={"type": "json_object"}, max_tokens=1200,
        )
        import json
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("📄 CV & Company Profile Scanner")
st.caption("Upload dokumen perusahaan → AI scoring legalitas, pengalaman, kemampuan teknis, keuangan")
st.markdown(f"API Key: {'✅ Aktif' if settings.OPENROUTER_API_KEY else '❌ Tidak ada (set di .env)'}")
st.markdown("---")

col_up, col_info = st.columns([2, 1])
with col_up:
    st.markdown("#### Upload Dokumen")
    cv_file = st.file_uploader(
        "PDF atau TXT (Company Profile / CV Perusahaan / Dokumen Legal)",
        type=["pdf", "txt"], key="cv_standalone"
    )
with col_info:
    st.markdown("#### Dokumen yang Bisa Di-scan")
    st.markdown("""
    - Company Profile PDF
    - Profil CV / Portofolio
    - Akta + SK Kemenkumham
    - Gabungan dokumen legal
    - Laporan pengalaman kerja
    """)

if cv_file:
    if st.button("🔍 Scan & Scoring Sekarang", type="primary", use_container_width=True):
        with st.spinner("Membaca dokumen..."):
            try:
                if cv_file.name.lower().endswith(".pdf"):
                    import pdfplumber
                    with pdfplumber.open(cv_file) as pdf:
                        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                else:
                    text = cv_file.read().decode("utf-8", errors="ignore")
            except Exception as e:
                st.error(f"Gagal baca file: {e}")
                st.stop()

        if len(text.strip()) < 50:
            st.error("Teks terlalu sedikit — PDF kemungkinan scan/gambar. Coba file teks atau PDF digital.")
            st.stop()

        with st.spinner("AI menganalisa dokumen..."):
            result = ai_scan_cv(text)

        if "error" in result:
            st.error(f"AI error: {result['error']}")
            st.stop()

        # ── Hasil Scoring ─────────────────────────────────────────────────────
        verdict_cv = result.get("verdict", "—")
        skor_total = result.get("skor_total", 0)
        peluang_cv = result.get("peluang_lolos_tender_pct", 0)

        st.markdown("---")
        if verdict_cv == "KUAT":
            st.success(f"**VERDICT: {verdict_cv}** | Skor Total: {skor_total}/100 | Peluang Lolos Tender: {peluang_cv}%")
        elif verdict_cv == "CUKUP":
            st.warning(f"**VERDICT: {verdict_cv}** | Skor Total: {skor_total}/100 | Peluang Lolos Tender: {peluang_cv}%")
        else:
            st.error(f"**VERDICT: {verdict_cv}** | Skor Total: {skor_total}/100 | Peluang Lolos Tender: {peluang_cv}%")

        if result.get("nama_perusahaan"):
            st.markdown(f"**Perusahaan:** {result['nama_perusahaan']} &nbsp;|&nbsp; **Bidang:** {result.get('bidang_usaha','—')}")

        st.markdown("---")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Legalitas",        f"{result.get('skor_legalitas',0)}/100")
        s2.metric("Pengalaman",       f"{result.get('skor_pengalaman',0)}/100")
        s3.metric("Kemampuan Teknis", f"{result.get('skor_kemampuan_teknis',0)}/100")
        s4.metric("Keuangan",         f"{result.get('skor_keuangan',0)}/100")

        st.markdown("---")
        cl, cr = st.columns(2)
        with cl:
            if result.get("kekuatan"):
                st.markdown("**Kekuatan:**")
                for k in result["kekuatan"]:
                    st.success(f"✅ {k}")
            if result.get("dokumen_lengkap"):
                st.markdown("**Dokumen Terdeteksi:**")
                for d in result["dokumen_lengkap"]:
                    st.info(f"📄 {d}")
        with cr:
            if result.get("kelemahan"):
                st.markdown("**Kelemahan:**")
                for k in result["kelemahan"]:
                    st.warning(f"⚠️ {k}")
            if result.get("dokumen_kurang"):
                st.markdown("**Dokumen Kurang:**")
                for d in result["dokumen_kurang"]:
                    st.error(f"❌ {d}")

        if result.get("rekomendasi"):
            st.markdown("---")
            st.info(f"**Rekomendasi AI:** {result['rekomendasi']}")
else:
    st.info("Upload file untuk mulai scanning.")
