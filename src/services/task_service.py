from src.models.status import Status


class TaskService:
    def __init__(self, repo):
        self.repo = repo

    def create(self, task):
        self.repo.add(task)

    def list(self):
        return self.repo.list()

    def get(self, code: str):
        return self.repo.get(code)

    def move(self, code: str, new_status: Status):
        task = self.repo.get(code)
        old_status = task.status
        task.move_to(new_status)
        self.repo.update(task)
        return old_status, new_status

    def remove(self, code: str):
        self.repo.remove(code)

    def update(self, task):
        self.repo.update(task)
