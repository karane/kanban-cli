import pytest
from datetime import date

from src.models.sprint import Sprint
from src.models.task import Task
from src.models.status import Status


def test_create_sprint():
    sprint = Sprint(code="S-1", name="Sprint 1")

    assert sprint.code == "S-1"
    assert sprint.tasks == []


def test_add_task_to_sprint():
    sprint = Sprint(code="S-2", name="Sprint 2")
    task = Task(code="T-300", name="Sprint task")

    sprint.add_task(task)

    assert task in sprint.tasks
    assert task.sprint_code == "S-2"


def test_cannot_add_done_task_to_sprint():
    sprint = Sprint(code="S-3", name="Sprint 3")
    task = Task(
        code="T-301",
        name="Done task",
        status=Status.DONE,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
    )

    with pytest.raises(ValueError):
        sprint.add_task(task)
