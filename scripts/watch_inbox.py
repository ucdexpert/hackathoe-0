#!/usr/bin/env python3
"""
Vault Watcher - Monitor Inbox for new .md files

Lightweight file system watcher that triggers AI processing workflow
when new markdown files are detected in the Inbox folder.

Usage:
    python scripts/watch_inbox.py              # Continuous mode (20s interval)
    python scripts/watch_inbox.py --once       # Single run
    python scripts/watch_inbox.py -i 15        # Custom interval (15s)
    python scripts/watch_inbox.py --stats      # Show statistics
"""

import os
import sys
import json
import hashlib
import time
import argparse
from datetime import datetime
from typing import List, Dict, Optional

# ============================================================================
# Configuration
# ============================================================================

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.dirname(SCRIPT_DIR)

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
    
    Implementation options (uncomment one):
    1. Subprocess call to external script
    2. Direct import and function call
    3. File movement to trigger existing watchers
    """
    try:
        # Log the trigger
        _log_action("ai_workflow_triggered", {
            "filepath": filepath,
            "filename": os.path.basename(filepath)
        })
        
        # OPTION 1: Subprocess call (uncomment to use)
        # import subprocess
        # script_path = os.path.join(VAULT_ROOT, "run_ai_employee.py")
        # result = subprocess.run(
        #     ["python", script_path, "--once"],
        #     capture_output=True,
        #     text=True,
        #     timeout=300
        # )
        # if result.returncode != 0:
        #     _log_error("workflow_error", result.stderr)
        #     return False
        
        # OPTION 2: Direct import (uncomment to use)
        # sys.path.insert(0, VAULT_ROOT)
        # from orchestrator import process_all
        # process_all()
        
        # OPTION 3: Move file to Needs_Action (uncomment to use)
        # needs_action_dir = os.path.join(VAULT_ROOT, "Needs_Action")
        # os.makedirs(needs_action_dir, exist_ok=True)
        # dest_path = os.path.join(needs_action_dir, os.path.basename(filepath))
        # import shutil
        # shutil.move(filepath, dest_path)
        
        # For now, just log the trigger (placeholder)
        # Replace with actual implementation as needed
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

def main():
    parser = argparse.ArgumentParser(
        description="Vault Watcher - Monitor Inbox for new .md files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python watch_inbox.py              # Continuous mode (20s interval)
  python watch_inbox.py --once       # Single run
  python watch_inbox.py -i 15        # Custom interval (15s)
  python watch_inbox.py --stats      # Show statistics
        """
    )
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
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        tracker = FileTracker()
        stats = tracker.get_stats()
        print(f"{'Vault Watcher Statistics':^40}")
        print("=" * 40)
        print(f"Total files processed: {stats['total_processed']}")
        print(f"Last updated:          {stats['last_updated']}")
        print(f"Tracking file:         {TRACKING_FILE}")
        sys.exit(0)
    
    # Print startup info
    print(f"{'Vault Watcher':^40}")
    print("=" * 40)
    print(f"Mode:           {'once' if args.once else 'continuous'}")
    print(f"Check interval: {args.interval}s")
    print(f"Monitoring:     {INBOX_PATH}")
    print(f"Logs:           {ACTIONS_LOG}")
    if not args.once:
        print(f"\nPress Ctrl+C to stop")
    print("=" * 40)
    
    if args.verbose:
        print(f"Vault root:     {VAULT_ROOT}")
        print(f"Tracking file:  {TRACKING_FILE}")
    
    # Run watcher
    result = vault_watcher_skill(check_interval=args.interval, once=args.once)
    
    # Print summary
    if args.once or result.get('stopped_at'):
        print(f"\n{'Summary':^40}")
        print("-" * 40)
        print(f"Files processed: {result['files_processed']}")
        print(f"Files skipped:   {result['files_skipped']}")
        print(f"Errors:          {len(result['errors'])}")
        
        if result['errors']:
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        print(f"\nCompleted at: {result.get('completed_at', 'N/A')}")

if __name__ == "__main__":
    main()
