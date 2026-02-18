#!/usr/bin/env python3
"""
Task Planner - Analyze Inbox files and create action plans

Reads .md files from Inbox, analyzes content, creates step-by-step plans,
and manages file workflow. Integrates with vault-file-manager for moving
processed files to Done folder.

Usage:
    python scripts/task_planner.py              # Continuous mode (30s interval)
    python scripts/task_planner.py --once       # Single run
    python scripts/task_planner.py -i 20        # Custom interval (20s)
    python scripts/task_planner.py -f Inbox     # Custom folder
    python scripts/task_planner.py --stats      # Show statistics
"""

import os
import sys
import json
import hashlib
import time
import re
import argparse
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Any

# ============================================================================
# Configuration
# ============================================================================

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.dirname(SCRIPT_DIR)

INBOX_PATH = os.path.join(VAULT_ROOT, "Inbox")
NEEDS_ACTION_PATH = os.path.join(VAULT_ROOT, "Needs_Action")
PLANS_PATH = os.path.join(VAULT_ROOT, "Plans")
DONE_PATH = os.path.join(VAULT_ROOT, "Done")
LOGS_PATH = os.path.join(VAULT_ROOT, "Logs")
TRACKING_FILE = os.path.join(LOGS_PATH, "task_planner_tracking.json")
ACTIONS_LOG = os.path.join(LOGS_PATH, "actions.log")
DASHBOARD_FILE = os.path.join(VAULT_ROOT, "Dashboard.md")

DEFAULT_CHECK_INTERVAL = 30  # seconds
MIN_CHECK_INTERVAL = 10
MAX_CHECK_INTERVAL = 60

# ============================================================================
# File Tracker (Idempotency)
# ============================================================================

class TaskTracker:
    """Tracks processed files to ensure idempotent operation."""

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

    def mark_processed(self, file_hash: str, metadata: Dict = None):
        """Mark a file as processed."""
        self._processed_files.add(file_hash)
        self._save_tracking_data(metadata)

    def _save_tracking_data(self, metadata: Dict = None):
        """Save tracking data to file."""
        try:
            os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
            data = {
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "processed_files": list(self._processed_files),
                "count": len(self._processed_files),
                "last_metadata": metadata
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
        pass

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
        List of dicts with filepath, filename, hash, size, modified, content
    """
    files = []
    
    if not os.path.exists(inbox_path):
        os.makedirs(inbox_path, exist_ok=True)
        return files
    
    try:
        for filename in sorted(os.listdir(inbox_path)):  # Sorted for consistent ordering
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
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "content": _read_file_content(filepath)
            })
    except PermissionError as e:
        _log_error("permission_error", f"Cannot access inbox: {str(e)}")
    except OSError as e:
        _log_error("os_error", f"OS error scanning inbox: {str(e)}")
    
    return files

def _read_file_content(filepath: str) -> str:
    """Read file content safely."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception:
            return "[Binary file - content not readable]"
    except Exception as e:
        _log_error("read_error", f"Failed to read {filepath}: {str(e)}")
        return f"[Error reading file: {str(e)}]"

# ============================================================================
# Content Analyzer
# ============================================================================

def _analyze_content(content: str, filename: str) -> Dict:
    """
    Analyze file content to understand the task.
    
    Returns:
        Dict with task_type, priority, keywords, summary, suggested_actions
    """
    analysis = {
        "task_type": "general",
        "priority": "normal",
        "keywords": [],
        "summary": "",
        "suggested_actions": [],
        "entities": {},
        "word_count": 0
    }
    
    # Word count
    analysis["word_count"] = len(content.split())
    
    # Extract first paragraph as summary
    paragraphs = content.split('\n\n')
    if paragraphs:
        first_para = paragraphs[0].strip()
        # Remove markdown headers from summary
        first_para = re.sub(r'^#+\s*', '', first_para)
        analysis["summary"] = first_para[:200] + "..." if len(first_para) > 200 else first_para
    
    # Keyword extraction (simple frequency-based)
    words = re.findall(r'\b\w+\b', content.lower())
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once'}
    
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) > 3:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Top 5 keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    analysis["keywords"] = [word for word, _ in sorted_words[:5]]
    
    # Task type detection
    content_lower = content.lower()
    
    if any(kw in content_lower for kw in ['email', 'send', 'recipient', 'subject']):
        analysis["task_type"] = "email"
        analysis["suggested_actions"].extend([
            "Review email content and recipient",
            "Check for approval requirements",
            "Draft response if needed",
            "Send via approved channel"
        ])
    
    if any(kw in content_lower for kw in ['linkedin', 'post', 'social', 'publish']):
        analysis["task_type"] = "social_media"
        analysis["suggested_actions"].extend([
            "Review post content for brand alignment",
            "Check for approval requirements",
            "Schedule or publish via approved channel",
            "Monitor engagement after posting"
        ])
    
    if any(kw in content_lower for kw in ['report', 'analysis', 'document', 'review']):
        analysis["task_type"] = "document_review"
        analysis["suggested_actions"].extend([
            "Read and understand the document",
            "Identify key findings or issues",
            "Create summary or response",
            "File or distribute as appropriate"
        ])
    
    if any(kw in content_lower for kw in ['meeting', 'schedule', 'calendar', 'attend']):
        analysis["task_type"] = "scheduling"
        analysis["suggested_actions"].extend([
            "Check calendar availability",
            "Confirm or decline invitation",
            "Prepare agenda or materials if needed",
            "Set reminders"
        ])
    
    if any(kw in content_lower for kw in ['urgent', 'asap', 'immediate', 'priority', 'critical']):
        analysis["priority"] = "urgent"
    
    if any(kw in content_lower for kw in ['approval', 'authorize', 'permission', 'review required']):
        analysis["suggested_actions"].insert(0, "⚠️ REQUIRES HUMAN APPROVAL")
    
    # Default actions if none detected
    if not analysis["suggested_actions"]:
        analysis["suggested_actions"] = [
            "Review the task content",
            "Identify required actions",
            "Execute or delegate as appropriate",
            "Mark complete when done"
        ]
    
    # Entity extraction (simple patterns)
    # Emails
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
    if emails:
        analysis["entities"]["emails"] = emails
    
    # Dates
    dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', content)
    if dates:
        analysis["entities"]["dates"] = dates
    
    return analysis

