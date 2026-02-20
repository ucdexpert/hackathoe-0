# personal-task-handler

## Description
Personal task management system for the AI Employee. Manages personal tasks, goals, habits, and journal entries. Integrates with the existing Plan workflow and provides scheduler integration for habit tracking. All activity is logged to `Logs/personal.log`.

## Parameters
- `action` (string, required): Action to perform - "create_task", "list_tasks", "complete_task", "track_habit", "add_goal", "list_goals", "add_journal", "get_summary"
- `title` (string, optional): Task or goal title
- `priority` (string, optional): Task priority - "high", "medium", "low"
- `due_date` (string, optional): Due date (YYYY-MM-DD)
- `habit_name` (string, optional): Name of habit to track
- `completed` (boolean, optional): Whether habit was completed
- `content` (string, optional): Journal entry content or goal description
- `category` (string, optional): Task/goal category

## Functionality
When invoked, this skill enables the AI Employee to:

1. **Manage Personal Tasks**
   - Create tasks with priority and due date
   - List tasks by status (pending, completed)
   - Mark tasks as complete
   - Organize by category

2. **Track Habits**
   - Track daily habit completion
   - View habit streak and history
   - Generate habit reports

3. **Manage Goals**
   - Set personal goals with descriptions
   - Track goal progress
   - Review goal status

4. **Journal Entries**
   - Add dated journal entries
   - Search past entries
   - Generate summaries

5. **Dashboard Summary**
   - Get overview of tasks, habits, goals
   - View today's priorities
   - Track progress metrics

## Constraints
- All dates in YYYY-MM-DD format
- Tasks stored in Personal/Tasks/
- Habits tracked in Personal/Habits/
- Journal entries in Personal/Journal/
- Goals stored in Personal/Goals/
- All operations logged to Logs/personal.log

## File Structure

```
AI_Employee_Vault/
├── Personal/
│   ├── Tasks/            # Personal task files
│   │   ├── pending/      # Active tasks
│   │   └── completed/    # Completed tasks
│   ├── Goals/            # Personal goals
│   ├── Habits/           # Habit tracking
│   │   ├── habits.json   # Habit definitions
│   │   └── history/      # Daily habit logs
│   └── Journal/          # Journal entries
│       └── entries/      # Dated journal files
├── Logs/
│   └── personal.log      # Activity log
└── .claude/skills/personal-task-handler/
    ├── SKILL.md          # This file
    └── personal_handler.py  # Implementation
```

## Personal/Tasks Format

```markdown
# Task: [Task Title]

**Created:** 2026-02-20 10:30:00
**Due:** 2026-02-25
**Priority:** high
**Category:** personal
**Status:** pending

---

## Description

Task description and details go here.

---

## Checklist

- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

---

## Notes

Additional notes and context.

---

*Created by personal-task-handler skill*
```

## Personal/Habits/habits.json Format

```json
{
  "habits": [
    {
      "name": "Morning Exercise",
      "category": "health",
      "frequency": "daily",
      "created": "2026-02-01",
      "current_streak": 15,
      "best_streak": 30
    }
  ],
  "history": {
    "2026-02-20": {
      "Morning Exercise": true,
      "Read 30 minutes": true,
      "Meditation": false
    }
  }
}
```

## Personal/Journal Format

```markdown
# Journal Entry - 2026-02-20

**Date:** 2026-02-20
**Mood:** [optional]
**Tags:** [optional tags]

---

## Entry

Journal content goes here.

---

## Reflections

Key takeaways and reflections.

---

*Created by personal-task-handler skill*
```

