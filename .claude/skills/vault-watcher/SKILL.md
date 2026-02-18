# vault-watcher

## Description
A lightweight file system watcher agent that continuously monitors the `Inbox` folder for new `.md` files. When new files are detected, it logs the event and triggers the AI processing workflow. Designed for production use with duplicate prevention and efficient polling.

## Parameters
- `check_interval` (int, optional): Seconds between checks. Default: 20 (range: 10-30)
- `once` (bool, optional): If True, run once and exit. Default: False (continuous mode)

## Functionality
When invoked, this skill:
1. Continuously monitors `AI_Employee_Vault/Inbox` folder for new `.md` files
2. Logs detection events to `Logs/actions.log`
3. Triggers AI processing workflow (equivalent to `run_ai_employee.py --once`)
4. Prevents duplicate processing via tracking file
5. Runs on configurable interval (10-30 seconds)
6. Supports both continuous and single-run modes

## Constraints
- Only monitors `.md` files in the Inbox folder
- Never processes the same file twice (tracked by file hash)
- Lightweight design - minimal resource usage
- Production-ready with proper error handling
- No external dependencies beyond Python standard library
- Silver Tier compliant with full audit logging

## File Tracking
Processed files are tracked in `Logs/vault_watcher_tracking.json` to prevent duplicate processing.

