"""Account system: users, authentication, follows, and auth UI.

Lightweight and file-backed (data/users.json) to match the rest of the app.
Passwords are salted + SHA-256 hashed (sufficient for a demo; not production
crypto). A set of dummy accounts is seeded on first run so the app is usable
immediately — see DEMO_HINT.
"""
from __future__ import annotations

import json
import hashlib
import secrets
from datetime import datetime
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"

DEMO_HINT = "Akun demo — username **budi**, password **budi123**"

# Avatar palette (warm, matches the design system).
AVATAR_COLORS = ["#B5701A", "#B23A2E", "#3F7A52", "#6E5AA8", "#C2541C", "#2A6F77", "#9A3F6E"]

# Seeded on first run. Passwords here are plaintext only to generate hashes once;
# they are never stored in plaintext. Reporter names match the seed reports so
# existing posts attribute to real accounts.
_SEED_ACCOUNTS = [
    ("budi", "budi123", "Budi Santoso", "Warga Sleman yang peduli infrastruktur. Rajin lapor jalan rusak. 🛣️", "warga"),
    ("dewi", "dewi123", "Dewi Rahayu", "Ibu rumah tangga, aktif menjaga lingkungan sekitar.", "warga"),
    ("ahmad", "ahmad123", "Ahmad Fauzi", "Relawan komunitas Gunungkidul.", "warga"),
    ("siti", "siti123", "Siti Nurhaliza", "Guru. Jalan aman untuk anak sekolah.", "warga"),
    ("rizki", "rizki123", "Rizki Pratama", "Pengendara harian. Anti lubang!", "warga"),
    ("admin", "admin123", "Admin Dinas PU", "Akun resmi Dinas Pekerjaan Umum.", "admin"),
]


# ── Persistence ───────────────────────────────────────────────────────────────
def _hash(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}${password}".encode("utf-8")).hexdigest()


def _make_user(username, password, nama, bio, role, color) -> dict:
    salt = secrets.token_hex(8)
    return {
        "username": username,
        "salt": salt,
        "password_hash": _hash(password, salt),
        "nama": nama,
        "bio": bio,
        "role": role,
        "avatar_color": color,
        "joined": datetime.now().isoformat(),
        "following": [],
    }


def _seed() -> list:
    users = [
        _make_user(u, p, n, b, r, AVATAR_COLORS[i % len(AVATAR_COLORS)])
        for i, (u, p, n, b, r) in enumerate(_SEED_ACCOUNTS)
    ]
    save_users(users)
    return users


def load_users() -> list:
    if not USERS_FILE.exists():
        return _seed()
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_user(username: str) -> dict | None:
    if not username:
        return None
    return next((u for u in load_users() if u["username"] == username), None)


# ── Auth operations ───────────────────────────────────────────────────────────
def authenticate(username: str, password: str) -> bool:
    u = get_user(username.strip().lower())
    if not u:
        return False
    return _hash(password, u["salt"]) == u["password_hash"]


def register(username: str, password: str, nama: str) -> tuple[bool, str]:
    username = username.strip().lower()
    if not username or not password or not nama.strip():
        return False, "Semua kolom wajib diisi."
    if len(username) < 3 or " " in username:
        return False, "Username minimal 3 karakter, tanpa spasi."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    users = load_users()
    if any(u["username"] == username for u in users):
        return False, "Username sudah dipakai."
    color = AVATAR_COLORS[len(users) % len(AVATAR_COLORS)]
    users.append(_make_user(username, password, nama.strip(), "", "warga", color))
    save_users(users)
    return True, "Akun berhasil dibuat. Silakan masuk."


def update_profile(username: str, nama: str = None, bio: str = None,
                   avatar_color: str = None, new_password: str = None) -> None:
    users = load_users()
    for u in users:
        if u["username"] == username:
            if nama is not None:
                u["nama"] = nama
            if bio is not None:
                u["bio"] = bio
            if avatar_color is not None:
                u["avatar_color"] = avatar_color
            if new_password:
                u["salt"] = secrets.token_hex(8)
                u["password_hash"] = _hash(new_password, u["salt"])
            break
    save_users(users)


def toggle_follow(follower: str, target: str) -> bool:
    """Follow/unfollow target. Returns True if now following."""
    if follower == target:
        return False
    users = load_users()
    now_following = False
    for u in users:
        if u["username"] == follower:
            following = u.setdefault("following", [])
            if target in following:
                following.remove(target)
            else:
                following.append(target)
                now_following = True
            break
    save_users(users)
    return now_following