## Implementation
```python
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
import uuid


class PersonalTaskHandler:
    """Personal task, habit, goal, and journal management."""

    def __init__(self):
        """Initialize personal task handler."""
        self.vault_root = Path(__file__).parent.parent.parent
        self.personal_dir = self.vault_root / "Personal"
        self.tasks_dir = self.personal_dir / "Tasks"
        self.goals_dir = self.personal_dir / "Goals"
        self.habits_dir = self.personal_dir / "Habits"
        self.journal_dir = self.personal_dir / "Journal"
        self.logs_dir = self.vault_root / "Logs"

        # Ensure directories exist
        for directory in [
            self.tasks_dir / "pending",
            self.tasks_dir / "completed",
            self.goals_dir,
            self.habits_dir / "history",
            self.journal_dir / "entries",
            self.logs_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        # File paths
        self.habits_file = self.habits_dir / "habits.json"
        self.log_file = self.logs_dir / "personal.log"

        # Initialize habits file if not exists
        self._init_habits_file()

    def _log_activity(self, action: str, details: Dict[str, Any], status: str = 'success'):
        """Log activity to personal.log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'status': status,
            'details': details
        }

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        except Exception as e:
            print(f"Failed to log activity: {e}")

    def _init_habits_file(self):
        """Initialize habits tracking file."""
        if not self.habits_file.exists():
            initial_data = {
                'habits': [],
                'history': {}
            }
            with open(self.habits_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2)

    def _load_habits(self) -> Dict:
        """Load habits data."""
        try:
            with open(self.habits_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'habits': [], 'history': {}}

    def _save_habits(self, data: Dict):
        """Save habits data."""
        with open(self.habits_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def _generate_task_id(self) -> str:
        """Generate unique task ID."""
        return f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    def create_task(self, title: str, priority: str = 'medium',
                    due_date: str = None, category: str = 'personal',
                    description: str = '', checklist: List[str] = None) -> Dict[str, Any]:
        """
        Create a new personal task.

        Args:
            title: Task title
            priority: Priority level (high, medium, low)
            due_date: Due date (YYYY-MM-DD)
            category: Task category
            description: Task description
            checklist: List of checklist items

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'task_id': None,
            'task_path': None,
            'error': None
        }

        if not title or len(title.strip()) == 0:
            result['error'] = 'Task title is required'
            self._log_activity('create_task', {'title': title}, 'error')
            return result

        # Validate priority
        valid_priorities = ['high', 'medium', 'low']
        if priority not in valid_priorities:
            priority = 'medium'

        # Set due date
        if due_date is None:
            due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

        # Generate task ID and filename
        task_id = self._generate_task_id()
        filename = f"{task_id}.md"
        task_path = self.tasks_dir / "pending" / filename

        # Create task content
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        content = f"""# Task: {title}

**Created:** {created_at}
**Due:** {due_date}
**Priority:** {priority}
**Category:** {category}
**Status:** pending
**Task ID:** {task_id}

---

## Description

{description if description else 'No description provided.'}

---

## Checklist

"""
        if checklist:
            for item in checklist:
                content += f"- [ ] {item}\n"
        else:
            content += "- [ ] Task item\n"

        content += f"""
---

## Notes



---

*Created by personal-task-handler skill*
"""

        try:
            with open(task_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result['success'] = True
            result['task_id'] = task_id
            result['task_path'] = str(task_path)

            self._log_activity('create_task', {
                'task_id': task_id,
                'title': title,
                'priority': priority,
                'due_date': due_date
            }, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('create_task', {'title': title, 'error': str(e)}, 'error')

        return result

    def list_tasks(self, status: str = 'pending', category: str = None,
                   priority: str = None) -> List[Dict]:
        """
        List personal tasks.

        Args:
            status: Task status (pending, completed)
            category: Filter by category
            priority: Filter by priority

        Returns:
            List of task dictionaries
        """
        tasks = []
        status_dir = self.tasks_dir / status

        if not status_dir.exists():
            return tasks

        for task_file in status_dir.glob('*.md'):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse task metadata
                task = {
                    'file': str(task_file),
                    'filename': task_file.name
                }

                # Extract metadata from content
                for line in content.split('\n'):
                    if line.startswith('**Title:**') or line.startswith('# Task:'):
                        task['title'] = line.split(':', 1)[1].strip().lstrip('#').strip()
                    elif line.startswith('**Due:**'):
                        task['due_date'] = line.split(':', 1)[1].strip()
                    elif line.startswith('**Priority:**'):
                        task['priority'] = line.split(':', 1)[1].strip()
                    elif line.startswith('**Category:**'):
                        task['category'] = line.split(':', 1)[1].strip()
                    elif line.startswith('**Created:**'):
                        task['created'] = line.split(':', 1)[1].strip()
                    elif line.startswith('**Task ID:**'):
                        task['task_id'] = line.split(':', 1)[1].strip()

                # Apply filters
                if category and task.get('category') != category:
                    continue
                if priority and task.get('priority') != priority:
                    continue

                tasks.append(task)

            except Exception as e:
                self._log_activity('list_tasks', {'error': str(e)}, 'error')

        # Sort by priority and due date
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        tasks.sort(key=lambda x: (
            priority_order.get(x.get('priority', 'medium'), 1),
            x.get('due_date', '9999-99-99')
        ))

        return tasks

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """
        Mark a task as complete.

        Args:
            task_id: Task ID to complete

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'error': None
        }

        # Find task in pending
        pending_dir = self.tasks_dir / "pending"
        task_file = None

        for f in pending_dir.glob(f'{task_id}.md'):
            task_file = f
            break

        if not task_file:
            result['error'] = f'Task not found: {task_id}'
            return result

        try:
            # Read and update content
            with open(task_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update status
            content = content.replace('**Status:** pending', '**Status:** completed')
            content = content.replace('**Status:**pending', '**Status:** completed')

            # Add completion timestamp
            completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if '**Completed:**' not in content:
                content = content.replace(
                    '**Status:** completed',
                    f'**Status:** completed\n**Completed:** {completed_at}'
                )

            # Move to completed folder
            completed_file = self.tasks_dir / "completed" / task_file.name

            with open(completed_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Remove from pending
            task_file.unlink()

            result['success'] = True
            result['task_id'] = task_id

            self._log_activity('complete_task', {'task_id': task_id}, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('complete_task', {'task_id': task_id, 'error': str(e)}, 'error')

        return result

    def track_habit(self, habit_name: str, completed: bool = True,
                    date: str = None) -> Dict[str, Any]:
        """
        Track daily habit completion.

        Args:
            habit_name: Name of habit
            completed: Whether habit was completed
            date: Date to track (YYYY-MM-DD, default: today)

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'habit': None,
            'streak': 0,
            'error': None
        }

        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        habits_data = self._load_habits()

        # Find or create habit
        habit = None
        for h in habits_data['habits']:
            if h['name'].lower() == habit_name.lower():
                habit = h
                break

        if not habit:
            # Create new habit
            habit = {
                'name': habit_name,
                'category': 'personal',
                'frequency': 'daily',
                'created': date,
                'current_streak': 0,
                'best_streak': 0,
                'total_completions': 0
            }
            habits_data['habits'].append(habit)

        # Record completion
        if date not in habits_data['history']:
            habits_data['history'][date] = {}

        habits_data['history'][date][habit_name] = completed

        # Update streak
        if completed:
            habit['current_streak'] += 1
            habit['total_completions'] = habit.get('total_completions', 0) + 1
            if habit['current_streak'] > habit.get('best_streak', 0):
                habit['best_streak'] = habit['current_streak']
        else:
            habit['current_streak'] = 0

        self._save_habits(habits_data)

        result['success'] = True
        result['habit'] = habit
        result['streak'] = habit['current_streak']

        self._log_activity('track_habit', {
            'habit_name': habit_name,
            'completed': completed,
            'date': date,
            'streak': habit['current_streak']
        }, 'success')

        return result

    def add_goal(self, title: str, description: str = '',
                 target_date: str = None, category: str = 'personal') -> Dict[str, Any]:
        """
        Add a personal goal.

        Args:
            title: Goal title
            description: Goal description
            target_date: Target completion date
            category: Goal category

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'goal_id': None,
            'goal_path': None,
            'error': None
        }

        if not title or len(title.strip()) == 0:
            result['error'] = 'Goal title is required'
            return result

        goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        filename = f"{goal_id}.md"
        goal_path = self.goals_dir / filename

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = f"""# Goal: {title}

**Created:** {created_at}
**Target Date:** {target_date if target_date else 'Open-ended'}
**Category:** {category}
**Status:** active
**Goal ID:** {goal_id}

---

## Description

{description if description else 'No description provided.'}

---

## Progress

- [ ] Goal defined
- [ ] Action plan created
- [ ] In progress
- [ ] Completed

---

## Notes



---

*Created by personal-task-handler skill*
"""

        try:
            with open(goal_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result['success'] = True
            result['goal_id'] = goal_id
            result['goal_path'] = str(goal_path)

            self._log_activity('add_goal', {
                'goal_id': goal_id,
                'title': title,
                'category': category
            }, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('add_goal', {'title': title, 'error': str(e)}, 'error')

        return result

    def list_goals(self, status: str = 'active') -> List[Dict]:
        """
        List personal goals.

        Args:
            status: Goal status (active, completed)

        Returns:
            List of goal dictionaries
        """
        goals = []

        for goal_file in self.goals_dir.glob('*.md'):
            try:
                with open(goal_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                goal = {
                    'file': str(goal_file),
                    'filename': goal_file.name
                }

                for line in content.split('\n'):
                    if line.startswith('**Title:**') or line.startswith('# Goal:'):
                        goal['title'] = line.split(':', 1)[1].strip().lstrip('#').strip()
                    elif line.startswith('**Target Date:**'):
                        goal['target_date'] = line.split(':', 1)[1].strip()
                    elif line.startswith('**Category:**'):
                        goal['category'] = line.split(':', 1)[1].strip()
                    elif line.startswith('**Status:**'):
                        goal['status'] = line.split(':', 1)[1].strip()
                    elif line.startswith('**Goal ID:**'):
                        goal['goal_id'] = line.split(':', 1)[1].strip()

                if status and goal.get('status') != status:
                    continue

                goals.append(goal)

            except Exception as e:
                self._log_activity('list_goals', {'error': str(e)}, 'error')

        return goals

    def add_journal_entry(self, content: str, mood: str = None,
                          tags: List[str] = None) -> Dict[str, Any]:
        """
        Add a journal entry.

        Args:
            content: Journal entry content
            mood: Optional mood
            tags: Optional tags

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'entry_id': None,
            'entry_path': None,
            'error': None
        }

        if not content or len(content.strip()) == 0:
            result['error'] = 'Journal content is required'
            return result

        today = datetime.now()
        date_str = today.strftime('%Y-%m-%d')
        entry_id = f"journal_{date_str}_{today.strftime('%H%M%S')}"
        filename = f"{entry_id}.md"
        entry_path = self.journal_dir / "entries" / filename

        entry_content = f"""# Journal Entry - {date_str}

**Date:** {date_str}
**Time:** {today.strftime('%H:%M:%S')}
"""

        if mood:
            entry_content += f"**Mood:** {mood}\n"

        if tags:
            entry_content += f"**Tags:** {', '.join(tags)}\n"

        entry_content += f"""
---

## Entry

{content}

---

*Created by personal-task-handler skill*
"""

        try:
            with open(entry_path, 'w', encoding='utf-8') as f:
                f.write(entry_content)

            result['success'] = True
            result['entry_id'] = entry_id
            result['entry_path'] = str(entry_path)

            self._log_activity('add_journal', {
                'entry_id': entry_id,
                'mood': mood,
                'tags': tags
            }, 'success')

        except Exception as e:
            result['error'] = str(e)
            self._log_activity('add_journal', {'error': str(e)}, 'error')

        return result

    def get_personal_summary(self) -> Dict[str, Any]:
        """
        Get personal dashboard summary.

        Returns:
            Dict with summary statistics
        """
        summary = {
            'tasks': {
                'pending': 0,
                'completed_today': 0,
                'overdue': 0,
                'high_priority': 0
            },
            'habits': {
                'total': 0,
                'completed_today': 0,
                'active_streaks': 0
            },
            'goals': {
                'active': 0,
                'completed': 0
            },
            'journal': {
                'entries_this_week': 0
            },
            'generated_at': datetime.now().isoformat()
        }

        # Count tasks
        pending_tasks = self.list_tasks(status='pending')
        summary['tasks']['pending'] = len(pending_tasks)

        today = datetime.now().strftime('%Y-%m-%d')
        for task in pending_tasks:
            if task.get('priority') == 'high':
                summary['tasks']['high_priority'] += 1
            if task.get('due_date', '9999-99-99') < today:
                summary['tasks']['overdue'] += 1

        completed_tasks = self.list_tasks(status='completed')
        for task in completed_tasks:
            if task.get('completed', '').startswith(today):
                summary['tasks']['completed_today'] += 1

        # Count habits
        habits_data = self._load_habits()
        summary['habits']['total'] = len(habits_data['habits'])

        today_history = habits_data['history'].get(today, {})
        summary['habits']['completed_today'] = sum(1 for v in today_history.values() if v)

        for habit in habits_data['habits']:
            if habit.get('current_streak', 0) > 0:
                summary['habits']['active_streaks'] += 1

        # Count goals
        all_goals = self.list_goals(status=None)
        for goal in all_goals:
            if goal.get('status') == 'active':
                summary['goals']['active'] += 1
            elif goal.get('status') == 'completed':
                summary['goals']['completed'] += 1

        # Count journal entries this week
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        entries_dir = self.journal_dir / "entries"
        if entries_dir.exists():
            for entry_file in entries_dir.glob('*.md'):
                if entry_file.name >= f"journal_{week_ago}":
                    summary['journal']['entries_this_week'] += 1

        self._log_activity('get_summary', summary, 'success')

        return summary


# ============================================================================
# Skill Entry Point
# ============================================================================

def personal_task_handler_skill(action: str, **kwargs) -> Dict[str, Any]:
    """
    Main entry point for the personal-task-handler skill.

    Args:
        action: Action to perform
        **kwargs: Action-specific parameters

    Returns:
        Result dictionary
    """
    handler = PersonalTaskHandler()

    if action == 'create_task':
        return handler.create_task(
            title=kwargs.get('title', ''),
            priority=kwargs.get('priority', 'medium'),
            due_date=kwargs.get('due_date'),
            category=kwargs.get('category', 'personal'),
            description=kwargs.get('description', ''),
            checklist=kwargs.get('checklist', [])
        )

    elif action == 'list_tasks':
        return {
            'success': True,
            'tasks': handler.list_tasks(
                status=kwargs.get('status', 'pending'),
                category=kwargs.get('category'),
                priority=kwargs.get('priority')
            )
        }

    elif action == 'complete_task':
        return handler.complete_task(
            task_id=kwargs.get('task_id', '')
        )

    elif action == 'track_habit':
        return handler.track_habit(
            habit_name=kwargs.get('habit_name', ''),
            completed=kwargs.get('completed', True),
            date=kwargs.get('date')
        )

    elif action == 'add_goal':
        return handler.add_goal(
            title=kwargs.get('title', ''),
            description=kwargs.get('description', ''),
            target_date=kwargs.get('target_date'),
            category=kwargs.get('category', 'personal')
        )

    elif action == 'list_goals':
        return {
            'success': True,
            'goals': handler.list_goals(
                status=kwargs.get('status', 'active')
            )
        }

    elif action == 'add_journal':
        return handler.add_journal_entry(
            content=kwargs.get('content', ''),
            mood=kwargs.get('mood'),
            tags=kwargs.get('tags', [])
        )

    elif action == 'get_summary':
        return {
            'success': True,
            'summary': handler.get_personal_summary()
        }

    else:
        return {
            'success': False,
            'error': f"Unknown action: {action}. Valid actions: create_task, list_tasks, complete_task, track_habit, add_goal, list_goals, add_journal, get_summary"
        }


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Personal Task Handler Skill')
    parser.add_argument('--action', '-a', required=True, help='Action to perform')
    parser.add_argument('--title', '-t', help='Task/goal title')
    parser.add_argument('--priority', '-p', choices=['high', 'medium', 'low'], default='medium')
    parser.add_argument('--due-date', '-d', help='Due date (YYYY-MM-DD)')
    parser.add_argument('--category', '-c', default='personal')
    parser.add_argument('--description', '-D', help='Description')
    parser.add_argument('--habit-name', '-H', help='Habit name')
    parser.add_argument('--completed', action='store_true', default=True)
    parser.add_argument('--not-completed', action='store_false', dest='completed')
    parser.add_argument('--content', '-C', help='Journal content')
    parser.add_argument('--task-id', '-i', help='Task ID')
    parser.add_argument('--status', '-s', help='Status filter')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    result = personal_task_handler_skill(
        action=args.action,
        title=args.title,
        priority=args.priority,
        due_date=args.due_date,
        category=args.category,
        description=args.description,
        habit_name=args.habit_name,
        completed=args.completed,
        content=args.content,
        task_id=args.task_id,
        status=args.status
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if result.get('success'):
            print(f"SUCCESS: {args.action.replace('_', ' ').title()} completed")
            if 'task_id' in result:
                print(f"Task ID: {result['task_id']}")
            if 'streak' in result:
                print(f"Current streak: {result['streak']} days")
            if 'summary' in result:
                summary = result['summary']
                print(f"\nPersonal Dashboard:")
                print(f"  Pending tasks: {summary['tasks']['pending']}")
                print(f"  High priority: {summary['tasks']['high_priority']}")
                print(f"  Habits today: {summary['habits']['completed_today']}/{summary['habits']['total']}")
                print(f"  Active goals: {summary['goals']['active']}")
        else:
            print(f"ERROR: {result.get('error', 'Unknown error')}")

    sys.exit(0 if result.get('success') else 1)
```

