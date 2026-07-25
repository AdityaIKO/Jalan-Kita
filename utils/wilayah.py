"""Indonesian administrative regions: provinsi -> kabupaten/kota -> kecamatan ->
kelurahan/desa, for the cascading location picker and structured search.

Data is bundled under ``data/wilayah/`` as four small CSVs (Kemendagri codes),
so lookups are fully offline with no external service. Codes nest by prefix
(province ``11`` -> regency ``1101`` -> district ``1101010`` -> village
``1101010001``), which makes each cascade level a cheap dict lookup.

Framework-agnostic: uses ``functools.lru_cache`` rather than Streamlit caching so
it can be imported and tested anywhere.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

WILAYAH_DIR = Path(__file__).parent.parent / "data" / "wilayah"

# Acronyms that must stay uppercase after title-casing display names.
_KEEP_UPPER = {"Dki Jakarta": "DKI Jakarta", "Di Yogyakarta": "DI Yogyakarta"}


def _display(name: str) -> str:
    out = name.strip().title()
    for wrong, right in _KEEP_UPPER.items():
        out = out.replace(wrong, right)
    return out


def _read(fname: str) -> list[tuple]:
    path = WILAYAH_DIR / fname
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [tuple(row) for row in csv.reader(f) if row]


# ── Cached indexes (built once per process) ─────────────────────────────────────
@lru_cache(maxsize=1)
def _provinces() -> list[tuple[str, str]]:
    # rows: code, name
    rows = [(c, _display(n)) for c, n in _read("provinces.csv")]
    return sorted(rows, key=lambda r: r[1])


@lru_cache(maxsize=1)
def _regencies_by_prov() -> dict:
    idx: dict[str, list] = {}
    for code, prov_code, name in _read("regencies.csv"):
        idx.setdefault(prov_code, []).append((code, _display(name)))
    for v in idx.values():
        v.sort(key=lambda r: r[1])
    return idx


@lru_cache(maxsize=1)
def _districts_by_reg() -> dict:
    idx: dict[str, list] = {}
    for code, reg_code, name in _read("districts.csv"):
        idx.setdefault(reg_code, []).append((code, _display(name)))
    for v in idx.values():
        v.sort(key=lambda r: r[1])
    return idx


@lru_cache(maxsize=1)
def _villages_by_dist() -> dict:
    idx: dict[str, list] = {}
    for code, dist_code, name in _read("villages.csv"):
        idx.setdefault(dist_code, []).append((code, _display(name)))
    for v in idx.values():
        v.sort(key=lambda r: r[1])
    return idx


# ── Public cascade API ──────────────────────────────────────────────────────────
def available() -> bool:
    """True when the bundled dataset is present."""
    return bool(_provinces())


def provinces() -> list[tuple[str, str]]:
    """List of ``(code, name)`` for all provinces."""
    return _provinces()


def regencies(province_code: str) -> list[tuple[str, str]]:
    return _regencies_by_prov().get(province_code, [])


def districts(regency_code: str) -> list[tuple[str, str]]:
    return _districts_by_reg().get(regency_code, [])


def villages(district_code: str) -> list[tuple[str, str]]:
    return _villages_by_dist().get(district_code, [])