# ============================================================================
# Plan Generator
# ============================================================================

def _generate_plan(filename: str, content: str, analysis: Dict) -> str:
    """
    Generate a step-by-step action plan.
    
    Returns:
        Markdown plan content
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    plan = f"""# Action Plan: {filename}

**Generated:** {timestamp}
**Task Type:** {analysis['task_type'].replace('_', ' ').title()}
**Priority:** {analysis['priority'].upper()}
**Word Count:** {analysis['word_count']}

---

## Summary

{analysis['summary']}

---

## Key Topics

{', '.join(analysis['keywords']) if analysis['keywords'] else 'No specific keywords identified'}

---

## Action Steps

"""
    
    # Add numbered action steps
    for i, action in enumerate(analysis['suggested_actions'], 1):
        plan += f"{i}. [ ] {action}\n"
    
    plan += f"""
---

## Timeline

- **Created:** {timestamp}
- **Priority:** {analysis['priority'].title()}
- **Estimated Completion:** {'Same day' if analysis['priority'] == 'urgent' else '1-2 business days'}

---

## Resources Needed

- [ ] Access to relevant systems
- [ ] Reference materials
- [ ] Team collaboration (if applicable)

---

## Notes

Add any additional context, decisions, or observations here.

---

## Completion Checklist

- [ ] All action steps completed
- [ ] Results documented
- [ ] Stakeholders notified (if applicable)
- [ ] File moved to Done folder

---

