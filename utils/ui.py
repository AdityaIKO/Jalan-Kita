"""Shared UI system — design tokens, global CSS, header, navigation.

Identity: "warm asphalt + safety-amber on paper". A grounded, civic-infrastructure
look that deliberately avoids the generic gov-tech navy/sky-blue palette. Colours
use OKLCH; neutrals are tinted warm. Centralised so every page is consistent.
"""
import streamlit as st

# ── Palette (hex mirrors of the CSS OKLCH tokens, for inline use & charts) ─────
INK = "#241F18"
INK_SOFT = "#6B6155"
INK_FAINT = "#9A8F80"
PAPER = "#FAF7F2"
SURFACE = "#FFFEFB"
LINE = "#E7DFD3"
AMBER = "#B5701A"

# Status colours (used by storage.get_status_color + feed badges)
STATUS_COLORS = {
    "Menunggu": "#B5701A",          # amber — awaiting triage
    "Prioritas Publik": "#B23A2E",  # red — escalated by the public
    "CSR Dashboard": "#6E5AA8",     # violet — routed to private funding
    "Selesai": "#3F7A52",           # green — resolved
}

# Priority colours (Kritis → Rendah)
PRIO_COLORS = {
    "Kritis": "#B23A2E",
    "Tinggi": "#C2541C",
    "Sedang": "#B5701A",
    "Rendah": "#3F7A52",
}

# Severity colours
SEVERITY_COLORS = {"Berat": "#B23A2E", "Sedang": "#B5701A", "Ringan": "#3F7A52"}

# Chart accents for the dashboard
CHART_AMBER = "#B5701A"
CHART_INK = "#3A332A"
CHART_RED = "#B23A2E"
CHART_GREEN = "#3F7A52"
CHART_VIOLET = "#6E5AA8"

