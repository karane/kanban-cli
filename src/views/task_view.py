import shutil
from src.colors import Colors, colorize, status_color
from src.models.status import Status


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

    def board(self, tasks, sprint_filter=None, vertical=False):
        """Display tasks as a visual Kanban board with columns."""
        if vertical:
            self._board_vertical(tasks, sprint_filter)
            return

        # Get terminal width, default to 120 if not available
        term_width = shutil.get_terminal_size((120, 24)).columns

        # Group tasks by status
        statuses = Status.ordered()
        columns = {s: [] for s in statuses}
        for task in tasks:
            columns[task.status].append(task)

        # Calculate column width (divide evenly, minimum 20)
        num_cols = len(statuses)
        col_width = max(20, (term_width - num_cols - 1) // num_cols)

        # Column headers
        headers = []
        for status in statuses:
            emoji = self.STATUS_EMOJI.get(status.value, "")
            color = status_color(status.value)
            count = len(columns[status])
            # Shorten status names for display
            short_names = {
                "TODO": "TODO",
                "IN_PROGRESS": "PROGRESS",
                "REVIEW": "REVIEW",
                "TESTING_DEPLOYMENT": "TESTING",
                "DONE": "DONE",
            }
            name = short_names.get(status.value, status.value)
            header_text = f"{emoji} {name} ({count})"
            header = colorize(header_text.center(col_width - 2), color, Colors.BOLD)
            headers.append(header)

        # Print title
        title = "📋 KANBAN BOARD"
        if sprint_filter:
            title += f" — Sprint: {colorize(sprint_filter, Colors.CYAN, Colors.BOLD)}"
        print(colorize(title.center(term_width), Colors.BOLD))
        print(colorize("═" * term_width, Colors.DIM))

        # Print headers
        print("│" + "│".join(headers) + "│")
        print("├" + "┼".join(["─" * (col_width - 2) for _ in statuses]) + "┤")

        # Find max rows needed
        max_rows = max(len(columns[s]) for s in statuses) if any(columns.values()) else 0

        if max_rows == 0:
            empty_msg = colorize("(no tasks)", Colors.DIM).center(col_width - 2 + len(Colors.DIM) + len(Colors.RESET))
            row = "│" + "│".join([empty_msg for _ in statuses]) + "│"
            print(row)
        else:
            # Print task rows
            for i in range(max_rows):
                row_cells = []
                for status in statuses:
                    task_list = columns[status]
                    if i < len(task_list):
                        task = task_list[i]
                        cell = self._format_board_cell(task, col_width - 2)
                    else:
                        cell = " " * (col_width - 2)
                    row_cells.append(cell)
                print("│" + "│".join(row_cells) + "│")

        # Bottom border
        print("└" + "┴".join(["─" * (col_width - 2) for _ in statuses]) + "┘")

    def _format_board_cell(self, task, width):
        """Format a single task cell for the board view."""
        # Task code (bold)
        code = task.code

        # Truncate name to fit remaining width
        # Account for code + space + potential icons
        icons = ""
        if task.comment:
            icons += "💬"
        if task.jira_link:
            icons += "🔗"

        # Calculate available space for name
        # Code takes ~6 chars, icons take ~2 each
        name_width = width - len(code) - 1 - len(icons)
        name = task.name
        if len(name) > name_width:
            name = name[: name_width - 1] + "…"

        # Build cell content
        cell_content = f"{colorize(code, Colors.BOLD, Colors.CYAN)} {name}{icons}"

        # Calculate visible length (without ANSI codes)
        visible_len = len(code) + 1 + len(name) + len(icons)
        padding = width - visible_len

        if padding > 0:
            cell_content += " " * padding

        return cell_content

    def _board_vertical(self, tasks, sprint_filter=None):
        """Display tasks as a vertical Kanban board with stacked sections."""
        term_width = shutil.get_terminal_size((80, 24)).columns

        # Group tasks by status
        statuses = Status.ordered()
        columns = {s: [] for s in statuses}
        for task in tasks:
            columns[task.status].append(task)

        # Print title
        title = "📋 KANBAN BOARD"
        if sprint_filter:
            title += f" — Sprint: {colorize(sprint_filter, Colors.CYAN, Colors.BOLD)}"
        print(colorize(title.center(term_width), Colors.BOLD))
        print(colorize("═" * term_width, Colors.DIM))

        # Print each status section vertically
        for status in statuses:
            task_list = columns[status]
            emoji = self.STATUS_EMOJI.get(status.value, "")
            color = status_color(status.value)
            count = len(task_list)

            # Section header
            header = f"{emoji} {status.value} ({count})"
            print()
            print(colorize(header, color, Colors.BOLD))
            print(colorize("─" * min(40, term_width), Colors.DIM))

            if not task_list:
                print(colorize("  (no tasks)", Colors.DIM))
            else:
                for task in task_list:
                    self._print_vertical_task(task, term_width)

        print()

    def _print_vertical_task(self, task, term_width):
        """Print a single task for vertical board view."""
        # Build icons
        icons = ""
        if task.comment:
            icons += " 💬"
        if task.jira_link:
            icons += " 🔗"

        # Task code and name
        code = colorize(task.code, Colors.BOLD, Colors.CYAN)
        name = task.name

        # Truncate name if too long
        max_name_len = term_width - len(task.code) - len(icons) - 6
        if len(name) > max_name_len:
            name = name[: max_name_len - 1] + "…"

        print(f"  {code} {name}{icons}")
