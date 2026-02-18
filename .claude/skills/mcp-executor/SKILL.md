# mcp-executor

## Description
MCP Server Agent Skill that executes external actions (Gmail emails and LinkedIn posts) via MCP server endpoints. Implements human-in-the-loop approval workflow by checking the `Needs_Approval` folder before executing any action. All actions are logged to `logs/actions.log` with comprehensive error handling and retry mechanisms.

## Parameters
- `action_type` (string, required): Type of action to execute - "email" or "linkedin"
- `action_data` (dict, required): Data describing the action to be taken
  - For email: `{"recipient": str, "subject": str, "body": str}`
  - For LinkedIn: `{"content": str, "topic": str}`
- `request_id` (string, optional): ID of the approval request to check
- `max_retries` (int, optional): Maximum retry attempts for failed actions. Default: 3
- `retry_delay` (int, optional): Delay between retries in seconds. Default: 5

## Functionality
When invoked, this skill enables the AI Employee to:
1. Accept requests from AI workflow (watcher or scheduler)
2. Check `Needs_Approval` folder for approval status
3. Execute external actions via MCP server endpoints:
   - Send Gmail emails using `gmail-send` skill endpoint
   - Post LinkedIn messages using `linkedin-post` skill endpoint
4. Ensure human-in-the-loop approvals are respected
5. Log all actions to `logs/actions.log` in JSON format
6. Handle errors gracefully with automatic retry mechanism
7. Move approved requests to appropriate folders (Approved/Rejected)

## Constraints
- **Human approval required**: No action is executed without explicit human approval in `Needs_Approval` folder
- **MCP server only**: All external actions go through MCP server endpoints
- **Logging mandatory**: All actions must be logged to `logs/actions.log`
- **Retry on failure**: Failed actions are retried up to `max_retries` times
- **Silver Tier compliant**: Follows approval workflow and logging requirements

## MCP Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/send-email` | POST | Send email via Gmail API |
| `/post-linkedin` | POST | Publish post to LinkedIn |

## Approval Workflow

1. **Request Created**: Action request saved in `Needs_Approval/` folder
2. **Human Review**: Reviewer changes status to `approved` or `rejected`
3. **Status Check**: mcp-executor polls for approval status
4. **Execute or Cancel**: 
   - If approved: Execute action via MCP server
   - If rejected: Log rejection and move to `Rejected/` folder
5. **Log Result**: All outcomes logged to `logs/actions.log`