*Plan generated automatically by task-planner skill.*
*Original file: {filename}*
"""
    
    return plan

# ============================================================================
# File Operations
# ============================================================================

def _save_plan(plan_content: str, filename: str, needs_action_path: str = NEEDS_ACTION_PATH) -> str:
    """Save plan to Needs_Action folder."""
    try:
        os.makedirs(needs_action_path, exist_ok=True)
        
        # Generate plan filename
        base_name = os.path.splitext(filename)[0]
        plan_filename = f"Plan_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        plan_filepath = os.path.join(needs_action_path, plan_filename)
        
        with open(plan_filepath, 'w', encoding='utf-8') as f:
            f.write(plan_content)
        
        return plan_filepath
    except Exception as e:
        _log_error("plan_save_error", f"Failed to save plan: {str(e)}")
        return None

def _move_to_done(filepath: str, done_path: str = DONE_PATH) -> str:
    """Move processed file to Done folder."""
    try:
        os.makedirs(done_path, exist_ok=True)
        
        filename = os.path.basename(filepath)
        dest_path = os.path.join(done_path, filename)
        
        # Handle duplicates
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_path = os.path.join(done_path, f"{base}_{timestamp}{ext}")
        
        shutil.move(filepath, dest_path)
        return dest_path
    except Exception as e:
        _log_error("move_error", f"Failed to move file: {str(e)}")
        return None

def _update_dashboard(filename: str, plan_path: str):
    """Update Dashboard.md with recent activity."""
    try:
        # Create if doesn't exist
        if not os.path.exists(DASHBOARD_FILE):
            with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
                f.write("# Dashboard\n\n## Recent Activity\n\n")
        
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insert activity
        marker = "## Recent Activity"
        if marker in content:
            pos = content.find(marker) + len(marker)
            entry = f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Created plan for {filename} → {os.path.basename(plan_path)}"
            content = content[:pos] + entry + content[pos:]
        else:
            content += f"\n## Recent Activity\n- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Created plan for {filename}"
        
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        _log_error("dashboard_error", f"Failed to update dashboard: {str(e)}")

# ============================================================================
# Task Processor
# ============================================================================

def _process_file(file_info: Dict, tracker: TaskTracker) -> Dict:
    """
    Process a single file: analyze, create plan, move to Done.
    
    Returns:
        Processing result dict
    """
    filepath = file_info["filepath"]
    filename = file_info["filename"]
    file_hash = file_info["hash"]
    content = file_info.get("content", "")
    
    result = {
        "filename": filename,
        "filepath": filepath,
        "hash": file_hash[:16] + "...",
        "status": "pending",
        "plan_path": None,
        "done_path": None,
        "error": None
    }
    
    try:
        # Analyze content
        analysis = _analyze_content(content, filename)
        _log_action("content_analyzed", {
            "filename": filename,
            "task_type": analysis["task_type"],
            "priority": analysis["priority"]
        })
        
        # Generate plan
        plan_content = _generate_plan(filename, content, analysis)
        plan_path = _save_plan(plan_content, filename)
        
        if not plan_path:
            raise Exception("Failed to save plan")
        
        result["plan_path"] = plan_path
        _log_action("plan_created", {
            "filename": filename,
            "plan_path": plan_path
        })
        
        # Move original to Done
        done_path = _move_to_done(filepath)
        result["done_path"] = done_path
        _log_action("file_moved", {
            "filename": filename,
            "done_path": done_path
        })
        
        # Update dashboard
        _update_dashboard(filename, plan_path)
        
        # Mark as processed
        tracker.mark_processed(file_hash, {
            "filename": filename,
            "plan_path": plan_path,
            "done_path": done_path,
            "task_type": analysis["task_type"]
        })
        
        result["status"] = "success"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        _log_error("process_error", f"Failed to process {filename}: {str(e)}")
    
    return result

# ============================================================================
# Main Task Planner
# ============================================================================

def task_planner_skill(source_folder: str = "Inbox",
                      once: bool = False,
                      check_interval: int = DEFAULT_CHECK_INTERVAL) -> Dict:
    """
    Main entry point for the task-planner skill.
    
    Args:
        source_folder: Folder to scan for new files
        once: If True, run once and exit
        check_interval: Seconds between checks (10-60)
    
    Returns:
        Execution summary dictionary
    """
    # Validate interval
    check_interval = max(MIN_CHECK_INTERVAL, min(MAX_CHECK_INTERVAL, check_interval))
    
    # Resolve source path
    inbox_path = INBOX_PATH
    if source_folder and source_folder != "Inbox":
        inbox_path = os.path.join(VAULT_ROOT, source_folder)
    
    # Initialize tracker
    tracker = TaskTracker()
    
    # Ensure folders exist
    for path in [inbox_path, NEEDS_ACTION_PATH, PLANS_PATH, DONE_PATH, LOGS_PATH]:
        os.makedirs(path, exist_ok=True)
    
    # Log start
    _log_action("task_planner_started", {
        "source_folder": source_folder,
        "check_interval": check_interval,
        "mode": "once" if once else "continuous"
    })
    
    summary = {
        "started_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "source_folder": source_folder,
        "check_interval": check_interval,
        "mode": "once" if once else "continuous",
        "files_processed": 0,
        "files_skipped": 0,
        "errors": []
    }
    
    try:
        while True:
            # Scan inbox
            files = _scan_inbox(inbox_path)
            
            for file_info in files:
                file_hash = file_info["hash"]
                filename = file_info["filename"]
                
                # Check if already processed (idempotency)
                if tracker.is_processed(file_hash):
                    summary["files_skipped"] += 1
                    continue
                
                # Process the file
                result = _process_file(file_info, tracker)
                
                if result["status"] == "success":
                    summary["files_processed"] += 1
                else:
                    summary["errors"].append(f"{filename}: {result['error']}")
            
            # If once mode, exit after first scan
            if once:
                break
            
            # Wait for next check
            time.sleep(check_interval)
    
    except KeyboardInterrupt:
        _log_action("task_planner_stopped", {"reason": "user_interrupt"})
        summary["stopped_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        _log_error("planner_error", f"Unexpected error: {str(e)}")
        summary["errors"].append(str(e))
        summary["stopped_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add final stats
    summary["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    summary["tracker_stats"] = tracker.get_stats()
    
    return summary

# ============================================================================
# Convenience Functions
# ============================================================================

def plan_once() -> Dict:
    """Run planner once and exit."""
    return task_planner_skill(once=True)

def plan_continuous(interval: int = 30) -> Dict:
    """Run planner continuously with specified interval."""
    return task_planner_skill(check_interval=interval, once=False)

def plan_from_folder(folder_name: str) -> Dict:
    """Run planner once on a specific folder."""
    return task_planner_skill(source_folder=folder_name, once=True)

# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Task Planner - Analyze Inbox files and create action plans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python task_planner.py              # Continuous mode (30s interval)
  python task_planner.py --once       # Single run
  python task_planner.py -i 20        # Custom interval (20s)
  python task_planner.py -f Inbox     # Custom folder
  python task_planner.py --stats      # Show statistics
        """
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=DEFAULT_CHECK_INTERVAL,
        help=f"Check interval in seconds (10-60, default: {DEFAULT_CHECK_INTERVAL})"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (default: continuous mode)"
    )
    parser.add_argument(
        "--folder", "-f",
        type=str,
        default="Inbox",
        help="Source folder to scan (default: Inbox)"
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
        tracker = TaskTracker()
        stats = tracker.get_stats()
        print(f"{'Task Planner Statistics':^40}")
        print("=" * 40)
        print(f"Total files processed: {stats['total_processed']}")
        print(f"Last updated:          {stats['last_updated']}")
        print(f"Tracking file:         {TRACKING_FILE}")
        sys.exit(0)
    
    # Print startup info
    print(f"{'Task Planner':^40}")
    print("=" * 40)
    print(f"Source folder:   {args.folder}")
    print(f"Mode:            {'once' if args.once else 'continuous'}")
    print(f"Check interval:  {args.interval}s")
    print(f"Monitoring:      {INBOX_PATH}")
    if not args.once:
        print(f"\nPress Ctrl+C to stop")
    print("=" * 40)
    
    if args.verbose:
        print(f"Vault root:     {VAULT_ROOT}")
        print(f"Tracking file:  {TRACKING_FILE}")
    
    # Run planner
    result = task_planner_skill(
        source_folder=args.folder,
        check_interval=args.interval,
        once=args.once
    )
    
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