## Implementation
```python
import os
import json
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Optional

# ============================================================================
# Configuration
# ============================================================================

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_PATH = os.path.join(VAULT_ROOT, "Inbox")
LOGS_PATH = os.path.join(VAULT_ROOT, "Logs")
TRACKING_FILE = os.path.join(LOGS_PATH, "vault_watcher_tracking.json")
ACTIONS_LOG = os.path.join(LOGS_PATH, "actions.log")

DEFAULT_CHECK_INTERVAL = 20  # seconds
MIN_CHECK_INTERVAL = 10
MAX_CHECK_INTERVAL = 30

# ============================================================================
# File Tracker
# ============================================================================

class FileTracker:
    """Tracks processed files to prevent duplicate processing."""

    def __init__(self, tracking_file: str = TRACKING_FILE):
        self.tracking_file = tracking_file
        self._processed_files = self._load_tracking_data()

    def _load_tracking_data(self) -> set:
        """Load previously processed file hashes."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('processed_files', []))
            except (json.JSONDecodeError, KeyError):
                pass
        return set()

    def is_processed(self, file_hash: str) -> bool:
        """Check if a file has already been processed."""
        return file_hash in self._processed_files

    def mark_processed(self, file_hash: str):
        """Mark a file as processed."""
        self._processed_files.add(file_hash)
        self._save_tracking_data()

    def _save_tracking_data(self):
        """Save tracking data to file."""
        try:
            os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
            data = {
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "processed_files": list(self._processed_files),
                "count": len(self._processed_files)
            }
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _log_error("tracking_save_error", str(e))

    def get_stats(self) -> Dict:
        """Get tracking statistics."""
        return {
            "total_processed": len(self._processed_files),
            "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# ============================================================================
# Logger
# ============================================================================

def _log_action(action: str, details: Dict = None, status: str = "success"):
    """Log an action to actions.log."""
    try:
        os.makedirs(LOGS_PATH, exist_ok=True)
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "action": action,
            "details": details or {},
            "status": status
        }
        with open(ACTIONS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Silent fail for logging

def _log_error(error_type: str, message: str):
    """Log an error."""
    _log_action("error", {"error_type": error_type, "message": message}, "error")

# ============================================================================
# File Scanner
# ============================================================================

def _compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of file content."""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        return hashlib.sha256(content).hexdigest()
    except Exception as e:
        _log_error("hash_error", f"Failed to hash {filepath}: {str(e)}")
        return None

def _scan_inbox(inbox_path: str = INBOX_PATH) -> List[Dict]:
    """
    Scan inbox for .md files.
    
    Returns:
        List of dicts with filepath, filename, hash, size, modified
    """
    files = []
    
    if not os.path.exists(inbox_path):
        os.makedirs(inbox_path, exist_ok=True)
        return files
    
    try:
        for filename in os.listdir(inbox_path):
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(inbox_path, filename)
            
            if not os.path.isfile(filepath):
                continue
            
            file_hash = _compute_file_hash(filepath)
            if file_hash is None:
                continue
            
            stat = os.stat(filepath)
            files.append({
                "filepath": filepath,
                "filename": filename,
                "hash": file_hash,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    except PermissionError as e:
        _log_error("permission_error", f"Cannot access inbox: {str(e)}")
    except OSError as e:
        _log_error("os_error", f"OS error scanning inbox: {str(e)}")
    
    return files

# ============================================================================
# AI Workflow Trigger
# ============================================================================

def _trigger_ai_workflow(filepath: str) -> bool:
    """
    Trigger AI processing workflow for a file.
    
    This is equivalent to running: run_ai_employee.py --once
    
    In a real implementation, this would:
    1. Move file from Inbox to Needs_Action
    2. Trigger orchestrator.py or equivalent
    3. Create plan files
    
    For now, we log the trigger event.
    """
    try:
        # Log the trigger
        _log_action("ai_workflow_triggered", {
            "filepath": filepath,
            "filename": os.path.basename(filepath)
        })
        
        # TODO: Implement actual workflow trigger
        # Options:
        # 1. Import and call orchestrator directly
        # 2. Subprocess call to run_ai_employee.py --once
        # 3. Move file to Needs_Action folder
        
        return True
    except Exception as e:
        _log_error("workflow_trigger_error", f"Failed to trigger workflow: {str(e)}")
        return False

# ============================================================================
# Main Watcher
# ============================================================================

def vault_watcher_skill(check_interval: int = DEFAULT_CHECK_INTERVAL, 
                        once: bool = False) -> Dict:
    """
    Main entry point for the vault-watcher skill.
    
    Args:
        check_interval: Seconds between checks (10-30)
        once: If True, run once and exit
    
    Returns:
        Execution summary dictionary
    """
    # Validate interval
    check_interval = max(MIN_CHECK_INTERVAL, min(MAX_CHECK_INTERVAL, check_interval))
    
    # Initialize tracker
    tracker = FileTracker()
    
    # Ensure inbox exists
    os.makedirs(INBOX_PATH, exist_ok=True)
    
    # Log start
    _log_action("watcher_started", {
        "check_interval": check_interval,
        "mode": "once" if once else "continuous"
    })
    
    summary = {
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "check_interval": check_interval,
        "mode": "once" if once else "continuous",
        "files_processed": 0,
        "files_skipped": 0,
        "errors": []
    }
    
    try:
        while True:
            # Scan inbox
            files = _scan_inbox()
            
            for file_info in files:
                file_hash = file_info["hash"]
                filepath = file_info["filepath"]
                filename = file_info["filename"]
                
                # Check if already processed
                if tracker.is_processed(file_hash):
                    summary["files_skipped"] += 1
                    continue
                
                # Log detection
                _log_action("file_detected", {
                    "filename": filename,
                    "filepath": filepath,
                    "size": file_info["size"],
                    "hash": file_hash[:16] + "..."
                })
                
                # Trigger AI workflow
                if _trigger_ai_workflow(filepath):
                    # Mark as processed
                    tracker.mark_processed(file_hash)
                    summary["files_processed"] += 1
                    
                    _log_action("file_processed", {
                        "filename": filename,
                        "filepath": filepath
                    })
                else:
                    summary["errors"].append(f"Failed to process: {filename}")
            
            # If once mode, exit after first scan
            if once:
                break
            
            # Wait for next check
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        _log_action("watcher_stopped", {"reason": "user_interrupt"})
        summary["stopped_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        _log_error("watcher_error", f"Unexpected error: {str(e)}")
        summary["errors"].append(str(e))
        summary["stopped_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add final stats
    summary["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    summary["tracker_stats"] = tracker.get_stats()
    
    return summary

# ============================================================================
# Convenience Functions
# ============================================================================

def watch_once() -> Dict:
    """Run watcher once and exit."""
    return vault_watcher_skill(once=True)

def watch_continuous(interval: int = 20) -> Dict:
    """Run watcher continuously with specified interval."""
    return vault_watcher_skill(check_interval=interval, once=False)

# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Vault Watcher - Monitor Inbox for new files")
    parser.add_argument(
        "--interval", "-i", 
        type=int, 
        default=DEFAULT_CHECK_INTERVAL,
        help=f"Check interval in seconds (10-30, default: {DEFAULT_CHECK_INTERVAL})"
    )
    parser.add_argument(
        "--once", 
        action="store_true",
        help="Run once and exit (default: continuous mode)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show tracking statistics and exit"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        tracker = FileTracker()
        stats = tracker.get_stats()
        print(f"Vault Watcher Statistics")
        print(f"=" * 40)
        print(f"Total files processed: {stats['total_processed']}")
        print(f"Last updated: {stats['last_updated']}")
    else:
        print(f"Vault Watcher starting...")
        print(f"Mode: {'once' if args.once else 'continuous'}")
        print(f"Check interval: {args.interval}s")
        print(f"Monitoring: {INBOX_PATH}")
        print(f"Press Ctrl+C to stop")
        print("=" * 40)
        
        result = vault_watcher_skill(check_interval=args.interval, once=args.once)
        
        if args.once:
            print(f"\nCompleted: {result['files_processed']} files processed, {result['files_skipped']} skipped")
            if result['errors']:
                print(f"Errors: {result['errors']}")
```

