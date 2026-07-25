"""Report integrity: authenticity signals, duplicate detection, and spatial
clustering. All pure Python + Pillow so it works offline with no extra deps.

Together these answer the "fake / recycled report" risk (Risk #1 in the README)
and stop the same pothole being counted many times:

* :func:`dhash` / :func:`hamming` give a perceptual fingerprint of a photo, so a
  reused or lightly edited image is recognised even if re-saved.
* :func:`exif_signals` reads camera metadata and flags images that look like
  screenshots or downloads rather than a fresh capture.
* :func:`find_similar` and :func:`cluster_reports` group reports that are the
  same photo or the same spot, so duplicates are surfaced and de-duplicated.
"""
from __future__ import annotations

import math
from datetime import datetime

from PIL import Image


# ── Perceptual hash (dHash, 64-bit) ─────────────────────────────────────────────
def dhash(image: Image.Image, size: int = 8) -> str:
    """Row difference hash. Robust to resize/recompress; sensitive to content."""
    small = image.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(small.getdata())
    bits = []
    for row in range(size):
        base = row * (size + 1)
        for col in range(size):
            bits.append("1" if px[base + col] > px[base + col + 1] else "0")
    return f"{int(''.join(bits), 2):016x}"


def hamming(a: str, b: str) -> int:
    """Bit distance between two hex hashes (0 = identical, 64 = opposite)."""
    if not a or not b:
        return 64
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except ValueError:
        return 64


# ── EXIF authenticity signals ───────────────────────────────────────────────────
def exif_signals(image: Image.Image) -> dict:
    """Soft authenticity signals from image metadata.

    Absence of EXIF is not proof of fraud (many phones and chat apps strip it),
    so this returns advisory flags and a 0-100 confidence, never a hard verdict.
    """
    has_exif = has_datetime = has_gps = False
    try:
        exif = image.getexif()
    except Exception:
        exif = None

    if exif:
        has_exif = len(exif) > 0
        # 0x9003 DateTimeOriginal, 0x0132 DateTime, 0x8769 ExifIFD, 0x8825 GPSIFD
        has_datetime = any(t in exif for t in (0x9003, 0x0132)) or 0x8769 in exif
        has_gps = 0x8825 in exif

    flags = []
    if not has_exif:
        flags.append("Tanpa metadata EXIF (kemungkinan tangkapan layar, unduhan, atau hasil edit).")
    if has_exif and not has_datetime:
        flags.append("Tidak ada waktu pengambilan pada metadata.")

    score = 40
    if has_exif:
        score += 25
    if has_datetime:
        score += 20
    if has_gps:
        score += 15
    score = min(100, score)

    return {
        "has_exif": has_exif,
        "has_datetime": has_datetime,
        "has_gps": has_gps,
        "flags": flags,
        "score": score,
        "label": "Kuat" if score >= 75 else ("Sedang" if score >= 50 else "Perlu dicek"),
    }


# ── GPS from photo metadata ─────────────────────────────────────────────────────
def _to_degrees(value) -> float:
    """Convert an EXIF (deg, min, sec) rational tuple to decimal degrees."""
    d, m, s = (float(x) for x in value)
    return d + m / 60.0 + s / 3600.0


def gps_from_exif(image: Image.Image):
    """Return ``(lat, lon)`` embedded in the photo by the camera, or None.

    This is the location where the photo was actually taken, which is more
    reliable for a report than a device's current position. Many chat apps strip
    EXIF, so absence is common and simply falls back to manual entry.
    """
    try:
        exif = image.getexif()
        gps = exif.get_ifd(0x8825) if exif else None  # GPSInfo IFD
    except Exception:
        gps = None
    if not gps:
        return None
    try:
        lat = _to_degrees(gps[2])
        lon = _to_degrees(gps[4])
        if gps.get(1) in ("S", "s"):
            lat = -lat
        if gps.get(3) in ("W", "w"):
            lon = -lon
        if lat == 0 and lon == 0:
            return None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return round(lat, 6), round(lon, 6)
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


# ── Distance + duplicate detection ──────────────────────────────────────────────
def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _coords(report: dict):
    lat, lon = report.get("lat"), report.get("lon")
    if lat is None or lon is None:
        return None
    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None


def find_similar(new_hash: str, new_coords, reports: list,
                 max_hamming: int = 8, max_meters: float = 40.0) -> list:
    """Return existing reports that look like the same damage as a new one.

    A match is either a near-identical photo (small Hamming distance) or a report
    at almost the same GPS coordinate. Resolved reports are ignored.
    """
    matches = []
    for r in reports:
        if r.get("status") == "Selesai":
            continue
        reason = None
        h = r.get("foto_phash")
        if h and new_hash and hamming(new_hash, h) <= max_hamming:
            reason = "foto identik"
        elif new_coords:
            rc = _coords(r)
            if rc and haversine_m(new_coords[0], new_coords[1], rc[0], rc[1]) <= max_meters:
                reason = "lokasi berdekatan"
        if reason:
            matches.append({"id": r.get("id"), "lokasi": r.get("lokasi", ""), "alasan": reason})
    return matches


# ── Spatial clustering ──────────────────────────────────────────────────────────
def cluster_reports(reports: list, radius_m: float = 30.0) -> dict:
    """Greedily group reports whose GPS coordinates fall within ``radius_m``.

    Returns ``{report_id: cluster_size}`` so the feed can show how many separate
    reports describe the same spot (a stronger priority signal than one report).
    """
    placed = [r for r in reports if _coords(r)]
    clusters: list[list] = []
    for r in placed:
        rc = _coords(r)
        joined = False
        for cluster in clusters:
            c0 = _coords(cluster[0])
            if c0 and haversine_m(rc[0], rc[1], c0[0], c0[1]) <= radius_m:
                cluster.append(r)
                joined = True
                break
        if not joined:
            clusters.append([r])

    sizes: dict[str, int] = {}
    for cluster in clusters:
        if len(cluster) > 1:
            for r in cluster:
                sizes[r["id"]] = len(cluster)
    return sizes
