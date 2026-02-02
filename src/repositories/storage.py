import json
import os


class JsonStorage:
    def __init__(self, filename="kanban.json"):
        self.filename = filename

    def load(self):
        if not os.path.exists(self.filename):
            return {"tasks": {}, "sprints": {}}
        with open(self.filename) as f:
            return json.load(f)

    def save(self, data):
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=2)
