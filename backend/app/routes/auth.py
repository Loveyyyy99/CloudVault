import re

import requests
from flask import Blueprint, g, jsonify, request

from ..config import Config
from ..models import repo
from ..utils.auth import require_auth
from ..utils.errors import ApiError

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _supabase(path, payload, params=None):
    try:
        r = requests.post(f"{Config.SUPABASE_URL}/auth/v1/{path}", json=payload, params=params, timeout=10,
                          headers={"apikey": Config.SUPABASE_ANON_KEY or ""})
    except requests.RequestException:
        raise ApiError("Authentication service is unreachable. Please try again.", 503)
    return r


def _creds():
    body = request.get_json(silent=True) or {}
    email, pw = (body.get("email") or "").strip().lower(), body.get("password") or ""
    if not EMAIL.match(email) or len(email) > 254:
        raise ApiError("Enter a valid email address.", 400)
    if len(pw) < 8 or len(pw) > 128:
        raise ApiError("Password must be 8–128 characters.", 400)
    return email, pw


def _session(data):
    return {"access_token": data["access_token"], "refresh_token": data.get("refresh_token"),
            "user": {"id": data["user"]["id"], "email": data["user"].get("email")}}


@bp.post("/register")
def register():
    email, pw = _creds()
    r = _supabase("signup", {"email": email, "password": pw})
    if r.status_code >= 400:
        raise ApiError("Could not create the account. The email may already be registered.", 400)
    data = r.json()
    if data.get("access_token"):
        repo.upsert_user(data["user"]["id"], email)
        return jsonify(_session(data)), 201
    return jsonify({"message": "Account created. Check your email to confirm, then sign in."}), 201


@bp.post("/login")
def login():
    email, pw = _creds()
    r = _supabase("token", {"email": email, "password": pw}, {"grant_type": "password"})
    if r.status_code != 200:
        raise ApiError("Incorrect email or password.", 401)
    data = r.json()
    repo.upsert_user(data["user"]["id"], email)
    return jsonify(_session(data))


@bp.post("/refresh")
def refresh():
    token = (request.get_json(silent=True) or {}).get("refresh_token")
    if not token:
        raise ApiError("Missing refresh token.", 400)
    r = _supabase("token", {"refresh_token": token}, {"grant_type": "refresh_token"})
    if r.status_code != 200:
        raise ApiError("Your session has expired. Please sign in again.", 401)
    return jsonify(_session(r.json()))


@bp.get("/me")
@require_auth
def me():
    return jsonify(g.user)
