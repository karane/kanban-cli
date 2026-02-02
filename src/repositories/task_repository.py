from datetime import date
from src.models.task import Task
from src.models.status import Status


class TaskRepository:
    def __init__(self, storage):
        self.storage = storage

    def add(self, task: Task):
        data = self.storage.load()
        if task.code in data["tasks"]:
            raise ValueError("Task already exists")

        data["tasks"][task.code] = self._to_dict(task)
        self.storage.save(data)

    def list(self):
        data = self.storage.load()
        return [self._from_dict(t) for t in data["tasks"].values()]

    def get(self, code: str):
        data = self.storage.load()
        task_data = data["tasks"].get(code)
        if not task_data:
            raise ValueError(f"Task '{code}' not found")
        return self._from_dict(task_data)

    def update(self, task: Task):
        data = self.storage.load()
        if task.code not in data["tasks"]:
            raise ValueError(f"Task '{task.code}' not found")
        data["tasks"][task.code] = self._to_dict(task)
        self.storage.save(data)

    def remove(self, code: str):
        data = self.storage.load()
        if code not in data["tasks"]:
            raise ValueError(f"Task '{code}' not found")
        del data["tasks"][code]
        self.storage.save(data)

    # ---------- Internal helpers ----------
    def _to_dict(self, task: Task) -> dict:
        """Convert Task object to JSON-serializable dict."""
        return {
            "code": task.code,
            "name": task.name,
            "status": task.status.value,
            "sprint_code": task.sprint_code,
            "start_date": task.start_date.isoformat() if task.start_date else None,
            "review_date": task.review_date.isoformat() if task.review_date else None,
            "end_date": task.end_date.isoformat() if task.end_date else None,
            "estimated_time": task.estimated_time,
            "actual_time": task.actual_time,
            "jira_link": task.jira_link,
            "comment": task.comment,
        }

    def _from_dict(self, raw: dict) -> Task:
        raw_copy = raw.copy()

        # Pop keys that we want to handle separately
        status_str = raw_copy.pop("status", "TODO")
        start_date_str = raw_copy.pop("start_date", None)
        review_date_str = raw_copy.pop("review_date", None)
        end_date_str = raw_copy.pop("end_date", None)

        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        review_date = date.fromisoformat(review_date_str) if review_date_str else None
        end_date = date.fromisoformat(end_date_str) if end_date_str else None

        return Task(
            **raw_copy,
            status=Status(status_str),
            start_date=start_date,
            review_date=review_date,
            end_date=end_date,
        )
