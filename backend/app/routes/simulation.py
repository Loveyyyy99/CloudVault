from flask import Blueprint, g, jsonify

from ..models import repo
from ..utils.auth import require_auth

bp = Blueprint("simulation", __name__, url_prefix="/api/simulation")


def _set(b2=None, supabase=None, reset=False):
    cur = repo.get_simulation(g.user["id"])
    a = False if reset else (cur["b2_down"] if b2 is None else b2)
    z = False if reset else (cur["supabase_down"] if supabase is None else supabase)
    repo.set_simulation(g.user["id"], g.user["email"], a, z)
    return jsonify({"b2_down": a, "supabase_down": z})


@bp.get("")
@require_auth
def get():
    return jsonify(repo.get_simulation(g.user["id"]))


@bp.post("/b2-failure")
@require_auth
def b2_failure():
    return _set(b2=True)


@bp.post("/supabase-failure")
@require_auth
def supabase_failure():
    return _set(supabase=True)


@bp.post("/reset")
@require_auth
def reset():
    return _set(reset=True)
