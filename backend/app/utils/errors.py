import logging

import psycopg2
from werkzeug.exceptions import HTTPException

log = logging.getLogger("cloudvault")


class ApiError(Exception):
    def __init__(self, message, status=400, extra=None):
        super().__init__(message)
        self.message, self.status, self.extra = message, status, extra or {}


def register_error_handlers(app):
    from flask import jsonify

    @app.errorhandler(ApiError)
    def _api(e):
        return jsonify({"error": e.message, **e.extra}), e.status

    @app.errorhandler(HTTPException)
    def _http(e):
        msgs = {413: "That file is larger than the allowed upload size.", 404: "Resource not found.",
                405: "Method not allowed."}
        return jsonify({"error": msgs.get(e.code, e.description)}), e.code

    @app.errorhandler(psycopg2.Error)
    def _db(e):
        log.exception("database error")
        return jsonify({"error": "The database is temporarily unavailable. Please try again."}), 503

    @app.errorhandler(Exception)
    def _any(e):
        log.exception("unhandled error")  # stack trace goes to logs only
        return jsonify({"error": "Something went wrong on our side. Please try again."}), 500
