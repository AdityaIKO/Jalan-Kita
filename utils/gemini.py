"""AI layer: Gemini-backed road-damage CV + RAB estimation.

Hardened over the original prototype with:
  * robust JSON extraction (tolerates ```json fences and surrounding prose)
  * automatic retries with backoff on transient failures
  * a deterministic offline heuristic fallback so the app stays fully usable
    for demos when GEMINI_API_KEY is missing or the API is unreachable. Results
    produced offline are flagged with ``_demo: True`` so the UI can label them.
"""
import os
import re
import json
import time
import hashlib

from PIL import Image
from dotenv import load_dotenv
import io

load_dotenv()

MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
HAS_API = bool(API_KEY)

# The genai client is created lazily so importing this module never fails when
# the dependency or key is absent (offline/demo mode still works).
_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=API_KEY)
    return _client


PROMPT_CV = """
Kamu adalah sistem analisis kerusakan infrastruktur jalan berbasis computer vision.
Analisis foto jalan yang diberikan secara seksama.

Identifikasi dan kembalikan hasil dalam format JSON berikut (tanpa markdown, hanya JSON murni):
{
  "tipe_kerusakan": "<tipe: Lubang (Pothole) | Retak Buaya (Alligator Crack) | Retak Memanjang (Longitudinal Crack) | Retak Melintang (Transverse Crack) | Ambles (Settlement) | Pengelupasan (Raveling) | Tidak Terdeteksi>",
  "tingkat_keparahan": "<Ringan | Sedang | Berat>",
  "estimasi_dimensi": "<estimasi dimensi dalam meter, contoh: 1.2m x 0.8m x 0.15m>",
  "confidence": "<persentase keyakinan, contoh: 87%>",
  "catatan": "<deskripsi singkat kondisi dan potensi bahaya dalam 1-2 kalimat>"
}

Jika gambar bukan foto jalan atau tidak ada kerusakan terdeteksi, set tipe_kerusakan ke "Tidak Terdeteksi".
Berikan hanya JSON, tanpa penjelasan tambahan.
"""

PROMPT_PII = """
Deteksi SEMUA wajah manusia dan pelat nomor kendaraan yang terlihat pada gambar.
Kembalikan JSON murni (tanpa markdown) dalam format:
{
  "regions": [
    {"tipe": "wajah", "box": [ymin, xmin, ymax, xmax]},
    {"tipe": "plat", "box": [ymin, xmin, ymax, xmax]}
  ]
}
Koordinat box ternormalisasi pada skala 0 sampai 1000 (0 = tepi atas/kiri, 1000 = tepi bawah/kanan).
Jika tidak ada wajah atau pelat nomor, kembalikan {"regions": []}.
Berikan hanya JSON.
"""

