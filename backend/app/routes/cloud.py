from flask import Blueprint, g, jsonify

from ..models import repo
from ..services.backup import build_providers
from ..utils.auth import require_auth

bp = Blueprint("cloud", __name__, url_prefix="/api/cloud")


def _status(name):
    sim = repo.get_simulation(g.user["id"])
    if sim[f"{name}_down"]:
        return {"provider": name, "status": "SIMULATED_FAILURE", "healthy": False}
    healthy = build_providers(g.user["id"])[name].health()
    return {"provider": name, "status": "HEALTHY" if healthy else "UNAVAILABLE", "healthy": healthy}


@bp.get("/b2/status")
@require_auth
def b2():
    return jsonify(_status("b2"))


@bp.get("/supabase/status")
@require_auth
def supabase():
    return jsonify(_status("supabase"))
