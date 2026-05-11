import os
import sys

WEB_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(WEB_DIR)
WEB_SRC = os.path.join(WEB_DIR, "src")

sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, WEB_SRC)

from webui.app import create_app

app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
