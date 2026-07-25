import streamlit as st
import sys
import io
from pathlib import Path
from PIL import Image

sys.path.append(str(Path(__file__).parent.parent))

from utils.storage import (
    load_reports, toggle_like, update_status, update_assignment,
    add_progress_update, add_comment, author_color,
    format_rupiah, format_timestamp,
    get_status_color, get_sla_info, get_foto_base64,
    priority_score, priority_label, reports_to_csv,
    PROVINSI_INDONESIA, detect_provinsi,
)
from utils.geo import report_coords, in_indonesia, ID_VIEW
from utils.ui import (
    inject_css, render_header, PRIO_COLORS, SEVERITY_COLORS, INK_SOFT, avatar_html,
    sdg_badges_html, impact_strip_html, eco_card_html,
)
from utils import auth, sustainability, integrity, wilayah
from utils.security import esc, validate_image_upload

st.set_page_config(
    page_title="JalanKita · Feed Komunitas",
    page_icon="🗺️", layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
me = auth.require_auth()
is_admin = me.get("role") == "admin"

# ── Session state ─────────────────────────────────────────────────────────────
if "liked_ids" not in st.session_state:
    st.session_state.liked_ids = set()

# ── Header ─────────────────────────────────────────────────────────────────────
render_header(
    "Ruang Publik · Transparansi Laporan",
    "🗺️ Feed Komunitas",
    "Pantau setiap laporan kerusakan jalan, berikan dukungan untuk menaikkan prioritas, dan ikuti progres penanganannya.",
)
auth.render_topbar("feed")

st.divider()

# ── Load data ─────────────────────────────────────────────────────────────────
reports = load_reports()

# Spatial clustering: how many separate reports describe the same spot.
cluster_sizes = integrity.cluster_reports(reports)

# ── Stats ──────────────────────────────────────────────────────────────────────
total = len(reports)
menunggu = sum(1 for r in reports if r["status"] == "Menunggu")
prioritas = sum(1 for r in reports if r["status"] == "Prioritas Publik")
selesai = sum(1 for r in reports if r["status"] == "Selesai")
csr = sum(1 for r in reports if r["status"] == "CSR Dashboard")

stat_cols = st.columns(5)
stat_defs = [
    (total, "Total Laporan", "kpi--accent"),
    (menunggu, "Menunggu", ""),
    (prioritas, "Prioritas Publik", "kpi--danger"),
    (csr, "CSR Dashboard", ""),
    (selesai, "Selesai", "kpi--ok"),
]
for col, (num, label, mod) in zip(stat_cols, stat_defs):
    col.markdown(f'<div class="kpi {mod}"><div class="lbl">{label}</div><div class="num">{num}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Peta sebaran laporan ───────────────────────────────────────────────────────
show_map = st.toggle("🗺️ Tampilkan peta sebaran laporan (wilayah Indonesia)", value=True)
if show_map:
    import pandas as pd
    # Every coordinate is already constrained to Indonesia (report_coords falls
    # back to a province centroid for any out-of-country GPS), so the map only
    # ever frames Indonesian points and never leaves the country.
    map_rows = []
    for r in reports:
        coords = report_coords(r)
        if coords and in_indonesia(*coords):
            map_rows.append({"lat": coords[0], "lon": coords[1]})
    if map_rows:
        st.map(pd.DataFrame(map_rows), size=140, color="#B5701A", zoom=5)
        st.caption("Peta dibatasi wilayah Indonesia. Titik memakai koordinat GPS laporan bila tersedia, atau perkiraan pusat provinsi.")
    else:
        st.info("Belum ada laporan untuk ditampilkan di peta.")
    st.markdown("<br>", unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────────────────
fr1 = st.columns(3)
with fr1[0]:
    filter_status = st.selectbox("Status", ["Semua", "Menunggu", "Prioritas Publik", "CSR Dashboard", "Selesai"])
fprov_code = None
if wilayah.available():
    provs = wilayah.provinces()
    with fr1[1]:
        filter_provinsi = st.selectbox("Provinsi", ["Semua Provinsi"] + [n for _, n in provs])
        fprov_code = next((c for c, n in provs if n == filter_provinsi), None)
    with fr1[2]:
        if fprov_code:
            kab_opts = ["Semua Kab/Kota"] + [n for _, n in wilayah.regencies(fprov_code)]
        else:
            kab_opts = ["Semua Kab/Kota"]
        filter_kab = st.selectbox("Kabupaten/Kota", kab_opts, disabled=not fprov_code)
else:
    with fr1[1]:
        filter_provinsi = st.selectbox("Wilayah", PROVINSI_INDONESIA)
    filter_kab = "Semua Kab/Kota"

fr2 = st.columns([1, 2])
with fr2[0]:
    sort_by = st.selectbox("Urutkan", ["Prioritas", "Terbaru", "Terlama", "Terpopuler"])
with fr2[1]:
    search = st.text_input("Cari lokasi", placeholder="Ketik nama jalan atau wilayah...")

following = set(me.get("following", []))
only_following = st.checkbox(
    f"👥 Hanya dari yang saya ikuti ({len(following)})",
    value=False, disabled=not following,
)

# ── Filter logic ───────────────────────────────────────────────────────────────
filtered = reports
if only_following:
    filtered = [r for r in filtered if r.get("pelapor_username") in following]
if filter_status != "Semua":
    filtered = [r for r in filtered if r["status"] == filter_status]
if filter_provinsi not in ("Semua Wilayah", "Semua Provinsi"):
    filtered = [r for r in filtered if r.get("provinsi", "") == filter_provinsi or detect_provinsi(r.get("lokasi", "")) == filter_provinsi]
if filter_kab != "Semua Kab/Kota":
    filtered = [r for r in filtered if r.get("kabupaten", "") == filter_kab]
if search:
    filtered = [r for r in filtered if search.lower() in r["lokasi"].lower()]
if sort_by == "Terpopuler":
    filtered = sorted(filtered, key=lambda x: x["likes"], reverse=True)
elif sort_by == "Terlama":
    filtered = sorted(filtered, key=lambda x: x["timestamp"])
elif sort_by == "Prioritas":
    filtered = sorted(filtered, key=lambda x: priority_score(x), reverse=True)
else:
    filtered = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)

cap_col, exp_col = st.columns([3, 1])
with cap_col:
    st.caption(f"Menampilkan {len(filtered)} laporan")
with exp_col:
    st.download_button(
        "⬇️ Ekspor CSV",
        data=reports_to_csv(filtered),
        file_name="jalankita_laporan.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=not filtered,
    )
st.markdown("---")

# ── Report cards ───────────────────────────────────────────────────────────────
if not filtered:
    st.info("Tidak ada laporan yang sesuai filter.")

for report in filtered:
    det = report.get("deteksi", {})
    rab = report.get("rab", {})
    sla = get_sla_info(report)
    status = report["status"]
    status_color = get_status_color(status)
    rid = report["id"]
    is_liked = rid in st.session_state.liked_ids
    sla_color = "var(--danger)" if sla["lewat"] else ("var(--ok)" if sla.get("resolved") else "var(--amber)")
    keparahan = det.get("tingkat_keparahan", "")
    kep_color = SEVERITY_COLORS.get(keparahan, INK_SOFT)
    pelapor_name = report.get("pelapor", "Anonim")
    author_username = report.get("pelapor_username", "")
    author = auth.get_user(author_username) if author_username else None
    av_color = author.get("avatar_color") if author else author_color(pelapor_name)
    is_own_post = author_username == me["username"]
    following_author = author_username in following
    comments = report.get("comments", [])
    assigned_to = report.get("assigned_to", "")
    progress_updates = report.get("progress_updates", [])
    p_score = priority_score(report)
    p_label = priority_label(p_score)
    p_color = PRIO_COLORS.get(p_label, INK_SOFT)

    # Sustainability layer: environmental cost, eco-material, SDG mapping.
    impact = sustainability.estimate_impact(report)
    eco_rec = sustainability.recommend_material(det.get("tipe_kerusakan", ""))
    sdg = sustainability.sdg_tags(report)

    # Responsible-AI trust indicators: duplicates, privacy, authenticity.
    chips = []
    cluster_n = cluster_sizes.get(rid)
    if cluster_n:
        chips.append(f'<span class="trust-chip cluster">🧩 {cluster_n} laporan di titik ini</span>')
    if report.get("foto_redacted"):
        chips.append('<span class="trust-chip priv">🔒 Privasi tersensor</span>')
    ex_label = report.get("exif_label")
    if ex_label:
        tone = {"Kuat": "ok", "Sedang": "warn", "Perlu dicek": "danger"}.get(ex_label, "warn")
        chips.append(f'<span class="trust-chip {tone}">🛡️ Keaslian: {esc(ex_label)}</span>')
    trust_html = f'<div class="trust-row">{"".join(chips)}</div>' if chips else ""

    if sla.get("resolved"):
        sla_note = "✓ Selesai dalam SLA"
    elif sla["lewat"]:
        sla_note = "⚠ Melewati SLA"
    else:
        sla_note = f"{sla['sisa']} hari tersisa"

    # ── Pre-compute assigned banner HTML (all user text escaped) ──────────────
    if assigned_to:
        by_line = ""
        if report.get("assigned_by"):
            by_line = f'<div style="font-size:0.74rem;color:var(--ok);margin-top:0.1rem">oleh {esc(report.get("assigned_by","–"))} · {esc(report.get("assignment_notes",""))}</div>'
        assigned_banner_html = f'<div class="assigned-banner"><div class="label">Ditugaskan kepada</div><div class="value">{esc(assigned_to)}</div>{by_line}</div>'
    else:
        assigned_banner_html = ""

    # ── Card HTML ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="report-card">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
        <div>
          <div class="meta-line">{esc(rid)} · {esc(format_timestamp(report["timestamp"]))}</div>
          <div class="loc-title">{esc(report["lokasi"])}</div>
          <div class="reporter-chip">
            {avatar_html(pelapor_name, av_color, 22)}
            {esc(pelapor_name)}{' · ✓ diikuti' if following_author else ''}
          </div>
        </div>
        <div style="text-align:right; flex-shrink:0;">
          <span class="status-badge" style="background:{status_color}1a; color:{status_color}; border:1px solid {status_color}44">{esc(status)}</span>
          <div style="margin-top:0.45rem;"><span class="prio-pill" style="background:{p_color}1a; color:{p_color}; border:1px solid {p_color}44;">🚦 {p_label} · {p_score}</span></div>
        </div>
      </div>

      <div class="deteksi-row">
        <div class="deteksi-item"><span class="deteksi-label">Tipe</span><span class="deteksi-val">{esc(det.get("tipe_kerusakan","–"))}</span></div>
        <div class="deteksi-item"><span class="deteksi-label">Tingkat</span><span class="deteksi-val" style="color:{kep_color}">{esc(keparahan)}</span></div>
        <div class="deteksi-item"><span class="deteksi-label">Dimensi</span><span class="deteksi-val">{esc(det.get("estimasi_dimensi","–"))}</span></div>
        <div class="deteksi-item"><span class="deteksi-label">Confidence</span><span class="deteksi-val">{esc(det.get("confidence","–"))}</span></div>
      </div>

      <div class="rab-bar"><span class="label">Estimasi Anggaran Perbaikan</span><span class="amount">{format_rupiah(rab.get("total",0))}</span></div>

      <div style="margin:0.7rem 0 0.5rem;">
        <div class="sla-head"><span>SLA · hari ke-{sla["hari_berjalan"]} dari {sla["sla_hari"]}</span><span style="color:{sla_color}; font-weight:700;">{sla_note}</span></div>
        <div class="sla-track"><div class="sla-fill" style="width:{sla['persen']}%; background:{sla_color}"></div></div>
      </div>

      <div class="note">ℹ️ {esc(det.get("catatan","–"))}</div>

      {impact_strip_html(impact)}
      {trust_html}
      {sdg_badges_html(sdg)}

      {assigned_banner_html}

      <div class="engage" style="margin-top:0.85rem; padding-top:0.75rem; border-top:1px solid var(--line);">
        <span class="it">❤️ <b>{report['likes']}</b> dukungan</span>
        <span class="it">💬 <b>{len(comments)}</b> komentar</span>
        <span class="it">📋 <b>{len(progress_updates)}</b> update</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Preview foto laporan ───────────────────────────────────────────────────
    foto_path = report.get("foto_path")
    if foto_path and Path(foto_path).exists():
        with st.expander("🖼️ Lihat Foto Kerusakan"):
            img = Image.open(foto_path)
            img.thumbnail((600, 600))
            st.image(img, use_container_width=True)

    # ── Dampak lingkungan & material berkelanjutan ────────────────────────────
    with st.expander("🌱 Dampak Lingkungan & Material Berkelanjutan"):
        st.markdown(eco_card_html(eco_rec), unsafe_allow_html=True)
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("CO₂ terbuang / tahun", f'{impact["co2_year_kg"]:,} kg'.replace(",", "."))
        ec2.metric("BBM terbuang / tahun", f'{impact["fuel_year_litre"]:,} L'.replace(",", "."))
        ec3.metric("Kerugian BBM / tahun", format_rupiah(impact["fuel_cost_year_rp"]))
        st.caption(
            f'Estimasi berbasis asumsi lalu lintas {sustainability.ASSUMPTIONS["traffic_per_day"]:,} kendaraan/hari '
            f'dan faktor emisi {sustainability.ASSUMPTIONS["co2_kg_per_litre"]} kg CO₂/liter. '
            'Angka bersifat estimasi teknis untuk perbandingan prioritas.'.replace(",", ".")
        )

    # ── Aksi bawah card ────────────────────────────────────────────────────────
    bc1, bc2, bc3 = st.columns([1, 1, 1])
    with bc1:
        like_label = f"❤️ Dukung ({report['likes']})" if not is_liked else f"💗 Didukung ({report['likes']})"
        if st.button(like_label, key=f"like_{rid}", use_container_width=True):
            _, new_liked = toggle_like(rid, st.session_state.liked_ids)
            st.session_state.liked_ids = new_liked
            st.rerun()
    with bc2:
        if is_own_post or not author_username:
            st.button("📝 Laporan Anda" if is_own_post else "👤 Anonim",
                      key=f"follow_{rid}", use_container_width=True, disabled=True)
        else:
            flbl = "✓ Mengikuti" if following_author else "➕ Ikuti"
            if st.button(flbl, key=f"follow_{rid}", use_container_width=True):
                auth.toggle_follow(me["username"], author_username)
                st.rerun()
    with bc3:
        if is_admin:
            new_status = st.selectbox("Status", ["Menunggu","Prioritas Publik","CSR Dashboard","Selesai"],
                index=["Menunggu","Prioritas Publik","CSR Dashboard","Selesai"].index(status),
                key=f"status_{rid}", label_visibility="collapsed")
            if new_status != status:
                update_status(rid, new_status)
                st.rerun()
        else:
            with st.expander("📊 Rincian RAB"):
                for item in rab.get("breakdown", []):
                    ic1, ic2 = st.columns([3, 1])
                    ic1.caption(f"{item.get('item','–')} ({item.get('volume','–')})")
                    ic2.caption(f"**{format_rupiah(item.get('subtotal',0))}**")
                if rab.get("total"):
                    st.markdown(f"**Total: {format_rupiah(rab.get('total',0))}**")

    # ── Komentar ───────────────────────────────────────────────────────────────
    with st.expander(f"💬 Komentar ({len(comments)})"):
        if not comments:
            st.caption("Belum ada komentar. Jadilah yang pertama berkomentar.")
        for cm in comments:
            c_color = (auth.get_user(cm.get("username","")) or {}).get("avatar_color") or author_color(cm.get("nama",""))
            st.markdown(
                f'''<div class="comment">{avatar_html(cm.get("nama","?"), c_color, 30)}
                  <div class="body">
                    <span class="who">{esc(cm.get("nama","Anonim"))}</span>
                    <span class="when"> · {esc(format_timestamp(cm.get("timestamp","")))}</span>
                    <div class="tx">{esc(cm.get("text",""))}</div>
                  </div></div>''',
                unsafe_allow_html=True,
            )
        with st.form(key=f"comment_form_{rid}", clear_on_submit=True):
            ctext = st.text_input("Tulis komentar", placeholder="Tambahkan komentar…",
                                  label_visibility="collapsed", key=f"ctext_{rid}")
            if st.form_submit_button("Kirim komentar", use_container_width=True):
                if ctext.strip():
                    add_comment(rid, me["username"], me["nama"], ctext)
                    st.rerun()
                else:
                    st.warning("Komentar tidak boleh kosong.")

    # ── Progress & Penugasan expander ─────────────────────────────────────────
    with st.expander(f"📋 Progress & Penugasan {'🟢' if assigned_to else '⚪'} · {len(progress_updates)} update"):
        tab_assign, tab_progress, tab_add_progress = st.tabs(["🎯 Penugasan (Admin)", "📜 Riwayat Progress", "➕ Tambah Update"])

        # Tab 1: Penugasan Admin (hanya akun ber-role admin)
        with tab_assign:
            if not is_admin:
                st.info("🔐 Penugasan hanya dapat dilakukan oleh akun **Admin Dinas PU**. "
                        "Masuk dengan akun admin (demo: `admin` / `admin123`).")
            else:
                st.success(f"✅ Login sebagai Admin · {me['nama']}")
                with st.form(key=f"assign_form_{rid}"):
                    new_assigned_to = st.text_input("Ditugaskan kepada", value=report.get("assigned_to",""), placeholder="Contoh: Dinas PU Sleman")
                    new_notes = st.text_area("Catatan penugasan", value=report.get("assignment_notes",""), placeholder="Contoh: Prioritaskan sebelum musim hujan", height=80)
                    if st.form_submit_button("💾 Simpan Penugasan", use_container_width=True):
                        update_assignment(rid, new_assigned_to, me["nama"], new_notes)
                        st.success("Penugasan disimpan!")
                        st.rerun()

        # Tab 2: Riwayat Progress
        with tab_progress:
            if not progress_updates:
                st.info("Belum ada update progress untuk laporan ini.")
            else:
                for pu in progress_updates:
                    foto_pu = pu.get("foto_path")
                    st.markdown(f"""
                    <div class="progress-item">
                      <div class="progress-time">{esc(format_timestamp(pu.get("timestamp","")))}</div>
                      <div class="progress-uploader">👤 {esc(pu.get("uploader","Anonim"))}</div>
                      <div class="progress-desc">{esc(pu.get("deskripsi","–"))}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if foto_pu and Path(foto_pu).exists():
                        img_pu = Image.open(foto_pu)
                        img_pu.thumbnail((400, 400))
                        st.image(img_pu, caption="Foto bukti progress", use_container_width=False, width=300)

        # Tab 3: Tambah Update Progress
        with tab_add_progress:
            st.caption(f"Mengirim sebagai **{me['nama']}**")
            with st.form(key=f"progress_form_{rid}"):
                uploader_name = me["nama"]
                deskripsi_progress = st.text_area("Deskripsi Update", placeholder="Contoh: Tim survey sudah tiba di lokasi. Pengerjaan dijadwalkan Senin.", height=100)
                foto_progress = st.file_uploader("Foto Bukti (opsional)", type=["jpg","jpeg","png"], key=f"foto_progress_{rid}")
                submitted = st.form_submit_button("📤 Kirim Update Progress", use_container_width=True)
                if submitted:
                    if not deskripsi_progress.strip():
                        st.warning("Deskripsi wajib diisi!")
                    else:
                        foto_bytes = None
                        foto_ext = "jpg"
                        valid_upload = True
                        if foto_progress:
                            candidate = foto_progress.read()
                            ok_up, msg_up = validate_image_upload(candidate, foto_progress.name)
                            if not ok_up:
                                st.error(f"Foto ditolak: {msg_up}")
                                valid_upload = False
                            else:
                                foto_bytes = candidate
                                foto_ext = foto_progress.name.split(".")[-1].lower()
                        if valid_upload:
                            add_progress_update(rid, uploader_name, deskripsi_progress, foto_bytes, foto_ext)
                            st.success("Update progress berhasil ditambahkan!")
                            st.rerun()

    st.markdown("---")