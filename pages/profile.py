import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from utils.storage import load_reports, format_rupiah, format_timestamp, get_status_color
from utils.ui import inject_css, avatar_html, PRIO_COLORS
from utils import auth
from utils.security import esc

st.set_page_config(
    page_title="JalanKita · Profil Saya",
    page_icon="👤", layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
me = auth.require_auth()
auth.render_topbar("profile")

reports = load_reports()
uname = me["username"]
my_reports = [r for r in reports if r.get("pelapor_username") == uname]

dukungan = sum(r.get("likes", 0) for r in my_reports)
following_n = len(me.get("following", []))
followers_n = auth.follower_count(uname)
role_label = "Admin Dinas PU" if me.get("role") == "admin" else "Warga Pelapor"

# ── Profile header ──────────────────────────────────────────────────────────────
big_av = avatar_html(me["nama"], me.get("avatar_color", "#B5701A"), 68)
bio = me.get("bio") or "Belum ada bio."
st.markdown(
    f"""
    <div class="profile-head">
      <div style="display:flex; gap:1.1rem; align-items:center;">
        {big_av}
        <div>
          <div class="pname">{esc(me['nama'])}</div>
          <div class="phandle">@{esc(uname)} · {role_label}</div>
        </div>
      </div>
      <div class="pbio">{esc(bio)}</div>
      <div class="pstats">
        <div class="pstat"><div class="n">{len(my_reports)}</div><div class="l">Laporan</div></div>
        <div class="pstat"><div class="n">{dukungan}</div><div class="l">Dukungan diterima</div></div>
        <div class="pstat"><div class="n">{following_n}</div><div class="l">Mengikuti</div></div>
        <div class="pstat"><div class="n">{followers_n}</div><div class="l">Pengikut</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

tab_posts, tab_activity, tab_settings = st.tabs(["📋 Laporan Saya", "⚡ Aktivitas", "⚙️ Pengaturan"])

# ── Tab: my posts ───────────────────────────────────────────────────────────────
with tab_posts:
    if not my_reports:
        st.info("Anda belum membuat laporan. Mulai di halaman 📋 Laporkan.")
    for r in sorted(my_reports, key=lambda x: x["timestamp"], reverse=True):
        det = r.get("deteksi", {})
        sc = get_status_color(r["status"])
        st.markdown(
            f"""
            <div class="report-card" style="margin-bottom:0.7rem;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                  <div class="meta-line">{esc(r['id'])} · {esc(format_timestamp(r['timestamp']))}</div>
                  <div class="loc-title">{esc(r['lokasi'])}</div>
                </div>
                <span class="status-badge" style="background:{sc}1a; color:{sc}; border:1px solid {sc}44">{esc(r['status'])}</span>
              </div>
              <div class="engage" style="margin-top:0.7rem;">
                <span class="it">🧱 <b>{esc(det.get('tipe_kerusakan','–'))}</b></span>
                <span class="it">💰 <b>{format_rupiah(r.get('rab',{}).get('total',0))}</b></span>
                <span class="it">❤️ <b>{r.get('likes',0)}</b></span>
                <span class="it">💬 <b>{len(r.get('comments',[]))}</b></span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Tab: activity timeline ──────────────────────────────────────────────────────
with tab_activity:
    events = []
    for r in reports:
        loc = esc(r.get("lokasi", ""))
        if r.get("pelapor_username") == uname:
            events.append((r["timestamp"], "📸", f"Membuat laporan di <b>{loc}</b>"))
        for cm in r.get("comments", []):
            if cm.get("username") == uname:
                events.append((cm.get("timestamp", ""), "💬",
                               f"Berkomentar di <b>{loc}</b>: <span class='mut'>“{esc(cm.get('text',''))}”</span>"))
        for pu in r.get("progress_updates", []):
            if pu.get("uploader") == me["nama"]:
                events.append((pu.get("timestamp", ""), "📋",
                               f"Memberi update progress di <b>{loc}</b>"))
    events.sort(key=lambda e: e[0], reverse=True)

    if not events:
        st.info("Belum ada aktivitas. Beri dukungan, komentar, atau buat laporan untuk memulai.")
    for ts, icon, text in events:
        st.markdown(
            f"""<div class="timeline-item"><div class="ic">{icon}</div>
                  <div class="tx">{text}<div class="mut">{format_timestamp(ts)}</div></div>
                </div>""",
            unsafe_allow_html=True,
        )

# ── Tab: settings ───────────────────────────────────────────────────────────────
with tab_settings:
    st.markdown("##### Edit Profil")
    with st.form("profile_settings"):
        new_nama = st.text_input("Nama Lengkap", value=me["nama"])
        new_bio = st.text_area("Bio", value=me.get("bio", ""), height=90,
                               placeholder="Ceritakan sedikit tentang Anda…")
        new_color = st.color_picker("Warna Avatar", value=me.get("avatar_color", "#B5701A"))
        st.markdown("**Ubah Password** (opsional)")
        new_pw = st.text_input("Password Baru", type="password", placeholder="Kosongkan jika tidak diubah")
        if st.form_submit_button("💾 Simpan Perubahan", use_container_width=True):
            if new_pw and len(new_pw) < 6:
                st.error("Password baru minimal 6 karakter.")
            else:
                auth.update_profile(uname, nama=new_nama.strip() or me["nama"],
                                    bio=new_bio, avatar_color=new_color,
                                    new_password=new_pw or None)
                st.success("Profil diperbarui.")
                st.rerun()

    st.divider()
    st.markdown("##### Akun")
    if st.button("🚪 Keluar dari akun", use_container_width=True):
        auth.logout()
        st.rerun()
