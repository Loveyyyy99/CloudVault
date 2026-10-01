import time
from functools import wraps

import requests
from flask import g, request

from ..config import Config
from .errors import ApiError

_cache: dict = {}


def verify_token(token: str) -> dict:
    """Validate a Supabase access token by asking Supabase Auth (works for any signing-key type)."""
    hit = _cache.get(token)
    if hit and hit[0] > time.time():
        return hit[1]
    try:
        r = requests.get(
            f"{Config.SUPABASE_URL}/auth/v1/user",
            headers={"apikey": Config.SUPABASE_ANON_KEY or "", "Authorization": f"Bearer {token}"},
            timeout=8,
        )
    except requests.RequestException:
        raise ApiError("Authentication service is unreachable. Please try again.", 503)
    if r.status_code != 200:
        raise ApiError("Your session has expired. Please sign in again.", 401)
    u = r.json()
    user = {"id": u["id"], "email": u.get("email", "")}
    _cache[token] = (time.time() + 60, user)
    if len(_cache) > 500:
        _cache.clear()
    return user


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer ") or len(header) < 20:
            raise ApiError("Please sign in to continue.", 401)
        g.user = verify_token(header[7:])
        return fn(*args, **kwargs)

    return wrapper
