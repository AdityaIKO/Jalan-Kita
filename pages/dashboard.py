import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))

from utils.storage import load_reports, format_rupiah, reports_to_csv
from utils.ui import (
    inject_css, render_header,
    CHART_AMBER, CHART_INK, CHART_RED, CHART_GREEN, CHART_VIOLET,
)
from utils import analytics, auth, sustainability

st.set_page_config(
    page_title="JalanKita · Dashboard",
    page_icon="📊", layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
auth.require_auth()
render_header(
    "Intelijen Operasional · Dinas PU & CSR",
    "📊 Dashboard Analitik",
    "Ringkasan kinerja penanganan jalan rusak: penyelesaian, kepatuhan SLA, kebutuhan anggaran, dan sebaran prioritas.",
)
auth.render_topbar("dashboard")
st.divider()

reports = load_reports()

if not reports:
    st.info("Belum ada laporan. Buat laporan pertama di halaman 📋 Laporkan.")
    st.stop()

k = analytics.kpis(reports)

# ── KPI cards ──────────────────────────────────────────────────────────────────
def kpi(col, num, label, sub="", mod=""):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    col.markdown(
        f'<div class="kpi {mod}"><div class="lbl">{label}</div><div class="num">{num}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )

r1 = st.columns(4)
kpi(r1[0], k["total"], "Total Laporan", f'{k["open"]} masih aktif', "kpi--accent")
kpi(r1[1], f'{k["resolution"]}%', "Tingkat Penyelesaian", f'{k["selesai"]} selesai', "kpi--ok")
kpi(r1[2], k["overdue"], "Melewati SLA", "perlu tindakan segera" if k["overdue"] else "semua on-track",
    "kpi--danger" if k["overdue"] else "kpi--ok")
kpi(r1[3], f'{k["compliance"]}%', "Kepatuhan SLA")

st.markdown("<br>", unsafe_allow_html=True)
r2 = st.columns(3)
kpi(r2[0], format_rupiah(k["total_rab"]), "Total Estimasi RAB", "seluruh laporan")
kpi(r2[1], format_rupiah(k["outstanding_rab"]), "RAB Belum Tertangani", "laporan aktif", "kpi--accent")
kpi(r2[2], k["likes"], "Total Dukungan Warga", "akumulasi like")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    st.markdown("##### Distribusi Status")
    df = analytics.by_status(reports)
    st.bar_chart(df, x="Status", y="Jumlah", color=CHART_INK, height=260)
with c2:
    st.markdown("##### Tingkat Keparahan")
    df = analytics.by_severity(reports)
    st.bar_chart(df, x="Keparahan", y="Jumlah", color=CHART_RED, height=260)

c3, c4 = st.columns(2)
with c3:
    st.markdown("##### Prioritas Penanganan")
    df = analytics.by_priority(reports)
    st.bar_chart(df, x="Prioritas", y="Jumlah", color=CHART_AMBER, height=260)
with c4:
    st.markdown("##### Tipe Kerusakan Terbanyak")
    df = analytics.by_type(reports)
    st.bar_chart(df, x="Tipe Kerusakan", y="Jumlah", color=CHART_VIOLET, height=260)

st.markdown("##### Estimasi RAB per Provinsi")
df_rab = analytics.rab_by_provinsi(reports)
st.bar_chart(df_rab, x="Provinsi", y="Estimasi RAB", color=CHART_GREEN, height=300)

# ── Dampak Keberlanjutan (AI for Sustainable Future) ───────────────────────────
st.divider()
st.markdown("### 🌱 Dampak Keberlanjutan")
st.caption(
    "Menerjemahkan kerusakan jalan menjadi dampak iklim: emisi CO₂ dan bahan bakar "
    "yang terbuang selama jalan dibiarkan rusak, serta emisi yang dihindari setelah diperbaiki."
)

imp = sustainability.aggregate_impact(reports)
s1 = st.columns(4)
def _eco_kpi(col, num, label, sub, mod=""):
    col.markdown(
        f'<div class="kpi {mod}"><div class="lbl">{label}</div><div class="num">{num}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )
_eco_kpi(s1[0], f'{imp["co2_year_open_tonnes"]:,} t'.replace(",", "."), "CO₂ Terbuang / Tahun",
         f'{imp["open_count"]} laporan aktif', "kpi--danger")
_eco_kpi(s1[1], f'{imp["co2_year_saved_tonnes"]:,} t'.replace(",", "."), "CO₂ Dihindari / Tahun",
         f'{imp["resolved_count"]} laporan selesai', "kpi--ok")
_eco_kpi(s1[2], f'{imp["fuel_year_open_litre"]:,} L'.replace(",", "."), "BBM Terbuang / Tahun",
         "akibat jalan rusak aktif", "kpi--accent")
_eco_kpi(s1[3], f'{imp["trees_to_offset"]:,}'.replace(",", "."), "Pohon untuk Offset",
         "menyerap CO₂ setahun")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("##### Kontribusi terhadap Tujuan Pembangunan Berkelanjutan (SDGs)")
sdg_rows = sustainability.sdg_summary(reports)
if sdg_rows:
    cols = st.columns(len(sdg_rows))
    for col, s in zip(cols, sdg_rows):
        col.markdown(
            f'<div class="sdg-tile" style="background:{s["warna"]}">'
            f'<div class="n">{s["jumlah"]}</div>'
            f'<div class="g">SDG {s["nomor"]}</div>'
            f'<div class="c">{s["nama"]}</div></div>',
            unsafe_allow_html=True,
        )
st.caption(
    f'Asumsi: {sustainability.ASSUMPTIONS["traffic_per_day"]:,} kendaraan/hari per titik, '
    f'faktor emisi {sustainability.ASSUMPTIONS["co2_kg_per_litre"]} kg CO₂/liter, '
    f'1 pohon menyerap {sustainability.ASSUMPTIONS["tree_kg_co2_per_year"]:.0f} kg CO₂/tahun.'.replace(",", ".")
)

# ── Cara skor prioritas dihitung ───────────────────────────────────────────────
with st.expander("🚦 Bagaimana skor prioritas dihitung?"):
    st.markdown(
        """
Setiap laporan diberi **skor 0 sampai 100** yang menggabungkan tiga faktor, lalu dipetakan ke label:

| Faktor | Bobot |
|---|---|
| **Tingkat keparahan** | Berat +50 · Sedang +30 · Ringan +15 |
| **Tekanan SLA** | Melewati SLA +30 · ≥70% waktu terpakai +18 · ≥40% +8 |
| **Dukungan publik** | +1 per *like* (maksimal +20) |

Laporan berstatus **Selesai** otomatis bernilai 0.

**Label:** `≥70` Kritis · `≥45` Tinggi · `≥25` Sedang · lainnya Rendah.
        """
    )

st.divider()

# ── Detail table + export ──────────────────────────────────────────────────────
st.markdown("##### 📋 Tabel Detail Laporan")
table = analytics.table_df(reports)
st.dataframe(
    table[["id", "lokasi", "provinsi", "keparahan", "rab_total", "status",
           "prioritas", "skor_prioritas", "lewat_sla", "likes"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "rab_total": st.column_config.NumberColumn("RAB (Rp)", format="%d"),
        "skor_prioritas": st.column_config.ProgressColumn(
            "Skor", min_value=0, max_value=100, format="%d"
        ),
    },
)

st.download_button(
    "⬇️ Ekspor Semua Laporan (CSV)",
    data=reports_to_csv(reports),
    file_name="jalankita_dashboard.csv",
    mime="text/csv",
)
