# controllers/task_controller.py
import os
import subprocess
import tempfile
from types import SimpleNamespace
from src.models.task import Task
from src.models.status import Status
from src.repositories.task_repository import TaskRepository
from src.services.task_service import TaskService
from src.repositories.storage import JsonStorage
from src.views.task_view import TaskView
from src.models.sprint import Sprint
from src.colors import Colors, colorize, status_color


class TaskController:
    def __init__(self, service=None, view=None, storage_path=None):
        if service is None:
            storage = storage_path if hasattr(storage_path, "load") else JsonStorage(storage_path)
            repo = TaskRepository(storage)
            service = TaskService(repo)
            self.storage = storage  # Keep storage reference for sprints
        else:
            repo = getattr(service, "repo", None)
            self.storage = repo.storage if repo else None

        if view is None:
            view = TaskView()

        self.service = service
        self.view = view

    def add(self, args):
        try:
            # Parse dates if provided as strings
            from datetime import datetime
            start_date = None
            review_date = None
            end_date = None

            if getattr(args, "start_date", None):
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            if getattr(args, "review_date", None):
                review_date = datetime.strptime(args.review_date, "%Y-%m-%d").date()
            if getattr(args, "end_date", None):
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()

            # Parse time estimate if provided
            estimated_time = None
            if getattr(args, "estimate", None):
                estimated_time = self._parse_hours(args.estimate)

            task = Task(
                code=args.code,
                name=args.name,
                status=Status(args.status),
                sprint_code=getattr(args, "sprint", None),
                start_date=start_date,
                review_date=review_date,
                end_date=end_date,
                estimated_time=estimated_time,
                jira_link=getattr(args, "jira_link", None),
                comment=getattr(args, "comment", None),
            )

            # Add task to sprint if provided
            if getattr(args, "sprint", None):
                data = self.storage.load()
                sprint_data = data.get("sprints", {}).get(args.sprint)
                if not sprint_data:
                    raise ValueError(f"Sprint '{args.sprint}' does not exist")
                if sprint_data.get("closed", False):
                    raise ValueError(f"Sprint '{args.sprint}' is closed")
                # Keep sprint code in task (already set) and optionally update sprint tasks list
                sprint_tasks = sprint_data.get("tasks", [])
                if task.code in sprint_tasks:
                    raise ValueError(f"Task '{task.code}' already in sprint '{args.sprint}'")
                sprint_tasks.append(task.code)
                sprint_data["tasks"] = sprint_tasks
                data["sprints"][args.sprint] = sprint_data
                self.storage.save(data)

            self.service.create(task)
            self.view.task_created(task)

        except ValueError as e:
            raise

    def list(self, args):
        tasks = self.service.list()

        if getattr(args, "status", None):
            tasks = [t for t in tasks if t.status == Status(args.status)]
        if getattr(args, "sprint", None):
            tasks = [t for t in tasks if t.sprint_code == args.sprint]
        if getattr(args, "filter", None):
            tasks = self._filter_tasks(tasks, args.filter)

        self.view.list(tasks)

    def board(self, args):
        tasks = self.service.list()
        sprint_filter = getattr(args, "sprint", None)
        vertical = getattr(args, "vertical", False)

        if sprint_filter:
            tasks = [t for t in tasks if t.sprint_code == sprint_filter]
        if getattr(args, "filter", None):
            tasks = self._filter_tasks(tasks, args.filter)

        self.view.board(tasks, sprint_filter, vertical=vertical)

    def move(self, args):
        try:
            new_status = Status(args.status)
            old_status, new_status = self.service.move(args.code, new_status)
            self.view.task_moved(args.code, old_status, new_status)
        except ValueError as e:
            raise

    def remove(self, args):
        try:
            self.service.remove(args.code)
            self.view.task_removed(args.code)
        except ValueError as e:
            raise

    def show(self, args):
        try:
            task = self.service.get(args.code)
            self.view.show_task(task)
        except ValueError as e:
            raise

    def jira_open(self, args):
        try:
            task = self.service.get(args.code)
            if not task.jira_link:
                code = colorize(args.code, Colors.BOLD)
                print(f"⚠️  Task '{code}' has no Jira link")
                return
            import webbrowser
            webbrowser.open(task.jira_link)
            code = colorize(args.code, Colors.BOLD, Colors.CYAN)
            print(f"🔗 Opened Jira for {code}")
        except ValueError as e:
            raise

    def edit(self, args):
        task = self.service.get(args.code)

        # Build editable content
        content = self._task_to_editable(task)

        # Write to temp file and open in editor
        editor = os.environ.get("EDITOR", "vi")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Get original content hash to detect changes
            original_content = content

            # Open editor
            result = subprocess.run([editor, temp_path])
            if result.returncode != 0:
                raise ValueError(f"Editor exited with code {result.returncode}")

            # Read modified content
            with open(temp_path, "r") as f:
                modified_content = f.read()

            # Check if cancelled (no changes)
            if modified_content.strip() == original_content.strip():
                self.view.edit_cancelled(args.code)
                return

            # Parse and apply changes
            updated_task = self._parse_editable(task, modified_content)
            self.service.update(updated_task)
            self.view.task_edited(updated_task)

        finally:
            os.unlink(temp_path)

    def _task_to_editable(self, task):
        """Convert task to editable text format."""
        lines = [
            f"# Editing task: {task.code}",
            f"# Lines starting with # are ignored",
            f"# Leave value empty to clear a field",
            "",
            f"name: {task.name}",
            f"status: {task.status.value}",
            f"sprint_code: {task.sprint_code or ''}",
            f"start_date: {task.start_date.isoformat() if task.start_date else ''}",
            f"review_date: {task.review_date.isoformat() if task.review_date else ''}",
            f"end_date: {task.end_date.isoformat() if task.end_date else ''}",
            f"estimated_time: {task.estimated_time or ''}",
            f"actual_time: {task.actual_time or ''}",
            f"jira_link: {task.jira_link or ''}",
            "",
            "# Comment (everything after 'comment:' line):",
            f"comment: {task.comment or ''}",
        ]
        return "\n".join(lines)

    def _parse_editable(self, original_task, content):
        """Parse edited content and return updated task."""
        from datetime import datetime

        # Parse key-value pairs
        values = {}
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                values[key] = value if value else None

        # Build updated task (code is immutable)
        def parse_date(val):
            if not val:
                return None
            return datetime.strptime(val, "%Y-%m-%d").date()

        def parse_float(val):
            if not val:
                return None
            return float(val)

        return Task(
            code=original_task.code,
            name=values.get("name") or original_task.name,
            status=Status(values.get("status", original_task.status.value)),
            sprint_code=values.get("sprint_code"),
            start_date=parse_date(values.get("start_date")),
            review_date=parse_date(values.get("review_date")),
            end_date=parse_date(values.get("end_date")),
            estimated_time=parse_float(values.get("estimated_time")),
            actual_time=parse_float(values.get("actual_time")),
            jira_link=values.get("jira_link"),
            comment=values.get("comment"),
        )

    def _filter_tasks(self, tasks, keyword):
        """Filter tasks by case-insensitive keyword match on code or name."""
        keyword = keyword.lower()
        return [
            t for t in tasks
            if keyword in t.code.lower()
            or keyword in t.name.lower()
        ]

    # ---------- Helpers for tests ----------
    def add_task(self, code, name, status="TODO", sprint=None):
        args = SimpleNamespace(code=code, name=name, status=status, sprint=sprint)
        self.add(args)

    def list_tasks(self):
        tasks = self.service.list()
        return tasks
    

    # -------- Sprint-related methods in TaskController --------
    def add_sprint(self, args):
        data = self.storage.load()
        if "sprints" not in data:
            data["sprints"] = {}
        if args.code in data["sprints"]:
            raise ValueError("Sprint already exists")

        sprint = {
            "code": args.code,
            "name": args.name,
            "start_date": getattr(args, "start_date", None),
            "end_date": getattr(args, "end_date", None),
            "closed": False,
            "tasks": [],
        }
        data["sprints"][args.code] = sprint
        self.storage.save(data)
        code = colorize(args.code, Colors.BOLD, Colors.CYAN)
        print(f"🏃 Sprint '{code}' created")

    def list_sprints(self, args):
        data = self.storage.load()
        sprints = data.get("sprints", {}).values()
        if not sprints:
            print(colorize("📭 No sprints found", Colors.DIM))
            return
        for s in sprints:
            tasks_str = ", ".join(s.get("tasks", []))
            status_icon = "🔒" if s["closed"] else "🏃"
            code = colorize(s["code"], Colors.BOLD, Colors.CYAN)
            name = colorize(s["name"], Colors.WHITE)
            tasks = colorize(tasks_str, Colors.DIM) if tasks_str else colorize("(none)", Colors.DIM)
            print(f"{status_icon} {code} - {name} | Tasks: {tasks}")

    def add_task_to_sprint(self, args):
        data = self.storage.load()

        # Check sprint exists
        sprint_data = data.get("sprints", {}).get(args.sprint)
        if not sprint_data:
            raise ValueError(f"Sprint '{args.sprint}' does not exist")
        if sprint_data.get("closed", False):
            raise ValueError(f"Sprint '{args.sprint}' is closed")

        # Check task exists
        task_data = data.get("tasks", {}).get(args.task)
        if not task_data:
            raise ValueError(f"Task '{args.task}' does not exist")

        # Add task to sprint
        if args.task in sprint_data.get("tasks", []):
            raise ValueError(f"Task '{args.task}' already in sprint '{args.sprint}'")

        sprint_data["tasks"].append(args.task)
        task_data["sprint_code"] = args.sprint
        data["sprints"][args.sprint] = sprint_data
        data["tasks"][args.task] = task_data
        self.storage.save(data)
        task = colorize(args.task, Colors.BOLD)
        sprint = colorize(args.sprint, Colors.BOLD, Colors.CYAN)
        print(f"➕ Task '{task}' added to sprint '{sprint}'")

    def close_sprint(self, args):
        data = self.storage.load()
        sprint_data = data.get("sprints", {}).get(args.code)

        if not sprint_data or sprint_data.get("closed", False):
            raise ValueError("Sprint not found or already closed")

        # Move all non-DONE tasks out of the sprint
        for task_code, task_data in data.get("tasks", {}).items():
            if task_data.get("sprint_code") == args.code and task_data.get("status") != "DONE":
                task_data["sprint_code"] = None

        # Mark sprint as closed
        sprint_data["closed"] = True
        data["sprints"][args.code] = sprint_data
        self.storage.save(data)
        code = colorize(args.code, Colors.BOLD, Colors.CYAN)
        print(f"🔒 Sprint '{code}' closed")

    def report_sprint(self, args):
        data = self.storage.load()
        sprint_data = data.get("sprints", {}).get(args.code)

        if not sprint_data:
            raise ValueError("Sprint not found")

        # Get all tasks in this sprint
        tasks = [t for t in data.get("tasks", {}).values() if t.get("sprint_code") == args.code]

        if not tasks:
            print(colorize("📭 No tasks in sprint", Colors.DIM))
            return

        # Count tasks by status
        status_order = [s.value for s in Status.ordered()]
        counts = {s: 0 for s in status_order}
        for t in tasks:
            status = t.get("status", "TODO")
            if status in counts:
                counts[status] += 1

        # Calculate completion
        total = len(tasks)
        done = counts.get("DONE", 0)
        pct = int((done / total) * 100) if total > 0 else 0

        # Status emojis for report
        status_emoji = {
            "TODO": "📋",
            "IN_PROGRESS": "🔄",
            "REVIEW": "👀",
            "TESTING_DEPLOYMENT": "🧪",
            "DONE": "✅",
        }

        # Display report
        code = colorize(sprint_data["code"], Colors.BOLD, Colors.CYAN)
        name = colorize(sprint_data["name"], Colors.WHITE)
        print(f"🏃 Sprint {code} — {name}")
        print(colorize("=" * 40, Colors.DIM))
        for s in status_order:
            emoji = status_emoji.get(s, "")
            color = status_color(s)
            status_text = colorize(f"{s:20}", color)
            count = colorize(str(counts[s]), Colors.BOLD) if counts[s] > 0 else colorize("0", Colors.DIM)
            print(f"{emoji} {status_text} {count}")
        print(colorize("-" * 40, Colors.DIM))
        pct_color = Colors.GREEN if pct >= 75 else Colors.YELLOW if pct >= 25 else Colors.RED
        pct_text = colorize(f"{pct}%", pct_color, Colors.BOLD)
        print(f"📊 Completed: {done}/{total} ({pct_text})")

    # ---------- Helpers ----------
    def _parse_hours(self, value):
        """Parse time values like '2h', '30m' into hours as float."""
        if not value:
            return None
        v = value.strip().lower()
        try:
            if v.endswith("h"):
                return float(v[:-1])
            if v.endswith("m"):
                return float(v[:-1]) / 60
        except ValueError:
            return None
        return None

