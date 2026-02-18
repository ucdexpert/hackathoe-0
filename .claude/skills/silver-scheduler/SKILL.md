# silver-scheduler

## Description
Scheduler Agent that orchestrates the AI Employee workflow by running vault-watcher and task-planner in a configurable loop. Supports multiple execution modes (daemon, once, status), implements duplicate instance prevention with lock files, and provides comprehensive logging with automatic rotation at 5MB.

## Parameters
- `--daemon` (flag): Run continuously in background mode
- `--once` (flag): Execute a single iteration and exit
- `--status` (flag): Show active tasks and inbox count, then exit
- `--interval` (int, optional): Interval between iterations in minutes. Default: 5
- `--log-file` (string, optional): Custom log file path. Default: `logs/ai_employee.log`
- `--max-log-size` (int, optional): Maximum log file size in MB before rotation. Default: 5
- `--lock-file` (string, optional): Custom lock file path. Default: `logs/.ai_employee.lock`

## Functionality
When invoked, this skill:
1. **Prevents duplicate instances** using lock files
2. **Runs vault-watcher** to monitor file system changes
3. **Runs task-planner** to analyze Inbox and create action plans
4. **Supports multiple execution modes**:
   - `--daemon`: Continuous background operation
   - `--once`: Single execution for testing/manual runs
   - `--status`: Quick status check without execution
5. **Logs all actions** to `logs/ai_employee.log` with timestamps
6. **Rotates logs automatically** when file exceeds 5MB
7. **Tracks scheduler statistics** (iterations, errors, uptime)
8. **Handles graceful shutdown** on SIGINT/SIGTERM

## Constraints
- **Single instance**: Only one scheduler can run at a time (lock file enforced)
- **Minimum interval**: 1 minute between iterations (prevents resource exhaustion)
- **Log rotation**: Automatic at 5MB to prevent disk space issues
- **Silver Tier compliant**: Follows logging and workflow requirements

## Execution Modes

| Mode | Flag | Behavior | Use Case |
|------|------|----------|----------|
| Daemon | `--daemon` | Runs continuously, 5-min intervals | Production deployment |
| Once | `--once` | Single iteration, then exits | Testing, manual runs |
| Status | `--status` | Shows status, no execution | Monitoring, health checks |

## Folder Structure

```
AI_Employee_Vault/
├── Inbox/              # Input files to process
├── Needs_Action/       # Items requiring attention
├── Plans/              # Generated action plans
├── Done/               # Completed items
├── Logs/
│   ├── ai_employee.log      # Main scheduler log
│   ├── ai_employee.log.1    # Rotated log (previous)
│   └── .ai_employee.lock    # Lock file (prevents duplicates)
└── Dashboard.md        # Activity summary
```

