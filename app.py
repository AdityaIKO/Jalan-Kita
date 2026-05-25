import streamlit as st
from PIL import Image
from datetime import datetime
import sys
import io
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from utils.gemini import analyze_image, generate_rab
from utils.storage import (
    load_reports,
    add_report,
    generate_report_id,
    format_rupiah,
    save_report_foto,
    detect_provinsi,
)

st.set_page_config(
    page_title="JalanKita — Laporkan Jalan Rusak",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

  .main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    padding: 2.5rem 2rem; border-radius: 16px; margin-bottom: 2rem;
    border: 1px solid rgba(56,189,248,0.15);
  }
  .main-header h1 { color: #f0f9ff; font-size: 2rem; font-weight: 800; margin: 0 0 0.25rem 0; }
  .main-header p { color: #7dd3fc; margin: 0; font-size: 0.95rem; }

  .result-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; }

  .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
  .badge-berat { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
  .badge-sedang { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
  .badge-ringan { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }

  .rab-total { background: linear-gradient(135deg, #0f172a, #1e3a5f); color: white; border-radius: 12px; padding: 1.25rem 1.5rem; text-align: center; margin-top: 1rem; }
  .rab-total .label { font-size: 0.8rem; color: #7dd3fc; letter-spacing: 1px; text-transform: uppercase; }
  .rab-total .amount { font-size: 1.75rem; font-weight: 800; color: #f0f9ff; }

  .breakdown-row { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9; font-size: 0.875rem; }
  .breakdown-row:last-child { border-bottom: none; }
  .breakdown-item { color: #475569; }
  .breakdown-amount { color: #0f172a; font-weight: 600; }

  div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #0369a1, #0ea5e9); color: white; border: none;
    border-radius: 10px; padding: 0.6rem 1.5rem; font-weight: 600;
    font-family: 'Plus Jakarta Sans', sans-serif; transition: all 0.2s; width: 100%;
  }
  div[data-testid="stButton"] > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(14,165,233,0.35); }

  .success-banner { background: linear-gradient(135deg, #064e3b, #065f46); border: 1px solid #34d399; border-radius: 12px; padding: 1rem 1.5rem; color: #d1fae5; font-weight: 600; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "rab_result" not in st.session_state:
    st.session_state.rab_result = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "uploaded_bytes" not in st.session_state:
    st.session_state.uploaded_bytes = None
if "report_submitted" not in st.session_state:
    st.session_state.report_submitted = False
if "liked_ids" not in st.session_state:
    st.session_state.liked_ids = set()

st.markdown("""
<div class="main-header">
  <h1>🛣️ JalanKita</h1>
  <p>Platform crowdsourcing pelaporan infrastruktur jalan berbasis AI — transparan, akuntabel, frictionless.</p>
</div>
""", unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 4])
with col_nav1:
    st.page_link("app.py", label="📋 Laporkan", use_container_width=True)
with col_nav2:
    st.page_link("pages/feed.py", label="🗺️ Feed Komunitas", use_container_width=True)

st.divider()

if st.session_state.report_submitted:
    st.markdown("""<div class="success-banner">✅ Laporan berhasil dikirim dan tersimpan! Lihat di Feed Komunitas.</div>""", unsafe_allow_html=True)
    if st.button("➕ Buat Laporan Baru"):
        st.session_state.analysis_result = None
        st.session_state.rab_result = None
        st.session_state.uploaded_image = None
        st.session_state.uploaded_bytes = None
        st.session_state.report_submitted = False
        st.rerun()
    st.stop()

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown("#### 📝 Data Laporan")
    pelapor = st.text_input("Nama Pelapor", placeholder="Masukkan nama Anda")
    lokasi = st.text_input("Lokasi Jalan", placeholder="Contoh: Jl. Kaliurang KM 12, Sleman, DIY")

    st.markdown("#### 📸 Foto Kerusakan")
    uploaded_file = st.file_uploader(
        "Upload foto jalan rusak",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload foto langsung dari kamera untuk hasil terbaik",
    )

    if uploaded_file:
        file_bytes = uploaded_file.read()
        image = Image.open(io.BytesIO(file_bytes))
        # Buat thumbnail kecil untuk preview (max 800px)
        thumb = image.copy()
        thumb.thumbnail((800, 800))
        st.session_state.uploaded_image = image
        st.session_state.uploaded_bytes = file_bytes
        st.image(thumb, caption=f"Preview foto ({uploaded_file.size // 1024} KB)", use_container_width=True)

    btn_analyze = st.button(
        "🔍 Analisis dengan AI",
        disabled=not (uploaded_file and lokasi and pelapor),
        use_container_width=True,
    )
    if not pelapor or not lokasi or not uploaded_file:
        st.caption("⚠️ Lengkapi nama, lokasi, dan upload foto untuk melanjutkan.")

with col_right:
    st.markdown("#### 🤖 Hasil Analisis AI")

    if btn_analyze and uploaded_file and lokasi and pelapor:
        with st.spinner("🔍 Computer Vision sedang menganalisis kerusakan..."):
            result_cv = analyze_image(st.session_state.uploaded_image)
        if result_cv["success"]:
            st.session_state.analysis_result = result_cv["data"]
            with st.spinner("📊 LLM sedang menghitung estimasi RAB..."):
                result_rab = generate_rab(result_cv["data"], lokasi)
            if result_rab["success"]:
                st.session_state.rab_result = result_rab["data"]
            else:
                st.error(f"Gagal generate RAB: {result_rab['error']}")
        else:
            st.error(f"Gagal analisis gambar: {result_cv['error']}")

    if st.session_state.analysis_result:
        det = st.session_state.analysis_result
        sev = det.get("tingkat_keparahan", "")
        badge_class = {"Berat": "badge-berat", "Sedang": "badge-sedang", "Ringan": "badge-ringan"}.get(sev, "badge-sedang")

        st.markdown(f"""
        <div class="result-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <strong>Hasil Deteksi CV</strong>
            <span class="badge {badge_class}">{sev}</span>
          </div>
          <table style="width:100%; font-size:0.875rem; border-collapse:collapse;">
            <tr><td style="color:#64748b; padding:0.3rem 0; width:40%">Tipe Kerusakan</td>
                <td style="font-weight:600; color:#0f172a">{det.get('tipe_kerusakan','–')}</td></tr>
            <tr><td style="color:#64748b; padding:0.3rem 0">Estimasi Dimensi</td>
                <td style="font-weight:600; color:#0f172a">{det.get('estimasi_dimensi','–')}</td></tr>
            <tr><td style="color:#64748b; padding:0.3rem 0">Confidence AI</td>
                <td style="font-weight:600; color:#0f172a">{det.get('confidence','–')}</td></tr>
          </table>
          <div style="margin-top:0.75rem; padding:0.75rem; background:#f1f5f9; border-radius:8px; font-size:0.825rem; color:#475569; line-height:1.5;">
            💬 {det.get('catatan','–')}
          </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.rab_result:
        rab = st.session_state.rab_result
        st.markdown("#### 💰 Estimasi RAB")

        breakdown = rab.get("breakdown", [])
        if breakdown:
            rows_html = ""
            for item in breakdown:
                rows_html += f"""
                <div class="breakdown-row">
                  <span class="breakdown-item">{item.get('item','–')} <span style="color:#94a3b8">({item.get('volume','–')})</span></span>
                  <span class="breakdown-amount">{format_rupiah(item.get('subtotal', 0))}</span>
                </div>"""
            st.markdown(f"""
            <div class="result-card">
              <strong style="font-size:0.875rem; color:#64748b; text-transform:uppercase; letter-spacing:0.5px;">Rincian Biaya</strong>
              <div style="margin-top:0.75rem">{rows_html}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="rab-total">
          <div class="label">Total Estimasi RAB</div>
          <div class="amount">{format_rupiah(rab.get('total', 0))}</div>
          <div style="font-size:0.75rem; color:#7dd3fc; margin-top:0.25rem;">
            Material {format_rupiah(rab.get('material',0))} · Tenaga {format_rupiah(rab.get('tenaga_kerja',0))} · Alat {format_rupiah(rab.get('peralatan',0))}
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📤 Kirim Laporan ke Feed Komunitas", use_container_width=True):
            reports = load_reports()
            new_id = generate_report_id(reports)

            # Simpan foto sebagai file fisik
            foto_path = None
            if st.session_state.uploaded_bytes:
                foto_path = save_report_foto(st.session_state.uploaded_bytes, new_id)

            new_report = {
                "id": new_id,
                "pelapor": pelapor,
                "lokasi": lokasi,
                "provinsi": detect_provinsi(lokasi),
                "timestamp": datetime.now().isoformat(),
                "foto_path": foto_path,
                "deteksi": st.session_state.analysis_result,
                "rab": st.session_state.rab_result,
                "status": "Menunggu",
                "likes": 0,
                "sla_hari": 7,
                "hari_berjalan": 0,
                "assigned_to": "",
                "assigned_by": "",
                "assignment_notes": "",
                "progress_updates": [],
            }
            add_report(new_report)
            st.session_state.report_submitted = True
            st.rerun()

    elif not st.session_state.analysis_result:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem; color:#94a3b8;">
          <div style="font-size:3rem; margin-bottom:1rem;">🔍</div>
          <div style="font-size:0.9rem;">Hasil analisis AI akan muncul di sini<br>setelah foto diproses</div>
        </div>
        """, unsafe_allow_html=True)