import os
import json
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv
import io

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

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


def pil_to_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def analyze_image(image: Image.Image) -> dict:
    try:
        image_bytes = pil_to_bytes(image)
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                PROMPT_CV,
            ],
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return {"success": True, "data": result}
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Gagal memparse respons AI. Coba lagi.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_rab(deteksi: dict, lokasi: str) -> dict:
    prompt = PROMPT_RAB.format(
        tipe_kerusakan=deteksi.get("tipe_kerusakan", "-"),
        tingkat_keparahan=deteksi.get("tingkat_keparahan", "-"),
        estimasi_dimensi=deteksi.get("estimasi_dimensi", "-"),
        lokasi=lokasi,
    )
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return {"success": True, "data": result}
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Gagal memparse respons RAB. Coba lagi.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}