## Implementation
```python
import os
import sys
import json
import time
import signal
import argparse
import logging
import fcntl
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

# ============================================================================
# Configuration
# ============================================================================

# Resolve paths relative to vault root
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.dirname(SCRIPT_DIR)

# Default paths
LOGS_DIR = os.path.join(VAULT_ROOT, "Logs")
DEFAULT_LOG_FILE = os.path.join(LOGS_DIR, "ai_employee.log")
DEFAULT_LOCK_FILE = os.path.join(LOGS_DIR, ".ai_employee.lock")
DEFAULT_INTERVAL_MINUTES = 5
DEFAULT_MAX_LOG_SIZE_MB = 5
MIN_INTERVAL_MINUTES = 1

# Scripts to run
WATCHER_SCRIPT = os.path.join(VAULT_ROOT, "filesystem_watcher.py")
TASK_PLANNER_SCRIPT = os.path.join(SCRIPT_DIR, "task_planner.py")

# ============================================================================
# Lock File Manager
# ============================================================================

class LockFileManager:
    """Manages lock files to prevent duplicate instances."""

    def __init__(self, lock_file: str = DEFAULT_LOCK_FILE):
        self.lock_file = lock_file
        self.lock_fd = None
        self._ensure_logs_dir()

    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR, exist_ok=True)

    def acquire(self) -> bool:
        """
        Acquire the lock file.

        Returns:
            bool: True if lock acquired, False if already locked
        """
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write process info
            lock_info = {
                "pid": os.getpid(),
                "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "hostname": os.environ.get('COMPUTERNAME', 'unknown')
            }
            json.dump(lock_info, self.lock_fd)
            self.lock_fd.flush()

            return True

        except (IOError, OSError, BlockingIOError):
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            return False

    def release(self):
        """Release the lock file."""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
            except Exception:
                pass
            finally:
                self.lock_fd = None

    def check_existing(self) -> Optional[Dict]:
        """
        Check if another instance is running.

        Returns:
            dict: Lock info if locked, None otherwise
        """
        if not os.path.exists(self.lock_file):
            return None

        try:
            with open(self.lock_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None


# ============================================================================
# Rotating Logger
# ============================================================================

class SchedulerLogger:
    """Logger with automatic rotation at specified size."""

    def __init__(self, log_file: str = DEFAULT_LOG_FILE,
                 max_size_mb: int = DEFAULT_MAX_LOG_SIZE_MB):
        self.log_file = log_file
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self._ensure_logs_dir()
        self.logger = self._setup_logger()

    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR, exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """Set up rotating file logger."""
        logger = logging.getLogger('ai_employee_scheduler')
        logger.setLevel(logging.INFO)

        # Clear existing handlers
        logger.handlers = []

        # Rotating file handler
        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_size_bytes,
            backupCount=3,  # Keep 3 rotated logs
            encoding='utf-8'
        )

        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)


# ============================================================================
# Scheduler Statistics
# ============================================================================

class SchedulerStats:
    """Tracks scheduler execution statistics."""

    def __init__(self):
        self.start_time = None
        self.iterations = 0
        self.errors = 0
        self.last_run = None
        self.last_error = None
        self.watcher_runs = 0
        self.planner_runs = 0

    def start(self):
        """Mark scheduler start."""
        self.start_time = datetime.now()

    def record_iteration(self):
        """Record a completed iteration."""
        self.iterations += 1
        self.last_run = datetime.now()

    def record_error(self, error: str):
        """Record an error."""
        self.errors += 1
        self.last_error = error

    def record_watcher_run(self):
        """Record a watcher execution."""
        self.watcher_runs += 1

    def record_planner_run(self):
        """Record a planner execution."""
        self.planner_runs += 1

    def get_uptime(self) -> str:
        """Get uptime as formatted string."""
        if not self.start_time:
            return "N/A"
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            "uptime": self.get_uptime(),
            "iterations": self.iterations,
            "errors": self.errors,
            "last_run": self.last_run.strftime('%Y-%m-%d %H:%M:%S') if self.last_run else None,
            "last_error": self.last_error,
            "watcher_runs": self.watcher_runs,
            "planner_runs": self.planner_runs
        }


# ============================================================================
# Vault Status Checker
# ============================================================================

class VaultStatusChecker:
    """Checks status of vault folders and active tasks."""

    def __init__(self):
        self.inbox_dir = os.path.join(VAULT_ROOT, "Inbox")
        self.needs_action_dir = os.path.join(VAULT_ROOT, "Needs_Action")
        self.plans_dir = os.path.join(VAULT_ROOT, "Plans")
        self.done_dir = os.path.join(VAULT_ROOT, "Done")

    def count_files(self, directory: str) -> int:
        """Count files in a directory."""
        if not os.path.exists(directory):
            return 0
        return len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive vault status."""
        return {
            "inbox_count": self.count_files(self.inbox_dir),
            "needs_action_count": self.count_files(self.needs_action_dir),
            "plans_count": self.count_files(self.plans_dir),
            "done_count": self.count_files(self.done_dir),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# ============================================================================
# Script Runner
# ============================================================================

class ScriptRunner:
    """Runs external Python scripts."""

    def __init__(self, logger: SchedulerLogger):
        self.logger = logger

    def run_script(self, script_path: str, args: list = None) -> tuple:
        """
        Run a Python script.

        Args:
            script_path: Path to script
            args: Optional command-line arguments

        Returns:
            tuple: (success: bool, output: str)
        """
        if not os.path.exists(script_path):
            error_msg = f"Script not found: {script_path}"
            self.logger.error(error_msg)
            return False, error_msg

        try:
            import subprocess
            cmd = [sys.executable, script_path]
            if args:
                cmd.extend(args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr

            if result.returncode == 0:
                self.logger.info(f"Script executed successfully: {script_path}")
                return True, output
            else:
                error_msg = f"Script failed with code {result.returncode}: {output}"
                self.logger.error(error_msg)
                return False, output

        except subprocess.TimeoutExpired:
            error_msg = f"Script timed out: {script_path}"
            self.logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Script execution error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg


# ============================================================================
# Silver Scheduler
# ============================================================================

class SilverScheduler:
    """Main scheduler that orchestrates vault-watcher and task-planner."""

    def __init__(self, interval_minutes: int = DEFAULT_INTERVAL_MINUTES,
                 log_file: str = DEFAULT_LOG_FILE,
                 lock_file: str = DEFAULT_LOCK_FILE,
                 max_log_size_mb: int = DEFAULT_MAX_LOG_SIZE_MB):
        self.interval_minutes = max(interval_minutes, MIN_INTERVAL_MINUTES)
        self.interval_seconds = self.interval_minutes * 60

        self.logger = SchedulerLogger(log_file, max_log_size_mb)
        self.lock_manager = LockFileManager(lock_file)
        self.stats = SchedulerStats()
        self.status_checker = VaultStatusChecker()
        self.script_runner = ScriptRunner(self.logger)

        self.running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up graceful shutdown handlers."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def run_watcher(self) -> bool:
        """Run the vault watcher script."""
        self.logger.info("Running vault-watcher...")
        success, output = self.script_runner.run_script(WATCHER_SCRIPT)

        if success:
            self.stats.record_watcher_run()
            self.logger.debug(f"Watcher output: {output[:200]}...")
        else:
            self.stats.record_error(f"Watcher failed: {output}")

        return success

    def run_planner(self) -> bool:
        """Run the task planner script."""
        self.logger.info("Running task-planner...")
        success, output = self.script_runner.run_script(TASK_PLANNER_SCRIPT, ['--once'])

        if success:
            self.stats.record_planner_run()
            self.logger.debug(f"Planner output: {output[:200]}...")
        else:
            self.stats.record_error(f"Planner failed: {output}")

        return success

    def run_iteration(self) -> bool:
        """Run a single iteration (watcher + planner)."""
        self.logger.info(f"Starting iteration {self.stats.iterations + 1}")

        # Run watcher
        watcher_success = self.run_watcher()

        # Run planner
        planner_success = self.run_planner()

        # Record iteration
        self.stats.record_iteration()

        # Log status
        vault_status = self.status_checker.get_status()
        self.logger.info(f"Iteration complete. Inbox: {vault_status['inbox_count']}, "
                        f"Needs_Action: {vault_status['needs_action_count']}, "
                        f"Plans: {vault_status['plans_count']}")

        return watcher_success and planner_success

    def run_daemon(self) -> int:
        """
        Run in daemon mode (continuous).

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting AI Employee Scheduler (Daemon Mode)")
        self.logger.info(f"Interval: {self.interval_minutes} minutes")
        self.logger.info(f"Log file: {self.logger.log_file}")
        self.logger.info("=" * 60)

        # Acquire lock
        if not self.lock_manager.acquire():
            existing = self.lock_manager.check_existing()
            self.logger.error(f"Another instance is already running: {existing}")
            return 1

        self.logger.info("Lock acquired")

        try:
            self.running = True
            self.stats.start()

            while self.running:
                try:
                    self.run_iteration()

                    if self.running:
                        self.logger.info(f"Sleeping for {self.interval_minutes} minutes...")
                        time.sleep(self.interval_seconds)

                except KeyboardInterrupt:
                    self.logger.info("Interrupted by user")
                    break

                except Exception as e:
                    error_msg = f"Iteration error: {str(e)}"
                    self.logger.error(error_msg)
                    self.stats.record_error(error_msg)

                    if self.running:
                        self.logger.info(f"Retrying in {self.interval_minutes} minutes...")
                        time.sleep(self.interval_seconds)

        finally:
            self.lock_manager.release()
            self.logger.info("Lock released")

        # Log final stats
        self.logger.info("=" * 60)
        self.logger.info("Scheduler stopped")
        stats = self.stats.to_dict()
        self.logger.info(f"Uptime: {stats['uptime']}")
        self.logger.info(f"Iterations: {stats['iterations']}")
        self.logger.info(f"Errors: {stats['errors']}")
        self.logger.info(f"Watcher runs: {stats['watcher_runs']}")
        self.logger.info(f"Planner runs: {stats['planner_runs']}")
        self.logger.info("=" * 60)

        return 0 if self.stats.errors == 0 else 1

    def run_once(self) -> int:
        """
        Run a single iteration.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        self.logger.info("Running single iteration (Once Mode)")

        # Acquire lock
        if not self.lock_manager.acquire():
            existing = self.lock_manager.check_existing()
            self.logger.error(f"Another instance is already running: {existing}")
            return 1

        try:
            self.stats.start()
            success = self.run_iteration()
            return 0 if success else 1

        finally:
            self.lock_manager.release()

    def show_status(self) -> int:
        """
        Show current status.

        Returns:
            int: Exit code (0 for success)
        """
        print("\n" + "=" * 60)
        print("AI Employee Scheduler Status")
        print("=" * 60)

        # Check for running instance
        lock_info = self.lock_manager.check_existing()
        if lock_info:
            print(f"\nScheduler Status: RUNNING")
            print(f"PID: {lock_info.get('pid', 'N/A')}")
            print(f"Started: {lock_info.get('started_at', 'N/A')}")
        else:
            print(f"\nScheduler Status: NOT RUNNING")

        # Vault status
        vault_status = self.status_checker.get_status()
        print(f"\nVault Status:")
        print(f"  Inbox:        {vault_status['inbox_count']} files")
        print(f"  Needs_Action: {vault_status['needs_action_count']} files")
        print(f"  Plans:        {vault_status['plans_count']} files")
        print(f"  Done:         {vault_status['done_count']} files")

        # Log file status
        if os.path.exists(self.logger.log_file):
            log_size = os.path.getsize(self.logger.log_file) / (1024 * 1024)
            print(f"\nLog File: {self.logger.log_file}")
            print(f"Log Size: {log_size:.2f} MB")
        else:
            print(f"\nLog File: Not created yet")

        print("=" * 60 + "\n")

        return 0


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Command-line interface for Silver Scheduler."""
    parser = argparse.ArgumentParser(
        description='AI Employee Scheduler - Orchestrates vault-watcher and task-planner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run in daemon mode (continuous, 5-min intervals):
    python run_ai_employee.py --daemon

  Run single iteration:
    python run_ai_employee.py --once

  Show status:
    python run_ai_employee.py --status

  Custom interval (10 minutes):
    python run_ai_employee.py --daemon --interval 10

  Custom log file:
    python run_ai_employee.py --daemon --log-file logs/custom.log
        """
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--daemon', '-d',
        action='store_true',
        help='Run continuously in daemon mode (default: 5-min intervals)'
    )
    mode_group.add_argument(
        '--once', '-o',
        action='store_true',
        help='Run a single iteration and exit'
    )
    mode_group.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show status and exit'
    )

    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=DEFAULT_INTERVAL_MINUTES,
        help=f'Interval in minutes (default: {DEFAULT_INTERVAL_MINUTES})'
    )
    parser.add_argument(
        '--log-file', '-l',
        default=DEFAULT_LOG_FILE,
        help=f'Log file path (default: {DEFAULT_LOG_FILE})'
    )
    parser.add_argument(
        '--lock-file',
        default=DEFAULT_LOCK_FILE,
        help=f'Lock file path (default: {DEFAULT_LOCK_FILE})'
    )
    parser.add_argument(
        '--max-log-size',
        type=int,
        default=DEFAULT_MAX_LOG_SIZE_MB,
        help=f'Max log size in MB before rotation (default: {DEFAULT_MAX_LOG_SIZE_MB})'
    )

    args = parser.parse_args()

    # Default to daemon mode if no mode specified
    if not (args.daemon or args.once or args.status):
        print("No mode specified. Use --daemon, --once, or --status")
        print("Defaulting to --status for safety")
        args.status = True

    # Create scheduler
    scheduler = SilverScheduler(
        interval_minutes=args.interval,
        log_file=args.log_file,
        lock_file=args.lock_file,
        max_log_size_mb=args.max_log_size
    )

    # Execute based on mode
    if args.status:
        return scheduler.show_status()
    elif args.once:
        return scheduler.run_once()
    elif args.daemon:
        return scheduler.run_daemon()
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## Usage Examples

### Daemon Mode (Production)
```bash
# Run continuously with default 5-minute intervals
python scripts/run_ai_employee.py --daemon

