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
from utils.geo import parse_latlon, in_indonesia
from utils.ui import inject_css, render_header, PRIO_COLORS, avatar_html, eco_card_html
from utils import auth, sustainability, integrity, privacy, wilayah
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
for _k in ("exif_info", "foto_phash", "similar_reports", "exif_gps"):
    if _k not in st.session_state:
        st.session_state[_k] = None
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

    # ── Foto lebih dulu, agar koordinat GPS bisa dibaca dari metadata foto ─────
    st.markdown("#### 📸 Foto Kerusakan")
    uploaded_file = st.file_uploader(
        "Upload foto jalan rusak",
        type=["jpg", "jpeg", "png", "webp"],
        help="Foto langsung dari kamera ponsel memberi hasil terbaik dan sering menyimpan lokasi GPS.",
    )

    upload_ok = False
    if uploaded_file:
        file_bytes = uploaded_file.read()
        ok, msg = validate_image_upload(file_bytes, uploaded_file.name)
        if not ok:
            st.error(f"⚠️ {msg}")
            st.session_state.uploaded_image = None
            st.session_state.uploaded_bytes = None
            st.session_state.exif_gps = None
        else:
            upload_ok = True
            image = Image.open(io.BytesIO(file_bytes))
            thumb = image.copy()
            thumb.thumbnail((800, 800))
            st.session_state.uploaded_image = image
            st.session_state.uploaded_bytes = file_bytes
            st.image(thumb, caption=f"Preview foto ({uploaded_file.size // 1024} KB)", use_container_width=True)
            # Auto GPS tagging from the photo's embedded location (Indonesia only).
            gps = integrity.gps_from_exif(image)
            if gps and not in_indonesia(*gps):
                st.caption("📍 Lokasi GPS pada foto berada di luar wilayah Indonesia dan diabaikan.")
                gps = None
            st.session_state.exif_gps = gps
            if gps:
                st.success(f"📍 Lokasi GPS terbaca otomatis dari foto: {gps[0]}, {gps[1]}")

    blur_privacy = st.checkbox(
        "🔒 Sensor privasi otomatis (blur wajah & pelat nomor)",
        value=True,
        help="AI mendeteksi wajah dan pelat nomor, lalu memburamkannya sebelum foto tampil publik.",
    )

    # ── Lokasi berjenjang: Provinsi → Kabupaten/Kota → Kecamatan → Kelurahan ──
    st.markdown("#### 📍 Lokasi")
    prov_name = kab_name = kec_name = kel_name = ""
    prov_code = kab_code = kec_code = kel_code = None

    if wilayah.available():
        provs = wilayah.provinces()
        prov_sel = st.selectbox("Provinsi", ["Pilih Provinsi"] + [n for _, n in provs])
        prov_code = next((c for c, n in provs if n == prov_sel), None)
        prov_name = prov_sel if prov_code else ""

        if prov_code:
            kabs = wilayah.regencies(prov_code)
            kab_sel = st.selectbox("Kabupaten/Kota", ["Pilih Kabupaten/Kota"] + [n for _, n in kabs])
            kab_code = next((c for c, n in kabs if n == kab_sel), None)
            kab_name = kab_sel if kab_code else ""

            if kab_code:
                kecs = wilayah.districts(kab_code)
                kec_sel = st.selectbox("Kecamatan (opsional)", ["Pilih Kecamatan"] + [n for _, n in kecs])
                kec_code = next((c for c, n in kecs if n == kec_sel), None)
                kec_name = kec_sel if kec_code else ""

                if kec_code:
                    kels = wilayah.villages(kec_code)
                    kel_sel = st.selectbox("Kelurahan/Desa (opsional)", ["Pilih Kelurahan/Desa"] + [n for _, n in kels])
                    kel_code = next((c for c, n in kels if n == kel_sel), None)
                    kel_name = kel_sel if kel_code else ""

        jalan = st.text_input("Nama jalan / patokan", placeholder="Contoh: Jl. Kaliurang KM 12")
        loc_ok = bool(jalan.strip() and prov_name and kab_name)
    else:
        jalan = st.text_input("Lokasi Jalan", placeholder="Contoh: Jl. Kaliurang KM 12, Sleman, DIY")
        loc_ok = bool(jalan.strip())

    # Compose a human-readable location string, most specific first.
    lokasi = ", ".join([p for p in [jalan.strip(), kel_name, kec_name, kab_name, prov_name] if p])

    koordinat = st.text_input(
        "Koordinat GPS (opsional)",
        placeholder="Terisi otomatis dari foto, atau salin dari Google Maps: -7.7560, 110.4090",
        help="Dibaca otomatis dari metadata foto bila tersedia. Isi manual untuk menimpa.",
    )
    manual_coord = parse_latlon(koordinat)
    if koordinat and not manual_coord:
        st.caption("⚠️ Format koordinat tidak valid. Gunakan format: lat, lon")
    elif manual_coord and not in_indonesia(*manual_coord):
        st.caption("⚠️ Koordinat berada di luar wilayah Indonesia dan tidak akan dipakai.")
        manual_coord = None

    btn_analyze = st.button(
        "🔍 Analisis dengan AI",
        disabled=not (upload_ok and loc_ok),
        use_container_width=True,
    )
    if not loc_ok or not upload_ok:
        st.caption("⚠️ Lengkapi foto, Provinsi, Kabupaten/Kota, dan nama jalan untuk melanjutkan.")

