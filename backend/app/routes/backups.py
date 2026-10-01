from flask import Blueprint, g, jsonify, request

from ..models import repo
from ..utils.auth import require_auth
from ..utils.errors import ApiError

bp = Blueprint("backups", __name__, url_prefix="/api/backups")


@bp.get("/history")
@require_auth
def history():
    status = (request.args.get("status") or "").upper() or None
    if status and status not in {"PENDING", "UPLOADING", "PARTIAL", "VERIFIED", "FAILED"}:
        raise ApiError("Unknown status filter.", 400)
    return jsonify(repo.history(g.user["id"], status))


@bp.get("/status")
@require_auth
def status():
    return jsonify(repo.status_counts(g.user["id"]))