def is_following(follower: str, target: str) -> bool:
    u = get_user(follower)
    return bool(u and target in u.get("following", []))


def follower_count(username: str) -> int:
    return sum(1 for u in load_users() if username in u.get("following", []))


# ── Session ───────────────────────────────────────────────────────────────────
def current_user() -> dict | None:
    uname = st.session_state.get("auth_user")
    return get_user(uname) if uname else None


def login_session(username: str) -> None:
    st.session_state.auth_user = username


def logout() -> None:
    st.session_state.auth_user = None
    st.session_state.pop("liked_ids", None)


# ── Auth UI ───────────────────────────────────────────────────────────────────
def render_auth_gate() -> None:
    """Render the login/signup screen and halt the page."""
    from utils.ui import avatar_html  # local import avoids any import cycle

    col_brand, col_form = st.columns([1.1, 1], gap="large")
    with col_brand:
        st.markdown(
            """
            <div class="auth-hero">
              <div class="eyebrow">Platform Pelaporan Jalan · Berbasis AI</div>
              <h1>🛣️ JalanKita</h1>
              <p>Komunitas warga yang menjaga jalan tetap aman. Foto kerusakan,
                 AI menghitung anggaran, dan ribuan warga ikut mendorong perbaikan.</p>
              <div class="auth-feature"><span class="ic">📸</span><span class="tx"><b>Lapor sekali klik</b> — AI mendeteksi & menaksir biaya.</span></div>
              <div class="auth-feature"><span class="ic">❤️</span><span class="tx"><b>Dukung & komentari</b> laporan tetangga Anda.</span></div>
              <div class="auth-feature"><span class="ic">📊</span><span class="tx"><b>Pantau transparan</b> dari laporan hingga selesai.</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_form:
        st.markdown("#### Selamat datang 👋")
        st.caption(DEMO_HINT)
        tab_login, tab_signup = st.tabs(["Masuk", "Daftar"])

        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Username", placeholder="Masukkan username Anda")
                p = st.text_input("Password", type="password", placeholder="Masukkan password")
                if st.form_submit_button("Masuk", use_container_width=True):
                    if not u.strip():
                        st.error("Username belum diisi.")
                    elif authenticate(u, p.strip()):
                        login_session(u.strip().lower())
                        st.rerun()
                    else:
                        st.error("Username atau password salah.")
            if st.button("⚡ Masuk cepat sebagai demo (budi)", use_container_width=True):
                login_session("budi")
                st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                nama = st.text_input("Nama Lengkap", placeholder="Nama Anda")
                u2 = st.text_input("Username", placeholder="minimal 3 karakter, tanpa spasi")
                p2 = st.text_input("Password", type="password", placeholder="minimal 6 karakter")
                if st.form_submit_button("Buat Akun", use_container_width=True):
                    ok, msg = register(u2, p2, nama)
                    if ok:
                        login_session(u2.strip().lower())
                        st.rerun()
                    else:
                        st.error(msg)
    st.stop()


def require_auth() -> dict:
    """Return the logged-in user, or render the gate and stop the page."""
    user = current_user()
    if not user:
        render_auth_gate()
    return user


def render_topbar(active: str = "") -> None:
    """Top navigation row with page links and the signed-in user menu.

    All navigation uses st.page_link so Streamlit routes client-side and keeps
    the session (a raw <a> would hard-reload and drop the login state).
    """
    from utils.ui import avatar_html

    user = current_user() or {}
    c1, c2, c3, c4, _, c_user, c_out = st.columns([1, 1.3, 1, 0.95, 0.9, 1.55, 0.9])
    with c1:
        st.page_link("app.py", label="Laporkan", icon="📋", use_container_width=True)
    with c2:
        st.page_link("pages/feed.py", label="Feed Komunitas", icon="🗺️", use_container_width=True)
    with c3:
        st.page_link("pages/dashboard.py", label="Dashboard", icon="📊", use_container_width=True)
    with c4:
        st.page_link("pages/profile.py", label="Profil", icon="👤", use_container_width=True)
    with c_user:
        av = avatar_html(user.get("nama", "?"), user.get("avatar_color", "#B5701A"), 30)
        role = "Admin Dinas PU" if user.get("role") == "admin" else "Warga"
        st.markdown(
            f'<div class="user-chip">{av}'
            f'<span><span class="nm">{user.get("nama","")}</span><br><span class="rl">{role}</span></span></div>',
            unsafe_allow_html=True,
        )
    with c_out:
        if st.button("Keluar", key="logout_btn", use_container_width=True):
            logout()
            st.rerun()
