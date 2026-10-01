import hashlib
import mimetypes
import os

from werkzeug.utils import secure_filename

from ..config import Config
from .errors import ApiError


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(name: str) -> str:
    """Strip path components / unsafe characters (path traversal protection)."""
    name = os.path.basename((name or "").replace("\\", "/"))
    return secure_filename(name)[:150]


def validate_upload(filename: str, size: int):
    name = safe_filename(filename)
    if not name or "." not in name:
        raise ApiError("Invalid file name. Use a name with a supported extension.", 400)
    ext = name.rsplit(".", 1)[1].lower()
    if ext not in Config.ALLOWED_EXTENSIONS:
        raise ApiError(f".{ext} files are not allowed. Allowed: {', '.join(sorted(Config.ALLOWED_EXTENSIONS))}.", 415)
    if size == 0:
        raise ApiError("The file is empty.", 400)
    if size > Config.MAX_FILE_SIZE:
        raise ApiError(f"File exceeds the {Config.MAX_FILE_SIZE // (1024 * 1024)} MB limit.", 413)
    return name, (mimetypes.guess_type(name)[0] or "application/octet-stream")
