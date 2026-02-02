from datetime import date
import pytest

from src.models.task import Task
from src.models.status import Status


def test_cycle_time_happy_case():
    task = Task(
        code="T-220",
        name="Cycle time",
        status=Status.DONE,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 10),
    )

    assert task.cycle_time() == 9


def test_cycle_time_requires_done_status():
    task = Task(
        code="T-221",
        name="Not done",
        status=Status.IN_PROGRESS,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 10),
    )

    with pytest.raises(ValueError):
        task.cycle_time()


def test_cycle_time_requires_dates():
    task = Task(code="T-222", name="Missing dates", status=Status.DONE)

    with pytest.raises(ValueError):
        task.cycle_time()
