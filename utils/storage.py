import io
import json
import os
import base64
from datetime import datetime
from pathlib import Path

from PIL import Image

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_FILE = DATA_DIR / "reports.json"
SEED_FILE = DATA_DIR / "seed_data.json"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Photos are resized/recompressed before saving so the data dir stays small.
MAX_PHOTO_PX = 1280
PHOTO_QUALITY = 80

# SLA target (days) per severity — more severe damage must be handled faster.
SLA_BY_SEVERITY = {"Berat": 3, "Sedang": 7, "Ringan": 14}
DEFAULT_SLA_DAYS = 7

PROVINSI_INDONESIA = [
    "Semua Wilayah",
    "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau",
    "Jambi", "Bengkulu", "Sumatera Selatan", "Kepulauan Bangka Belitung",
    "Lampung", "DKI Jakarta", "Jawa Barat", "Banten", "Jawa Tengah",
    "DI Yogyakarta", "Jawa Timur", "Bali", "Nusa Tenggara Barat",
    "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah",
    "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara",
    "Sulawesi Utara", "Gorontalo", "Sulawesi Tengah", "Sulawesi Barat",
    "Sulawesi Selatan", "Sulawesi Tenggara", "Maluku", "Maluku Utara",
    "Papua Barat", "Papua Barat Daya", "Papua", "Papua Pegunungan",
    "Papua Tengah", "Papua Selatan",
]

# Admin password is read from the environment when available so it isn't
# hardcoded for real deployments; falls back to the demo default otherwise.
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Fields added by later versions — back-filled onto older records on load.
_DEFAULT_FIELDS = {
    "progress_updates": list,
    "assigned_to": str,
    "assigned_by": str,
    "assignment_notes": str,
    "foto_path": lambda: None,
    "kategori": str,
    "lat": lambda: None,
    "lon": lambda: None,
    "demo_mode": bool,
    "comments": list,
    "pelapor_username": str,
}

# Avatar palette mirror (matches utils.auth.AVATAR_COLORS) for deterministic
# colours when a report has no linked account.
_AVATAR_PALETTE = ["#B5701A", "#B23A2E", "#3F7A52", "#6E5AA8", "#C2541C", "#2A6F77", "#9A3F6E"]

# Seed reporters → their seeded account usernames (see utils.auth).
_NAME_TO_USERNAME = {
    "Budi Santoso": "budi", "Dewi Rahayu": "dewi", "Ahmad Fauzi": "ahmad",
    "Siti Nurhaliza": "siti", "Rizki Pratama": "rizki",
}


def author_color(name: str) -> str:
    """Deterministic avatar colour from a display name."""
    if not name:
        return _AVATAR_PALETTE[0]
    idx = sum(ord(c) for c in name) % len(_AVATAR_PALETTE)
    return _AVATAR_PALETTE[idx]


def _migrate(report: dict) -> dict:
    """Back-fill fields introduced after a report was first written."""
    for key, factory in _DEFAULT_FIELDS.items():
        if key not in report:
            report[key] = factory()
    # Derive province if missing (older records stored only free-text lokasi).
    if not report.get("provinsi"):
        report["provinsi"] = detect_provinsi(report.get("lokasi", ""))
    # Link legacy seed reports to their seeded accounts.
    if not report.get("pelapor_username"):
        report["pelapor_username"] = _NAME_TO_USERNAME.get(report.get("pelapor", ""), "")
    return report


def add_comment(report_id: str, username: str, nama: str, text: str) -> list:
    reports = load_reports()
    comment = {
        "username": username,
        "nama": nama,
        "text": text.strip(),
        "timestamp": datetime.now().isoformat(),
    }
    for r in reports:
        if r["id"] == report_id:
            r.setdefault("comments", []).append(comment)
            break
    save_reports(reports)
    return reports


def load_reports() -> list:
    if not REPORTS_FILE.exists():
        seed = load_seed_data()
        save_reports(seed)
        return seed
    with open(REPORTS_FILE, "r", encoding="utf-8") as f:
        return [_migrate(r) for r in json.load(f)]


def save_reports(reports: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)


def load_seed_data() -> list:
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [_migrate(r) for r in data]


def add_report(report: dict) -> None:
    reports = load_reports()
    reports.insert(0, report)
    save_reports(reports)


def toggle_like(report_id: str, liked_ids: set) -> tuple:
    reports = load_reports()
    for r in reports:
        if r["id"] == report_id:
            if report_id in liked_ids:
                r["likes"] = max(0, r["likes"] - 1)
                liked_ids.discard(report_id)
            else:
                r["likes"] += 1
                liked_ids.add(report_id)
            break
    save_reports(reports)
    return reports, liked_ids


def update_status(report_id: str, new_status: str) -> list:
    reports = load_reports()
    for r in reports:
        if r["id"] == report_id:
            r["status"] = new_status
            break
    save_reports(reports)
    return reports


def update_assignment(report_id: str, assigned_to: str, assigned_by: str, notes: str) -> list:
    reports = load_reports()
    for r in reports:
        if r["id"] == report_id:
            r["assigned_to"] = assigned_to
            r["assigned_by"] = assigned_by
            r["assignment_notes"] = notes
            break
    save_reports(reports)
    return reports


