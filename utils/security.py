"""Security utilities: output escaping, password hashing, login throttling,
and upload validation.

Kept dependency-free (standard library + Pillow, which the app already uses) so
it works anywhere the app runs, including Streamlit Community Cloud.

Design notes
------------
* Rendered HTML: the app uses ``unsafe_allow_html=True`` in many places and
  interpolates user text (names, bios, locations, comments). Every such value
  must pass through :func:`esc` first, otherwise a stored comment like
  ``<img src=x onerror=alert(1)>`` runs for everyone who views the feed.
* Passwords: PBKDF2-HMAC-SHA256 with a per-user salt and a high iteration count.
  Old SHA-256 hashes from earlier builds still verify and are transparently
  re-hashed on the next successful login (see :func:`verify_password`).
* Login throttling: attempts are counted per username in a process-level store,
  so the limit holds across browser sessions hitting the same server.
"""
from __future__ import annotations

import hashlib
import hmac
import html
import io
import secrets
import time

from PIL import Image

# ── Output escaping ─────────────────────────────────────────────────────────────
def esc(value) -> str:
    """HTML-escape any value for safe interpolation into markup.

    Use for every user-controlled string rendered via ``unsafe_allow_html``.
    """
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


# ── Password hashing ────────────────────────────────────────────────────────────
# OWASP-aligned iteration count for PBKDF2-HMAC-SHA256 (2024 guidance: >= 210k).
_PBKDF2_ROUNDS = 240_000
_HASH_PREFIX = "pbkdf2_sha256"


def hash_password(password: str, salt: str | None = None) -> str:
    """Return a self-describing hash string: ``pbkdf2_sha256$rounds$salt$hex``."""
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS)
    return f"{_HASH_PREFIX}${_PBKDF2_ROUNDS}${salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str, legacy_salt: str | None = None) -> bool:
    """Verify a password against a stored hash.

    Supports the current PBKDF2 format and the legacy salted-SHA256 format
    (``sha256(f"{salt}${password}")`` with the salt kept in a separate field).
    Comparison is constant-time.
    """
    if not stored_hash:
        return False

    if stored_hash.startswith(_HASH_PREFIX + "$"):
        try:
            _, rounds, salt, expected = stored_hash.split("$", 3)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds))
            return hmac.compare_digest(dk.hex(), expected)
        except (ValueError, TypeError):
            return False

    # Legacy: salted SHA-256, salt stored separately on the user record.
    if legacy_salt is not None:
        legacy = hashlib.sha256(f"{legacy_salt}${password}".encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored_hash)

    return False


def needs_rehash(stored_hash: str) -> bool:
    """True when a stored hash uses an outdated scheme and should be upgraded."""
    if not stored_hash or not stored_hash.startswith(_HASH_PREFIX + "$"):
        return True
    try:
        rounds = int(stored_hash.split("$", 3)[1])
        return rounds < _PBKDF2_ROUNDS
    except (ValueError, IndexError):
        return True


# ── Login throttling ────────────────────────────────────────────────────────────
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutes
_WINDOW_SECONDS = 900   # attempts older than this are forgotten

# username -> list[timestamp] of recent failed attempts (process-level).
_failed: dict[str, list[float]] = {}


def _recent(username: str) -> list[float]:
    now = time.time()
    attempts = [t for t in _failed.get(username, []) if now - t < _WINDOW_SECONDS]
    _failed[username] = attempts
    return attempts


def is_locked(username: str) -> tuple[bool, int]:
    """Return ``(locked, seconds_remaining)`` for a username."""
    key = (username or "").strip().lower()
    attempts = _recent(key)
    if len(attempts) < _MAX_ATTEMPTS:
        return False, 0
    unlock_at = attempts[-1] + _LOCKOUT_SECONDS
    remaining = int(unlock_at - time.time())
    if remaining <= 0:
        _failed.pop(key, None)
        return False, 0
    return True, remaining


def register_failed_attempt(username: str) -> int:
    """Record a failed login; return how many attempts remain before lockout."""
    key = (username or "").strip().lower()
    attempts = _recent(key)
    attempts.append(time.time())
    _failed[key] = attempts
    return max(0, _MAX_ATTEMPTS - len(attempts))


def clear_attempts(username: str) -> None:
    """Reset the counter after a successful login."""
    _failed.pop((username or "").strip().lower(), None)


# ── Upload validation ───────────────────────────────────────────────────────────
_MAX_UPLOAD_BYTES = 8 * 1024 * 1024   # 8 MB
_MAX_PIXELS = 40_000_000              # ~40 MP guard against decompression bombs
_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# Leading magic bytes for the formats we accept.
_MAGIC = (
    (b"\xff\xd8\xff", "JPEG"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
)


def _looks_like_webp(head: bytes) -> bool:
    return len(head) >= 12 and head[0:4] == b"RIFF" and head[8:12] == b"WEBP"


def validate_image_upload(file_bytes: bytes, filename: str = "") -> tuple[bool, str]:
    """Validate an uploaded image by size, magic bytes, and decoded integrity.

    Returns ``(ok, message)``. The check never trusts the file extension alone:
    it sniffs the header and fully decodes the image with Pillow, rejecting
    corrupt files and oversized dimensions.
    """
    if not file_bytes:
        return False, "File kosong atau gagal dibaca."

    if len(file_bytes) > _MAX_UPLOAD_BYTES:
        mb = len(file_bytes) / (1024 * 1024)
        return False, f"Ukuran file {mb:.1f} MB melebihi batas 8 MB."

    head = file_bytes[:16]
    sniffed = next((fmt for magic, fmt in _MAGIC if head.startswith(magic)), None)
    if sniffed is None and _looks_like_webp(head):
        sniffed = "WEBP"
    if sniffed is None:
        return False, "Format tidak dikenali. Unggah foto JPG, PNG, atau WEBP."

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            if img.format not in _ALLOWED_FORMATS:
                return False, "Format gambar tidak didukung."
            w, h = img.size
            if w * h > _MAX_PIXELS:
                return False, "Resolusi gambar terlalu besar untuk diproses."
            img.verify()  # detect truncated / malformed data
    except Exception:
        return False, "File bukan gambar yang valid atau rusak."

    return True, ""
