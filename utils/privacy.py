"""Privacy protection: blur faces and licence plates before a photo goes public.

Answers Risk #2 in the README (sensitive data in stored photos). Detection is
done by the multimodal model we already use (see utils.gemini.detect_pii), which
returns normalised bounding boxes; the blurring itself is pure Pillow so it needs
no extra dependency and runs anywhere.

When no API key is present the detector returns no regions and the original photo
is kept unchanged, with the UI noting that auto-redaction needs the model.
"""
from __future__ import annotations

from PIL import Image, ImageFilter


def blur_regions(image: Image.Image, regions: list) -> tuple[Image.Image, int]:
    """Blur each region and return ``(new_image, count_blurred)``.

    Regions use normalised ``box = [ymin, xmin, ymax, xmax]`` on a 0-1000 scale,
    matching the model's output. Invalid or empty boxes are skipped.
    """
    out = image.convert("RGB").copy()
    w, h = out.size
    count = 0
    for reg in regions or []:
        box = reg.get("box") or []
        if len(box) != 4:
            continue
        ymin, xmin, ymax, xmax = box
        left = int(min(xmin, xmax) / 1000 * w)
        right = int(max(xmin, xmax) / 1000 * w)
        top = int(min(ymin, ymax) / 1000 * h)
        bottom = int(max(ymin, ymax) / 1000 * h)
        # Pad a little so edges of a face/plate are covered too.
        pad_x = max(2, (right - left) // 10)
        pad_y = max(2, (bottom - top) // 10)
        left = max(0, left - pad_x); right = min(w, right + pad_x)
        top = max(0, top - pad_y); bottom = min(h, bottom + pad_y)
        if right - left < 4 or bottom - top < 4:
            continue
        crop = out.crop((left, top, right, bottom))
        radius = max(8, (right - left) // 5)
        out.paste(crop.filter(ImageFilter.GaussianBlur(radius)), (left, top))
        count += 1
    return out, count


def redact(image: Image.Image) -> dict:
    """Detect and blur PII in one call.

    Returns ``{image, blurred_count, available, error}``. ``available`` is False
    when the detector could not run (no API key), so the UI can explain that the
    original photo was kept.
    """
    from utils.gemini import detect_pii

    det = detect_pii(image)
    if not det.get("success") or det.get("demo"):
        return {
            "image": image,
            "blurred_count": 0,
            "available": bool(det.get("success")) and not det.get("demo"),
            "error": det.get("error", ""),
        }
    blurred, count = blur_regions(image, det.get("regions", []))
    return {"image": blurred, "blurred_count": count, "available": True, "error": ""}
