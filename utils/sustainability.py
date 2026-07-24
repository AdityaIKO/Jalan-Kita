"""Sustainability intelligence: the layer that ties road repair to climate action.

This is JalanKita's answer to the theme "AI for Sustainable Future". Three
capabilities, all derived from the damage the AI already detects, so they add
value without extra user input:

1. Environmental cost of inaction  (:func:`estimate_impact`)
   A damaged road makes vehicles brake, re-accelerate, swerve, and detour, which
   burns extra fuel and emits extra CO2 every single day it stays broken. We turn
   the detected severity into a daily and annual estimate, plus intuitive
   equivalences (trees, fuel) that a non-technical judge can grasp in seconds.

2. Eco-material recommendation  (:func:`recommend_material`)
   For each damage type we suggest a lower-carbon repair method (recycled asphalt,
   plastic-waste modified asphalt, cold recycling) and the emissions it avoids
   versus conventional hot-mix.

3. SDG mapping  (:func:`sdg_tags`)
   Each report is linked to the UN Sustainable Development Goals it advances, so
   impact can be reported in the language funders and government use.

Every figure is an engineering estimate built from published emission factors and
clearly stated assumptions (:data:`ASSUMPTIONS`); the goal is a transparent,
defensible order-of-magnitude, not false precision.
"""
from __future__ import annotations

from datetime import datetime

# ── Transparent assumptions (surfaced in the UI so nothing is a black box) ──────
# Deliberately conservative so every headline figure is defensible as a lower-
# to-mid estimate rather than a best case.
ASSUMPTIONS = {
    "traffic_per_day": 2000,      # vehicles/day on a typical local/collector road
    "co2_kg_per_litre": 2.4,      # blended petrol/diesel fleet emission factor
    "tree_kg_co2_per_year": 21.0, # CO2 a mature tree absorbs per year
    "fuel_price_rp": 13000,       # Rp/litre, for the wasted-fuel cost figure
}

# Extra litres of fuel burned per affected vehicle-pass, by severity. Reflects a
# single brake / slow / re-accelerate cycle (roughly 4-12 mL), kept conservative.
_EXTRA_FUEL_PER_VEHICLE = {"Berat": 0.010, "Sedang": 0.004, "Ringan": 0.0015}
_DEFAULT_FUEL = 0.004

# Share of daily traffic actually slowed by the damage, scaled down so a single
# report never overclaims the whole road's flow.
_TRAFFIC_SHARE = {"Berat": 0.35, "Sedang": 0.25, "Ringan": 0.15}
_DEFAULT_SHARE = 0.25


def _days_open(report: dict) -> int:
    ts = report.get("timestamp", "")
    try:
        return max(0, (datetime.now() - datetime.fromisoformat(ts)).days)
    except Exception:
        return 0


def estimate_impact(report: dict, traffic_per_day: int | None = None) -> dict:
    """Estimate the environmental cost of leaving this damage unrepaired.

    Returns daily and annual fuel/CO2 figures plus friendly equivalences. If the
    report is resolved, the ongoing daily cost becomes the amount now *avoided*.
    """
    severity = report.get("deteksi", {}).get("tingkat_keparahan", "Sedang")
    traffic = traffic_per_day or ASSUMPTIONS["traffic_per_day"]

    per_vehicle = _EXTRA_FUEL_PER_VEHICLE.get(severity, _DEFAULT_FUEL)
    share = _TRAFFIC_SHARE.get(severity, _DEFAULT_SHARE)
    affected_vehicles = traffic * share

    fuel_day = affected_vehicles * per_vehicle           # litres/day
    co2_day = fuel_day * ASSUMPTIONS["co2_kg_per_litre"]  # kg/day
    co2_year = co2_day * 365
    fuel_year = fuel_day * 365

    days = _days_open(report)
    resolved = report.get("status") == "Selesai"

    trees_year = co2_year / ASSUMPTIONS["tree_kg_co2_per_year"]
    fuel_cost_year = fuel_year * ASSUMPTIONS["fuel_price_rp"]

    return {
        "severity": severity,
        "traffic_per_day": traffic,
        "fuel_day_litre": round(fuel_day, 1),
        "co2_day_kg": round(co2_day, 1),
        "fuel_year_litre": round(fuel_year),
        "co2_year_kg": round(co2_year),
        "co2_accumulated_kg": round(co2_day * days) if not resolved else round(co2_day * days),
        "days_open": days,
        "trees_equivalent": round(trees_year),
        "fuel_cost_year_rp": round(fuel_cost_year),
        "resolved": resolved,
    }


