import logging
import time
import uuid
from datetime import datetime, timezone

from ..config import Config
from ..models import repo
from ..storage.b2_storage import B2Storage
from ..storage.interface import GuardedProvider, ProviderError
from ..storage.supabase_storage import SupabaseStorage
from ..utils.errors import ApiError
from ..utils.security import sha256_hex, validate_upload
from .recovery import PROVIDERS, RestoreFailed, overall_status, restore_from

log = logging.getLogger("cloudvault")
_LABEL = {"b2": "Backblaze B2", "supabase": "Supabase Storage"}


def build_providers(user_id=None):
    """user_id=None → real providers, no simulation (used by the scheduled job)."""
    sim = repo.get_simulation(user_id) if user_id else {}
    return {
        "b2": GuardedProvider(B2Storage(), sim.get("b2_down")),
        "supabase": GuardedProvider(SupabaseStorage(), sim.get("supabase_down")),
    }


def _now():
    return datetime.now(timezone.utc)


def refresh_status(file_id):
    f = repo.get_file(file_id)
    status = overall_status(b["status"] for b in f["backups"])
    repo.update_file(file_id, status=status)
    return status


def replicate(f, data, providers, targets=PROVIDERS):
    """Upload → download → re-hash → compare, independently for every target cloud."""
    for name in targets:
        started = time.time()
        repo.upsert_backup(f["id"], name, status="UPLOADING", error_message=None)
        try:
            p = providers[name]
            p.upload(f["storage_key"], data, f["mime_type"])
            got = sha256_hex(p.download(f["storage_key"]))
            ok = got == f["sha256"].strip()
            repo.upsert_backup(
                f["id"], name, status="VERIFIED" if ok else "FAILED", provider_hash=got, uploaded_at=_now(),
                verified_at=_now() if ok else None, duration_ms=int((time.time() - started) * 1000),
                error_message=None if ok else "Checksum mismatch after upload.")
            repo.add_event(f["id"], f"{name.upper()}_VERIFIED" if ok else f"{name.upper()}_FAILED",
                           f"{_LABEL[name]} copy verified." if ok else f"{_LABEL[name]} checksum mismatch.")
        except ProviderError as e:
            repo.upsert_backup(f["id"], name, status="FAILED", uploaded_at=_now(), error_message=str(e))
            repo.add_event(f["id"], f"{name.upper()}_FAILED", str(e))
        except Exception:
            log.exception("unexpected replication error")
            repo.upsert_backup(f["id"], name, status="FAILED", uploaded_at=_now(),
                               error_message="Unexpected error during upload.")
            repo.add_event(f["id"], f"{name.upper()}_FAILED", "Unexpected error during upload.")
    return refresh_status(f["id"])


def upload_new(user, filename, data, description, providers):
    name, mime = validate_upload(filename, len(data))
    digest = sha256_hex(data)
    dup = repo.find_by_hash(user["id"], digest)
    if dup:
        return {"duplicate": True, "file": dup}
    if repo.total_bytes(user["id"]) + len(data) > Config.MAX_TOTAL_STORAGE:
        raise ApiError("Storage limit reached. Delete some files before uploading more.", 413)
    if repo.uploads_today(user["id"]) >= Config.MAX_DAILY_UPLOADS:
        raise ApiError("Daily upload limit reached. Try again tomorrow.", 429)

    file_id = str(uuid.uuid4())
    key = f"{user['id']}/{file_id}"  # server-generated: never derived from the user's file name
    f = repo.insert_file(file_id, user["id"], user["email"], name, len(data), mime, digest, description, key)
    repo.add_event(file_id, "UPLOAD_STARTED", f"Started backup of {name}.")
    for p in PROVIDERS:
        repo.upsert_backup(file_id, p, status="PENDING")
    replicate(f, data, providers)
    return {"duplicate": False, "file": repo.get_file(file_id, user["id"])}


def retry(f, providers):
    targets = [b["provider"] for b in f["backups"] if b["status"] != "VERIFIED"]
    if not targets:
        return f["status"]
    sources = [b["provider"] for b in f["backups"] if b["status"] == "VERIFIED"]
    try:
        res = restore_from(providers, f["storage_key"], f["sha256"].strip(), sources)
    except RestoreFailed:
        raise ApiError("No healthy copy is available to replicate from. Please upload the file again.", 409)
    repo.add_event(f["id"], "RETRY", f"Retrying {', '.join(_LABEL[t] for t in targets)} from {_LABEL[res.source]}.")
    return replicate(f, res.data, providers, targets)


def restore(f, providers, source="smart"):
    order = list(PROVIDERS) if source == "smart" else [source]
    repo.update_file(f["id"], restore_status="RESTORING")
    try:
        res = restore_from(providers, f["storage_key"], f["sha256"].strip(), order)
    except RestoreFailed as e:
        repo.update_file(f["id"], restore_status=None)
        repo.add_event(f["id"], "RESTORE_FAILED", "Restore failed: no verified copy could be downloaded.")
        raise ApiError("Restore failed — no verified copy could be downloaded.", 502, {"attempts": e.attempts})
    repo.update_file(f["id"], restore_status="RESTORED")
    repo.add_event(f["id"], "RESTORE_SUCCESS", f"Restored from {_LABEL[res.source]} (SHA-256 verified).")
    return res


def delete_everywhere(f, providers):
    failed = []
    for name in PROVIDERS:
        try:
            providers[name].delete(f["storage_key"])
        except ProviderError as e:
            failed.append(f"{_LABEL[name]}: {e}")
    if failed:
        raise ApiError("Could not delete from every cloud, so the record was kept. " + " ".join(failed), 502)
    repo.delete_file(f["id"])


def verify_file(f, providers):
    """Re-download every VERIFIED copy and compare hashes. Marks bad copies FAILED so retry can repair them."""
    issues = []
    for b in f["backups"]:
        if b["status"] != "VERIFIED":
            continue
        try:
            ok = sha256_hex(providers[b["provider"]].download(f["storage_key"])) == f["sha256"].strip()
            reason = None if ok else "checksum mismatch"
        except ProviderError as e:
            ok, reason = False, str(e)
        if ok:
            repo.upsert_backup(f["id"], b["provider"], verified_at=_now())
        else:
            repo.upsert_backup(f["id"], b["provider"], status="FAILED", error_message=reason)
            repo.add_event(f["id"], "INTEGRITY_FAILED", f"{_LABEL[b['provider']]}: {reason}")
            issues.append({"file": f["filename"], "provider": b["provider"], "reason": reason})
    refresh_status(f["id"])
    return issues
