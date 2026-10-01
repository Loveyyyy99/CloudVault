from flask import Blueprint, Response, g, jsonify, request

from ..models import repo
from ..services import backup as svc
from ..utils.auth import require_auth
from ..utils.errors import ApiError

bp = Blueprint("files", __name__, url_prefix="/api/files")
STATUSES = {"PENDING", "UPLOADING", "PARTIAL", "VERIFIED", "FAILED"}


def _owned(file_id):
    try:
        f = repo.get_file(file_id, g.user["id"])
    except Exception:  # malformed uuid → same as not found
        f = None
    if not f:
        raise ApiError("File not found.", 404)
    return f


@bp.post("/upload")
@require_auth
def upload():
    fl = request.files.get("file")
    if not fl or not fl.filename:
        raise ApiError("Choose a file to upload.", 400)
    res = svc.upload_new(g.user, fl.filename, fl.read(), (request.form.get("description") or "")[:500],
                         svc.build_providers(g.user["id"]))
    if res["duplicate"]:
        return jsonify({"duplicate": True, "error": "Duplicate detected.", "existing": res["file"]}), 409
    return jsonify({"duplicate": False, "file": res["file"]}), 201


@bp.get("")
@require_auth
def list_files():
    status = (request.args.get("status") or "").upper() or None
    if status and status not in STATUSES:
        raise ApiError("Unknown status filter.", 400)
    return jsonify(repo.list_files(g.user["id"], status))


@bp.get("/<file_id>")
@require_auth
def get_file(file_id):
    f = _owned(file_id)
    f["events"] = repo.list_events(f["id"])
    return jsonify(f)


@bp.delete("/<file_id>")
@require_auth
def delete_file(file_id):
    svc.delete_everywhere(_owned(file_id), svc.build_providers(g.user["id"]))
    return jsonify({"message": "File deleted from all clouds."})


@bp.post("/<file_id>/retry")
@require_auth
def retry(file_id):
    f = _owned(file_id)
    svc.retry(f, svc.build_providers(g.user["id"]))
    return jsonify(repo.get_file(file_id, g.user["id"]))


@bp.get("/<file_id>/restore")
@require_auth
def restore(file_id):
    import json

    from werkzeug.utils import secure_filename
    source = request.args.get("source", "smart")
    if source not in ("smart", "b2", "supabase"):
        raise ApiError("Unknown restore source.", 400)
    f = _owned(file_id)
    res = svc.restore(f, svc.build_providers(g.user["id"]), source)
    return Response(res.data, mimetype=f["mime_type"], headers={
        "Content-Disposition": f'attachment; filename="{secure_filename(f["filename"])}"',
        "X-Restore-Source": res.source, "X-Restore-Attempts": json.dumps(res.attempts),
        "X-Content-Type-Options": "nosniff"})
