from datetime import date
import pytest

from src.models.task import Task
from src.models.status import Status


def test_cannot_complete_without_testing():
    task = Task(code="T-210", name="Invalid completion")

    task.start(date(2025, 1, 1))

    with pytest.raises(ValueError):
        task.move_to_done(date(2025, 1, 2))


def test_end_date_must_be_after_start_date():
    task = Task(
        code="T-211",
        name="Bad dates",
        status=Status.DONE,
        start_date=date(2025, 1, 10),
        end_date=date(2025, 1, 5),
    )

    with pytest.raises(ValueError):
        task.cycle_time()


def test_cannot_start_task_twice():
    task = Task(code="T-212", name="Double start")

    task.start(date(2025, 1, 1))

    with pytest.raises(ValueError):
        task.start(date(2025, 1, 2))
