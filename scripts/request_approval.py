"""
Request Approval Script

This script provides the Human Approval skill for managing approval workflows.
It monitors the Needs_Approval folder, blocks execution until human writes
APPROVED/REJECTED in the file, and handles timeouts.

Usage:
    python scripts/request_approval.py --action-type email --recipient "user@example.com" --subject "Test" --body "Message"
    python scripts/request_approval.py --action-type linkedin --content "Post content" --topic "Topic"
    python scripts/request_approval.py --request-id "email_20260218_123456" --check-status
    python scripts/request_approval.py --action-type email --recipient "user@example.com" --subject "Test" --body "Message" --timeout-minutes 30 --priority urgent
"""

import os
import sys
import json
import argparse
import time
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from enum import Enum


# ============================================================================
# Configuration
# ============================================================================

VAULT_FOLDERS = {
    "needs_approval": "Needs_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "needs_action": "Needs_Action",
    "logs": "Logs"
}

# Default timeout: 1 hour
DEFAULT_TIMEOUT_MINUTES = 60

# Default polling interval: 10 seconds
DEFAULT_POLL_INTERVAL = 10

# Action log file
ACTION_LOG_FILE = "actions.log"


# ============================================================================
# Enums
# ============================================================================

class ApprovalStatus(Enum):
    """Approval status enumeration."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    TIMEOUT = "TIMEOUT"


class ApprovalResult(Enum):
    """Final approval result."""
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


# ============================================================================
# Action Logger
# ============================================================================

class ApprovalLogger:
    """Logs all approval actions to actions.log."""

    def __init__(self, logs_dir: str = None):
        self.logs_dir = logs_dir or VAULT_FOLDERS["logs"]
        self.log_file = os.path.join(self.logs_dir, ACTION_LOG_FILE)
        self._ensure_logs_dir()

    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, exist_ok=True)

    def log_approval_request(self, request_id: str, action_type: str,
                             action_data: Dict, priority: str):
        """Log a new approval request."""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event": "approval_request_created",
            "request_id": request_id,
            "action_type": action_type,
            "priority": priority,
            "action_data": self._sanitize_data(action_data)
        }
        self._write_log(log_entry)

    def log_approval_decision(self, request_id: str, status: ApprovalStatus,
                              decided_at: str = None, comments: str = None):
        """Log an approval decision."""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event": "approval_decision",
            "request_id": request_id,
            "status": status.value,
            "decided_at": decided_at,
            "comments": comments
        }
        self._write_log(log_entry)

    def log_file_operation(self, request_id: str, operation: str,
                           source_path: str, dest_path: str):
        """Log a file operation (move/rename)."""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event": "file_operation",
            "request_id": request_id,
            "operation": operation,
            "source_path": source_path,
            "dest_path": dest_path
        }
        self._write_log(log_entry)

    def log_timeout(self, request_id: str, timeout_minutes: int):
        """Log a timeout event."""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event": "approval_timeout",
            "request_id": request_id,
            "timeout_minutes": timeout_minutes
        }
        self._write_log(log_entry)

    def _sanitize_data(self, data: Dict) -> Dict:
        """Sanitize sensitive data for logging."""
        sanitized = data.copy()
        sensitive_fields = ['password', 'secret', 'token', 'api_key', 'credential']
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***'
        return sanitized

    def _write_log(self, log_entry: Dict):
        """Write log entry to actions.log (line-delimited JSON)."""
        try:
            existing_logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    try:
                        for line in f:
                            line = line.strip()
                            if line:
                                existing_logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        existing_logs = []

            existing_logs.append(log_entry)

            with open(self.log_file, 'w', encoding='utf-8') as f:
                for entry in existing_logs:
                    f.write(json.dumps(entry, default=str) + '\n')

        except Exception as e:
            print(f"Failed to write approval log: {str(e)}")


# ============================================================================
# Approval Request Manager
# ============================================================================

class ApprovalRequestManager:
    """Manages approval request files in the vault."""

    def __init__(self):
        self.logger = ApprovalLogger()
        self._ensure_folders()

    def _ensure_folders(self):
        """Ensure all required folders exist."""
        for folder in VAULT_FOLDERS.values():
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)

    def create_request(self, request_id: str, action_type: str,
                       action_data: Dict, priority: str = "normal") -> str:
        """
        Create an approval request file.

        Args:
            request_id: Unique request identifier
            action_type: Type of action requiring approval
            action_data: Action data
            priority: Priority level

        Returns:
            Path to the created request file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = f"{request_id}.md"
        filepath = os.path.join(VAULT_FOLDERS["needs_approval"], filename)

        # Format action data as readable JSON
        action_data_json = json.dumps(action_data, indent=2, default=str)

        content = f"""# Approval Request

## Request ID
{request_id}

## Action Type
{action_type}

## Created
{timestamp}

## Priority
{priority.upper()}

## Action Details
```json
{action_data_json}
```

## Instructions for Human Reviewer

To **APPROVE**: Change the status below to `APPROVED`
To **REJECT**: Change the status below to `REJECTED`

Optionally, add your comments in the section below.

## Status
<!-- AI Employee monitors this field - do not remove this comment -->
status: PENDING

## Reviewer Comments
<!-- Add optional comments here -->

---
*Generated by human-approval skill at {timestamp}*
*Request ID: {request_id}*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # Log the request
        self.logger.log_approval_request(request_id, action_type, action_data, priority)

        print(f"Approval request created: {filepath}")
        print(f"Request ID: {request_id}")
        print(f"Waiting for human review...")

        return filepath

    def check_status(self, request_id: str) -> Tuple[ApprovalStatus, Optional[str], Optional[str]]:
        """
        Check the approval status of a request.

        Args:
            request_id: Request identifier to check

        Returns:
            Tuple of (status, decided_at, comments)
        """
        filepath = self._find_request_file(request_id)
        if not filepath:
            return ApprovalStatus.PENDING, None, None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            status = self._parse_status(content)
            decided_at = self._parse_decided_at(content)
            comments = self._parse_comments(content)

            return status, decided_at, comments

        except Exception:
            return ApprovalStatus.PENDING, None, None

    def wait_for_decision(self, request_id: str,
                         timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES,
                         poll_interval: int = DEFAULT_POLL_INTERVAL,
                         verbose: bool = True) -> ApprovalResult:
        """
        Wait for human approval decision.

        Args:
            request_id: Request identifier to wait for
            timeout_minutes: Maximum wait time in minutes
            poll_interval: Polling interval in seconds
            verbose: If True, print status updates

        Returns:
            ApprovalResult (APPROVED, REJECTED, or TIMEOUT)
        """
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        elapsed = 0

        if verbose:
            print(f"Monitoring for approval (timeout: {timeout_minutes} minutes)...")
            print(f"Polling every {poll_interval} seconds")
            print("-" * 50)

        while elapsed < timeout_seconds:
            status, decided_at, comments = self.check_status(request_id)

            if verbose and elapsed % (poll_interval * 3) < poll_interval:
                remaining = (timeout_seconds - elapsed) / 60
                print(f"Status: {status.value} | Remaining: {remaining:.1f} min")

            if status == ApprovalStatus.APPROVED:
                self.logger.log_approval_decision(
                    request_id, status, decided_at, comments
                )
                if verbose:
                    print("-" * 50)
                    print(f"✓ APPROVED at {decided_at or 'unknown time'}")
                    if comments:
                        print(f"Comments: {comments}")
                return ApprovalResult.APPROVED

            elif status == ApprovalStatus.REJECTED:
                self.logger.log_approval_decision(
                    request_id, status, decided_at, comments
                )
                if verbose:
                    print("-" * 50)
                    print(f"✗ REJECTED at {decided_at or 'unknown time'}")
                    if comments:
                        print(f"Comments: {comments}")
                return ApprovalResult.REJECTED

            time.sleep(poll_interval)
            elapsed = time.time() - start_time

        # Timeout reached
        self.logger.log_timeout(request_id, timeout_minutes)
        if verbose:
            print("-" * 50)
            print(f"⏱ TIMEOUT after {timeout_minutes} minutes")

        return ApprovalResult.TIMEOUT

    def finalize_request(self, request_id: str, result: ApprovalResult) -> str:
        """
        Finalize the request by moving/renaming the file.

        Args:
            request_id: Request identifier
            result: Approval result

        Returns:
            New file path
        """
        source_path = self._find_request_file(request_id)
        if not source_path:
            print(f"Warning: Request file not found for {request_id}")
            return None

        # Determine destination folder and prefix
        if result == ApprovalResult.APPROVED:
            dest_folder = VAULT_FOLDERS["approved"]
            prefix = "approved"
        elif result == ApprovalResult.REJECTED:
            dest_folder = VAULT_FOLDERS["rejected"]
            prefix = "rejected"
        else:  # TIMEOUT
            dest_folder = VAULT_FOLDERS["needs_action"]
            prefix = "timeout"

        # Ensure destination folder exists
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder, exist_ok=True)

        # Create new filename
        filename = os.path.basename(source_path)
        new_filename = f"{prefix}_{filename}"
        dest_path = os.path.join(dest_folder, new_filename)

        # Handle existing file
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(new_filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{base}_{timestamp}{ext}"
            dest_path = os.path.join(dest_folder, new_filename)

        # Move the file
        with open(source_path, 'r', encoding='utf-8') as src:
            content = src.read()

        # Add finalization note
        finalization_note = f"\n\n---\n*{result.value.upper()} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        content += finalization_note

        with open(dest_path, 'w', encoding='utf-8') as dst:
            dst.write(content)

        # Remove original file
        if os.path.exists(source_path):
            os.remove(source_path)

        # Log the operation
        self.logger.log_file_operation(request_id, "move", source_path, dest_path)

        print(f"File moved to: {dest_path}")

        return dest_path

    def _find_request_file(self, request_id: str) -> Optional[str]:
        """Find the request file by request ID."""
        needs_approval_dir = VAULT_FOLDERS["needs_approval"]
        if not os.path.exists(needs_approval_dir):
            return None

        for filename in os.listdir(needs_approval_dir):
            if request_id in filename and filename.endswith('.md'):
                return os.path.join(needs_approval_dir, filename)

        return None

    def _parse_status(self, content: str) -> ApprovalStatus:
        """Parse status from file content."""
        content_lower = content.lower()

        if "status: approved" in content_lower or "**status:** approved" in content_lower:
            return ApprovalStatus.APPROVED
        elif "status: rejected" in content_lower or "**status:** rejected" in content_lower:
            return ApprovalStatus.REJECTED

        return ApprovalStatus.PENDING

    def _parse_decided_at(self, content: str) -> Optional[str]:
        """Parse decision timestamp from content."""
        match = re.search(r'\*(APPROVED|REJECTED)\s+at\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\*', content)
        if match:
            return match.group(2)
        return None

    def _parse_comments(self, content: str) -> Optional[str]:
        """Parse reviewer comments from content."""
        match = re.search(r'## Reviewer Comments\s*\n(.*?)(?=---|\Z)', content, re.DOTALL | re.IGNORECASE)
        if match:
            comments = match.group(1).strip()
            if comments and not comments.startswith('<!--'):
                return comments
        return None


# ============================================================================
# Human Approval Skill
# ============================================================================

class HumanApprovalSkill:
    """Main human approval skill implementation."""

    def __init__(self, timeout_minutes: int = DEFAULT_TIMEOUT_MINUTES,
                 poll_interval: int = DEFAULT_POLL_INTERVAL):
        self.request_manager = ApprovalRequestManager()
        self.timeout_minutes = timeout_minutes
        self.poll_interval = poll_interval

    def request_approval(self, action_type: str, action_data: Dict,
                        request_id: str = None,
                        priority: str = "normal",
                        wait: bool = True,
                        verbose: bool = True) -> Dict[str, Any]:
        """
        Request human approval for an action.

        Args:
            action_type: Type of action requiring approval
            action_data: Action data
            request_id: Optional request ID (auto-generated if not provided)
            priority: Priority level (low/normal/urgent)
            wait: If True, wait for decision (blocking)
            verbose: If True, print status updates

        Returns:
            dict: Result with status, request_id, and details
        """
        # Generate request ID if not provided
        if not request_id:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = uuid.uuid4().hex[:8]
            request_id = f"{action_type}_{timestamp}_{unique_id}"

        # Create the approval request
        filepath = self.request_manager.create_request(
            request_id, action_type, action_data, priority
        )

        result = {
            "status": "pending",
            "request_id": request_id,
            "filepath": filepath,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "timeout_minutes": self.timeout_minutes
        }

        if not wait:
            result["message"] = "Approval request created. Use wait_for_decision() to check status."
            if verbose:
                print(f"\nNon-blocking mode. Request ID: {request_id}")
                print(f"Check status with: python request_approval.py --request-id {request_id} --check-status")
            return result

        # Wait for decision (blocking)
        approval_result = self.request_manager.wait_for_decision(
            request_id, self.timeout_minutes, self.poll_interval, verbose
        )

        # Finalize the request
        final_path = self.request_manager.finalize_request(request_id, approval_result)

        result["result"] = approval_result.value
        result["status"] = approval_result.value
        result["final_path"] = final_path
        result["completed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if approval_result == ApprovalResult.APPROVED:
            result["message"] = "Action approved by human reviewer"
        elif approval_result == ApprovalResult.REJECTED:
            result["message"] = "Action rejected by human reviewer"
        else:
            result["message"] = f"Approval timeout after {self.timeout_minutes} minutes"

        return result

    def check_status(self, request_id: str) -> Dict[str, Any]:
        """
        Check the status of an approval request.

        Args:
            request_id: Request identifier

        Returns:
            dict: Status information
        """
        status, decided_at, comments = self.request_manager.check_status(request_id)

        return {
            "request_id": request_id,
            "status": status.value.lower(),
            "decided_at": decided_at,
            "comments": comments
        }

    def wait_for_decision(self, request_id: str,
                         timeout_minutes: int = None,
                         verbose: bool = True) -> ApprovalResult:
        """
        Wait for a decision on an existing request.

        Args:
            request_id: Request identifier
            timeout_minutes: Override timeout (optional)
            verbose: If True, print status updates

        Returns:
            ApprovalResult
        """
        timeout = timeout_minutes or self.timeout_minutes
        return self.request_manager.wait_for_decision(request_id, timeout, self.poll_interval, verbose)


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Command-line interface for Human Approval skill."""
    parser = argparse.ArgumentParser(
        description='Human Approval - Request and manage human approvals for AI actions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Request approval for email:
    python request_approval.py --action-type email --recipient "user@example.com" --subject "Test" --body "Message"

  Request approval for LinkedIn post:
    python request_approval.py --action-type linkedin --content "Post content" --topic "Topic"

  Check status of existing request:
    python request_approval.py --request-id "email_20260218_123456" --check-status

  Custom timeout and priority:
    python request_approval.py --action-type email -r "user@example.com" -s "Urgent" -b "Message" --timeout-minutes 15 --priority urgent

  Non-blocking mode (create request and return immediately):
    python request_approval.py --action-type email -r "user@example.com" -s "Test" -b "Message" --no-wait
        """
    )

    parser.add_argument(
        '--action-type', '-t',
        choices=['email', 'linkedin', 'file_operation', 'api_call', 'custom'],
        help='Type of action requiring approval'
    )
    parser.add_argument(
        '--recipient', '-r',
        help='Email recipient (for email action)'
    )
    parser.add_argument(
        '--subject', '-s',
        help='Email subject (for email action)'
    )
    parser.add_argument(
        '--body', '-b',
        help='Email body (for email action)'
    )
    parser.add_argument(
        '--content', '-c',
        help='LinkedIn post content (for linkedin action)'
    )
    parser.add_argument(
        '--topic',
        help='LinkedIn post topic (for linkedin action)'
    )
    parser.add_argument(
        '--operation',
        help='Operation type (for file_operation action)'
    )
    parser.add_argument(
        '--path',
        help='File path (for file_operation action)'
    )
    parser.add_argument(
        '--request-id',
        help='Existing request ID to check or wait for'
    )
    parser.add_argument(
        '--check-status',
        action='store_true',
        help='Check status of existing request and exit'
    )
    parser.add_argument(
        '--timeout-minutes',
        type=int,
        default=DEFAULT_TIMEOUT_MINUTES,
        help=f'Timeout in minutes (default: {DEFAULT_TIMEOUT_MINUTES})'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help=f'Polling interval in seconds (default: {DEFAULT_POLL_INTERVAL})'
    )
    parser.add_argument(
        '--priority',
        choices=['low', 'normal', 'urgent'],
        default='normal',
        help='Priority level (default: normal)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Non-blocking mode: create request and return immediately'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress status updates during waiting'
    )

    args = parser.parse_args()

    # Build action data based on action type
    action_data = {}

    if args.action_type == 'email':
        if not all([args.recipient, args.subject, args.body]):
            print("Error: --recipient, --subject, and --body are required for email action")
            sys.exit(1)
        action_data = {
            'recipient': args.recipient,
            'subject': args.subject,
            'body': args.body
        }
    elif args.action_type == 'linkedin':
        if not args.content:
            print("Error: --content is required for linkedin action")
            sys.exit(1)
        action_data = {
            'content': args.content,
            'topic': args.topic or ''
        }
    elif args.action_type == 'file_operation':
        if not all([args.operation, args.path]):
            print("Error: --operation and --path are required for file_operation action")
            sys.exit(1)
        action_data = {
            'operation': args.operation,
            'path': args.path
        }
    elif args.action_type == 'custom':
        action_data = {'type': 'custom', 'description': 'Custom action'}

    # Check if checking status of existing request
    if args.request_id and args.check_status:
        skill = HumanApprovalSkill(args.timeout_minutes, args.poll_interval)
        status = skill.check_status(args.request_id)

        if args.json:
            print(json.dumps(status, indent=2, default=str))
        else:
            print(f"\n{'='*50}")
            print(f"Approval Status")
            print(f"{'='*50}")
            print(f"Request ID: {status['request_id']}")
            print(f"Status: {status['status'].upper()}")
            if status['decided_at']:
                print(f"Decided At: {status['decided_at']}")
            if status['comments']:
                print(f"Comments: {status['comments']}")
            print(f"{'='*50}\n")
        return

    # Wait for existing request
    if args.request_id and not args.action_type:
        skill = HumanApprovalSkill(args.timeout_minutes, args.poll_interval)

        if args.no_wait:
            status = skill.check_status(args.request_id)
            if args.json:
                print(json.dumps(status, indent=2, default=str))
            else:
                print(f"Status: {status['status']}")
            return

        result = skill.wait_for_decision(args.request_id, verbose=not args.quiet)

        output = {
            "request_id": args.request_id,
            "result": result.value,
            "completed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if args.json:
            print(json.dumps(output, indent=2, default=str))
        else:
            print(f"\nResult: {result.value.upper()}")
        return

    # Validate action type for new request
    if not args.action_type:
        print("Error: --action-type is required for new approval requests")
        sys.exit(1)

    # Create new approval request
    skill = HumanApprovalSkill(args.timeout_minutes, args.poll_interval)

    result = skill.request_approval(
        action_type=args.action_type,
        action_data=action_data,
        priority=args.priority,
        wait=not args.no_wait,
        verbose=not args.quiet
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\n{'='*50}")
        print(f"Human Approval Result")
        print(f"{'='*50}")
        print(f"Request ID: {result['request_id']}")
        print(f"Status: {result['status'].upper()}")
        print(f"Message: {result.get('message', 'N/A')}")
        if result.get('final_path'):
            print(f"File: {result['final_path']}")
        print(f"Created: {result['created_at']}")
        print(f"Completed: {result.get('completed_at', 'N/A')}")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
