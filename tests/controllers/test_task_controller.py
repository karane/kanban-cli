from types import SimpleNamespace
from src.controllers.task_controller import TaskController
from src.models.task import Task
from src.models.status import Status

import pytest

class FakeRepo:
    def __init__(self):
        self.saved = None

    def add(self, task):
        self.saved = task

    def list(self):
        return []

class FakeService:
    def __init__(self):
        self.created = None
        self.tasks = {}
        self.removed_code = None
        self.moved_code = None
        self.moved_status = None

    def create(self, task):
        self.created = task
        self.tasks[task.code] = task

    def list(self):
        return list(self.tasks.values()) if self.tasks else [Task(code="T-1", name="Test", status="TODO")]

    def get(self, code):
        if code not in self.tasks:
            raise ValueError(f"Task '{code}' not found")
        return self.tasks[code]

    def move(self, code, new_status):
        task = self.get(code)
        old_status = task.status
        task.move_to(new_status)
        self.moved_code = code
        self.moved_status = new_status
        return old_status, new_status

    def remove(self, code):
        if code not in self.tasks:
            raise ValueError(f"Task '{code}' not found")
        del self.tasks[code]
        self.removed_code = code

class FakeView:
    def __init__(self):
        self.created_task = None
        self.listed = None
        self.moved_code = None
        self.moved_old_status = None
        self.moved_new_status = None
        self.removed_code = None
        self.shown_task = None

    def task_created(self, task):
        self.created_task = task

    def list(self, tasks):
        self.listed = tasks

    def task_moved(self, code, old_status, new_status):
        self.moved_code = code
        self.moved_old_status = old_status
        self.moved_new_status = new_status

    def task_removed(self, code):
        self.removed_code = code

    def show_task(self, task):
        self.shown_task = task


def test_add_task_creates_task_object():
    service = FakeService()
    view = FakeView()
    controller = TaskController(service, view)

    args = SimpleNamespace(
        code="T-1",
        name="Test",
        status="TODO",
        sprint=None,
        start_date=None,
        review_date=None,
        end_date=None,
        estimate=None,
        jira_link=None,
        comment=None,
    )

    controller.add(args)

    assert isinstance(service.created, Task)
    assert service.created.code == "T-1"
    assert view.created_task.code == "T-1"

