from src.colors import Colors, colorize, status_color


class TaskView:
    STATUS_EMOJI = {
        "TODO": "📋",
        "IN_PROGRESS": "🔄",
        "REVIEW": "👀",
        "TESTING_DEPLOYMENT": "🧪",
        "DONE": "✅",
    }

    def task_created(self, task):
        code = colorize(task.code, Colors.BOLD, Colors.CYAN)
        print(f"✨ Task '{code}' created")

    def list(self, tasks):
        if not tasks:
            print(colorize("📭 No tasks found", Colors.DIM))
            return

        for t in tasks:
            # Add visual indicators for comments and Jira links
            icons = ""
            if t.comment:
                icons += " 💬"
            if t.jira_link:
                icons += " 🔗"

            status_emoji = self.STATUS_EMOJI.get(t.status.value, "")
            color = status_color(t.status.value)
            status_text = colorize(f"[{t.status.value}]", color, Colors.BOLD)
            code = colorize(t.code, Colors.BOLD)
            sprint = colorize(t.sprint_code, Colors.CYAN) if t.sprint_code else colorize("-", Colors.DIM)
            print(f"{status_emoji} {status_text} {code} - {t.name}{icons} (sprint: {sprint})")

    def task_moved(self, code, old_status, new_status):
        new_emoji = self.STATUS_EMOJI.get(new_status.value, "")
        code_text = colorize(code, Colors.BOLD)
        old_color = status_color(old_status.value)
        new_color = status_color(new_status.value)
        old_text = colorize(old_status.value, old_color)
        new_text = colorize(new_status.value, new_color, Colors.BOLD)
        print(f"{new_emoji} {code_text}: {old_text} → {new_text}")

    def task_removed(self, code):
        code_text = colorize(code, Colors.BOLD, Colors.RED)
        print(f"🗑️  Task '{code_text}' removed")

    def show_task(self, task):
        """Display detailed task information."""
        status_emoji = self.STATUS_EMOJI.get(task.status.value, "")
        color = status_color(task.status.value)

        fields = [
            ("code", colorize(task.code, Colors.BOLD, Colors.CYAN)),
            ("name", task.name),
            ("status", f"{status_emoji} {colorize(task.status.value, color, Colors.BOLD)}"),
            ("sprint_code", colorize(task.sprint_code, Colors.CYAN) if task.sprint_code else colorize("-", Colors.DIM)),
            ("start_date", task.start_date.isoformat() if task.start_date else colorize("-", Colors.DIM)),
            ("review_date", task.review_date.isoformat() if task.review_date else colorize("-", Colors.DIM)),
            ("end_date", task.end_date.isoformat() if task.end_date else colorize("-", Colors.DIM)),
            ("estimated_time", f"{task.estimated_time}h" if task.estimated_time else colorize("-", Colors.DIM)),
            ("actual_time", f"{task.actual_time}h" if task.actual_time else colorize("-", Colors.DIM)),
            ("jira_link", colorize(f"🔗 {task.jira_link}", Colors.BLUE) if task.jira_link else colorize("-", Colors.DIM)),
        ]

        for key, value in fields:
            label = colorize(f"{key:15}", Colors.DIM)
            print(f"{label}: {value}")

        print(colorize("-" * 40, Colors.DIM))
        if task.comment:
            print(f"💬 {task.comment}")
        else:
            print(colorize("(no comment)", Colors.DIM))

    def task_edited(self, task):
        code = colorize(task.code, Colors.BOLD, Colors.CYAN)
        print(f"✏️  Task '{code}' updated")

    def edit_cancelled(self, code):
        code_text = colorize(code, Colors.BOLD)
        print(f"ℹ️  Edit cancelled for '{code_text}'")
