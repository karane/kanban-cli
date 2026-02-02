# kanban-cli

A command-line kanban board management tool for tracking tasks and sprints from your terminal.

## Features

- **Task Management**: Create, list, move, show, edit, and remove tasks
- **Sprint Management**: Organize tasks into sprints with start/end dates
- **Status Tracking**: Track tasks through workflow states (TODO → IN_PROGRESS → REVIEW → TESTING_DEPLOYMENT → DONE)
- **Sprint Reports**: View sprint progress and completion metrics
- **Jira Integration**: Link tasks to Jira tickets and open them directly
- **Time Tracking**: Estimate task duration and calculate cycle times
- **State Validation**: Enforces proper state transitions and business rules
- **JSON Storage**: Simple file-based persistence

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd kanban-cli

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Install dev dependencies (for testing)
pip install pytest pytest-cov
```

## Quick Start Journey

Here's a typical workflow showing the most common use cases:

```bash
# 1. Create a sprint for your work
kbcli sprint add --code S-1 --name "Sprint 1"

# 2. Add tasks to work on
kbcli task add --code T-1 --name "Setup database" --sprint S-1
kbcli task add --code T-2 --name "Create API endpoints" --sprint S-1
kbcli task add --code T-3 --name "Build frontend" --sprint S-1

# 3. View your board
kbcli task list

# 4. Start working on a task
kbcli task move T-1 IN_PROGRESS

# 5. Check sprint progress
kbcli sprint report S-1

# 6. Move task through workflow
kbcli task move T-1 REVIEW
kbcli task move T-1 TESTING_DEPLOYMENT
kbcli task move T-1 DONE

# 7. View task details
kbcli task show T-1

# 8. Check updated sprint report
kbcli sprint report S-1

