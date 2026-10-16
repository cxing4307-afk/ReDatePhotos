from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .core import MANIFEST_NAME, apply_plan, plan_renames, scan_directory, undo_last


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/scan")
    def scan():
        folder = _requested_directory()
        result = scan_directory(folder)
        plan = plan_renames(result)
        return jsonify(
            directory=str(folder),
            items=[
                {
                    "source": item.source.name,
                    "destination": item.destination.name,
                    "captured_at": item.captured_at.isoformat(sep=" "),
                    "date_source": item.date_source,
                }
                for item in plan
            ],
            skipped=[{"name": item.path.name, "reason": item.reason} for item in result.skipped],
            can_undo=(folder / MANIFEST_NAME).exists(),
        )

    @app.post("/api/apply")
    def apply():
        folder = _requested_directory()
        return jsonify(renamed=apply_plan(plan_renames(scan_directory(folder))))

    @app.post("/api/undo")
    def undo():
        return jsonify(restored=undo_last(_requested_directory()))

    @app.errorhandler(Exception)
    def handle_error(error: Exception):
        app.logger.exception("Request failed")
        return jsonify(error=str(error)), 400

    return app


def _requested_directory() -> Path:
    value = (request.get_json(silent=True) or {}).get("directory", "")
    folder = Path(value).expanduser().resolve()
    if not value or not folder.is_dir():
        raise ValueError("Enter an existing directory")
    return folder


def main() -> None:
    create_app().run(host="127.0.0.1", port=5050)


if __name__ == "__main__":
    main()
