import os
from flask import Flask

from webui.config import Config
from webui.routes.api import api_bp
from webui.routes.pages import pages_bp
from webui.services.task_manager import TaskManager


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["RESULTS_FOLDER"], exist_ok=True)

    app.extensions["task_manager"] = TaskManager(
        upload_folder=app.config["UPLOAD_FOLDER"],
        allowed_extensions=app.config["ALLOWED_EXTENSIONS"],
    )

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)
    return app