# Custom interval (10 minutes)
python scripts/run_ai_employee.py --daemon --interval 10

# Custom log file
python scripts/run_ai_employee.py --daemon --log-file logs/custom.log
```

### Once Mode (Testing)
```bash
# Run single iteration
python scripts/run_ai_employee.py --once

# With custom interval for next run
python scripts/run_ai_employee.py --once --interval 3
```

### Status Mode (Monitoring)
```bash
# Show current status
python scripts/run_ai_employee.py --status

# Output:
# ============================================================
# AI Employee Scheduler Status
# ============================================================
#
# Scheduler Status: RUNNING
# PID: 12345
# Started: 2026-02-18 10:00:00
#
# Vault Status:
#   Inbox:        5 files
#   Needs_Action: 3 files
#   Plans:        10 files
#   Done:         50 files
#
# Log File: Logs/ai_employee.log
# Log Size: 2.34 MB
# ============================================================
```

## Lock File Mechanism

The scheduler uses lock files to prevent duplicate instances:

```python
# Lock file format (JSON)
{
    "pid": 12345,
    "started_at": "2026-02-18 10:00:00",
    "hostname": "SERVER01"
}
```

If another instance tries to start:
```
ERROR - Another instance is already running: {'pid': 12345, ...}
```

## Log Rotation

Logs automatically rotate at 5MB:
- `ai_employee.log` - Current log
- `ai_employee.log.1` - Previous log
- `ai_employee.log.2` - Older log
- `ai_employee.log.3` - Oldest log

## Log Format

```
2026-02-18 10:00:00 - INFO - ============================================================
2026-02-18 10:00:00 - INFO - Starting AI Employee Scheduler (Daemon Mode)
2026-02-18 10:00:00 - INFO - Interval: 5 minutes
2026-02-18 10:00:00 - INFO - Lock acquired
2026-02-18 10:00:01 - INFO - Running vault-watcher...
2026-02-18 10:00:05 - INFO - Running task-planner...
2026-02-18 10:00:10 - INFO - Iteration complete. Inbox: 5, Needs_Action: 3, Plans: 10
```

## Signal Handling

Graceful shutdown on SIGINT/SIGTERM:
```
2026-02-18 12:00:00 - INFO - Received signal 2, shutting down...
2026-02-18 12:00:00 - INFO - Lock released
2026-02-18 12:00:00 - INFO - ============================================================
2026-02-18 12:00:00 - INFO - Scheduler stopped
2026-02-18 12:00:00 - INFO - Uptime: 2h 0m 0s
2026-02-18 12:00:00 - INFO - Iterations: 24
```

## Error Handling

| Error | Behavior |
|-------|----------|
| Lock exists | Exit with error message |
| Script not found | Log error, continue to next script |
| Script timeout | Log error, retry next iteration |
| KeyboardInterrupt | Graceful shutdown |
| Log rotation failure | Continue with degraded logging |

## Integration with CI/CD

```yaml
# Example GitHub Actions
- name: Run AI Employee Scheduler
  run: |
    python scripts/run_ai_employee.py --once
    python scripts/run_ai_employee.py --status
```

## Security Notes

- Lock files prevent race conditions
- Log rotation prevents disk exhaustion
- Script timeouts prevent hangs
- Graceful shutdown preserves state
- All operations logged for audit
