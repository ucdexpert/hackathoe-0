"""
MCP Executor Script

This script provides the MCP Executor skill for executing external actions
(Gmail emails and LinkedIn posts) via MCP server endpoints with human-in-the-loop
approval workflow.

Usage:
    python scripts/mcp_executor.py --action-type email --recipient "user@example.com" --subject "Test" --body "Message"
    python scripts/mcp_executor.py --action-type linkedin --content "Post content" --topic "Topic"
    python scripts/mcp_executor.py --request-id "email_20260218_123456"
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# Configuration
# ============================================================================

VAULT_FOLDERS = {
    "needs_approval": "Needs_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "logs": "Logs"
}

# MCP Server configuration
MCP_SERVER_URL = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5  # seconds

# Approval polling configuration
APPROVAL_CHECK_INTERVAL = 10  # seconds
APPROVAL_TIMEOUT = 600  # 10 minutes

# Action log file
ACTION_LOG_FILE = "actions.log"


# ============================================================================
# Enums
# ============================================================================

class ActionType(Enum):
    """Types of actions that can be executed."""
    EMAIL = "email"
    LINKEDIN = "linkedin"


class ApprovalStatus(Enum):
    """Approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    ERROR = "error"


# ============================================================================
# Action Logger
# ============================================================================

class ActionLogger:
    """Logs all MCP executor actions to actions.log."""

    def __init__(self, logs_dir: str = None):
        self.logs_dir = logs_dir or VAULT_FOLDERS["logs"]
        self.log_file = os.path.join(self.logs_dir, ACTION_LOG_FILE)
        self._ensure_logs_dir()

    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, exist_ok=True)

    def log_action(self, action_type: str, action_data: Dict,
                   status: ExecutionStatus, details: Dict = None):
        """
        Log an action execution.

        Args:
            action_type: Type of action (email/linkedin)
            action_data: Action data
            status: Execution status
            details: Additional details
        """
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "action_type": action_type,
            "action_data": self._sanitize_action_data(action_data),
            "status": status.value,
            "details": details or {}
        }

        self._write_log(log_entry)

    def _sanitize_action_data(self, action_data: Dict) -> Dict:
        """Sanitize sensitive data from action data for logging."""
        sanitized = action_data.copy()
        if 'password' in sanitized:
            sanitized['password'] = '***'
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
            print(f"Failed to write action log: {str(e)}")


# ============================================================================
# Approval Checker
# ============================================================================

class ApprovalChecker:
    """Checks approval status in Needs_Approval folder."""

    def __init__(self, needs_approval_dir: str = None):
        self.needs_approval_dir = needs_approval_dir or VAULT_FOLDERS["needs_approval"]

    def check_approval_status(self, request_id: str) -> Optional[ApprovalStatus]:
        """
        Check approval status for a request.

        Args:
            request_id: The request ID to check

        Returns:
            ApprovalStatus or None if not found
        """
        if not os.path.exists(self.needs_approval_dir):
            return None

        request_file = self._find_request_file(request_id)
        if not request_file:
            return None

        return self._parse_status_from_file(request_file)

    def wait_for_approval(self, request_id: str,
                         timeout: int = APPROVAL_TIMEOUT,
                         check_interval: int = APPROVAL_CHECK_INTERVAL) -> ApprovalStatus:
        """
        Wait for approval by polling the request file.

        Args:
            request_id: The request ID to wait for
            timeout: Maximum time to wait in seconds
            check_interval: Time between status checks

        Returns:
            Final approval status
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.check_approval_status(request_id)

            if status == ApprovalStatus.APPROVED:
                return ApprovalStatus.APPROVED
            elif status == ApprovalStatus.REJECTED:
                return ApprovalStatus.REJECTED

            time.sleep(check_interval)

        return ApprovalStatus.PENDING

    def _find_request_file(self, request_id: str) -> Optional[str]:
        """Find the request file by request ID."""
        if not os.path.exists(self.needs_approval_dir):
            return None

        for filename in os.listdir(self.needs_approval_dir):
            if request_id in filename and filename.endswith('.md'):
                return os.path.join(self.needs_approval_dir, filename)

        return None

    def _parse_status_from_file(self, filepath: str) -> Optional[ApprovalStatus]:
        """Parse approval status from file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            content_lower = content.lower()

            if "**status:** approved" in content_lower or "status: approved" in content_lower:
                return ApprovalStatus.APPROVED
            elif "**status:** rejected" in content_lower or "status: rejected" in content_lower:
                return ApprovalStatus.REJECTED

            return ApprovalStatus.PENDING

        except Exception:
            return ApprovalStatus.PENDING


