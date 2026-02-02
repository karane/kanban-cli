from datetime import date
from typing import Optional
from src.models.status import Status, VALID_TRANSITIONS

class Task:
    def __init__(
        self,
        code: str,
        name: str,
        status: Status = Status.TODO,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sprint_code: Optional[str] = None,
        review_date: Optional[date] = None,
        estimated_time: Optional[float] = None,
        actual_time: Optional[float] = None,
        jira_link: Optional[str] = None,
        comment: Optional[str] = None,
    ):
        self.code = code
        self.name = name
        self.status = status if isinstance(status, Status) else Status(status)
        self.start_date = start_date
        self.end_date = end_date
        self.sprint_code = sprint_code
        self.review_date = review_date
        self.estimated_time = estimated_time
        self.actual_time = actual_time
        self.jira_link = jira_link
        self.comment = comment

    def move_to(self, new_status: Status):
        allowed = VALID_TRANSITIONS[self.status]
        if new_status not in allowed:
            raise ValueError(f"Invalid transition {self.status.name} → {new_status.name}")
        self.status = new_status

    def start(self, start_date: date):
        if self.status != Status.TODO:
            raise ValueError("Task already started")
        self.status = Status.IN_PROGRESS
        self.start_date = start_date

    def send_to_review(self, when: date):
        self.move_to(Status.REVIEW)
        self.review_date = when

    def move_to_done(self, end_date: date):
        if self.status != Status.TESTING_DEPLOYMENT:
            raise ValueError("Task must be in TESTING_DEPLOYMENT to be completed")
        self.status = Status.DONE
        self.end_date = end_date

    def is_done(self) -> bool:
        return self.status == Status.DONE

    def cycle_time(self):
        if self.status != Status.DONE:
            raise ValueError("Cycle time only available for DONE tasks")
        if not self.start_date or not self.end_date:
            raise ValueError("Start and end dates required")
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        return (self.end_date - self.start_date).days
