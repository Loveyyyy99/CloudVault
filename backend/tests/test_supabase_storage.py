import pytest

from app.config import Config
from app.storage import supabase_storage as mod
from app.storage.interface import ObjectNotFound, ProviderError


class Resp:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code, self._body, self.content = status, body, content

    def json(self):
        return self._body


@pytest.fixture(autouse=True)
def cfg(monkeypatch):
    monkeypatch.setattr(Config, "SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setattr(Config, "SUPABASE_SERVICE_ROLE_KEY", "service-key")
    monkeypatch.setattr(Config, "SUPABASE_BUCKET_NAME", "cloudvault")


def patch(monkeypatch, resp):
    calls = []
    monkeypatch.setattr(mod.requests, "request", lambda m, u, **kw: calls.append((m, u)) or resp)
    return calls


def test_upload_and_download_paths(monkeypatch):
    calls = patch(monkeypatch, Resp(200, content=b"data"))
    s = mod.SupabaseStorage()
    s.upload("u/f", b"data", "text/plain")
    assert s.download("u/f") == b"data"
    assert calls[0] == ("POST", "https://x.supabase.co/storage/v1/object/cloudvault/u/f")
    assert calls[1][1].endswith("/object/authenticated/cloudvault/u/f")


def test_missing_object_maps_to_not_found(monkeypatch):
    patch(monkeypatch, Resp(400, {"statusCode": "404"}))
    with pytest.raises(ObjectNotFound):
        mod.SupabaseStorage().download("u/f")


def test_bad_credentials_and_too_large(monkeypatch):
    patch(monkeypatch, Resp(401))
    with pytest.raises(ProviderError):
        mod.SupabaseStorage().upload("u/f", b"x", "text/plain")
    patch(monkeypatch, Resp(413))
    with pytest.raises(ProviderError, match="50 MB"):
        mod.SupabaseStorage().upload("u/f", b"x", "text/plain")


def test_exists_uses_listing(monkeypatch):
    patch(monkeypatch, Resp(200, [{"name": "f", "metadata": {"size": 4}}]))
    s = mod.SupabaseStorage()
    assert s.exists("u/f") is True and s.get_metadata("u/f")["size"] == 4
    patch(monkeypatch, Resp(200, []))
    assert s.exists("u/f") is False
