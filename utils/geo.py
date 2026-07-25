"""Lightweight geolocation helpers for the map view.

We avoid any external geocoding API. Each report is placed on the map using
explicit lat/lon if the reporter supplied them, otherwise the centroid of the
detected province with a small deterministic jitter so multiple reports in the
same province don't stack on a single pixel.
"""
from __future__ import annotations

import hashlib

# Approximate province centroids (lat, lon).
PROVINSI_CENTROID = {
    "Aceh": (4.70, 96.70),
    "Sumatera Utara": (2.50, 99.00),
    "Sumatera Barat": (-0.70, 100.80),
    "Riau": (0.50, 101.70),
    "Kepulauan Riau": (0.90, 104.50),
    "Jambi": (-1.60, 103.00),
    "Bengkulu": (-3.50, 102.30),
    "Sumatera Selatan": (-3.30, 104.00),
    "Kepulauan Bangka Belitung": (-2.70, 106.40),
    "Lampung": (-4.80, 105.00),
    "DKI Jakarta": (-6.20, 106.84),
    "Jawa Barat": (-6.90, 107.60),
    "Banten": (-6.40, 106.10),
    "Jawa Tengah": (-7.30, 110.00),
    "DI Yogyakarta": (-7.80, 110.40),
    "Jawa Timur": (-7.50, 112.50),
    "Bali": (-8.40, 115.20),
    "Nusa Tenggara Barat": (-8.70, 117.40),
    "Nusa Tenggara Timur": (-8.70, 121.10),
    "Kalimantan Barat": (0.00, 109.30),
    "Kalimantan Tengah": (-1.70, 113.40),
    "Kalimantan Selatan": (-3.10, 115.30),
    "Kalimantan Timur": (0.50, 116.40),
    "Kalimantan Utara": (3.10, 116.00),
    "Sulawesi Utara": (1.40, 124.80),
    "Gorontalo": (0.70, 122.40),
    "Sulawesi Tengah": (-1.40, 121.40),
    "Sulawesi Barat": (-2.80, 119.20),
    "Sulawesi Selatan": (-4.00, 119.90),
    "Sulawesi Tenggara": (-4.10, 122.20),
    "Maluku": (-3.20, 129.00),
    "Maluku Utara": (1.60, 127.80),
    "Papua Barat": (-1.30, 133.20),
    "Papua Barat Daya": (-0.90, 131.30),
    "Papua": (-4.30, 138.10),
    "Papua Pegunungan": (-4.00, 138.90),
    "Papua Tengah": (-3.90, 136.50),
    "Papua Selatan": (-7.20, 139.60),
}

# Fallback: geographic centre of Indonesia.
DEFAULT_CENTER = (-2.50, 118.00)

# National bounding box (with a small margin) used to keep both the map view and
# any tagged coordinate inside Indonesia. Spans Sabang (Aceh) to Merauke (Papua).
ID_LAT_MIN, ID_LAT_MAX = -11.5, 6.5
ID_LON_MIN, ID_LON_MAX = 94.5, 141.5
# View bounds for the map (a touch tighter than the hard limits above).
ID_VIEW = {"lat_min": -11.0, "lat_max": 6.1, "lon_min": 95.0, "lon_max": 141.0}


def in_indonesia(lat, lon) -> bool:
    """True when a coordinate falls within Indonesia's bounding box."""
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return False
    return ID_LAT_MIN <= lat <= ID_LAT_MAX and ID_LON_MIN <= lon <= ID_LON_MAX


def _jitter(seed: str, spread: float = 0.35) -> tuple[float, float]:
    """Deterministic small offset in (lat, lon) derived from a seed string."""
    h = hashlib.md5(seed.encode("utf-8")).hexdigest()
    a = (int(h[:8], 16) / 0xFFFFFFFF - 0.5) * 2 * spread
    b = (int(h[8:16], 16) / 0xFFFFFFFF - 0.5) * 2 * spread
    return a, b


def report_coords(report: dict) -> tuple[float, float] | None:
    """Return (lat, lon) for a report, or None if it can't be placed.

    Explicit GPS is only trusted when it lies inside Indonesia; otherwise the
    report falls back to its province centroid so the map never leaves the
    country.
    """
    lat = report.get("lat")
    lon = report.get("lon")
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and in_indonesia(lat, lon):
        return float(lat), float(lon)

    prov = report.get("provinsi") or ""
    base = PROVINSI_CENTROID.get(prov, DEFAULT_CENTER)
    dlat, dlon = _jitter(report.get("id", prov))
    return base[0] + dlat, base[1] + dlon


def parse_latlon(text: str) -> tuple[float, float] | None:
    """Parse a 'lat, lon' string (as pasted from Google Maps). None if invalid."""
    if not text:
        return None
    try:
        parts = text.replace(";", ",").split(",")
        lat, lon = float(parts[0].strip()), float(parts[1].strip())
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    except (ValueError, IndexError):
        return None
    return None
