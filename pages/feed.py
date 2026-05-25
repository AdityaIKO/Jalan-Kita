import streamlit as st
import sys
import io
from pathlib import Path
from PIL import Image

sys.path.append(str(Path(__file__).parent.parent))

from utils.storage import (
    load_reports, toggle_like, update_status, update_assignment,
    add_progress_update, format_rupiah, format_timestamp,
    get_status_color, get_sla_info, get_foto_base64,
    PROVINSI_INDONESIA, ADMIN_PASSWORD, detect_provinsi,
)

st.set_page_config(
    page_title="JalanKita — Feed Komunitas",
    page_icon="🗺️", layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

  .main-header { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%); padding: 2.5rem 2rem; border-radius: 16px; margin-bottom: 2rem; border: 1px solid rgba(56,189,248,0.15); }
  .main-header h1 { color: #f0f9ff; font-size: 2rem; font-weight: 800; margin: 0 0 0.25rem 0; }
  .main-header p { color: #7dd3fc; margin: 0; font-size: 0.95rem; }

  .report-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 1rem; transition: box-shadow 0.2s; }
  .report-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }

  .reporter-chip { display:inline-flex; align-items:center; gap:0.4rem; background:#f1f5f9; border-radius:999px; padding:0.3rem 0.75rem; font-size:0.8rem; color:#334155; font-weight:600; margin-top:0.4rem; }
  .reporter-avatar { width:20px; height:20px; border-radius:50%; background:#0369a1; color:white; display:inline-flex; align-items:center; justify-content:center; font-size:0.65rem; font-weight:700; }

  .status-badge { display:inline-block; padding:0.3rem 0.85rem; border-radius:999px; font-size:0.72rem; font-weight:700; letter-spacing:0.5px; text-transform:uppercase; }

  .deteksi-row { display:flex; gap:0.75rem; flex-wrap:wrap; background:#f8fafc; border-radius:8px; padding:0.75rem 1rem; margin:0.75rem 0; font-size:0.825rem; }
  .deteksi-item { display:flex; flex-direction:column; gap:0.1rem; }
  .deteksi-label { color:#94a3b8; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.5px; }
  .deteksi-val { color:#0f172a; font-weight:600; }

  .rab-bar { background:#0f172a; color:white; border-radius:8px; padding:0.6rem 1rem; display:flex; justify-content:space-between; align-items:center; font-size:0.825rem; margin:0.5rem 0; }
  .rab-bar .label { color:#7dd3fc; }
  .rab-bar .amount { font-weight:700; font-size:1rem; }

  .sla-track { background:#f1f5f9; border-radius:999px; height:6px; overflow:hidden; }
  .sla-fill { height:100%; border-radius:999px; }

  .stat-box { background:white; border:1px solid #e2e8f0; border-radius:12px; padding:1rem; text-align:center; }
  .stat-box .num { font-size:1.75rem; font-weight:800; color:#0f172a; }
  .stat-box .lbl { font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; }

  .assigned-banner { background:#f0fdf4; border:1px solid #86efac; border-radius:8px; padding:0.75rem 1rem; font-size:0.825rem; margin:0.5rem 0; }
  .assigned-banner .label { color:#16a34a; font-weight:700; font-size:0.72rem; text-transform:uppercase; }
  .assigned-banner .value { color:#15803d; font-weight:600; }

  .progress-item { border-left:3px solid #e2e8f0; padding:0.5rem 0 0.5rem 1rem; margin-bottom:0.75rem; }
  .progress-item:last-child { margin-bottom:0; }
  .progress-time { font-size:0.72rem; color:#94a3b8; }
  .progress-uploader { font-size:0.8rem; font-weight:600; color:#0f172a; }
  .progress-desc { font-size:0.825rem; color:#475569; margin-top:0.2rem; }

  div[data-testid="stButton"] > button { font-family:'Plus Jakarta Sans',sans-serif; border-radius:8px; font-weight:600; transition:all 0.2s; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "liked_ids" not in st.session_state:
    st.session_state.liked_ids = set()
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🗺️ Feed Komunitas</h1>
  <p>Pantau semua laporan kerusakan jalan, berikan dukungan, dan lihat progres penanganan.</p>
</div>
""", unsafe_allow_html=True)

col_nav1, col_nav2, _ = st.columns([1, 1, 4])
with col_nav1:
    st.page_link("app.py", label="📋 Laporkan", use_container_width=True)
with col_nav2:
    st.page_link("pages/feed.py", label="🗺️ Feed Komunitas", use_container_width=True)

st.divider()

# ── Load data ─────────────────────────────────────────────────────────────────
reports = load_reports()

# ── Stats ──────────────────────────────────────────────────────────────────────
total = len(reports)
menunggu = sum(1 for r in reports if r["status"] == "Menunggu")
prioritas = sum(1 for r in reports if r["status"] == "Prioritas Publik")
selesai = sum(1 for r in reports if r["status"] == "Selesai")
csr = sum(1 for r in reports if r["status"] == "CSR Dashboard")

c1, c2, c3, c4, c5 = st.columns(5)
for col, num, label in zip([c1,c2,c3,c4,c5], [total,menunggu,prioritas,csr,selesai], ["Total Laporan","Menunggu","Prioritas 🔥","CSR Dashboard","Selesai ✅"]):
    col.markdown(f'<div class="stat-box"><div class="num">{num}</div><div class="lbl">{label}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────────────────
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
with fc1:
    filter_status = st.selectbox("Filter Status", ["Semua", "Menunggu", "Prioritas Publik", "CSR Dashboard", "Selesai"])
with fc2:
    filter_provinsi = st.selectbox("Filter Wilayah", PROVINSI_INDONESIA)
with fc3:
    sort_by = st.selectbox("Urutkan", ["Terbaru", "Terlama", "Terpopuler"])
with fc4:
    search = st.text_input("Cari lokasi...", placeholder="Ketik nama jalan...")

# ── Filter logic ───────────────────────────────────────────────────────────────
filtered = reports
if filter_status != "Semua":
    filtered = [r for r in filtered if r["status"] == filter_status]
if filter_provinsi != "Semua Wilayah":
    filtered = [r for r in filtered if detect_provinsi(r.get("lokasi","")) == filter_provinsi or r.get("provinsi","") == filter_provinsi]
if search:
    filtered = [r for r in filtered if search.lower() in r["lokasi"].lower()]
if sort_by == "Terpopuler":
    filtered = sorted(filtered, key=lambda x: x["likes"], reverse=True)
elif sort_by == "Terlama":
    filtered = sorted(filtered, key=lambda x: x["timestamp"])
else:
    filtered = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)

st.caption(f"Menampilkan {len(filtered)} laporan")
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
    sla_color = "#ef4444" if sla["lewat"] else "#3b82f6"
    keparahan = det.get("tingkat_keparahan", "")
    kep_color = {"Berat": "#dc2626", "Sedang": "#d97706", "Ringan": "#16a34a"}.get(keparahan, "#6b7280")
    pelapor_name = report.get("pelapor", "Anonim")
    pelapor_initial = pelapor_name[0].upper() if pelapor_name else "?"
    assigned_to = report.get("assigned_to", "")
    progress_updates = report.get("progress_updates", [])

    # ── Pre-compute assigned banner HTML ──────────────────────────────────────
    if assigned_to:
        by_line = ""
        if report.get("assigned_by"):
            by_line = f'<div style="font-size:0.75rem;color:#16a34a">oleh {report.get("assigned_by","–")} · {report.get("assignment_notes","")}</div>'
        assigned_banner_html = f'<div class="assigned-banner"><div class="label">✅ Ditugaskan kepada</div><div class="value">{assigned_to}</div>{by_line}</div>'
    else:
        assigned_banner_html = ""

    # ── Card HTML ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="report-card">
      <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
          <div style="font-size:0.75rem; color:#94a3b8; font-weight:600;">{rid} · {format_timestamp(report["timestamp"])}</div>
          <div style="font-size:1rem; font-weight:700; color:#0f172a; margin:0.2rem 0 0;">📍 {report["lokasi"]}</div>
          <div class="reporter-chip">
            <span class="reporter-avatar">{pelapor_initial}</span>
            {pelapor_name}
          </div>
        </div>
        <span class="status-badge" style="background:{status_color}22; color:{status_color}; border:1px solid {status_color}55">{status}</span>
      </div>

      <div class="deteksi-row">
        <div class="deteksi-item"><span class="deteksi-label">Tipe Kerusakan</span><span class="deteksi-val">{det.get("tipe_kerusakan","–")}</span></div>
        <div class="deteksi-item"><span class="deteksi-label">Tingkat</span><span class="deteksi-val" style="color:{kep_color}">{keparahan}</span></div>
        <div class="deteksi-item"><span class="deteksi-label">Dimensi</span><span class="deteksi-val">{det.get("estimasi_dimensi","–")}</span></div>
        <div class="deteksi-item"><span class="deteksi-label">Confidence AI</span><span class="deteksi-val">{det.get("confidence","–")}</span></div>
      </div>

      <div class="rab-bar"><span class="label">💰 Estimasi RAB</span><span class="amount">{format_rupiah(rab.get("total",0))}</span></div>

      <div style="margin:0.5rem 0;">
        <div style="font-size:0.75rem; color:#64748b; margin-bottom:0.25rem;">SLA: Hari ke-{sla["hari_berjalan"]}/{sla["sla_hari"]} {"⚠️ Melewati SLA!" if sla["lewat"] else f"({sla['sisa']} hari tersisa)"}</div>
        <div class="sla-track"><div class="sla-fill" style="width:{sla['persen']}%; background:{sla_color}"></div></div>
      </div>

      <div style="font-size:0.8rem; color:#64748b; font-style:italic;">💬 {det.get("catatan","–")}</div>

      {assigned_banner_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Preview foto laporan ───────────────────────────────────────────────────
    foto_path = report.get("foto_path")
    if foto_path and Path(foto_path).exists():
        with st.expander("🖼️ Lihat Foto Kerusakan"):
            img = Image.open(foto_path)
            img.thumbnail((600, 600))
            st.image(img, use_container_width=True)

    # ── Aksi bawah card ────────────────────────────────────────────────────────
    bc1, bc2, bc3 = st.columns([1, 2, 2])
    with bc1:
        like_label = f"❤️ {report['likes']}{' · Disukai' if is_liked else ''}"
        if st.button(like_label, key=f"like_{rid}", use_container_width=True):
            _, new_liked = toggle_like(rid, st.session_state.liked_ids)
            st.session_state.liked_ids = new_liked
            st.rerun()
    with bc2:
        new_status = st.selectbox("Status", ["Menunggu","Prioritas Publik","CSR Dashboard","Selesai"],
            index=["Menunggu","Prioritas Publik","CSR Dashboard","Selesai"].index(status),
            key=f"status_{rid}", label_visibility="collapsed")
        if new_status != status:
            update_status(rid, new_status)
            st.rerun()
    with bc3:
        with st.expander("📊 Rincian RAB"):
            for item in rab.get("breakdown", []):
                ic1, ic2 = st.columns([3, 1])
                ic1.caption(f"{item.get('item','–')} ({item.get('volume','–')})")
                ic2.caption(f"**{format_rupiah(item.get('subtotal',0))}**")
            if rab.get("total"):
                st.markdown(f"**Total: {format_rupiah(rab.get('total',0))}**")

    # ── Progress & Penugasan expander ─────────────────────────────────────────
    with st.expander(f"📋 Progress & Penugasan {'🟢' if assigned_to else '⚪'} · {len(progress_updates)} update"):
        tab_assign, tab_progress, tab_add_progress = st.tabs(["🎯 Penugasan (Admin)", "📜 Riwayat Progress", "➕ Tambah Update"])

        # Tab 1: Penugasan Admin
        with tab_assign:
            if not st.session_state.admin_authenticated:
                st.markdown("**🔐 Login Admin diperlukan**")
                pwd = st.text_input("Password Admin", type="password", key=f"pwd_{rid}")
                if st.button("Login", key=f"login_{rid}"):
                    if pwd == ADMIN_PASSWORD:
                        st.session_state.admin_authenticated = True
                        st.rerun()
                    else:
                        st.error("Password salah!")
            else:
                st.success("✅ Anda login sebagai Admin")
                with st.form(key=f"assign_form_{rid}"):
                    a1, a2 = st.columns(2)
                    with a1:
                        new_assigned_to = st.text_input("Ditugaskan kepada", value=report.get("assigned_to",""), placeholder="Contoh: Dinas PU Sleman")
                    with a2:
                        new_assigned_by = st.text_input("Oleh (nama admin)", value=report.get("assigned_by",""), placeholder="Contoh: Admin JalanKita")
                    new_notes = st.text_area("Catatan penugasan", value=report.get("assignment_notes",""), placeholder="Contoh: Prioritaskan sebelum musim hujan", height=80)
                    if st.form_submit_button("💾 Simpan Penugasan", use_container_width=True):
                        update_assignment(rid, new_assigned_to, new_assigned_by, new_notes)
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
                      <div class="progress-time">{format_timestamp(pu.get("timestamp",""))}</div>
                      <div class="progress-uploader">👤 {pu.get("uploader","Anonim")}</div>
                      <div class="progress-desc">{pu.get("deskripsi","–")}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if foto_pu and Path(foto_pu).exists():
                        img_pu = Image.open(foto_pu)
                        img_pu.thumbnail((400, 400))
                        st.image(img_pu, caption="Foto bukti progress", use_container_width=False, width=300)

        # Tab 3: Tambah Update Progress
        with tab_add_progress:
            with st.form(key=f"progress_form_{rid}"):
                uploader_name = st.text_input("Nama Anda", placeholder="Siapa yang mengupload update ini?")
                deskripsi_progress = st.text_area("Deskripsi Update", placeholder="Contoh: Tim survey sudah tiba di lokasi. Pengerjaan dijadwalkan Senin.", height=100)
                foto_progress = st.file_uploader("Foto Bukti (opsional)", type=["jpg","jpeg","png"], key=f"foto_progress_{rid}")
                submitted = st.form_submit_button("📤 Kirim Update Progress", use_container_width=True)
                if submitted:
                    if not uploader_name or not deskripsi_progress:
                        st.warning("Nama dan deskripsi wajib diisi!")
                    else:
                        foto_bytes = None
                        foto_ext = "jpg"
                        if foto_progress:
                            foto_bytes = foto_progress.read()
                            foto_ext = foto_progress.name.split(".")[-1].lower()
                        add_progress_update(rid, uploader_name, deskripsi_progress, foto_bytes, foto_ext)
                        st.success("Update progress berhasil ditambahkan!")
                        st.rerun()

    st.markdown("---")