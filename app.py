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
    severity_sla_days,
    priority_score,
    priority_label,
)
from utils.geo import parse_latlon
from utils.ui import inject_css, render_header, PRIO_COLORS, avatar_html, eco_card_html
from utils import auth, sustainability
from utils.security import esc, validate_image_upload

st.set_page_config(
    page_title="JalanKita · Laporkan Jalan Rusak",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
user = auth.require_auth()

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
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
if "liked_ids" not in st.session_state:
    st.session_state.liked_ids = set()

render_header(
    "Platform Pelaporan Jalan · Berbasis AI",
    "🛣️ JalanKita",
    "Warga memotret jalan rusak, AI mendeteksi kerusakan dan menghitung anggaran perbaikan, lalu laporan masuk ke ruang publik yang transparan dan akuntabel.",
)
auth.render_topbar("report")

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
    pelapor = user["nama"]
    av = avatar_html(pelapor, user.get("avatar_color", "#B5701A"), 30)
    st.markdown(
        f'<div class="reporter-chip" style="margin:0 0 0.6rem;">{av}'
        f'Melaporkan sebagai <b style="color:var(--ink);margin-left:0.2rem;">{esc(pelapor)}</b></div>',
        unsafe_allow_html=True,
    )
    lokasi = st.text_input("Lokasi Jalan", placeholder="Contoh: Jl. Kaliurang KM 12, Sleman, DIY")
    koordinat = st.text_input(
        "Koordinat GPS (opsional)",
        placeholder="Contoh: -7.7560, 110.4090 (salin dari Google Maps)",
        help="Tempel koordinat agar laporan muncul tepat di peta. Kosongkan untuk perkiraan otomatis dari provinsi.",
    )
    if lokasi:
        prov_preview = detect_provinsi(lokasi)
        if koordinat and not parse_latlon(koordinat):
            st.caption("⚠️ Format koordinat tidak valid. Gunakan format: lat, lon")
        else:
            st.caption(f"🗺️ Terdeteksi wilayah: **{prov_preview}**")

    st.markdown("#### 📸 Foto Kerusakan")
    uploaded_file = st.file_uploader(
        "Upload foto jalan rusak",
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload foto langsung dari kamera untuk hasil terbaik",
    )

    upload_ok = False
    if uploaded_file:
        file_bytes = uploaded_file.read()
        ok, msg = validate_image_upload(file_bytes, uploaded_file.name)
        if not ok:
            st.error(f"⚠️ {msg}")
            st.session_state.uploaded_image = None
            st.session_state.uploaded_bytes = None
        else:
            upload_ok = True
            image = Image.open(io.BytesIO(file_bytes))
            # Buat thumbnail kecil untuk preview (max 800px)
            thumb = image.copy()
            thumb.thumbnail((800, 800))
            st.session_state.uploaded_image = image
            st.session_state.uploaded_bytes = file_bytes
            st.image(thumb, caption=f"Preview foto ({uploaded_file.size // 1024} KB)", use_container_width=True)

    btn_analyze = st.button(
        "🔍 Analisis dengan AI",
        disabled=not (upload_ok and lokasi),
        use_container_width=True,
    )
    if not lokasi or not upload_ok:
        st.caption("⚠️ Lengkapi lokasi dan unggah foto yang valid untuk melanjutkan.")

with col_right:
    st.markdown("#### 🤖 Hasil Analisis AI")

    if btn_analyze and uploaded_file and lokasi and pelapor:
        with st.spinner("🔍 Computer Vision sedang menganalisis kerusakan..."):
            result_cv = analyze_image(st.session_state.uploaded_image)
        if result_cv["success"]:
            st.session_state.analysis_result = result_cv["data"]
            st.session_state.demo_mode = result_cv.get("demo", False)
            if result_cv.get("warning"):
                st.warning(result_cv["warning"])
            with st.spinner("📊 LLM sedang menghitung estimasi RAB..."):
                result_rab = generate_rab(result_cv["data"], lokasi)
            if result_rab["success"]:
                st.session_state.rab_result = result_rab["data"]
                if result_rab.get("warning"):
                    st.warning(result_rab["warning"])
            else:
                st.error(f"Gagal generate RAB: {result_rab['error']}")
        else:
            st.error(f"Gagal analisis gambar: {result_cv['error']}")

    if st.session_state.get("demo_mode") and st.session_state.analysis_result:
        st.markdown(
            '<span class="demo-pill">⚙️ Mode Demo · estimasi heuristik tanpa API key</span>',
            unsafe_allow_html=True,
        )

    if st.session_state.analysis_result:
        det = st.session_state.analysis_result
        sev = det.get("tingkat_keparahan", "")
        badge_class = {"Berat": "badge-berat", "Sedang": "badge-sedang", "Ringan": "badge-ringan"}.get(sev, "badge-sedang")

        st.markdown(f"""
        <div class="result-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.9rem;">
            <span class="eyebrow-sm">Hasil Deteksi Computer Vision</span>
            <span class="badge {badge_class}">{sev}</span>
          </div>
          <table style="width:100%; font-size:0.9rem; border-collapse:collapse;">
            <tr><td style="color:var(--ink-soft); padding:0.35rem 0; width:42%">Tipe Kerusakan</td>
                <td style="font-weight:700; color:var(--ink)">{esc(det.get('tipe_kerusakan','–'))}</td></tr>
            <tr><td style="color:var(--ink-soft); padding:0.35rem 0">Estimasi Dimensi</td>
                <td style="font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums">{esc(det.get('estimasi_dimensi','–'))}</td></tr>
            <tr><td style="color:var(--ink-soft); padding:0.35rem 0">Confidence AI</td>
                <td style="font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums">{esc(det.get('confidence','–'))}</td></tr>
          </table>
          <div class="note" style="margin-top:0.8rem; padding:0.75rem 0.9rem; background:var(--surface-2); border:1px solid var(--line); border-radius:10px;">
            💬 {esc(det.get('catatan','–'))}
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
                  <span class="breakdown-item">{esc(item.get('item','–'))} <span style="color:var(--ink-faint)">({esc(item.get('volume','–'))})</span></span>
                  <span class="breakdown-amount">{format_rupiah(item.get('subtotal', 0))}</span>
                </div>"""
            st.markdown(f"""
            <div class="result-card">
              <span class="eyebrow-sm">Rincian Biaya</span>
              <div style="margin-top:0.6rem">{rows_html}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="rab-total">
          <div class="label">Total Estimasi RAB</div>
          <div class="amount">{format_rupiah(rab.get('total', 0))}</div>
          <div class="sub">
            Material {format_rupiah(rab.get('material',0))} · Tenaga {format_rupiah(rab.get('tenaga_kerja',0))} · Alat {format_rupiah(rab.get('peralatan',0))}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Auto priority preview based on severity + SLA target.
        sev = st.session_state.analysis_result.get("tingkat_keparahan", "Sedang")
        sla_target = severity_sla_days(sev)
        preview_score = priority_score({
            "deteksi": st.session_state.analysis_result,
            "status": "Menunggu",
            "timestamp": datetime.now().isoformat(),
            "likes": 0,
            "sla_hari": sla_target,
        })
        prio = priority_label(preview_score)
        pcolor = PRIO_COLORS.get(prio, "#64748b")
        st.markdown(
            f"""<div style="margin-top:0.75rem; display:flex; gap:0.75rem; align-items:center; flex-wrap:wrap;">
              <span class="prio-pill" style="background:{pcolor}1a; color:{pcolor}; border:1px solid {pcolor}55; margin-left:0;">
                🚦 Prioritas: {prio} ({preview_score})
              </span>
              <span style="font-size:0.8rem; color:#64748b;">Target SLA: <b>{sla_target} hari</b> (otomatis dari tingkat keparahan)</span>
            </div>""",
            unsafe_allow_html=True,
        )

        # ── Sustainability preview: environmental cost + eco-material ──────────
        preview_report = {
            "deteksi": st.session_state.analysis_result,
            "status": "Menunggu",
            "timestamp": datetime.now().isoformat(),
        }
        impact_preview = sustainability.estimate_impact(preview_report)
        eco_preview = sustainability.recommend_material(
            st.session_state.analysis_result.get("tipe_kerusakan", "")
        )
        st.markdown("#### 🌱 Dampak Keberlanjutan")
        ic1, ic2 = st.columns(2)
        ic1.metric("CO₂ terbuang / hari jika dibiarkan", f'{impact_preview["co2_day_kg"]:,} kg'.replace(",", "."))
        ic2.metric("Setara serapan pohon / tahun", f'{impact_preview["trees_equivalent"]:,} pohon'.replace(",", "."))
        st.markdown(eco_card_html(eco_preview), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("📤 Kirim Laporan ke Feed Komunitas", use_container_width=True):
            reports = load_reports()
            new_id = generate_report_id(reports)

            # Simpan foto sebagai file fisik (dikompres otomatis)
            foto_path = None
            if st.session_state.uploaded_bytes:
                foto_path = save_report_foto(st.session_state.uploaded_bytes, new_id)

            coords = parse_latlon(koordinat)
            new_report = {
                "id": new_id,
                "pelapor": pelapor,
                "pelapor_username": user["username"],
                "lokasi": lokasi,
                "provinsi": detect_provinsi(lokasi),
                "timestamp": datetime.now().isoformat(),
                "foto_path": foto_path,
                "lat": coords[0] if coords else None,
                "lon": coords[1] if coords else None,
                "deteksi": st.session_state.analysis_result,
                "rab": st.session_state.rab_result,
                "status": "Menunggu",
                "likes": 0,
                "sla_hari": sla_target,
                "hari_berjalan": 0,
                "kategori": st.session_state.analysis_result.get("tipe_kerusakan", ""),
                "demo_mode": st.session_state.get("demo_mode", False),
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
        <div style="text-align:center; padding:3.5rem 1rem; border:1px dashed var(--line-strong); border-radius:14px; background:var(--surface);">
          <div style="font-size:2.4rem; margin-bottom:0.8rem; opacity:0.55;">🔍</div>
          <div style="font-size:0.9rem; color:var(--ink-soft); line-height:1.5;">Hasil analisis AI muncul di sini<br>setelah foto diproses.</div>
        </div>
        """, unsafe_allow_html=True)