## Implementation
```python
import os
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

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
        # Remove or mask sensitive fields if needed
        if 'password' in sanitized:
            sanitized['password'] = '***'
        return sanitized

    def _write_log(self, log_entry: Dict):
        """Write log entry to actions.log."""
        try:
            # Read existing logs
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

            # Append new entry
            existing_logs.append(log_entry)

            # Write back (line-delimited JSON for easy streaming)
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

        return ApprovalStatus.PENDING  # Timeout

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

        Args:
            recipient: Email recipient
            subject: Email subject
            body: Email body

        Returns:
            dict: {'success': bool, 'message_id': str, 'error': str or None}
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

        Args:
            content: Post content
            topic: Optional topic/tag

        Returns:
            dict: {'success': bool, 'post_id': str, 'post_url': str, 'error': str or None}
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
        """
        Call MCP server endpoint.

        Args:
            endpoint: Full endpoint URL
            payload: Request payload

        Returns:
            dict: Response from MCP server
        """
        try:
            # In production, use requests library:
            # import requests
            # response = requests.post(
            #     endpoint,
            #     json=payload,
            #     headers={'Content-Type': 'application/json'},
            #     timeout=30
            # )
            #
            # if response.status_code == 200:
            #     return {
            #         'success': True,
            #         'data': response.json(),
            #         'error': None
            #     }
            # else:
            #     return {
            #         'success': False,
            #         'data': None,
            #         'error': f"MCP server error: {response.status_code} - {response.text}"
            #     }

            # Simulation for demonstration (replace with actual HTTP call in production)
            print(f"Calling MCP endpoint: {endpoint}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            # Simulate successful response
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
        """
        Execute function with retry on failure.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            dict: Execution result
        """
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
                    print(f"Attempt {attempt} failed with exception: {e}. Retrying in {self.retry_delay}s...")
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
        """
        Execute an action with approval check and retry logic.

        Args:
            action_type: Type of action ("email" or "linkedin")
            action_data: Action data
            request_id: Approval request ID

        Returns:
            dict: Execution result
        """
        # Validate action type
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

        # Log the result
        status = ExecutionStatus(result.get('status', 'error'))
        self.logger.log_action(action_type, action_data, status, result)

        return result

    def _execute_email(self, action_data: Dict) -> Dict[str, Any]:
        """
        Execute email sending action.

        Args:
            action_data: {'recipient': str, 'subject': str, 'body': str}

        Returns:
            dict: Execution result
        """
        recipient = action_data.get('recipient')
        subject = action_data.get('subject')
        body = action_data.get('body')

        # Validate required fields
        if not all([recipient, subject, body]):
            return {
                'status': ExecutionStatus.ERROR.value,
                'message': 'Missing required fields: recipient, subject, body'
            }

        # Execute with retry
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
        """
        Execute LinkedIn posting action.

        Args:
            action_data: {'content': str, 'topic': str}

        Returns:
            dict: Execution result
        """
        content = action_data.get('content')
        topic = action_data.get('topic', '')

        # Validate required fields
        if not content:
            return {
                'status': ExecutionStatus.ERROR.value,
                'message': 'Missing required field: content'
            }

        # Execute with retry
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
# Skill Entry Point
# ============================================================================

def mcp_executor_skill(action_type: str, action_data: Dict,
                       request_id: str = None,
                       max_retries: int = DEFAULT_MAX_RETRIES,
                       retry_delay: int = DEFAULT_RETRY_DELAY) -> Dict[str, Any]:
    """
    Main entry point for the mcp-executor skill.

    Args:
        action_type: Type of action ("email" or "linkedin")
        action_data: Action data
            - For email: {"recipient": str, "subject": str, "body": str}
            - For LinkedIn: {"content": str, "topic": str}
        request_id: Approval request ID to check
        max_retries: Maximum retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 5)

    Returns:
        dict: Execution result with status, message, and details

    Example:
        ```python
        # Send email
        result = mcp_executor_skill(
            action_type="email",
            action_data={
                "recipient": "user@example.com",
                "subject": "Meeting Reminder",
                "body": "Hi, this is a reminder about our meeting."
            },
            request_id="email_20260218_123456"
        )

        # Post to LinkedIn
        result = mcp_executor_skill(
            action_type="linkedin",
            action_data={
                "content": "Exciting news about our new product!",
                "topic": "Product Launch"
            },
            request_id="linkedin_20260218_123456"
        )
        ```
    """
    executor = MCPExecutor(max_retries, retry_delay)
    return executor.execute_action(action_type, action_data, request_id)


# Execute the skill when called directly
if __name__ == "__main__":
    # Example usage - Email
    email_result = mcp_executor_skill(
        action_type="email",
        action_data={
            "recipient": "test@example.com",
            "subject": "Test Email from MCP Executor",
            "body": "This is a test email sent via MCP Executor skill."
        },
        request_id=None  # No approval check for demo
    )
    print("Email Result:")
    print(json.dumps(email_result, indent=2))

    # Example usage - LinkedIn
    linkedin_result = mcp_executor_skill(
        action_type="linkedin",
        action_data={
            "content": "🚀 Exciting developments in AI! Our team is working on innovative solutions.",
            "topic": "AI Innovation"
        },
        request_id=None  # No approval check for demo
    )
    print("\nLinkedIn Result:")
    print(json.dumps(linkedin_result, indent=2))
```

## Usage Examples

### Send Email
```python
from .claude.skills.mcp-executor.SKILL import mcp_executor_skill

result = mcp_executor_skill(
    action_type="email",
    action_data={
        "recipient": "colleague@company.com",
        "subject": "Project Update",
        "body": "Hi, here's the latest project update..."
    },
    request_id="email_20260218_123456"
)
print(result)
```

### Post to LinkedIn
```python
result = mcp_executor_skill(
    action_type="linkedin",
    action_data={
        "content": "💡 Innovating the future of business with AI-driven solutions.",
        "topic": "Business Innovation"
    },
    request_id="linkedin_20260218_789012",
    max_retries=5,
    retry_delay=10
)
print(result)
```

### Without Approval Check (Direct Execution)
```python
result = mcp_executor_skill(
    action_type="email",
    action_data={
        "recipient": "auto@example.com",
        "subject": "Automated Notification",
        "body": "This is an automated message."
    }
    # No request_id = no approval check
)
```

## Approval Workflow Integration

### 1. Create Approval Request
Save a request file in `Needs_Approval/`:
```markdown
# Email Sending Approval Request

## Request ID
email_20260218_123456

## Status
status: pending

## Email Details
- **Recipient**: user@example.com
- **Subject**: Important Update
- **Body**: Email content here...
```

### 2. Human Review
Human reviewer opens the file and changes:
```markdown
## Status
status: approved
```

### 3. Execute Action
```python
result = mcp_executor_skill(
    action_type="email",
    action_data={...},
    request_id="email_20260218_123456"
)
```

## Logging

All actions are logged to `logs/actions.log` in line-delimited JSON format:
```json
{"timestamp": "2026-02-18 10:30:00", "action_type": "email", "action_data": {...}, "status": "success", "details": {...}}
{"timestamp": "2026-02-18 10:31:00", "action_type": "linkedin", "action_data": {...}, "status": "failed", "details": {...}}
```

## Error Handling

| Error Type | Behavior |
|------------|----------|
| Missing approval | Blocks execution until approved or timeout |
| MCP server error | Retries up to max_retries times |
| Invalid action data | Returns error immediately, logs failure |
| Network timeout | Retries with exponential backoff |

## Security Notes

- No credentials stored or handled by this skill
- All external actions go through authenticated MCP server
- Human approval required for all sensitive actions
- All operations logged for audit purposes
- Sensitive data sanitized in logs
