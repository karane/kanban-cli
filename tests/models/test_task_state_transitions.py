from datetime import date
import pytest

from src.models.task import Task
from src.models.status import Status


def test_valid_happy_path_transition():
    task = Task(code="T-200", name="Happy path")

    task.start(date(2025, 1, 1))
    assert task.status == Status.IN_PROGRESS

    task.send_to_review(date(2025, 1, 2))
    assert task.status == Status.REVIEW

    task.move_to(Status.TESTING_DEPLOYMENT)
    assert task.status == Status.TESTING_DEPLOYMENT

    task.move_to_done(date(2025, 1, 4))
    assert task.status == Status.DONE


@pytest.mark.parametrize(
    "from_status,to_status",
    [
        (Status.TODO, Status.REVIEW),
        (Status.TODO, Status.TESTING_DEPLOYMENT),
        (Status.IN_PROGRESS, Status.DONE),
        (Status.REVIEW, Status.DONE),
        (Status.DONE, Status.IN_PROGRESS),
    ],
)
def test_invalid_state_transitions(from_status, to_status):
    task = Task(code="T-201", name="Invalid", status=from_status)

    with pytest.raises(ValueError):
        task.move_to(to_status)