# ── Eco-material recommendation ─────────────────────────────────────────────────
# type keyword -> (method, description, CO2 reduction vs hot-mix, note)
_MATERIALS = {
    "lubang": {
        "metode": "Aspal Campur Limbah Plastik (Plastic-Modified Asphalt)",
        "deskripsi": "Tambalan aspal yang mencampurkan cacahan limbah plastik sebagai pengganti sebagian bitumen.",
        "reduksi_co2": 0.30,
        "catatan": "Menyerap limbah plastik dari lingkungan sekaligus menambah ketahanan tambalan.",
    },
    "retak buaya": {
        "metode": "Cold In-Place Recycling (Daur Ulang Perkerasan di Tempat)",
        "deskripsi": "Perkerasan lama dihancurkan dan dipakai ulang sebagai material dasar tanpa dibawa ke AMP.",
        "reduksi_co2": 0.45,
        "catatan": "Memangkas transport material baru dan emisi pemanasan aspal panas.",
    },
    "ambles": {
        "metode": "Reclaimed Asphalt Pavement (RAP) + Cold Mix",
        "deskripsi": "Agregat aspal daur ulang dipadatkan dingin untuk memperbaiki area ambles.",
        "reduksi_co2": 0.40,
        "catatan": "Menggunakan kembali material eksisting, mengurangi galian tambang baru.",
    },
    "retak": {
        "metode": "Crack Sealing dengan Sealant Rendah Emisi",
        "deskripsi": "Retak ditutup sealant elastis sebelum meluas, menghindari overlay penuh.",
        "reduksi_co2": 0.60,
        "catatan": "Perawatan preventif memakai material minimal dibanding pengaspalan ulang.",
    },
    "pengelupasan": {
        "metode": "Micro-Surfacing / Slurry Seal",
        "deskripsi": "Lapis tipis emulsi dingin menutup permukaan yang mengelupas.",
        "reduksi_co2": 0.50,
        "catatan": "Proses dingin hemat energi, memperpanjang usia jalan tanpa bongkar total.",
    },
}
_DEFAULT_MATERIAL = {
    "metode": "Cold Mix Asphalt (Aspal Campur Dingin)",
    "deskripsi": "Campuran aspal emulsi yang diproses tanpa pemanasan tinggi.",
    "reduksi_co2": 0.35,
    "catatan": "Alternatif rendah emisi untuk perbaikan cepat berbagai jenis kerusakan.",
}


def recommend_material(damage_type: str) -> dict:
    """Suggest a lower-carbon repair method for a detected damage type."""
    key = (damage_type or "").lower()
    for token, rec in _MATERIALS.items():
        if token in key:
            return {**rec, "reduksi_persen": round(rec["reduksi_co2"] * 100)}
    return {**_DEFAULT_MATERIAL, "reduksi_persen": round(_DEFAULT_MATERIAL["reduksi_co2"] * 100)}


# ── SDG mapping ─────────────────────────────────────────────────────────────────
_SDG = {
    3:  {"nama": "Kehidupan Sehat & Sejahtera", "warna": "#4C9F38"},
    9:  {"nama": "Industri, Inovasi & Infrastruktur", "warna": "#FD6925"},
    11: {"nama": "Kota & Permukiman Berkelanjutan", "warna": "#FD9D24"},
    12: {"nama": "Konsumsi & Produksi Bertanggung Jawab", "warna": "#BF8B2E"},
    13: {"nama": "Penanganan Perubahan Iklim", "warna": "#3F7E44"},
}


def sdg_tags(report: dict) -> list[dict]:
    """Return the SDGs a report advances, based on severity and repair choices."""
    goals = [9, 11, 13]  # infrastructure, safe mobility, emissions cut: always
    severity = report.get("deteksi", {}).get("tingkat_keparahan", "")
    if severity == "Berat":
        goals.insert(0, 3)  # a severe hazard is first a safety/health issue
    goals.append(12)        # eco-material recommendation supports responsible use
    seen = []
    for g in goals:
        if g not in seen:
            seen.append(g)
    return [{"nomor": g, **_SDG[g]} for g in seen]


# ── Aggregations for the dashboard ──────────────────────────────────────────────
def aggregate_impact(reports: list) -> dict:
    """Sum environmental figures across reports, split by open vs resolved."""
    open_reports = [r for r in reports if r.get("status") != "Selesai"]
    resolved = [r for r in reports if r.get("status") == "Selesai"]

    co2_year_open = sum(estimate_impact(r)["co2_year_kg"] for r in open_reports)
    co2_year_saved = sum(estimate_impact(r)["co2_year_kg"] for r in resolved)
    fuel_year_open = sum(estimate_impact(r)["fuel_year_litre"] for r in open_reports)
    trees_open = round(co2_year_open / ASSUMPTIONS["tree_kg_co2_per_year"]) if co2_year_open else 0

    return {
        "co2_year_open_kg": round(co2_year_open),
        "co2_year_open_tonnes": round(co2_year_open / 1000, 1),
        "co2_year_saved_kg": round(co2_year_saved),
        "co2_year_saved_tonnes": round(co2_year_saved / 1000, 1),
        "fuel_year_open_litre": round(fuel_year_open),
        "trees_to_offset": trees_open,
        "open_count": len(open_reports),
        "resolved_count": len(resolved),
    }


def sdg_summary(reports: list) -> list[dict]:
    """Count how many reports advance each SDG, for the dashboard."""
    tally: dict[int, int] = {}
    for r in reports:
        for tag in sdg_tags(r):
            tally[tag["nomor"]] = tally.get(tag["nomor"], 0) + 1
    return [
        {"nomor": g, "jumlah": tally[g], **_SDG[g]}
        for g in sorted(tally, key=lambda x: tally[x], reverse=True)
    ]