## Usage Examples

### Create a Task
```python
result = personal_task_handler_skill(
    action="create_task",
    title="Complete project proposal",
    priority="high",
    due_date="2026-02-25",
    category="work",
    description="Draft and submit the Q1 project proposal",
    checklist=["Research requirements", "Draft content", "Review with team", "Submit"]
)
```

### List Tasks
```python
result = personal_task_handler_skill(
    action="list_tasks",
    status="pending",
    priority="high"
)
```

### Complete a Task
```python
result = personal_task_handler_skill(
    action="complete_task",
    task_id="task_20260220_103000_abc123"
)
```

### Track a Habit
```python
result = personal_task_handler_skill(
    action="track_habit",
    habit_name="Morning Exercise",
    completed=True
)
```

### Add a Goal
```python
result = personal_task_handler_skill(
    action="add_goal",
    title="Run a marathon",
    description="Complete a full marathon by end of year",
    target_date="2026-12-31",
    category="health"
)
```

### Add Journal Entry
```python
result = personal_task_handler_skill(
    action="add_journal",
    content="Today was productive. Completed the project proposal ahead of schedule.",
    mood="accomplished",
    tags=["productivity", "work"]
)
```

### Get Personal Summary
```python
result = personal_task_handler_skill(action="get_summary")
```

