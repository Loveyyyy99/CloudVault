"""Supabase Storage via its REST API (free 1 GB, 50 MB max object size, no card)."""
import requests

from ..config import Config
from .interface import ObjectNotFound, ProviderError, StorageProvider


class SupabaseStorage(StorageProvider):
    name, label = "supabase", "Supabase Storage"

    # ---- helpers ------------------------------------------------------
    def _cfg(self):
        if not (Config.SUPABASE_URL and Config.SUPABASE_SERVICE_ROLE_KEY):
            raise ProviderError("Supabase Storage credentials are not configured.")

    def _req(self, method, path, headers=None, **kw):
        self._cfg()
        h = {"apikey": Config.SUPABASE_SERVICE_ROLE_KEY,
             "Authorization": f"Bearer {Config.SUPABASE_SERVICE_ROLE_KEY}", **(headers or {})}
        try:
            return requests.request(method, f"{Config.SUPABASE_URL}/storage/v1/{path}", headers=h,
                                    timeout=(5, 30), **kw)
        except requests.RequestException as e:
            raise ProviderError("Supabase Storage is unreachable or timed out.") from e

    @staticmethod
    def _missing(r):
        if r.status_code == 404:
            return True
        try:
            return r.status_code == 400 and str(r.json().get("statusCode")) == "404"
        except ValueError:
            return False

    def _fail(self, r, what):
        if r.status_code in (401, 403):
            raise ProviderError("Supabase Storage rejected the credentials or permissions.")
        if r.status_code == 413:
            raise ProviderError("File is larger than the Supabase free-plan limit (50 MB).")
        raise ProviderError(f"Supabase Storage {what} failed.")

    def _find(self, key):
        folder, _, name = key.rpartition("/")
        r = self._req("POST", f"object/list/{Config.SUPABASE_BUCKET_NAME}",
                      json={"prefix": folder, "search": name, "limit": 10})
        if r.status_code != 200:
            self._fail(r, "lookup")
        return next((o for o in r.json() if o.get("name") == name), None)

    # ---- StorageProvider ---------------------------------------------
    def upload(self, key, data, content_type):
        r = self._req("POST", f"object/{Config.SUPABASE_BUCKET_NAME}/{key}",
                      headers={"Content-Type": content_type, "x-upsert": "true"}, data=data)
        if r.status_code not in (200, 201):
            self._fail(r, "upload")

    def download(self, key):
        r = self._req("GET", f"object/authenticated/{Config.SUPABASE_BUCKET_NAME}/{key}")
        if self._missing(r):
            raise ObjectNotFound("File not found in Supabase Storage.")
        if r.status_code != 200:
            self._fail(r, "download")
        return r.content

    def delete(self, key):
        r = self._req("DELETE", f"object/{Config.SUPABASE_BUCKET_NAME}/{key}")
        if r.status_code not in (200, 204) and not self._missing(r):
            self._fail(r, "delete")

    def exists(self, key):
        return self._find(key) is not None

    def get_metadata(self, key):
        o = self._find(key)
        if not o:
            raise ObjectNotFound("File not found in Supabase Storage.")
        m = o.get("metadata") or {}
        return {"size": m.get("size"), "etag": m.get("eTag"), "last_modified": o.get("updated_at"),
                "content_type": m.get("mimetype")}

    def health(self):
        try:
            return self._req("GET", f"bucket/{Config.SUPABASE_BUCKET_NAME}").status_code == 200
        except ProviderError:
            return False
