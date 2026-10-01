from flask import Blueprint, g, jsonify

from ..config import Config
from ..models import repo
from ..utils.auth import require_auth

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _pct(used, cap):
    return round(min(100, used * 100 / cap), 1) if cap else 0


@bp.get("/stats")
@require_auth
def stats():
    totals, per, perf, trend, recent = repo.dashboard(g.user["id"])
    cap = Config.MAX_TOTAL_STORAGE
    providers = {p: {"used": per.get(p, 0), "pct": _pct(per.get(p, 0), cap)} for p in ("b2", "supabase")}
    return jsonify({
        "totals": totals,
        "providers": providers,
        "limits": {"max_file_size": Config.MAX_FILE_SIZE, "max_total_storage": cap,
                   "max_daily_uploads": Config.MAX_DAILY_UPLOADS},
        "usage": {"storage_pct": _pct(totals["bytes"], cap),
                  "daily_pct": _pct(totals["uploads_today"], Config.MAX_DAILY_UPLOADS)},
        "metrics": {"success_rate": round(perf["ok"] * 100 / perf["total"], 1) if perf["total"] else None,
                    "avg_backup_ms": perf["avg_ms"], "last_success": perf["last_ok"],
                    "failed_backups": totals["failed"] + totals["partial"]},
        "trend": trend, "recent": recent, "simulation": repo.get_simulation(g.user["id"]),
    })