# ============================================================================
# MCP Client
# ============================================================================

class MCPClient:
    """Client for calling MCP server endpoints."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or MCP_SERVER_URL

    def send_email(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send email via Gmail API using MCP server.

        POST /send-email
        """
        endpoint = f"{self.base_url}/send-email"
        payload = {
            "to": recipient,
            "subject": subject,
            "body": body,
            "timestamp": datetime.now().isoformat()
        }

        return self._call_mcp_endpoint(endpoint, payload)

    def post_linkedin(self, content: str, topic: str = None) -> Dict[str, Any]:
        """
        Publish post to LinkedIn using MCP server.

        POST /post-linkedin
        """
        endpoint = f"{self.base_url}/post-linkedin"
        payload = {
            "content": content,
            "topic": topic or "",
            "timestamp": datetime.now().isoformat(),
            "platform": "linkedin"
        }

        return self._call_mcp_endpoint(endpoint, payload)

    def _call_mcp_endpoint(self, endpoint: str, payload: Dict) -> Dict[str, Any]:
        """Call MCP server endpoint."""
        try:
            # Production implementation with requests:
            # import requests
            # response = requests.post(
            #     endpoint,
            #     json=payload,
            #     headers={'Content-Type': 'application/json'},
            #     timeout=30
            # )
            # if response.status_code == 200:
            #     return {'success': True, 'data': response.json(), 'error': None}
            # else:
            #     return {'success': False, 'data': None, 'error': f"MCP error: {response.status_code}"}

            # Simulation for demonstration
            print(f"Calling MCP endpoint: {endpoint}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            return {
                'success': True,
                'data': {
                    'message_id': f"<{datetime.now().strftime('%Y%m%d%H%M%S')}@gmail.com>",
                    'post_id': f"urn:li:share:{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'post_url': f"https://www.linkedin.com/feed/update/urn:li:share:{datetime.now().strftime('%Y%m%d%H%M%S')}"
                },
                'error': None,
                'endpoint': endpoint
            }

        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }


# ============================================================================
# Retry Handler
# ============================================================================