GLOBAL_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

  :root {
    --ink: oklch(0.26 0.012 75);
    --ink-soft: oklch(0.50 0.012 75);
    --ink-faint: oklch(0.64 0.012 75);
    --paper: oklch(0.975 0.006 80);
    --surface: oklch(0.995 0.004 85);
    --surface-2: oklch(0.955 0.009 80);
    --line: oklch(0.905 0.010 80);
    --line-strong: oklch(0.86 0.012 78);
    --amber: oklch(0.62 0.122 62);
    --amber-ink: oklch(0.50 0.115 58);
    --amber-wash: oklch(0.955 0.030 75);
    --asphalt: oklch(0.255 0.012 70);
    --danger: oklch(0.52 0.16 28);
    --ok: oklch(0.55 0.10 152);
    --shadow: 0 1px 2px rgba(36,31,24,0.04), 0 8px 24px -16px rgba(36,31,24,0.18);
    --shadow-lift: 0 2px 6px rgba(36,31,24,0.06), 0 18px 40px -22px rgba(36,31,24,0.28);
  }

  html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  }
  .stApp { background: var(--paper); }
  /* Top padding must clear Streamlit's fixed header bar, or the first element
     (nav row on pages without a masthead) gets clipped at the top. */
  .block-container { padding-top: 4.5rem; padding-left: 3rem; padding-right: 3rem; max-width: 1500px; }
  header[data-testid="stHeader"] { background: transparent; }

  /* Hide Streamlit's auto multipage sidebar — we use the top nav instead */
  section[data-testid="stSidebar"] { display: none !important; }
  [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
  [data-testid="stSidebarNav"], [data-testid="stExpandSidebarButton"] { display: none !important; }

  /* Typographic rhythm */
  h1, h2, h3, h4 { color: var(--ink); letter-spacing: -0.01em; }
  h4 { font-weight: 700; }
  p, span, label, li { color: var(--ink); }

  /* ── Masthead ─────────────────────────────────────────────────────────── */
  .masthead {
    position: relative; background: var(--asphalt);
    border-radius: 18px; padding: 2rem 2.25rem 1.85rem;
    margin-bottom: 1.4rem; overflow: hidden;
    border: 1px solid oklch(0.30 0.012 70);
  }
  .masthead::after {
    content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 3px;
    background: repeating-linear-gradient(90deg, var(--amber) 0 26px, transparent 26px 46px);
    opacity: 0.9;
  }
  .masthead .eyebrow {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.22em; text-transform: uppercase;
    color: oklch(0.72 0.09 62); margin-bottom: 0.55rem;
  }
  .masthead h1, .masthead h1 * { color: oklch(0.97 0.01 85); font-size: 1.95rem; font-weight: 800; margin: 0; line-height: 1.05; }
  .masthead p, .masthead p * { color: oklch(0.80 0.012 80); margin: 0.5rem 0 0; font-size: 0.95rem; max-width: 68ch; }
  .masthead .eyebrow, .masthead .eyebrow * { color: oklch(0.72 0.09 62); }

  /* ── Navigation (st.page_link row) ────────────────────────────────────── */
  div[data-testid="stPageLink"] a {
    border: 1px solid var(--line); border-radius: 10px; background: var(--surface);
    font-weight: 600; transition: background .15s, border-color .15s, transform .15s;
  }
  div[data-testid="stPageLink"] a:hover {
    border-color: var(--amber); background: var(--amber-wash); transform: translateY(-1px);
  }

  /* ── Buttons: flat, confident, no gradients ───────────────────────────── */
  div[data-testid="stButton"] > button,
  div[data-testid="stFormSubmitButton"] > button,
  div[data-testid="stDownloadButton"] > button {
    background: var(--amber); color: oklch(0.99 0.01 85); border: 1px solid var(--amber-ink);
    border-radius: 10px; padding: 0.55rem 1.3rem; font-weight: 700; font-size: 0.9rem;
    box-shadow: 0 1px 0 rgba(36,31,24,0.04); transition: filter .15s, transform .12s, box-shadow .15s;
    width: 100%;
  }
  div[data-testid="stButton"] > button:hover,
  div[data-testid="stFormSubmitButton"] > button:hover,
  div[data-testid="stDownloadButton"] > button:hover {
    filter: brightness(1.06); transform: translateY(-1px);
    box-shadow: 0 6px 16px -8px oklch(0.62 0.122 62 / 0.55);
  }
  div[data-testid="stButton"] > button:active { transform: translateY(0); }

  /* ── Inputs ───────────────────────────────────────────────────────────── */
  div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
    border-radius: 10px !important;
  }

  /* ── Surfaces & cards ─────────────────────────────────────────────────── */
  .result-card {
    background: var(--surface); border: 1px solid var(--line); border-radius: 14px;
    padding: 1.4rem 1.5rem; box-shadow: var(--shadow);
  }
  .report-card {
    background: var(--surface); border: 1px solid var(--line); border-radius: 16px;
    padding: 1.3rem 1.55rem; margin-bottom: 0.5rem; box-shadow: var(--shadow);
    transition: box-shadow .2s, border-color .2s;
  }
  .report-card:hover { box-shadow: var(--shadow-lift); border-color: var(--line-strong); }

  .eyebrow-sm { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-faint); }
  .meta-line { font-size: 0.74rem; color: var(--ink-faint); font-weight: 600; letter-spacing: 0.02em; }
  .loc-title { font-size: 1.06rem; font-weight: 700; color: var(--ink); margin: 0.25rem 0 0; letter-spacing: -0.01em; }

  .reporter-chip { display:inline-flex; align-items:center; gap:0.45rem; background:var(--surface-2); border:1px solid var(--line); border-radius:999px; padding:0.28rem 0.7rem 0.28rem 0.32rem; font-size:0.78rem; color:var(--ink-soft); font-weight:600; margin-top:0.5rem; }
  .reporter-avatar { width:22px; height:22px; border-radius:50%; background:var(--asphalt); color:oklch(0.97 0.01 85); display:inline-flex; align-items:center; justify-content:center; font-size:0.68rem; font-weight:700; }

  /* ── Badges & pills ───────────────────────────────────────────────────── */
  .badge { display:inline-block; padding:0.24rem 0.7rem; border-radius:999px; font-size:0.72rem; font-weight:700; letter-spacing:0.04em; text-transform:uppercase; }
  .badge-berat { background:oklch(0.96 0.03 28); color:var(--danger); border:1px solid oklch(0.86 0.06 28); }
  .badge-sedang { background:var(--amber-wash); color:var(--amber-ink); border:1px solid oklch(0.86 0.06 70); }
  .badge-ringan { background:oklch(0.95 0.03 152); color:var(--ok); border:1px solid oklch(0.85 0.05 152); }

  .status-badge { display:inline-block; padding:0.3rem 0.8rem; border-radius:999px; font-size:0.68rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; }
  .prio-pill { display:inline-flex; align-items:center; gap:0.3rem; padding:0.24rem 0.62rem; border-radius:999px; font-size:0.7rem; font-weight:700; letter-spacing:0.02em; }

  /* ── Detection grid ───────────────────────────────────────────────────── */
  .deteksi-row { display:grid; grid-template-columns:repeat(4, 1fr); gap:0.5rem 1.25rem; background:var(--surface-2); border:1px solid var(--line); border-radius:12px; padding:0.85rem 1.1rem; margin:0.9rem 0 0.7rem; }
  .deteksi-item { display:flex; flex-direction:column; gap:0.15rem; }
  .deteksi-label { color:var(--ink-faint); font-size:0.66rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:700; }
  .deteksi-val { color:var(--ink); font-weight:700; font-size:0.9rem; }

  /* ── RAB display ──────────────────────────────────────────────────────── */
  .rab-bar { background:var(--surface-2); border:1px solid var(--line-strong); border-radius:12px; padding:0.7rem 1.1rem; display:flex; justify-content:space-between; align-items:center; margin:0.5rem 0; }
  .rab-bar .label { color:var(--ink-soft); font-size:0.78rem; font-weight:600; }
  .rab-bar .amount { font-weight:800; font-size:1.12rem; color:var(--ink); letter-spacing:-0.01em; font-variant-numeric: tabular-nums; }

  .rab-total { background:var(--asphalt); border-radius:14px; padding:1.15rem 1.4rem; text-align:center; margin-top:0.9rem; }
  .rab-total .label { font-size:0.7rem; color:oklch(0.74 0.09 62); letter-spacing:0.14em; text-transform:uppercase; font-weight:700; }
  .rab-total .amount { font-size:1.7rem; font-weight:800; color:oklch(0.97 0.01 85); letter-spacing:-0.01em; font-variant-numeric: tabular-nums; }
  .rab-total .sub { font-size:0.72rem; color:oklch(0.74 0.012 80); margin-top:0.3rem; }

  .breakdown-row { display:flex; justify-content:space-between; padding:0.5rem 0; border-bottom:1px solid var(--line); font-size:0.86rem; }
  .breakdown-row:last-child { border-bottom:none; }
  .breakdown-item { color:var(--ink-soft); }
  .breakdown-amount { color:var(--ink); font-weight:700; font-variant-numeric: tabular-nums; }

  /* ── SLA meter ────────────────────────────────────────────────────────── */
  .sla-head { font-size:0.74rem; color:var(--ink-soft); margin-bottom:0.3rem; display:flex; justify-content:space-between; }
  .sla-track { background:var(--surface-2); border:1px solid var(--line); border-radius:999px; height:7px; overflow:hidden; }
  .sla-fill { height:100%; border-radius:999px; }

  /* ── KPI strip (dashboard) ────────────────────────────────────────────── */
  .kpi { background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:1.05rem 1.2rem; box-shadow:var(--shadow); height:100%; }
  .kpi .lbl { font-size:0.68rem; color:var(--ink-faint); text-transform:uppercase; letter-spacing:0.09em; font-weight:700; }
  .kpi .num { font-size:1.75rem; font-weight:800; color:var(--ink); line-height:1.05; margin-top:0.35rem; letter-spacing:-0.02em; font-variant-numeric: tabular-nums; }
  .kpi .sub { font-size:0.74rem; color:var(--ink-soft); margin-top:0.2rem; }
  .kpi--accent { border-top:3px solid var(--amber); }
  .kpi--danger { border-top:3px solid var(--danger); }
  .kpi--ok { border-top:3px solid var(--ok); }

  .assigned-banner { background:oklch(0.96 0.03 152); border:1px solid oklch(0.85 0.05 152); border-radius:10px; padding:0.7rem 1rem; font-size:0.82rem; margin:0.6rem 0 0; }
  .assigned-banner .label { color:var(--ok); font-weight:700; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.06em; }
  .assigned-banner .value { color:oklch(0.42 0.10 152); font-weight:700; }

  .progress-item { padding:0.15rem 0 0.6rem; border-bottom:1px solid var(--line); margin-bottom:0.6rem; }
  .progress-item:last-child { border-bottom:none; margin-bottom:0; }
  .progress-time { font-size:0.7rem; color:var(--ink-faint); font-weight:600; }
  .progress-uploader { font-size:0.82rem; font-weight:700; color:var(--ink); margin-top:0.1rem; }
  .progress-desc { font-size:0.84rem; color:var(--ink-soft); margin-top:0.2rem; line-height:1.5; }

  .success-banner { background:oklch(0.95 0.04 152); border:1px solid oklch(0.80 0.07 152); border-radius:12px; padding:0.9rem 1.3rem; color:oklch(0.40 0.10 152); font-weight:700; margin:1rem 0; }
  .demo-pill { display:inline-block; background:var(--amber-wash); color:var(--amber-ink); border:1px solid oklch(0.86 0.06 70); border-radius:999px; padding:0.22rem 0.7rem; font-size:0.72rem; font-weight:700; }

  .note { font-size:0.82rem; color:var(--ink-soft); font-style:italic; line-height:1.5; }
  hr { border-color: var(--line) !important; }

  /* ── Avatars ──────────────────────────────────────────────────────────── */
  .avatar { display:inline-flex; align-items:center; justify-content:center; border-radius:50%; color:#fff; font-weight:800; flex-shrink:0; box-shadow: inset 0 0 0 2px rgba(255,255,255,0.18); }

  /* ── Auth gate ────────────────────────────────────────────────────────── */
  .auth-hero { background:var(--asphalt); border-radius:20px; padding:2.4rem 2.2rem; position:relative; overflow:hidden; }
  .auth-hero::after { content:""; position:absolute; left:0; right:0; bottom:0; height:4px; background:repeating-linear-gradient(90deg, var(--amber) 0 26px, transparent 26px 46px); }
  .auth-hero .eyebrow { font-size:0.7rem; font-weight:700; letter-spacing:0.22em; text-transform:uppercase; color:oklch(0.72 0.09 62); }
  .auth-hero h1, .auth-hero h1 * { color:oklch(0.97 0.01 85); font-size:2.4rem; font-weight:800; margin:0.4rem 0 0; line-height:1.05; }
  .auth-hero p, .auth-hero p * { color:oklch(0.80 0.012 80); margin:0.7rem 0 0; font-size:0.95rem; line-height:1.55; }
  .auth-feature { display:flex; gap:0.6rem; align-items:flex-start; margin-top:1rem; }
  .auth-feature .ic { font-size:1.05rem; }
  .auth-feature .tx { color:oklch(0.86 0.012 80); font-size:0.86rem; line-height:1.4; }
  .auth-feature .tx b { color:oklch(0.95 0.01 85); }

  /* ── User menu (nav) ──────────────────────────────────────────────────── */
  .user-chip { display:flex; align-items:center; gap:0.6rem; background:var(--surface); border:1px solid var(--line); border-radius:999px; padding:0.3rem 0.85rem 0.3rem 0.35rem; }
  .user-chip .nm { font-weight:700; color:var(--ink); font-size:0.86rem; line-height:1; }
  .user-chip .rl { font-size:0.68rem; color:var(--ink-faint); text-transform:uppercase; letter-spacing:0.06em; font-weight:700; }

  /* ── Profile header ───────────────────────────────────────────────────── */
  .profile-head { background:var(--asphalt); border-radius:20px; padding:1.9rem 2rem 1.7rem; position:relative; overflow:hidden; }
  .profile-head::after { content:""; position:absolute; left:0; right:0; bottom:0; height:4px; background:repeating-linear-gradient(90deg, var(--amber) 0 26px, transparent 26px 46px); }
  .profile-head .pname, .profile-head .pname * { color:oklch(0.97 0.01 85); font-size:1.6rem; font-weight:800; margin:0; }
  .profile-head .phandle { color:oklch(0.72 0.09 62); font-weight:700; font-size:0.85rem; }
  .profile-head .pbio, .profile-head .pbio * { color:oklch(0.82 0.012 80); font-size:0.9rem; margin:0.5rem 0 0; max-width:60ch; line-height:1.5; }
  .pstats { display:flex; gap:1.8rem; margin-top:1.1rem; }
  .pstat .n { color:oklch(0.97 0.01 85); font-weight:800; font-size:1.2rem; font-variant-numeric:tabular-nums; }
  .pstat .l { color:oklch(0.72 0.012 80); font-size:0.7rem; text-transform:uppercase; letter-spacing:0.07em; font-weight:700; }

  /* ── Comments ─────────────────────────────────────────────────────────── */
  .comment { display:flex; gap:0.65rem; padding:0.6rem 0; border-bottom:1px solid var(--line); }
  .comment:last-child { border-bottom:none; }
  .comment .body { flex:1; }
  .comment .who { font-weight:700; color:var(--ink); font-size:0.84rem; }
  .comment .when { color:var(--ink-faint); font-size:0.72rem; font-weight:600; }
  .comment .tx { color:var(--ink-soft); font-size:0.86rem; margin-top:0.15rem; line-height:1.5; }

  /* ── Engagement bar ───────────────────────────────────────────────────── */
  .engage { display:flex; gap:1.2rem; align-items:center; padding:0.2rem 0; }
  .engage .it { display:inline-flex; align-items:center; gap:0.35rem; color:var(--ink-soft); font-size:0.82rem; font-weight:600; }
  .engage .it b { color:var(--ink); font-variant-numeric:tabular-nums; }

  .timeline-item { display:flex; gap:0.7rem; padding:0.55rem 0; border-bottom:1px solid var(--line); }
  .timeline-item:last-child { border-bottom:none; }
  .timeline-item .ic { width:30px; height:30px; border-radius:9px; display:inline-flex; align-items:center; justify-content:center; background:var(--surface-2); border:1px solid var(--line); font-size:0.9rem; flex-shrink:0; }
  .timeline-item .tx { font-size:0.86rem; color:var(--ink); }
  .timeline-item .tx .mut { color:var(--ink-faint); font-size:0.74rem; font-weight:600; }

  @media (max-width: 720px) {
    .deteksi-row { grid-template-columns: repeat(2, 1fr); }
    .pstats { gap:1.1rem; flex-wrap:wrap; }
  }
</style>
"""


def avatar_html(name: str, color: str = "#B5701A", size: int = 34) -> str:
    """Return an inline avatar bubble with the name's initial."""
    initial = (name.strip()[0].upper() if name and name.strip() else "?")
    fs = round(size * 0.42)
    return (
        f'<span class="avatar" style="width:{size}px;height:{size}px;'
        f'background:{color};font-size:{fs}px;">{initial}</span>'
    )


def inject_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'''<div class="masthead">
              <div class="eyebrow">{eyebrow}</div>
              <h1>{title}</h1>
              <p>{subtitle}</p>
            </div>''',
        unsafe_allow_html=True,
    )


def render_nav(active: str = "") -> None:
    """Top navigation shared across all pages."""
    c1, c2, c3, _ = st.columns([1, 1, 1, 3])
    with c1:
        st.page_link("app.py", label="Laporkan", icon="📋", use_container_width=True)
    with c2:
        st.page_link("pages/feed.py", label="Feed Komunitas", icon="🗺️", use_container_width=True)
    with c3:
        st.page_link("pages/dashboard.py", label="Dashboard", icon="📊", use_container_width=True)