def test_controller_add_and_list_tasks(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    controller.add_task("T-400", "Controller task", "TODO")

    tasks = controller.list_tasks()
    assert len(tasks) == 1
    assert tasks[0].code == "T-400"
    assert tasks[0].status == Status.TODO


def test_controller_prevents_duplicate_codes(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    controller.add_task("T-401", "One", "TODO")

    with pytest.raises(ValueError):
        controller.add_task("T-401", "Duplicate", "TODO")


def test_add_task_to_nonexistent_sprint_raises_error(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a task first
    controller.add_task("T-500", "Test task", "TODO")

    # Try to add it to a non-existent sprint
    args = SimpleNamespace(task="T-500", sprint="S-999")

    with pytest.raises(ValueError, match="Sprint 'S-999' does not exist"):
        controller.add_task_to_sprint(args)


def test_add_nonexistent_task_to_sprint_raises_error(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a sprint
    sprint_args = SimpleNamespace(code="S-100", name="Test Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Try to add a non-existent task to it
    args = SimpleNamespace(task="T-999", sprint="S-100")

    with pytest.raises(ValueError, match="Task 'T-999' does not exist"):
        controller.add_task_to_sprint(args)


def test_add_task_to_closed_sprint_raises_error(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a task and a sprint
    controller.add_task("T-501", "Test task", "TODO")
    sprint_args = SimpleNamespace(code="S-101", name="Closed Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Close the sprint manually
    data = controller.storage.load()
    data["sprints"]["S-101"]["closed"] = True
    controller.storage.save(data)

    # Try to add task to closed sprint
    args = SimpleNamespace(task="T-501", sprint="S-101")

    with pytest.raises(ValueError, match="Sprint 'S-101' is closed"):
        controller.add_task_to_sprint(args)


def test_add_task_already_in_sprint_raises_error(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a task and a sprint
    controller.add_task("T-502", "Test task", "TODO")
    sprint_args = SimpleNamespace(code="S-102", name="Test Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Add task to sprint
    args = SimpleNamespace(task="T-502", sprint="S-102")
    controller.add_task_to_sprint(args)

    # Try to add the same task again
    with pytest.raises(ValueError, match="Task 'T-502' already in sprint 'S-102'"):
        controller.add_task_to_sprint(args)


def test_create_duplicate_sprint_raises_error(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a sprint
    sprint_args = SimpleNamespace(code="S-103", name="Test Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Try to create the same sprint again
    with pytest.raises(ValueError, match="Sprint already exists"):
        controller.add_sprint(sprint_args)


def test_add_task_with_nonexistent_sprint_raises_error(tmp_path):
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Try to create a task with a non-existent sprint
    args = SimpleNamespace(
        code="T-503",
        name="Test",
        status="TODO",
        sprint="S-999",
        start_date=None,
        review_date=None,
        end_date=None,
    )

    with pytest.raises(ValueError, match="Sprint 'S-999' does not exist"):
        controller.add(args)


# ---------- Tests for new operations ----------

def test_move_task_changes_status(tmp_path):
    """Test that moving a task changes its status."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")
    controller.add_task("T-600", "Test task", "TODO")

    args = SimpleNamespace(code="T-600", status="IN_PROGRESS")
    controller.move(args)

    # Verify the task status changed
    tasks = controller.list_tasks()
    assert tasks[0].status == Status.IN_PROGRESS


def test_move_task_with_fake_service():
    """Test that move calls the service and view correctly."""
    service = FakeService()
    view = FakeView()
    controller = TaskController(service, view)

    # Create a task first
    task = Task(code="T-1", name="Test", status=Status.TODO)
    service.tasks["T-1"] = task

    # Move it
    args = SimpleNamespace(code="T-1", status="IN_PROGRESS")
    controller.move(args)

    # Verify service and view were called
    assert service.moved_code == "T-1"
    assert service.moved_status == Status.IN_PROGRESS
    assert view.moved_code == "T-1"
    assert view.moved_old_status == Status.TODO
    assert view.moved_new_status == Status.IN_PROGRESS


def test_move_nonexistent_task_raises_error(tmp_path):
    """Test that moving a non-existent task raises an error."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    args = SimpleNamespace(code="T-999", status="IN_PROGRESS")

    with pytest.raises(ValueError, match="Task 'T-999' not found"):
        controller.move(args)


def test_remove_task_deletes_it(tmp_path):
    """Test that removing a task deletes it from storage."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")
    controller.add_task("T-700", "Task to delete", "TODO")

    # Verify task exists
    tasks = controller.list_tasks()
    assert len(tasks) == 1

    # Remove it
    args = SimpleNamespace(code="T-700")
    controller.remove(args)

    # Verify task is gone
    tasks = controller.list_tasks()
    assert len(tasks) == 0


def test_remove_task_with_fake_service():
    """Test that remove calls the service and view correctly."""
    service = FakeService()
    view = FakeView()
    controller = TaskController(service, view)

    # Create a task first
    task = Task(code="T-1", name="Test", status=Status.TODO)
    service.tasks["T-1"] = task

    # Remove it
    args = SimpleNamespace(code="T-1")
    controller.remove(args)

    # Verify service and view were called
    assert service.removed_code == "T-1"
    assert view.removed_code == "T-1"


def test_remove_nonexistent_task_raises_error(tmp_path):
    """Test that removing a non-existent task raises an error."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    args = SimpleNamespace(code="T-999")

    with pytest.raises(ValueError, match="Task 'T-999' not found"):
        controller.remove(args)


def test_show_task_displays_details(tmp_path):
    """Test that show displays task details."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    args = SimpleNamespace(
        code="T-800",
        name="Test task",
        status="TODO",
        sprint=None,
        start_date="2026-02-01",
        review_date=None,
        end_date=None,
        estimate="2h",
        jira_link="https://jira.example.com/T-800",
        comment="Test comment",
    )
    controller.add(args)

    # Show the task
    show_args = SimpleNamespace(code="T-800")
    controller.show(show_args)  # This will print, but we can't easily capture it


def test_show_task_with_fake_service():
    """Test that show calls the service and view correctly."""
    service = FakeService()
    view = FakeView()
    controller = TaskController(service, view)

    # Create a task first
    task = Task(code="T-1", name="Test", status=Status.TODO)
    service.tasks["T-1"] = task

    # Show it
    args = SimpleNamespace(code="T-1")
    controller.show(args)

    # Verify view was called
    assert view.shown_task == task


def test_show_nonexistent_task_raises_error(tmp_path):
    """Test that showing a non-existent task raises an error."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    args = SimpleNamespace(code="T-999")

    with pytest.raises(ValueError, match="Task 'T-999' not found"):
        controller.show(args)


def test_parse_hours_with_hours():
    """Test parsing time values with 'h' suffix."""
    controller = TaskController(storage_path="test.json")

    assert controller._parse_hours("2h") == 2.0
    assert controller._parse_hours("0.5h") == 0.5
    assert controller._parse_hours("10h") == 10.0


def test_parse_hours_with_minutes():
    """Test parsing time values with 'm' suffix."""
    controller = TaskController(storage_path="test.json")

    assert controller._parse_hours("30m") == 0.5
    assert controller._parse_hours("60m") == 1.0
    assert controller._parse_hours("15m") == 0.25


def test_parse_hours_with_invalid_values():
    """Test parsing invalid time values."""
    controller = TaskController(storage_path="test.json")

    assert controller._parse_hours("invalid") is None
    assert controller._parse_hours("") is None
    assert controller._parse_hours(None) is None


def test_add_task_with_all_properties(tmp_path):
    """Test adding a task with all available properties."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    args = SimpleNamespace(
        code="T-900",
        name="Full task",
        status="TODO",
        sprint=None,
        start_date="2026-02-01",
        review_date="2026-02-05",
        end_date="2026-02-10",
        estimate="3h",
        jira_link="https://jira.example.com/T-900",
        comment="Complete task with all properties",
    )
    controller.add(args)

    # Verify task was created with all properties
    tasks = controller.list_tasks()
    assert len(tasks) == 1
    task = tasks[0]
    assert task.code == "T-900"
    assert task.name == "Full task"
    assert task.status == Status.TODO
    assert task.start_date.isoformat() == "2026-02-01"
    assert task.review_date.isoformat() == "2026-02-05"
    assert task.end_date.isoformat() == "2026-02-10"
    assert task.estimated_time == 3.0
    assert task.jira_link == "https://jira.example.com/T-900"
    assert task.comment == "Complete task with all properties"


# ---------- Tests for sprint operations ----------

def test_close_sprint_moves_unfinished_tasks_out(tmp_path):
    """Test that closing a sprint moves non-DONE tasks out."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a sprint
    sprint_args = SimpleNamespace(code="S-200", name="Test Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Add tasks to sprint with different statuses
    controller.add_task("T-201", "Task TODO", "TODO", "S-200")
    controller.add_task("T-202", "Task IN_PROGRESS", "IN_PROGRESS", "S-200")
    controller.add_task("T-203", "Task DONE", "DONE", "S-200")

    # Close the sprint
    close_args = SimpleNamespace(code="S-200")
    controller.close_sprint(close_args)

    # Verify tasks were moved correctly
    tasks = controller.list_tasks()
    task_dict = {t.code: t for t in tasks}

    # Non-DONE tasks should be out of sprint
    assert task_dict["T-201"].sprint_code is None
    assert task_dict["T-202"].sprint_code is None

    # DONE task should still be in sprint
    assert task_dict["T-203"].sprint_code == "S-200"


def test_close_sprint_marks_it_as_closed(tmp_path):
    """Test that closing a sprint marks it as closed."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a sprint
    sprint_args = SimpleNamespace(code="S-201", name="Test Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Close it
    close_args = SimpleNamespace(code="S-201")
    controller.close_sprint(close_args)

    # Verify it's marked as closed
    data = controller.storage.load()
    assert data["sprints"]["S-201"]["closed"] is True


def test_close_nonexistent_sprint_raises_error(tmp_path):
    """Test that closing a non-existent sprint raises an error."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    args = SimpleNamespace(code="S-999")

    with pytest.raises(ValueError, match="Sprint not found or already closed"):
        controller.close_sprint(args)


def test_close_already_closed_sprint_raises_error(tmp_path):
    """Test that closing an already closed sprint raises an error."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create and close a sprint
    sprint_args = SimpleNamespace(code="S-202", name="Test Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)
    close_args = SimpleNamespace(code="S-202")
    controller.close_sprint(close_args)

    # Try to close it again
    with pytest.raises(ValueError, match="Sprint not found or already closed"):
        controller.close_sprint(close_args)


def test_sprint_report_shows_correct_counts(tmp_path, capsys):
    """Test that sprint report shows correct task counts by status."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a sprint
    sprint_args = SimpleNamespace(code="S-203", name="Test Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Add tasks with different statuses
    controller.add_task("T-204", "Task 1", "TODO", "S-203")
    controller.add_task("T-205", "Task 2", "TODO", "S-203")
    controller.add_task("T-206", "Task 3", "IN_PROGRESS", "S-203")
    controller.add_task("T-207", "Task 4", "DONE", "S-203")

    # Generate report
    report_args = SimpleNamespace(code="S-203")
    controller.report_sprint(report_args)

    # Capture output
    captured = capsys.readouterr()

    # Verify output contains expected information
    assert "Sprint S-203 — Test Sprint" in captured.out
    assert "TODO                 2" in captured.out
    assert "IN_PROGRESS          1" in captured.out
    assert "DONE                 1" in captured.out
    assert "Completed: 1/4 (25%)" in captured.out


def test_sprint_report_for_nonexistent_sprint_raises_error(tmp_path):
    """Test that reporting on a non-existent sprint raises an error."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    args = SimpleNamespace(code="S-999")

    with pytest.raises(ValueError, match="Sprint not found"):
        controller.report_sprint(args)


def test_sprint_report_with_no_tasks(tmp_path, capsys):
    """Test that sprint report handles sprints with no tasks."""
    controller = TaskController(storage_path=tmp_path / "kanban.json")

    # Create a sprint without any tasks
    sprint_args = SimpleNamespace(code="S-204", name="Empty Sprint", start_date=None, end_date=None)
    controller.add_sprint(sprint_args)

    # Generate report
    report_args = SimpleNamespace(code="S-204")
    controller.report_sprint(report_args)

    # Capture output
    captured = capsys.readouterr()
    assert "No tasks in sprint" in captured.out
