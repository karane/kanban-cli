import argparse
from datetime import date

from src.controllers.task_controller import TaskController
from src.repositories.task_repository import TaskRepository
from src.services.task_service import TaskService
from src.repositories.storage import JsonStorage
from src.views.task_view import TaskView
from src.models.sprint import Sprint
from src.colors import Colors, colorize


# ---------------- Task Controller Builder ----------------
def build_task_controller():
    storage = JsonStorage()
    repo = TaskRepository(storage)
    service = TaskService(repo)
    view = TaskView()
    return TaskController(service, view)


# ---------------- Sprint Controller Builder ----------------
def build_sprint_controller(storage):
    class SprintController:
        def __init__(self):
            self.storage = storage

        def add(self, args):
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
            }
            data["sprints"][args.code] = sprint
            self.storage.save(data)
            print(f"Sprint '{args.code}' created")

        def list(self, args):
            data = self.storage.load()
            sprints = data.get("sprints", {}).values()
            if not sprints:
                print("No sprints found")
                return
            for s in sprints:
                print(f"{s['code']} - {s['name']} (Closed: {s['closed']})")

    return SprintController()


# ---------------- Main CLI ----------------
def main():
    task_controller = build_task_controller()  # Already has storage reference

    parser = argparse.ArgumentParser("Kanban CLI")
    sub = parser.add_subparsers(required=True)

    # ---------------- Task CLI ----------------
    task = sub.add_parser("task")
    task_sub = task.add_subparsers(required=True)

    add = task_sub.add_parser("add")
    add.add_argument("--code", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--status", default="TODO")
    add.add_argument("--sprint")
    add.add_argument("--estimate", help="Time estimate (e.g., '2h', '30m')")
    add.add_argument("--jira-link", help="Link to Jira ticket")
    add.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    add.add_argument("--review-date", help="Review date (YYYY-MM-DD)")
    add.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    add.add_argument("--comment", help="Task comment")
    add.set_defaults(func=task_controller.add)

    lst = task_sub.add_parser("list")
    lst.add_argument("--status")
    lst.add_argument("--sprint")
    lst.set_defaults(func=task_controller.list)

    move = task_sub.add_parser("move")
    move.add_argument("code", help="Task code")
    move.add_argument("status", help="New status")
    move.set_defaults(func=task_controller.move)

    rm = task_sub.add_parser("rm")
    rm.add_argument("code", help="Task code")
    rm.set_defaults(func=task_controller.remove)

    show = task_sub.add_parser("show")
    show.add_argument("code", help="Task code")
    show.set_defaults(func=task_controller.show)

    edit = task_sub.add_parser("edit")
    edit.add_argument("code", help="Task code")
    edit.set_defaults(func=task_controller.edit)

    jira = task_sub.add_parser("jira-open")
    jira.add_argument("code", help="Task code")
    jira.set_defaults(func=task_controller.jira_open)

    # ---------------- Sprint CLI ----------------
    sprint = sub.add_parser("sprint")
    sprint_sub = sprint.add_subparsers(required=True)

    sprint_add = sprint_sub.add_parser("add")
    sprint_add.add_argument("--code", required=True)
    sprint_add.add_argument("--name", required=True)
    sprint_add.add_argument("--start_date")
    sprint_add.add_argument("--end_date")
    sprint_add.set_defaults(func=task_controller.add_sprint)

    sprint_list = sprint_sub.add_parser("list")
    sprint_list.set_defaults(func=task_controller.list_sprints)

    sprint_add_task = sprint_sub.add_parser("add-task")
    sprint_add_task.add_argument("task", help="Task code")
    sprint_add_task.add_argument("sprint", help="Sprint code")
    sprint_add_task.set_defaults(func=task_controller.add_task_to_sprint)

    sprint_close = sprint_sub.add_parser("close")
    sprint_close.add_argument("code", help="Sprint code")
    sprint_close.set_defaults(func=task_controller.close_sprint)

    sprint_report = sprint_sub.add_parser("report")
    sprint_report.add_argument("code", help="Sprint code")
    sprint_report.set_defaults(func=task_controller.report_sprint)

    # ---------------- Parse args ----------------
    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as e:
        error_label = colorize("Error:", Colors.RED, Colors.BOLD)
        print(f"❌ {error_label} {e}")
        exit(1)


if __name__ == "__main__":
    main()
