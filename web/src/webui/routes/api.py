from flask import Blueprint, current_app, jsonify, request

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.post("/tasks")
def create_task():
    task_manager = current_app.extensions["task_manager"]
    input_mode = request.form.get("input_mode", "upload")

    config = {
        "coverage_type": request.form.get("coverage_type", "line"),
        "max_iters": int(request.form.get("max_iters", 5)),
        "coverage_threshold": float(request.form.get("coverage_threshold", 100.0)),
        "model": request.form.get("model", "gemini-2.5-flash"),
        "focus_mode": request.form.get("focus_mode", "coverage"),
    }
    if input_mode == "editor":
        source_code = request.form.get("source_code", "")
        source_filename = request.form.get("source_filename", "snippet.cpp")
        if not source_code.strip():
            return jsonify({"error": "Editor is empty. Please provide C++ code."}), 400
        task = task_manager.create_task_from_code(source_code, source_filename, config)
    else:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        if not task_manager.allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        task = task_manager.create_task(file, config)

    return jsonify({"task_id": task.task_id}), 202


@api_bp.get("/tasks/<task_id>")
def task_status(task_id: str):
    task_manager = current_app.extensions["task_manager"]
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict())


@api_bp.get("/tasks")
def list_tasks():
    task_manager = current_app.extensions["task_manager"]
    return jsonify(task_manager.all_tasks())