## CLI Usage
```bash
# Create a task
python personal_handler.py --action create_task --title "Buy groceries" --priority medium

# Track a habit
python personal_handler.py --action track_habit --habit-name "Exercise" --completed

# Get summary
python personal_handler.py --action get_summary --json

# List tasks
python personal_handler.py --action list_tasks --status pending --priority high
```

## Claude Integration

Once this skill is installed in `.claude/skills/personal-task-handler/`, Claude can:

1. **Manage personal tasks** alongside work tasks
2. **Track daily habits** for self-improvement
3. **Set and monitor goals** for personal development
4. **Maintain a journal** for reflection
5. **Provide dashboard summaries** for weekly reviews

## Scheduler Integration

This skill integrates with the silver-scheduler for automated habit tracking:

```bash
# Add to crontab or Task Scheduler for daily habit reminders
python personal_handler.py --action get_summary --json
```

## Requirements

- Python 3.10+
- No external dependencies (uses standard library)

## Error Handling

| Error | Description | Response |
|-------|-------------|----------|
| `MISSING_TITLE` | Title required | `error: "Task title is required"` |
| `NOT_FOUND` | Task/goal not found | `error: "Task not found: {id}"` |
| `WRITE_ERROR` | File write failed | `error: "Failed to write file"` |

## Best Practices

1. **Review daily** - Check summary each morning
2. **Track habits consistently** - Same time each day
3. **Set realistic goals** - Break into smaller tasks
4. **Journal regularly** - Reflect on progress weekly
5. **Archive completed items** - Keep folders organized