# 9. Close the sprint when done
kbcli sprint close S-1
```

## Command Reference

### Task Commands

#### Add a task
```bash
kbcli task add --code <code> --name <name> [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--code` | Unique task identifier (required) |
| `--name` | Task description (required) |
| `--status` | Initial status: TODO, IN_PROGRESS, REVIEW, TESTING_DEPLOYMENT, DONE (default: TODO) |
| `--sprint` | Sprint code to assign task to |
| `--estimate` | Time estimate (e.g., "2h", "30m") |
| `--jira-link` | URL to Jira ticket |
| `--start-date` | Start date (YYYY-MM-DD) |
| `--review-date` | Review date (YYYY-MM-DD) |
| `--end-date` | End date (YYYY-MM-DD) |
| `--comment` | Task notes/comments |

**Examples:**
```bash
# Simple task
kbcli task add --code T-100 --name "Fix login bug"

# Task with sprint assignment
kbcli task add --code T-101 --name "Add search feature" --sprint S-1

# Task with all details
kbcli task add --code T-102 --name "Refactor auth module" \
  --sprint S-1 \
  --estimate 4h \
  --jira-link "https://jira.example.com/T-102" \
  --comment "Needs security review"
```

#### List tasks
```bash
kbcli task list [options]
```

**Examples:**
```bash
# List all tasks
kbcli task list

# Filter by status
kbcli task list --status TODO
kbcli task list --status IN_PROGRESS

# Filter by sprint
kbcli task list --sprint S-1

# Combine filters
kbcli task list --status TODO --sprint S-1
```

#### Move task (change status)
```bash
kbcli task move <code> <new_status>
```

**Examples:**
```bash
# Start working on a task
kbcli task move T-100 IN_PROGRESS

# Send for review
kbcli task move T-100 REVIEW

# Move to testing
kbcli task move T-100 TESTING_DEPLOYMENT

# Mark as done
kbcli task move T-100 DONE
```

#### Show task details
```bash
kbcli task show <code>
```

**Example:**
```bash
kbcli task show T-100
```

Output:
```
code           : T-100
name           : Fix login bug
status         : IN_PROGRESS
sprint_code    : S-1
start_date     : 2026-02-01
review_date    : -
end_date       : -
estimated_time : 2.0h
actual_time    : -
jira_link      : https://jira.example.com/T-100
----------------------------------------
Remember to update unit tests
```

#### Remove a task
```bash
kbcli task rm <code>
```

**Example:**
```bash
kbcli task rm T-100
```

#### Edit a task
```bash
kbcli task edit <code>
```

Opens the task in your default editor (vi by default, or the value of `$EDITOR`) for editing. All task fields can be modified except the code.

**Example:**
```bash
kbcli task edit T-100
```

The editor will open with a file like:
```
# Editing task: T-100
# Lines starting with # are ignored
# Leave value empty to clear a field

name: Fix login bug
status: IN_PROGRESS
sprint_code: S-1
start_date: 2026-02-01
review_date:
end_date:
estimated_time: 2.0
actual_time:
jira_link: https://jira.example.com/T-100

# Comment (everything after 'comment:' line):
comment: Remember to update unit tests
```

Save and quit to apply changes, or quit without saving to cancel.

#### Open Jira link
```bash
kbcli task jira-open <code>
```

**Example:**
```bash
kbcli task jira-open T-100
```

### Sprint Commands

#### Create a sprint
```bash
kbcli sprint add --code <code> --name <name> [options]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--code` | Unique sprint identifier (required) |
| `--name` | Sprint name (required) |
| `--start_date` | Sprint start date (YYYY-MM-DD) |
| `--end_date` | Sprint end date (YYYY-MM-DD) |

**Examples:**
```bash
# Simple sprint
kbcli sprint add --code S-1 --name "Sprint 1"

# Sprint with dates
kbcli sprint add --code S-2 --name "Sprint 2" \
  --start_date 2026-02-15 \
  --end_date 2026-02-28
```

#### List sprints
```bash
kbcli sprint list
```

Output:
```
S-1 - Sprint 1 (Closed: False) | Tasks: T-1, T-2, T-3
S-2 - Sprint 2 (Closed: False) | Tasks:
```

#### Add task to sprint
```bash
kbcli sprint add-task <task_code> <sprint_code>
```

**Example:**
```bash
kbcli sprint add-task T-100 S-1
```

#### Sprint report
```bash
kbcli sprint report <code>
```

**Example:**
```bash
kbcli sprint report S-1
```

Output:
```
Sprint S-1 — Sprint 1
========================================
TODO                 2
IN_PROGRESS          1
REVIEW               0
TESTING_DEPLOYMENT   0
DONE                 1
----------------------------------------
Completed: 1/4 (25%)
```

#### Close a sprint
```bash
kbcli sprint close <code>
```

**Example:**
```bash
kbcli sprint close S-1
```

Note: Closing a sprint automatically removes unfinished tasks from the sprint. DONE tasks remain associated with the closed sprint.

## Task Workflow States

Tasks follow a strict workflow with validated state transitions:

```
TODO → IN_PROGRESS → REVIEW → TESTING_DEPLOYMENT → DONE
```

**Business rules enforced:**
- Cannot skip states in the workflow
- Cannot move backwards (e.g., DONE → IN_PROGRESS)
- Cannot complete a task without going through testing
- Cannot start a task twice
- End date must be after start date
- Cannot add DONE tasks to a sprint
- Cannot add tasks to closed sprints

## Project Structure

```
kanban-cli/
├── src/                        # Production code
│   ├── main.py                 # CLI entry point
│   ├── controllers/
│   │   └── task_controller.py  # Request handling
│   ├── models/
│   │   ├── task.py             # Task model
│   │   ├── sprint.py           # Sprint model
│   │   └── status.py           # Status enum & transitions
│   ├── repositories/
│   │   ├── task_repository.py  # Data access
│   │   └── storage.py          # JSON persistence
│   ├── services/
│   │   └── task_service.py     # Business logic
│   └── views/
│       └── task_view.py        # Output formatting
├── tests/                      # Test suite (mirrors src structure)
│   ├── controllers/
│   │   └── test_task_controller.py
│   └── models/
│       ├── test_sprint.py
│       ├── test_task_cycle_time.py
│       ├── test_task_state_invariants.py
│       └── test_task_state_transitions.py
├── kanban.json                 # Data storage (auto-generated)
└── pytest.ini                  # Test configuration
```

## Data Storage

All data is stored in `kanban.json` in the project root:

```json
{
  "tasks": {
    "T-1": {
      "code": "T-1",
      "name": "Setup database",
      "status": "DONE",
      "sprint_code": "S-1",
      "start_date": "2026-02-01",
      "end_date": "2026-02-03",
      "estimated_time": 4.0,
      "jira_link": null,
      "comment": null
    }
  },
  "sprints": {
    "S-1": {
      "code": "S-1",
      "name": "Sprint 1",
      "start_date": "2026-02-01",
      "end_date": "2026-02-14",
      "closed": false,
      "tasks": ["T-1", "T-2", "T-3"]
    }
  }
}
```

## Testing

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test directory
python -m pytest tests/models/ -v

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