with col_right:
    st.markdown("#### 🤖 Hasil Analisis AI")

    if btn_analyze and uploaded_file and lokasi and pelapor:
        source_image = st.session_state.uploaded_image

        # ── Authenticity signals read from the ORIGINAL photo's metadata ──────
        st.session_state.exif_info = integrity.exif_signals(source_image)

        # ── Privacy: detect & blur faces / plates before anything is stored ───
        if blur_privacy:
            with st.spinner("🔒 Menyensor wajah & pelat nomor..."):
                red = privacy.redact(source_image)
            source_image = red["image"]
            # The redacted image becomes what we analyse and store.
            buf = io.BytesIO()
            source_image.save(buf, format="JPEG", quality=88)
            st.session_state.uploaded_bytes = buf.getvalue()
            st.session_state.uploaded_image = source_image
            if red["available"] and red["blurred_count"]:
                st.info(f"🔒 {red['blurred_count']} area sensitif (wajah/pelat) telah disensor otomatis.")
            elif not red["available"]:
                st.caption("🔒 Sensor otomatis butuh API key; foto asli tetap dipakai untuk demo ini.")

        # ── Perceptual fingerprint + duplicate check ──────────────────────────
        st.session_state.foto_phash = integrity.dhash(source_image)
        coords_now = manual_coord or st.session_state.get("exif_gps")
        similar = integrity.find_similar(st.session_state.foto_phash, coords_now, load_reports())
        st.session_state.similar_reports = similar

        with st.spinner("🔍 Computer Vision sedang menganalisis kerusakan..."):
            result_cv = analyze_image(source_image)
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

    # ── Duplicate warning (soft) ──────────────────────────────────────────────
    if st.session_state.analysis_result and st.session_state.get("similar_reports"):
        sims = st.session_state.similar_reports
        ids = ", ".join(esc(f"{s['id']} ({s['alasan']})") for s in sims[:3])
        st.warning(
            f"🧩 Ditemukan {len(sims)} laporan serupa: {ids}. "
            "Jika ini kerusakan yang sama, dukung laporan yang ada alih-alih membuat baru."
        )

    # ── Authenticity signal ───────────────────────────────────────────────────
    if st.session_state.analysis_result and st.session_state.get("exif_info"):
        ex = st.session_state.exif_info
        tone = {"Kuat": "#3F7A52", "Sedang": "#B5701A", "Perlu dicek": "#B23A2E"}.get(ex["label"], "#6B6155")
        st.markdown(
            f'<div style="font-size:0.8rem; margin:0.2rem 0 0.4rem;">'
            f'<b style="color:{tone}">🛡️ Keaslian foto: {ex["label"]} ({ex["score"]}/100)</b>'
            + (f' · <span style="color:var(--ink-soft)">{esc(ex["flags"][0])}</span>' if ex["flags"] else "")
            + "</div>",
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

            coords = manual_coord or st.session_state.get("exif_gps")
            provinsi_final = prov_name or detect_provinsi(lokasi)
            new_report = {
                "id": new_id,
                "pelapor": pelapor,
                "pelapor_username": user["username"],
                "lokasi": lokasi,
                "jalan": jalan.strip(),
                "provinsi": provinsi_final,
                "kabupaten": kab_name,
                "kecamatan": kec_name,
                "kelurahan": kel_name,
                "wilayah_kode": kel_code or kec_code or kab_code or prov_code or "",
                "gps_dari_foto": bool(st.session_state.get("exif_gps")) and not manual_coord,
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
                # Responsible-AI metadata
                "foto_phash": st.session_state.get("foto_phash"),
                "foto_redacted": bool(blur_privacy),
                "exif_score": (st.session_state.get("exif_info") or {}).get("score"),
                "exif_label": (st.session_state.get("exif_info") or {}).get("label"),
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