def add_progress_update(report_id: str, uploader: str, deskripsi: str, foto_bytes: bytes = None, foto_ext: str = "jpg") -> list:
    reports = load_reports()
    foto_path = None
    if foto_bytes:
        fname = f"progress_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        fpath = UPLOADS_DIR / fname
        with open(fpath, "wb") as f:
            f.write(_compress_to_jpeg(foto_bytes))
        foto_path = str(fpath)

    update = {
        "timestamp": datetime.now().isoformat(),
        "uploader": uploader,
        "deskripsi": deskripsi,
        "foto_path": foto_path,
    }

    for r in reports:
        if r["id"] == report_id:
            if "progress_updates" not in r:
                r["progress_updates"] = []
            r["progress_updates"].insert(0, update)
            break
    save_reports(reports)
    return reports


def _compress_to_jpeg(foto_bytes: bytes) -> bytes:
    """Downscale to MAX_PHOTO_PX and re-encode as JPEG to cap storage size."""
    try:
        img = Image.open(io.BytesIO(foto_bytes))
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        img.thumbnail((MAX_PHOTO_PX, MAX_PHOTO_PX))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=PHOTO_QUALITY, optimize=True)
        return buf.getvalue()
    except Exception:
        # If anything goes wrong, fall back to storing the original bytes.
        return foto_bytes


def save_report_foto(foto_bytes: bytes, report_id: str, ext: str = "jpg") -> str:
    fname = f"report_{report_id}.jpg"
    fpath = UPLOADS_DIR / fname
    with open(fpath, "wb") as f:
        f.write(_compress_to_jpeg(foto_bytes))
    return str(fpath)


