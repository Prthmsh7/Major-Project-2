import os
import threading
import uuid
from datetime import datetime
from typing import Dict

from werkzeug.utils import secure_filename

from webui.models import WebCoverageTask
from webui.services.task_runner import run_coverage_job


class TaskManager:
    def __init__(self, upload_folder: str, allowed_extensions: set[str]):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        self.tasks: Dict[str, WebCoverageTask] = {}

    def allowed_file(self, filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in self.allowed_extensions

    def create_task(self, file_storage, config) -> WebCoverageTask:
        filename = secure_filename(file_storage.filename)
        task_id = str(uuid.uuid4())
        source_path = os.path.join(self.upload_folder, f"{task_id}_{filename}")
        file_storage.save(source_path)
        return self._spawn_task(task_id, source_path, config)

    def create_task_from_code(self, source_code: str, source_filename: str, config) -> WebCoverageTask:
        filename = secure_filename(source_filename or "snippet.cpp")
        if not filename.endswith((".cpp", ".cc", ".cxx", ".c++")):
            filename += ".cpp"
        task_id = str(uuid.uuid4())
        source_path = os.path.join(self.upload_folder, f"{task_id}_{filename}")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)
        return self._spawn_task(task_id, source_path, config)

    def _spawn_task(self, task_id: str, source_path: str, config) -> WebCoverageTask:
        task = WebCoverageTask(task_id=task_id, source_file=source_path, config=config)
        self.tasks[task_id] = task
        threading.Thread(target=self._run_task, args=(task,), daemon=True).start()
        return task

    def _run_task(self, task: WebCoverageTask) -> None:
        try:
            task.status = "running"
            task.progress = 10
            _, _, result = run_coverage_job(task.source_file, task.config)
            task.result = result
            task.status = "completed"
            task.progress = 100
        except Exception as exc:
            task.status = "error"
            task.error = str(exc)
        finally:
            task.end_time = datetime.now()

    def get_task(self, task_id: str):
        return self.tasks.get(task_id)

    def all_tasks(self):
        return {k: v.to_dict() for k, v in self.tasks.items()}
