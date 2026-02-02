"""ANSI color codes for terminal output."""


class Colors:
    # Reset
    RESET = "\033[0m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"


# Status color mapping
STATUS_COLORS = {
    "TODO": Colors.YELLOW,
    "IN_PROGRESS": Colors.BLUE,
    "REVIEW": Colors.CYAN,
    "TESTING_DEPLOYMENT": Colors.MAGENTA,
    "DONE": Colors.GREEN,
}


def colorize(text, *styles):
    """Apply color/style codes to text."""
    return f"{''.join(styles)}{text}{Colors.RESET}"


def status_color(status_value):
    """Get the color for a status value."""
    return STATUS_COLORS.get(status_value, "")
