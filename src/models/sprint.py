from dataclasses import dataclass
from datetime import date

from src.models.status import Status


@dataclass
class Sprint:
    code: str
    name: str
    start_date: date
    end_date: date
    closed: bool = False

    def __init__(
        self,
        code: str,
        name: str,
        start_date=None,
        end_date=None,
    ):
        self.code = code
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.tasks = []

    def add_task(self, task):
        if task.status == Status.DONE:
            raise ValueError("Cannot add DONE task to sprint")

        if task in self.tasks:
            return  # idempotent

        task.sprint_code = self.code
        self.tasks.append(task)

    def close(self):
        if self.closed:
            raise ValueError("Sprint already closed")
        self.closed = True

    def is_active_on(self, day: date) -> bool:
        return (self.start_date <= day <= self.end_date 
                and not self.closed
                )
    
    def is_active(self, today):
        return (self.start_date 
                and self.end_date 
                and self.start_date <= today <= self.end_date
                )

