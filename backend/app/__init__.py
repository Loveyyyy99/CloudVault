import logging
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from .config import Config
from .utils.errors import register_error_handlers


class _Json(DefaultJSONProvider):
    @staticmethod
    def default(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return DefaultJSONProvider.default(o)


def create_app():
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)
    app.json = _Json(app)
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_FILE_SIZE + 1024 * 1024
    CORS(app, origins=Config.CORS_ORIGINS,
         expose_headers=["X-Restore-Source", "X-Restore-Attempts", "Content-Disposition"])

    from .routes import auth, backups, cloud, dashboard, files, simulation
    for m in (auth, files, backups, cloud, simulation, dashboard):
        app.register_blueprint(m.bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    register_error_handlers(app)
    return app
