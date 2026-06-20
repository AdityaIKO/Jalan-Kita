"""Aggregations for the analytics dashboard.

Pure functions over the report list — no Streamlit imports — so they're easy to
reason about and reuse. pandas/altair ship with Streamlit, so no new deps.
"""
from __future__ import annotations

from collections import Counter

import pandas as pd

from utils.storage import get_sla_info, priority_score, priority_label, reports_to_records


def kpis(reports: list) -> dict:
    total = len(reports)
    selesai = sum(1 for r in reports if r.get("status") == "Selesai")
    open_reports = [r for r in reports if r.get("status") != "Selesai"]
    overdue = sum(1 for r in open_reports if get_sla_info(r)["lewat"])
    total_rab = sum(r.get("rab", {}).get("total", 0) for r in reports)
    outstanding_rab = sum(r.get("rab", {}).get("total", 0) for r in open_reports)
    likes = sum(r.get("likes", 0) for r in reports)

    # SLA compliance = resolved or still within target / total.
    on_track = sum(1 for r in reports if not get_sla_info(r)["lewat"])
    compliance = round(100 * on_track / total) if total else 0
    resolution = round(100 * selesai / total) if total else 0

    return {
        "total": total,
        "selesai": selesai,
        "open": len(open_reports),
        "overdue": overdue,
        "total_rab": total_rab,
        "outstanding_rab": outstanding_rab,
        "likes": likes,
        "compliance": compliance,
        "resolution": resolution,
    }


def _counter_df(counter: Counter, key_name: str, val_name: str = "Jumlah") -> pd.DataFrame:
    if not counter:
        return pd.DataFrame({key_name: [], val_name: []})
    items = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)
    return pd.DataFrame({key_name: [k for k, _ in items], val_name: [v for _, v in items]})


def by_status(reports: list) -> pd.DataFrame:
    return _counter_df(Counter(r.get("status", "?") for r in reports), "Status")


def by_severity(reports: list) -> pd.DataFrame:
    c = Counter(r.get("deteksi", {}).get("tingkat_keparahan", "?") for r in reports)
    return _counter_df(c, "Keparahan")


def by_type(reports: list) -> pd.DataFrame:
    c = Counter(r.get("deteksi", {}).get("tipe_kerusakan", "?") for r in reports)
    return _counter_df(c, "Tipe Kerusakan")


def by_priority(reports: list) -> pd.DataFrame:
    c = Counter(priority_label(priority_score(r)) for r in reports)
    # Keep a meaningful order rather than count order for priority.
    order = ["Kritis", "Tinggi", "Sedang", "Rendah"]
    return pd.DataFrame({
        "Prioritas": [p for p in order if c.get(p)],
        "Jumlah": [c[p] for p in order if c.get(p)],
    })


def rab_by_provinsi(reports: list) -> pd.DataFrame:
    agg: dict[str, int] = {}
    for r in reports:
        prov = r.get("provinsi") or "Lainnya"
        agg[prov] = agg.get(prov, 0) + r.get("rab", {}).get("total", 0)
    items = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return pd.DataFrame({
        "Provinsi": [k for k, _ in items],
        "Estimasi RAB": [v for _, v in items],
    })


def map_df(reports: list) -> pd.DataFrame:
    """lat/lon DataFrame for st.map, only for placeable reports."""
    from utils.geo import report_coords
    rows = []
    for r in reports:
        coords = report_coords(r)
        if coords:
            rows.append({"lat": coords[0], "lon": coords[1]})
    return pd.DataFrame(rows) if rows else pd.DataFrame({"lat": [], "lon": []})


def table_df(reports: list) -> pd.DataFrame:
    return pd.DataFrame(reports_to_records(reports))
