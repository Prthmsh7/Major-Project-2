from flask import Blueprint, current_app, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/tasks")
def create_task():
    manager = current_app.extensions["task_manager"]
    input_mode = request.form.get("input_mode", "upload")

    config = {
        "coverage_type": request.form.get("coverage_type", "line"),
        "max_iters": int(request.form.get("max_iters", 5)),
        "coverage_threshold": float(request.form.get("coverage_threshold", 100.0)),
        "objective": request.form.get("objective", "coverage"),
        "mutation_threshold": float(request.form.get("mutation_threshold", 70.0)),
    }

    if input_mode == "editor":
        source_code = request.form.get("source_code", "")
        if not source_code.strip():
            return jsonify({"error": "Editor is empty."}), 400
        filename = request.form.get("source_filename", "snippet.cpp")
        task = manager.create_task_from_code(source_code, filename, config)
        return jsonify({"task_id": task.task_id}), 202

    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not manager.allowed_file(file.filename):
        return jsonify({"error": "Invalid file type."}), 400

    task = manager.create_task(file, config)
    return jsonify({"task_id": task.task_id}), 202


@api_bp.get("/tasks/<task_id>")
def get_task(task_id: str):
    manager = current_app.extensions["task_manager"]
    task = manager.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict())
