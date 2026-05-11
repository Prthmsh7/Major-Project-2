import os


class Config:
    SECRET_KEY = os.environ.get("WEB_SECRET_KEY", "dev-secret-key")
    UPLOAD_FOLDER = os.path.join("web", "uploads")
    RESULTS_FOLDER = os.path.join("web", "results")
    ALLOWED_EXTENSIONS = {"cpp", "cc", "cxx", "c++"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
