import pytest

from app.services.recovery import RestoreFailed, overall_status, restore_from
from app.storage.interface import GuardedProvider, ObjectNotFound, ProviderError, StorageProvider
from app.utils.security import sha256_hex


class Fake(StorageProvider):
    def __init__(self, name, blobs=None):
        self.name, self.label, self.blobs = name, name.upper(), dict(blobs or {})

    def upload(self, key, data, content_type): self.blobs[key] = data
    def download(self, key):
        if key not in self.blobs:
            raise ObjectNotFound("missing")
        return self.blobs[key]
    def delete(self, key): self.blobs.pop(key, None)
    def exists(self, key): return key in self.blobs
    def get_metadata(self, key): return {"size": len(self.blobs[key])}
    def health(self): return True


DATA = b"hello cloudvault"
H = sha256_hex(DATA)


def test_overall_status():
    assert overall_status(["VERIFIED", "VERIFIED"]) == "VERIFIED"
    assert overall_status(["VERIFIED", "FAILED"]) == "PARTIAL"
    assert overall_status(["FAILED", "FAILED"]) == "FAILED"
    assert overall_status(["PENDING", "PENDING"]) == "PENDING"
    assert overall_status(["VERIFIED", "UPLOADING"]) == "UPLOADING"


def test_smart_restore_uses_b2_when_healthy():
    p = {"b2": Fake("b2", {"k": DATA}), "supabase": Fake("supabase", {"k": DATA})}
    assert restore_from(p, "k", H, ["b2", "supabase"]).source == "b2"


def test_smart_restore_falls_back_to_supabase_when_b2_simulated_down():
    p = {"b2": GuardedProvider(Fake("b2", {"k": DATA}), simulate_down=True), "supabase": Fake("supabase", {"k": DATA})}
    res = restore_from(p, "k", H, ["b2", "supabase"])
    assert res.source == "supabase"
    assert [a["ok"] for a in res.attempts] == [False, True]


def test_corrupted_copy_is_skipped():
    p = {"b2": Fake("b2", {"k": b"corrupt"}), "supabase": Fake("supabase", {"k": DATA})}
    assert restore_from(p, "k", H, ["b2", "supabase"]).source == "supabase"


def test_restore_fails_when_no_valid_copy():
    p = {"b2": Fake("b2"), "supabase": Fake("supabase", {"k": b"bad"})}
    with pytest.raises(RestoreFailed) as e:
        restore_from(p, "k", H, ["b2", "supabase"])
    assert len(e.value.attempts) == 2


def test_guarded_provider_blocks_all_operations():
    g = GuardedProvider(Fake("b2"), simulate_down=True)
    for call in (lambda: g.upload("k", b"x", "text/plain"), lambda: g.download("k"), lambda: g.exists("k")):
        with pytest.raises(ProviderError):
            call()
    assert g.health() is False