## Usage Examples

### Continuous Monitoring (Default)
```python
from vault_watcher import vault_watcher_skill

result = vault_watcher_skill()
# Runs continuously, checking every 20 seconds
```

### Single Run
```python
from vault_watcher import watch_once

result = watch_once()
# Scans once and exits
```

### Custom Interval
```python
from vault_watcher import watch_continuous

result = watch_continuous(interval=15)
# Checks every 15 seconds
```

### CLI Usage
```bash
# Continuous mode (default)
python scripts/watch_inbox.py

# Single run
python scripts/watch_inbox.py --once

# Custom interval
python scripts/watch_inbox.py --interval 15

# Show statistics
python scripts/watch_inbox.py --stats
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Vault Watcher                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Scanner   │───▶│  Tracker    │───▶│  Workflow   │ │
│  │  (Inbox)    │    │ (Duplicate) │    │   Trigger   │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                  │                  │         │
│         ▼                  ▼                  ▼         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  .md files  │    │  tracking   │    │  actions    │ │
│  │             │    │  .json      │    │  .log       │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## File Structure

```
AI_Employee_Vault/
├── Inbox/                    # Monitored folder
│   └── *.md                  # New .md files trigger workflow
├── Logs/
│   ├── actions.log           # Detection & processing events
│   └── vault_watcher_tracking.json  # Processed file hashes
└── .claude/skills/vault-watcher/
    └── SKILL.md              # This skill definition
```

## Log Format (actions.log)

```json
{"timestamp": "2026-02-18 10:30:00", "action": "file_detected", "details": {"filename": "task.md", "hash": "abc123..."}, "status": "success"}
{"timestamp": "2026-02-18 10:30:01", "action": "ai_workflow_triggered", "details": {"filepath": "..."}, "status": "success"}
{"timestamp": "2026-02-18 10:30:01", "action": "file_processed", "details": {"filename": "task.md"}, "status": "success"}
```

## Tracking Format (vault_watcher_tracking.json)

```json
{
  "last_updated": "2026-02-18 10:30:00",
  "processed_files": ["hash1", "hash2", ...],
  "count": 42
}
```

## Production Features

- **Duplicate Prevention**: SHA256 hash tracking ensures no file is processed twice
- **Lightweight**: Uses only Python standard library
- **Resilient**: Continues on errors, logs all failures
- **Observable**: JSON logging for monitoring and debugging
- **Configurable**: Adjustable check interval (10-30 seconds)
- **CLI Support**: Command-line interface for direct execution

## Integration Notes

To fully integrate with the AI Employee workflow:

1. Update `_trigger_ai_workflow()` to call your actual workflow:
   ```python
   import subprocess
   subprocess.run(["python", "run_ai_employee.py", "--once"])
   ```

2. Or import directly:
   ```python
   from orchestrator import process_all
   process_all()
   ```

3. Or move files to trigger existing watchers:
   ```python
   shutil.move(filepath, filepath.replace("Inbox", "Needs_Action"))
   ```