PROMPT_RAB = """
Kamu adalah quantity surveyor infrastruktur jalan yang berpengalaman.
Berdasarkan data kerusakan jalan berikut, buat estimasi Rencana Anggaran Biaya (RAB) perbaikan.

Data Kerusakan:
- Tipe: {tipe_kerusakan}
- Tingkat Keparahan: {tingkat_keparahan}
- Estimasi Dimensi: {estimasi_dimensi}
- Lokasi: {lokasi}

Kembalikan hasil dalam format JSON berikut (tanpa markdown, hanya JSON murni):
{{
  "material": <total biaya material dalam integer Rupiah>,
  "tenaga_kerja": <total biaya tenaga kerja dalam integer Rupiah>,
  "peralatan": <total biaya peralatan dalam integer Rupiah>,
  "total": <total keseluruhan dalam integer Rupiah>,
  "breakdown": [
    {{
      "item": "<nama item>",
      "volume": "<volume dengan satuan>",
      "harga_satuan": <harga satuan integer>,
      "subtotal": <subtotal integer>
    }}
  ]
}}

Gunakan harga satuan standar Permen PUPR untuk wilayah Jawa.
Pastikan breakdown mencakup material, tenaga kerja, dan peralatan secara terpisah.
Berikan hanya JSON, tanpa penjelasan tambahan.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────
def pil_to_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    if image.mode in ("RGBA", "P", "LA"):
        image = image.convert("RGB")
    image.save(buf, format="JPEG")
    return buf.getvalue()


def _extract_json(text: str):
    """Best-effort JSON extraction tolerant of fences and surrounding prose."""
    if not text:
        raise json.JSONDecodeError("empty", "", 0)
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to the first balanced {...} block.
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise json.JSONDecodeError("no json object found", cleaned, 0)


def _call_with_retry(contents):
    """Call Gemini with retries; returns parsed JSON dict or raises."""
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            response = _get_client().models.generate_content(
                model=MODEL, contents=contents
            )
            return _extract_json(response.text)
        except Exception as e:  # transient network / parse / quota
            last_err = e
            time.sleep(0.6 * (attempt + 1))
    raise last_err if last_err else RuntimeError("unknown error")


# ── Offline heuristic fallback ────────────────────────────────────────────────
_DEMO_TYPES = [
    ("Lubang (Pothole)", "Berat", "1.1m x 0.7m x 0.14m", "Lubang dalam berpotensi merusak kendaraan dan membahayakan pengendara motor."),
    ("Retak Buaya (Alligator Crack)", "Sedang", "2.0m x 1.5m", "Retak buaya menandakan kelelahan struktur perkerasan, perlu penanganan sebelum meluas."),
    ("Retak Memanjang (Longitudinal Crack)", "Ringan", "3.2m x 0.02m", "Retak memanjang ringan, dapat ditangani dengan sealant untuk mencegah air masuk."),
    ("Ambles (Settlement)", "Berat", "2.5m x 2.0m x 0.10m", "Permukaan ambles cukup luas, berisiko menyebabkan genangan dan kecelakaan."),
]


def _demo_analysis(image: Image.Image) -> dict:
    """Deterministic plausible CV result derived from image bytes (no model)."""
    digest = hashlib.md5(pil_to_bytes(image)).hexdigest()
    tipe, kep, dim, catatan = _DEMO_TYPES[int(digest[:2], 16) % len(_DEMO_TYPES)]
    conf = 78 + int(digest[2:4], 16) % 18  # 78–95%
    return {
        "tipe_kerusakan": tipe,
        "tingkat_keparahan": kep,
        "estimasi_dimensi": dim,
        "confidence": f"{conf}%",
        "catatan": catatan,
        "_demo": True,
    }


def _demo_rab(deteksi: dict, lokasi: str) -> dict:
    """Coherent heuristic RAB based on severity (no model)."""
    kep = deteksi.get("tingkat_keparahan", "Sedang")
    base = {"Berat": 2_200_000, "Sedang": 1_150_000, "Ringan": 480_000}.get(kep, 1_150_000)
    material = int(base * 0.55)
    tenaga = int(base * 0.28)
    alat = base - material - tenaga
    breakdown = [
        {"item": "Aspal hotmix (AC-BC)", "volume": "0.14 m³", "harga_satuan": 850_000, "subtotal": int(material * 0.8)},
        {"item": "Agregat base course", "volume": "0.10 m³", "harga_satuan": 600_000, "subtotal": int(material * 0.2)},
        {"item": "Tenaga kerja (mandor + pekerja)", "volume": "3 OH", "harga_satuan": int(tenaga / 3), "subtotal": tenaga},
        {"item": "Sewa alat (stamper/compactor)", "volume": "1 hari", "harga_satuan": alat, "subtotal": alat},
    ]
    return {
        "material": material,
        "tenaga_kerja": tenaga,
        "peralatan": alat,
        "total": base,
        "breakdown": breakdown,
        "_demo": True,
    }


# ── Public API ────────────────────────────────────────────────────────────────
def analyze_image(image: Image.Image) -> dict:
    if not HAS_API:
        return {"success": True, "data": _demo_analysis(image), "demo": True}
    try:
        from google.genai import types
        result = _call_with_retry([
            types.Part.from_bytes(data=pil_to_bytes(image), mime_type="image/jpeg"),
            PROMPT_CV,
        ])
        result["_demo"] = False
        return {"success": True, "data": result, "demo": False}
    except json.JSONDecodeError:
        return {"success": False, "error": "Gagal memparse respons AI. Coba lagi."}
    except Exception as e:
        # Graceful degradation: keep the demo usable even if the API fails.
        return {"success": True, "data": _demo_analysis(image), "demo": True,
                "warning": f"API tidak tersedia ({e}); menggunakan estimasi heuristik."}


def detect_pii(image: Image.Image) -> dict:
    """Detect faces and licence plates for privacy redaction.

    Returns ``{success, regions, demo}``. In offline demo mode there is no
    detector, so ``regions`` is empty and ``demo`` is True.
    """
    if not HAS_API:
        return {"success": True, "regions": [], "demo": True}
    try:
        from google.genai import types
        result = _call_with_retry([
            types.Part.from_bytes(data=pil_to_bytes(image), mime_type="image/jpeg"),
            PROMPT_PII,
        ])
        regions = result.get("regions", []) if isinstance(result, dict) else []
        return {"success": True, "regions": regions, "demo": False}
    except Exception as e:
        return {"success": False, "regions": [], "demo": False, "error": str(e)}


def generate_rab(deteksi: dict, lokasi: str) -> dict:
    if not HAS_API:
        return {"success": True, "data": _demo_rab(deteksi, lokasi), "demo": True}
    prompt = PROMPT_RAB.format(
        tipe_kerusakan=deteksi.get("tipe_kerusakan", "-"),
        tingkat_keparahan=deteksi.get("tingkat_keparahan", "-"),
        estimasi_dimensi=deteksi.get("estimasi_dimensi", "-"),
        lokasi=lokasi,
    )
    try:
        result = _call_with_retry(prompt)
        result["_demo"] = False
        return {"success": True, "data": result, "demo": False}
    except json.JSONDecodeError:
        return {"success": False, "error": "Gagal memparse respons RAB. Coba lagi."}
    except Exception as e:
        return {"success": True, "data": _demo_rab(deteksi, lokasi), "demo": True,
                "warning": f"API tidak tersedia ({e}); menggunakan estimasi heuristik."}