def get_foto_base64(foto_path: str) -> str:
    if not foto_path or not Path(foto_path).exists():
        return None
    with open(foto_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generate_report_id(reports: list) -> str:
    if not reports:
        return "RPT-006"
    existing_nums = []
    for r in reports:
        try:
            num = int(r["id"].split("-")[1])
            existing_nums.append(num)
        except (IndexError, ValueError):
            pass
    next_num = max(existing_nums) + 1 if existing_nums else 6
    return f"RPT-{next_num:03d}"


def format_rupiah(amount: int) -> str:
    return f"Rp {amount:,.0f}".replace(",", ".")


def format_timestamp(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return ts


def get_status_color(status: str) -> str:
    colors = {
        "Menunggu": "#B5701A",
        "Prioritas Publik": "#B23A2E",
        "CSR Dashboard": "#6E5AA8",
        "Selesai": "#3F7A52",
    }
    return colors.get(status, "#6B6155")


def severity_sla_days(severity: str) -> int:
    return SLA_BY_SEVERITY.get(severity, DEFAULT_SLA_DAYS)


def _days_since(ts: str) -> int:
    try:
        dt = datetime.fromisoformat(ts)
        return max(0, (datetime.now() - dt).days)
    except Exception:
        return 0


def get_sla_info(report: dict) -> dict:
    """Compute SLA progress dynamically from the report timestamp.

    The original prototype stored a static ``hari_berjalan`` that never moved.
    Here the elapsed days are derived from the report's creation time, and the
    SLA target is driven by severity. Resolved ("Selesai") reports freeze.
    """
    severity = report.get("deteksi", {}).get("tingkat_keparahan", "")
    sla_hari = report.get("sla_hari") or severity_sla_days(severity)

    resolved = report.get("status") == "Selesai"
    if resolved:
        # Once resolved, stop the clock at whatever it was (capped at SLA).
        hari_berjalan = min(_days_since(report.get("timestamp", "")), sla_hari)
    else:
        hari_berjalan = _days_since(report.get("timestamp", ""))

    sisa = sla_hari - hari_berjalan
    persen = min(100, int((hari_berjalan / sla_hari) * 100)) if sla_hari else 0
    lewat = (not resolved) and hari_berjalan >= sla_hari
    return {
        "hari_berjalan": hari_berjalan,
        "sla_hari": sla_hari,
        "sisa": sisa,
        "persen": persen,
        "lewat": lewat,
        "resolved": resolved,
    }


# ── Priority scoring ──────────────────────────────────────────────────────────
_SEVERITY_WEIGHT = {"Berat": 50, "Sedang": 30, "Ringan": 15}


def priority_score(report: dict) -> int:
    """0–100 urgency score blending severity, SLA pressure, and public support."""
    if report.get("status") == "Selesai":
        return 0

    det = report.get("deteksi", {})
    score = _SEVERITY_WEIGHT.get(det.get("tingkat_keparahan", ""), 15)

    sla = get_sla_info(report)
    if sla["lewat"]:
        score += 30
    elif sla["persen"] >= 70:
        score += 18
    elif sla["persen"] >= 40:
        score += 8

    # Community support, capped so likes can't dominate severity.
    score += min(report.get("likes", 0), 20) * 1.0

    return int(min(100, score))


def priority_label(score: int) -> str:
    if score >= 70:
        return "Kritis"
    if score >= 45:
        return "Tinggi"
    if score >= 25:
        return "Sedang"
    return "Rendah"


def reports_to_records(reports: list) -> list:
    """Flatten reports into export-friendly rows (used for CSV + dashboard)."""
    rows = []
    for r in reports:
        det = r.get("deteksi", {})
        rab = r.get("rab", {})
        sla = get_sla_info(r)
        score = priority_score(r)
        rows.append({
            "id": r.get("id", ""),
            "tanggal": format_timestamp(r.get("timestamp", "")),
            "pelapor": r.get("pelapor", ""),
            "lokasi": r.get("lokasi", ""),
            "provinsi": r.get("provinsi", "") or detect_provinsi(r.get("lokasi", "")),
            "tipe_kerusakan": det.get("tipe_kerusakan", ""),
            "keparahan": det.get("tingkat_keparahan", ""),
            "dimensi": det.get("estimasi_dimensi", ""),
            "confidence": det.get("confidence", ""),
            "rab_total": rab.get("total", 0),
            "status": r.get("status", ""),
            "prioritas": priority_label(score),
            "skor_prioritas": score,
            "sla_hari": sla["sla_hari"],
            "hari_berjalan": sla["hari_berjalan"],
            "lewat_sla": "Ya" if sla["lewat"] else "Tidak",
            "likes": r.get("likes", 0),
            "ditugaskan_ke": r.get("assigned_to", ""),
            "jumlah_update": len(r.get("progress_updates", [])),
        })
    return rows


def reports_to_csv(reports: list) -> str:
    import csv as _csv
    rows = reports_to_records(reports)
    if not rows:
        return ""
    buf = io.StringIO()
    writer = _csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def detect_provinsi(lokasi: str) -> str:
    lokasi_lower = lokasi.lower()
    mapping = {
        "aceh": "Aceh",
        "medan": "Sumatera Utara", "sumatera utara": "Sumatera Utara",
        "padang": "Sumatera Barat", "sumatera barat": "Sumatera Barat",
        "pekanbaru": "Riau", "riau": "Riau",
        "batam": "Kepulauan Riau", "kepulauan riau": "Kepulauan Riau",
        "jambi": "Jambi",
        "bengkulu": "Bengkulu",
        "palembang": "Sumatera Selatan", "sumatera selatan": "Sumatera Selatan",
        "bangka": "Kepulauan Bangka Belitung", "belitung": "Kepulauan Bangka Belitung",
        "lampung": "Lampung",
        "jakarta": "DKI Jakarta", "dki": "DKI Jakarta",
        "bandung": "Jawa Barat", "bogor": "Jawa Barat", "depok": "Jawa Barat",
        "jawa barat": "Jawa Barat", "jabar": "Jawa Barat",
        "serang": "Banten", "tangerang": "Banten", "banten": "Banten",
        "semarang": "Jawa Tengah", "solo": "Jawa Tengah", "jawa tengah": "Jawa Tengah",
        "klaten": "Jawa Tengah", "magelang": "Jawa Tengah",
        "yogyakarta": "DI Yogyakarta", "diy": "DI Yogyakarta",
        "sleman": "DI Yogyakarta", "bantul": "DI Yogyakarta",
        "gunungkidul": "DI Yogyakarta", "kulonprogo": "DI Yogyakarta",
        "surabaya": "Jawa Timur", "malang": "Jawa Timur", "jawa timur": "Jawa Timur",
        "bali": "Bali", "denpasar": "Bali",
        "lombok": "Nusa Tenggara Barat", "ntb": "Nusa Tenggara Barat",
        "kupang": "Nusa Tenggara Timur", "ntt": "Nusa Tenggara Timur",
        "pontianak": "Kalimantan Barat", "kalimantan barat": "Kalimantan Barat",
        "palangkaraya": "Kalimantan Tengah", "kalimantan tengah": "Kalimantan Tengah",
        "banjarmasin": "Kalimantan Selatan", "kalimantan selatan": "Kalimantan Selatan",
        "balikpapan": "Kalimantan Timur", "samarinda": "Kalimantan Timur",
        "kalimantan timur": "Kalimantan Timur",
        "tarakan": "Kalimantan Utara", "kalimantan utara": "Kalimantan Utara",
        "manado": "Sulawesi Utara", "sulawesi utara": "Sulawesi Utara",
        "gorontalo": "Gorontalo",
        "palu": "Sulawesi Tengah", "sulawesi tengah": "Sulawesi Tengah",
        "mamuju": "Sulawesi Barat", "sulawesi barat": "Sulawesi Barat",
        "makassar": "Sulawesi Selatan", "sulawesi selatan": "Sulawesi Selatan",
        "kendari": "Sulawesi Tenggara", "sulawesi tenggara": "Sulawesi Tenggara",
        "ambon": "Maluku", "maluku": "Maluku",
        "ternate": "Maluku Utara", "maluku utara": "Maluku Utara",
        "manokwari": "Papua Barat", "papua barat": "Papua Barat",
        "jayapura": "Papua", "papua": "Papua",
    }
    for key, prov in mapping.items():
        if key in lokasi_lower:
            return prov
    return "Lainnya"