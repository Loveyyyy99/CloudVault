"""Pure disaster-recovery logic (no DB / no Flask) so it is easy to unit-test and explain."""
from dataclasses import dataclass, field

from ..storage.interface import ProviderError
from ..utils.security import sha256_hex

PROVIDERS = ("b2", "supabase")


def overall_status(statuses):
    s = list(statuses)
    if not s:
        return "PENDING"
    if all(x == "VERIFIED" for x in s):
        return "VERIFIED"
    if any(x == "UPLOADING" for x in s):
        return "UPLOADING"
    if all(x == "PENDING" for x in s):
        return "PENDING"
    if any(x == "VERIFIED" for x in s):
        return "PARTIAL"
    return "FAILED"


@dataclass
class RestoreResult:
    source: str
    data: bytes
    attempts: list = field(default_factory=list)


class RestoreFailed(Exception):
    def __init__(self, attempts):
        super().__init__("restore failed")
        self.attempts = attempts


def restore_from(providers, key, expected_hash, order):
    """Try providers in `order`; return the first copy whose SHA-256 matches `expected_hash`."""
    attempts = []
    for name in order:
        try:
            data = providers[name].download(key)
        except ProviderError as e:
            attempts.append({"provider": name, "ok": False, "reason": str(e)})
            continue
        if sha256_hex(data) != expected_hash:
            attempts.append({"provider": name, "ok": False, "reason": "Checksum mismatch — copy is corrupted."})
            continue
        attempts.append({"provider": name, "ok": True, "reason": "Downloaded and SHA-256 verified."})
        return RestoreResult(name, data, attempts)
    raise RestoreFailed(attempts)
