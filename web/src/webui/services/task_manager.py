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
        upload_path = os.path.join(self.upload_folder, f"{task_id}_{filename}")
        file_storage.save(upload_path)

        task = WebCoverageTask(task_id=task_id, source_file=upload_path, config=config)
        self.tasks[task_id] = task

        thread = threading.Thread(target=self._run_task, args=(task,), daemon=True)
        thread.start()
        return task

    def _run_task(self, task: WebCoverageTask) -> None:
        try:
            task.status = "running"
            task.progress = 5
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
        return {task_id: task.to_dict() for task_id, task in self.tasks.items()}
