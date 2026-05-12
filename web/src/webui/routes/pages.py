from flask import Blueprint, current_app, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.get("/")
def landing():
    return render_template("landing.html")


@pages_bp.get("/app")
def index():
    return render_template("index.html")


@pages_bp.get("/results/<task_id>")
def results(task_id: str):
    manager = current_app.extensions["task_manager"]
    task = manager.get_task(task_id)
    if not task:
        return render_template("results.html", error="Task not found", task_id=task_id), 404
    if task.status != "completed":
        return render_template("results.html", error="Task not completed yet", task_id=task_id), 400
    payload = task.to_dict()
    return render_template("results.html", task=payload)
