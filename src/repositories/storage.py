import json
import os
from pathlib import Path

DEFAULT_DIR = Path.home() / ".kanban"
DEFAULT_FILE = DEFAULT_DIR / "kanban.json"


class JsonStorage:
    def __init__(self, filepath=None):
        if filepath is None:
            self.filepath = DEFAULT_FILE
        else:
            self.filepath = Path(filepath)

    def _ensure_dir(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.filepath.exists():
            return {"tasks": {}, "sprints": {}}
        with open(self.filepath) as f:
            return json.load(f)

    def save(self, data):
        self._ensure_dir()
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)