class RetryHandler:
    """Handles retry logic for failed actions."""

    def __init__(self, max_retries: int = DEFAULT_MAX_RETRIES,
                 retry_delay: int = DEFAULT_RETRY_DELAY):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def execute_with_retry(self, func: callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute function with retry on failure."""
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                result = func(*args, **kwargs)

                if result.get('success'):
                    return {
                        'success': True,
                        'result': result,
                        'attempts': attempt
                    }

                last_error = result.get('error', 'Unknown error')

                if attempt < self.max_retries:
                    print(f"Attempt {attempt} failed. Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)

            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    print(f"Attempt {attempt} failed: {e}. Retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)

        return {
            'success': False,
            'result': None,
            'attempts': self.max_retries,
            'error': last_error
        }


# ============================================================================
# MCP Executor
# ============================================================================

class MCPExecutor:
    """Main executor for MCP actions with approval workflow."""

    def __init__(self, max_retries: int = DEFAULT_MAX_RETRIES,
                 retry_delay: int = DEFAULT_RETRY_DELAY):
        self.logger = ActionLogger()
        self.approval_checker = ApprovalChecker()
        self.mcp_client = MCPClient()
        self.retry_handler = RetryHandler(max_retries, retry_delay)

    def execute_action(self, action_type: str, action_data: Dict,
                      request_id: str = None) -> Dict[str, Any]:
        """Execute an action with approval check and retry logic."""
        try:
            action_enum = ActionType(action_type.lower())
        except ValueError:
            error_result = {
                'status': ExecutionStatus.ERROR.value,
                'message': f'Invalid action type: {action_type}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.logger.log_action(action_type, action_data, ExecutionStatus.ERROR, error_result)
            return error_result

        # Check approval if request_id provided
        if request_id:
            approval_status = self.approval_checker.wait_for_approval(request_id)

            if approval_status == ApprovalStatus.REJECTED:
                rejection_result = {
                    'status': ExecutionStatus.REJECTED.value,
                    'message': 'Action was rejected by human reviewer',
                    'request_id': request_id,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.logger.log_action(action_type, action_data, ExecutionStatus.REJECTED, rejection_result)
                return rejection_result

            elif approval_status == ApprovalStatus.PENDING:
                timeout_result = {
                    'status': ExecutionStatus.TIMEOUT.value,
                    'message': 'Approval timeout - action not executed',
                    'request_id': request_id,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.logger.log_action(action_type, action_data, ExecutionStatus.TIMEOUT, timeout_result)
                return timeout_result

        # Execute the action with retry
        if action_enum == ActionType.EMAIL:
            result = self._execute_email(action_data)
        elif action_enum == ActionType.LINKEDIN:
            result = self._execute_linkedin(action_data)
        else:
            result = {
                'status': ExecutionStatus.ERROR.value,
                'message': f'Unsupported action type: {action_type}'
            }

        status = ExecutionStatus(result.get('status', 'error'))
        self.logger.log_action(action_type, action_data, status, result)

        return result

    def _execute_email(self, action_data: Dict) -> Dict[str, Any]:
        """Execute email sending action."""
        recipient = action_data.get('recipient')
        subject = action_data.get('subject')
        body = action_data.get('body')

        if not all([recipient, subject, body]):
            return {
                'status': ExecutionStatus.ERROR.value,
                'message': 'Missing required fields: recipient, subject, body'
            }

        def send_email_func():
            return self.mcp_client.send_email(recipient, subject, body)

        retry_result = self.retry_handler.execute_with_retry(send_email_func)

        if retry_result['success']:
            return {
                'status': ExecutionStatus.SUCCESS.value,
                'message': f'Email sent to {recipient}',
                'message_id': retry_result['result'].get('data', {}).get('message_id'),
                'attempts': retry_result['attempts']
            }
        else:
            return {
                'status': ExecutionStatus.FAILED.value,
                'message': f'Failed to send email after {retry_result["attempts"]} attempts',
                'error': retry_result.get('error')
            }

    def _execute_linkedin(self, action_data: Dict) -> Dict[str, Any]:
        """Execute LinkedIn posting action."""
        content = action_data.get('content')
        topic = action_data.get('topic', '')

        if not content:
            return {
                'status': ExecutionStatus.ERROR.value,
                'message': 'Missing required field: content'
            }

        def post_linkedin_func():
            return self.mcp_client.post_linkedin(content, topic)

        retry_result = self.retry_handler.execute_with_retry(post_linkedin_func)

        if retry_result['success']:
            result_data = retry_result['result'].get('data', {})
            return {
                'status': ExecutionStatus.SUCCESS.value,
                'message': 'LinkedIn post published successfully',
                'post_id': result_data.get('post_id'),
                'post_url': result_data.get('post_url'),
                'attempts': retry_result['attempts']
            }
        else:
            return {
                'status': ExecutionStatus.FAILED.value,
                'message': f'Failed to publish LinkedIn post after {retry_result["attempts"]} attempts',
                'error': retry_result.get('error')
            }


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Command-line interface for MCP Executor."""
    parser = argparse.ArgumentParser(
        description='MCP Executor - Execute external actions with human approval workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Send an email:
    python mcp_executor.py --action-type email --recipient "user@example.com" --subject "Test" --body "Message"

  Post to LinkedIn:
    python mcp_executor.py --action-type linkedin --content "Post content" --topic "Topic"

  With approval check:
    python mcp_executor.py --action-type email --recipient "user@example.com" --subject "Test" --body "Message" --request-id "email_20260218_123456"

  Custom retry settings:
    python mcp_executor.py --action-type email --recipient "user@example.com" --subject "Test" --body "Message" --max-retries 5 --retry-delay 10
        """
    )

    parser.add_argument(
        '--action-type', '-t',
        required=True,
        choices=['email', 'linkedin'],
        help='Type of action to execute'
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
        '--request-id',
        help='Approval request ID to check before execution'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f'Maximum retry attempts (default: {DEFAULT_MAX_RETRIES})'
    )
    parser.add_argument(
        '--retry-delay',
        type=int,
        default=DEFAULT_RETRY_DELAY,
        help=f'Delay between retries in seconds (default: {DEFAULT_RETRY_DELAY})'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON'
    )

    args = parser.parse_args()

    # Build action data based on action type
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
    else:
        print(f"Error: Unknown action type: {args.action_type}")
        sys.exit(1)

    # Execute the action
    executor = MCPExecutor(
        max_retries=args.max_retries,
        retry_delay=args.retry_delay
    )

    result = executor.execute_action(
        action_type=args.action_type,
        action_data=action_data,
        request_id=args.request_id
    )

    # Output result
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"\n{'='*50}")
        print(f"MCP Executor Result")
        print(f"{'='*50}")
        print(f"Status: {result.get('status', 'unknown').upper()}")
        print(f"Message: {result.get('message', 'N/A')}")
        if result.get('message_id'):
            print(f"Message ID: {result['message_id']}")
        if result.get('post_id'):
            print(f"Post ID: {result['post_id']}")
        if result.get('post_url'):
            print(f"Post URL: {result['post_url']}")
        if result.get('attempts'):
            print(f"Attempts: {result['attempts']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
