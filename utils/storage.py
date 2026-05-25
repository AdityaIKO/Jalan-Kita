import json
import os
import base64
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_FILE = DATA_DIR / "reports.json"
SEED_FILE = DATA_DIR / "seed_data.json"
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

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

ADMIN_PASSWORD = "admin123"


def load_reports() -> list:
    if not REPORTS_FILE.exists():
        seed = load_seed_data()
        save_reports(seed)
        return seed
    with open(REPORTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_reports(reports: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)


def load_seed_data() -> list:
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for r in data:
        if "progress_updates" not in r:
            r["progress_updates"] = []
        if "assigned_to" not in r:
            r["assigned_to"] = ""
        if "assigned_by" not in r:
            r["assigned_by"] = ""
        if "assignment_notes" not in r:
            r["assignment_notes"] = ""
        if "foto_path" not in r:
            r["foto_path"] = None
    return data


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
        fname = f"progress_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{foto_ext}"
        fpath = UPLOADS_DIR / fname
        with open(fpath, "wb") as f:
            f.write(foto_bytes)
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


def save_report_foto(foto_bytes: bytes, report_id: str, ext: str = "jpg") -> str:
    fname = f"report_{report_id}.{ext}"
    fpath = UPLOADS_DIR / fname
    with open(fpath, "wb") as f:
        f.write(foto_bytes)
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
        "Menunggu": "#F59E0B",
        "Prioritas Publik": "#EF4444",
        "CSR Dashboard": "#8B5CF6",
        "Selesai": "#10B981",
    }
    return colors.get(status, "#6B7280")


def get_sla_info(report: dict) -> dict:
    hari_berjalan = report.get("hari_berjalan", 0)
    sla_hari = report.get("sla_hari", 7)
    sisa = sla_hari - hari_berjalan
    persen = min(100, int((hari_berjalan / sla_hari) * 100))
    lewat = hari_berjalan >= sla_hari
    return {
        "hari_berjalan": hari_berjalan,
        "sla_hari": sla_hari,
        "sisa": sisa,
        "persen": persen,
        "lewat": lewat,
    }


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