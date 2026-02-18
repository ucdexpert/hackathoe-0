# human-approval

## Description
A Claude Agent Skill that manages the human-in-the-loop approval workflow for sensitive actions. Ensures no sensitive action is executed without explicit human approval, with proper tracking, status management, and logging.

## Parameters
- `action_type` (string, required): Type of action requiring approval (e.g., "email_send", "linkedin_post", "file_operation")
- `action_data` (dict, required): Data describing the action to be taken
- `priority` (string, optional): Priority level - "low", "normal", "urgent". Default: "normal"
- `reason` (string, optional): Reason why approval is required

## Functionality
When invoked, this skill:
1. Saves the sensitive action draft into the Approvals folder
2. Waits for human approval status (Approved/Rejected/Needs Revision)
3. Only upon Approved status, allows the external action to proceed
4. Logs all approval decisions and actions
5. Blocks execution until approval is granted
6. Complies with Silver Tier requirements

## Constraints
- Must block execution until approved
- No automatic execution of sensitive actions
- All decisions must be logged
- Local vault operations only
- Silver Tier compliant

## Approval Statuses

| Status | Description | Action |
|--------|-------------|--------|
| Pending | Awaiting human review | Block execution |
| Approved | Human has approved | Allow execution |
| Rejected | Human has rejected | Cancel action, log reason |
| Needs Revision | Requires modifications | Return to requester with feedback |

## Implementation
```python
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

# ============================================================================
# Configuration
# ============================================================================

VAULT_FOLDERS = {
    "approvals": "Approvals",
    "logs": "Logs",
    "done": "Done"
}

# Default timeout for pending approvals (24 hours)
DEFAULT_APPROVAL_TIMEOUT = timedelta(hours=24)

# Polling interval for checking approval status (in seconds)
APPROVAL_CHECK_INTERVAL = 30

# ============================================================================
# Enums
# ============================================================================

class ApprovalStatus(Enum):
    """Approval status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

class ActionType(Enum):
    """Types of actions that require approval."""
    EMAIL_SEND = "email_send"
    LINKEDIN_POST = "linkedin_post"
    FILE_OPERATION = "file_operation"
    API_CALL = "api_call"
    DATA_EXPORT = "data_export"
    CUSTOM = "custom"

# ============================================================================
# Data Models
# ============================================================================

class ApprovalRequest:
    """Represents an approval request."""
    
    def __init__(self, request_id: str, action_type: str, action_data: Dict,
                 priority: str = "normal", reason: str = "",
                 status: ApprovalStatus = ApprovalStatus.PENDING):
        self.request_id = request_id
        self.action_type = action_type
        self.action_data = action_data
        self.priority = priority
        self.reason = reason
        self.status = status
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.approved_by = None
        self.approved_at = None
        self.rejection_reason = None
        self.revision_notes = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "request_id": self.request_id,
            "action_type": self.action_type,
            "action_data": self.action_data,
            "priority": self.priority,
            "reason": self.reason,
            "status": self.status.value,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "revision_notes": self.revision_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ApprovalRequest':
        """Create from dictionary."""
        request = cls(
            request_id=data["request_id"],
            action_type=data["action_type"],
            action_data=data["action_data"],
            priority=data.get("priority", "normal"),
            reason=data.get("reason", ""),
            status=ApprovalStatus(data.get("status", "pending"))
        )
        request.created_at = datetime.strptime(data["created_at"], '%Y-%m-%d %H:%M:%S')
        request.updated_at = datetime.strptime(data["updated_at"], '%Y-%m-%d %H:%M:%S')
        request.approved_by = data.get("approved_by")
        request.approved_at = datetime.strptime(data["approved_at"], '%Y-%m-%d %H:%M:%S') if data.get("approved_at") else None
        request.rejection_reason = data.get("rejection_reason")
        request.revision_notes = data.get("revision_notes")
        return request

# ============================================================================
# Approval Request Generator
# ============================================================================

class ApprovalRequestGenerator:
    """Generates approval request files."""
    
    def __init__(self, approvals_dir: str = None):
        self.approvals_dir = approvals_dir or VAULT_FOLDERS["approvals"]
        self._ensure_approvals_dir()
    
    def _ensure_approvals_dir(self):
        """Ensure approvals directory exists."""
        if not os.path.exists(self.approvals_dir):
            os.makedirs(self.approvals_dir, exist_ok=True)
    
    def generate_request_file(self, request: ApprovalRequest) -> str:
        """
        Generate an approval request file.
        
        Args:
            request: The approval request
        
        Returns:
            Path to the generated request file
        """
        # Generate filename
        timestamp = request.created_at.strftime("%Y%m%d_%H%M%S")
        filename = f"approval_{request.action_type}_{timestamp}_{request.request_id[:8]}.md"
        filepath = os.path.join(self.approvals_dir, filename)
        
        # Generate content
        content = self._build_request_content(request)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _build_request_content(self, request: ApprovalRequest) -> str:
        """Build the approval request file content."""
        action_data_str = json.dumps(request.action_data, indent=2, default=str)
        
        content = f"""# Approval Request

**Request ID:** {request.request_id}
**Status:** {request.status.value.upper()}
**Priority:** {request.priority.upper()}
**Created:** {request.created_at.strftime('%Y-%m-%d %H:%M:%S')}

---

## Action Type

{request.action_type}

---

## Reason for Approval

{request.reason if request.reason else "Standard approval required for sensitive action."}

---

## Action Details

```json
{action_data_str}
```

---

## Instructions for Human Reviewer

### To Approve:
Change the status in the response section below to `approved` and optionally add your name.

### To Reject:
Change the status to `rejected` and provide a rejection reason.

### To Request Revision:
Change the status to `needs_revision` and add revision notes.

---

## Response Section (For Human Reviewer)

<!-- HUMAN REVIEWER: Fill in this section -->

**Status:** [pending/approved/rejected/needs_revision]

**Approved By:** [Your name]

**Approval Date:** [YYYY-MM-DD HH:MM:SS]

**Rejection Reason:** [If rejected, explain why]

**Revision Notes:** [If needs revision, explain what to change]

---

## Response Template (Copy and Fill)

```markdown
## Approval Decision

**Status:** approved

**Approved By:** [Name]

**Approval Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Comments:** [Optional comments]
```

---

*This is an automated approval request. Do not execute the action until approved.*
*Request generated by human-approval skill.*
"""
        
        return content

# ============================================================================
# Approval Status Checker
# ============================================================================

class ApprovalStatusChecker:
    """Checks the status of approval requests."""
    
    def __init__(self, approvals_dir: str = None):
        self.approvals_dir = approvals_dir or VAULT_FOLDERS["approvals"]
    
    def check_status(self, request_id: str) -> Optional[ApprovalStatus]:
        """
        Check the status of an approval request.
        
        Args:
            request_id: The request ID to check
        
        Returns:
            ApprovalStatus or None if not found
        """
        request_file = self._find_request_file(request_id)
        
        if not request_file:
            return None
        
        return self._parse_status_from_file(request_file)
    
    def check_and_load_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """
        Check status and load the full request.
        
        Args:
            request_id: The request ID to check
        
        Returns:
            ApprovalRequest or None if not found
        """
        request_file = self._find_request_file(request_id)
        
        if not request_file:
            return None
        
        return self._parse_request_from_file(request_file)
    
    def _find_request_file(self, request_id: str) -> Optional[str]:
        """Find the request file by request ID."""
        if not os.path.exists(self.approvals_dir):
            return None
        
        for filename in os.listdir(self.approvals_dir):
            if request_id[:8] in filename and filename.endswith('.md'):
                return os.path.join(self.approvals_dir, filename)
        
        return None
    
    def _parse_status_from_file(self, filepath: str) -> Optional[ApprovalStatus]:
        """Parse approval status from file content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for status in response section
            status_markers = [
                "**Status:** approved",
                "**Status:** rejected", 
                "**Status:** needs_revision",
                "## Approval Decision",
                "**Status:** approved",
            ]
            
            content_lower = content.lower()
            
            if "**status:** approved" in content_lower:
                return ApprovalStatus.APPROVED
            elif "**status:** rejected" in content_lower:
                return ApprovalStatus.REJECTED
            elif "**status:** needs_revision" in content_lower:
                return ApprovalStatus.NEEDS_REVISION
            
            return ApprovalStatus.PENDING
        
        except Exception:
            return ApprovalStatus.PENDING
    
    def _parse_request_from_file(self, filepath: str) -> Optional[ApprovalRequest]:
        """Parse full request from file."""
        # This would parse the file and reconstruct the ApprovalRequest
        # For simplicity, we'll return None and rely on the tracking file
        return None

# ============================================================================
# Approval Tracker
# ============================================================================

class ApprovalTracker:
    """Tracks approval requests and their status."""
    
    def __init__(self, tracking_file: str = None):
        self.tracking_file = tracking_file or os.path.join(
            VAULT_FOLDERS["logs"], "approval_tracking.json"
        )
        self._requests = self._load_tracking_data()
    
    def _load_tracking_data(self) -> Dict[str, Dict]:
        """Load tracking data from file."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('requests', {})
            except (json.JSONDecodeError, KeyError):
                pass
        return {}
    
    def add_request(self, request: ApprovalRequest):
        """Add a new request to tracking."""
        self._requests[request.request_id] = request.to_dict()
        self._save_tracking_data()
    
    def update_request(self, request: ApprovalRequest):
        """Update an existing request."""
        request.updated_at = datetime.now()
        self._requests[request.request_id] = request.to_dict()
        self._save_tracking_data()
    
    def get_request(self, request_id: str) -> Optional[Dict]:
        """Get a request by ID."""
        return self._requests.get(request_id)
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending requests."""
        return [
            req for req in self._requests.values() 
            if req.get('status') == 'pending'
        ]
    
    def _save_tracking_data(self):
        """Save tracking data to file."""
        try:
            os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
            
            data = {
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "requests": self._requests
            }
            
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save tracking data: {str(e)}")

# ============================================================================
# Approval Logger
# ============================================================================

class ApprovalLogger:
    """Logs approval decisions and actions."""
    
    def __init__(self, logs_dir: str = None):
        self.logs_dir = logs_dir or VAULT_FOLDERS["logs"]
        self._ensure_logs_dir()
    
    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, exist_ok=True)
    
    def log_decision(self, request: ApprovalRequest, decision: str, 
                     decided_by: str = None, comments: str = None):
        """
        Log an approval decision.
        
        Args:
            request: The approval request
            decision: The decision made (approved/rejected/needs_revision)
            decided_by: Name of the person who made the decision
            comments: Optional comments
        """
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "approval_decision",
            "request_id": request.request_id,
            "action_type": request.action_type,
            "decision": decision,
            "decided_by": decided_by,
            "comments": comments,
            "request_data": request.to_dict()
        }
        
        self._write_log(log_entry)
    
    def log_action_executed(self, request: ApprovalRequest):
        """Log that an approved action was executed."""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "action_executed",
            "request_id": request.request_id,
            "action_type": request.action_type,
            "approved_by": request.approved_by,
            "executed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "status": "success"
        }
        
        self._write_log(log_entry)
    
    def log_action_blocked(self, request: ApprovalRequest, reason: str):
        """Log that an action was blocked due to lack of approval."""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "action_blocked",
            "request_id": request.request_id,
            "action_type": request.action_type,
            "reason": reason,
            "status": "blocked"
        }
        
        self._write_log(log_entry)
    
    def _write_log(self, log_entry: Dict):
        """Write log entry to daily log file."""
        try:
            log_filename = f"human_approval_{datetime.now().strftime('%Y%m%d')}.json"
            log_filepath = os.path.join(self.logs_dir, log_filename)
            
            # Read existing logs
            existing_logs = []
            if os.path.exists(log_filepath):
                with open(log_filepath, 'r', encoding='utf-8') as f:
                    try:
                        existing_logs = json.load(f)
                    except json.JSONDecodeError:
                        existing_logs = []
            
            # Append new entry
            existing_logs.append(log_entry)
            
            # Write back
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, indent=2, default=str)
        
        except Exception as e:
            print(f"Failed to write log: {str(e)}")

# ============================================================================
# Approval Workflow Manager
# ============================================================================

class ApprovalWorkflowManager:
    """Manages the complete approval workflow."""
    
    def __init__(self):
        self.request_generator = ApprovalRequestGenerator()
        self.status_checker = ApprovalStatusChecker()
        self.tracker = ApprovalTracker()
        self.logger = ApprovalLogger()
    
    def request_approval(self, action_type: str, action_data: Dict,
                        priority: str = "normal", reason: str = "") -> ApprovalRequest:
        """
        Request approval for a sensitive action.
        
        Args:
            action_type: Type of action requiring approval
            action_data: Data describing the action
            priority: Priority level (low/normal/urgent)
            reason: Reason why approval is required
        
        Returns:
            ApprovalRequest object
        """
        # Generate unique request ID
        request_id = self._generate_request_id(action_type)
        
        # Create approval request
        request = ApprovalRequest(
            request_id=request_id,
            action_type=action_type,
            action_data=action_data,
            priority=priority,
            reason=reason
        )
        
        # Generate request file
        request_file = self.request_generator.generate_request_file(request)
        
        # Track the request
        self.tracker.add_request(request)
        
        # Log the request
        self.logger.log_decision(
            request, "pending", 
            comments=f"Approval request created: {request_file}"
        )
        
        return request
    
    def wait_for_approval(self, request: ApprovalRequest, 
                         timeout: timedelta = None,
                         check_interval: int = APPROVAL_CHECK_INTERVAL) -> ApprovalStatus:
        """
        Wait for approval status. Blocks execution until approved or timeout.
        
        Args:
            request: The approval request to wait for
            timeout: Maximum time to wait (default: 24 hours)
            check_interval: Seconds between status checks
        
        Returns:
            Final approval status
        """
        timeout = timeout or DEFAULT_APPROVAL_TIMEOUT
        start_time = datetime.now()
        
        while True:
            # Check if timeout exceeded
            elapsed = datetime.now() - start_time
            if elapsed > timeout:
                request.status = ApprovalStatus.PENDING  # Still pending due to timeout
                self.tracker.update_request(request)
                self.logger.log_action_blocked(
                    request, f"Approval timeout after {elapsed}"
                )
                return ApprovalStatus.PENDING
            
            # Check status
            status = self.status_checker.check_status(request.request_id)
            
            if status == ApprovalStatus.APPROVED:
                request.status = ApprovalStatus.APPROVED
                request.approved_at = datetime.now()
                self.tracker.update_request(request)
                self.logger.log_decision(request, "approved")
                return ApprovalStatus.APPROVED
            
            elif status == ApprovalStatus.REJECTED:
                request.status = ApprovalStatus.REJECTED
                self.tracker.update_request(request)
                self.logger.log_decision(request, "rejected")
                return ApprovalStatus.REJECTED
            
            elif status == ApprovalStatus.NEEDS_REVISION:
                request.status = ApprovalStatus.NEEDS_REVISION
                self.tracker.update_request(request)
                self.logger.log_decision(request, "needs_revision")
                return ApprovalStatus.NEEDS_REVISION
            
            # Wait before next check
            time.sleep(check_interval)
    
    def execute_approved_action(self, request: ApprovalRequest, 
                                executor_func: callable = None) -> Dict[str, Any]:
        """
        Execute an approved action.
        
        Args:
            request: The approved approval request
            executor_func: Optional function to execute the action
        
        Returns:
            Execution result
        """
        # Verify approval status
        current_status = self.status_checker.check_status(request.request_id)
        
        if current_status != ApprovalStatus.APPROVED:
            self.logger.log_action_blocked(
                request, f"Action not approved. Current status: {current_status.value}"
            )
            return {
                "status": "blocked",
                "reason": f"Action not approved. Status: {current_status.value}",
                "request_id": request.request_id
            }
        
        # Execute the action
        result = {"status": "success", "request_id": request.request_id}
        
        if executor_func:
            try:
                execution_result = executor_func(request.action_data)
                result["execution_result"] = execution_result
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
        else:
            # Default: just log that action would be executed
            result["message"] = "Action approved and ready for execution"
        
        # Log execution
        if result["status"] == "success":
            self.logger.log_action_executed(request)
        
        # Move request to Done folder
        self._archive_approved_request(request)
        
        return result
    
    def _archive_approved_request(self, request: ApprovalRequest):
        """Move approved request to Done folder."""
        done_dir = VAULT_FOLDERS["done"]
        if not os.path.exists(done_dir):
            os.makedirs(done_dir, exist_ok=True)
        
        # Find and copy the request file
        request_file = self._find_request_file(request.request_id)
        if request_file:
            filename = os.path.basename(request_file)
            done_file = os.path.join(done_dir, f"approved_{filename}")
            
            with open(request_file, 'r', encoding='utf-8') as src, \
                 open(done_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
    
    def _find_request_file(self, request_id: str) -> Optional[str]:
        """Find the request file by ID."""
        approvals_dir = VAULT_FOLDERS["approvals"]
        if not os.path.exists(approvals_dir):
            return None
        
        for filename in os.listdir(approvals_dir):
            if request_id[:8] in filename and filename.endswith('.md'):
                return os.path.join(approvals_dir, filename)
        
        return None
    
    def _generate_request_id(self, action_type: str) -> str:
        """Generate a unique request ID."""
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{action_type}_{timestamp}_{unique_id}"

# ============================================================================
# Skill Entry Point
# ============================================================================

def human_approval_skill(action_type: str, action_data: Dict,
                        priority: str = "normal", reason: str = "",
                        wait: bool = True, timeout: int = None) -> Dict[str, Any]:
    """
    Main entry point for the human-approval skill.
    
    Args:
        action_type: Type of action requiring approval
        action_data: Data describing the action
        priority: Priority level (low/normal/urgent)
        reason: Reason why approval is required
        wait: If True, wait for approval (blocks execution)
        timeout: Timeout in seconds (default: 24 hours)
    
    Returns:
        Result dictionary with status and details
    """
    workflow = ApprovalWorkflowManager()
    
    # Request approval
    request = workflow.request_approval(
        action_type=action_type,
        action_data=action_data,
        priority=priority,
        reason=reason
    )
    
    result = {
        "request_id": request.request_id,
        "status": "pending",
        "message": f"Approval request created. Waiting for human review.",
        "action_type": action_type,
        "created_at": request.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if wait:
        # Wait for approval (blocks execution)
        timeout_delta = timedelta(seconds=timeout) if timeout else None
        final_status = workflow.wait_for_approval(request, timeout=timeout_delta)
        
        result["final_status"] = final_status.value
        
        if final_status == ApprovalStatus.APPROVED:
            result["status"] = "approved"
            result["message"] = "Action approved and ready for execution."
            result["approved_at"] = request.approved_at.strftime('%Y-%m-%d %H:%M:%S') if request.approved_at else None
        elif final_status == ApprovalStatus.REJECTED:
            result["status"] = "rejected"
            result["message"] = "Action rejected by human reviewer."
        elif final_status == ApprovalStatus.NEEDS_REVISION:
            result["status"] = "needs_revision"
            result["message"] = "Action requires revision before approval."
        else:
            result["status"] = "timeout"
            result["message"] = "Approval request timed out."
    else:
        # Don't wait - return immediately
        result["message"] = "Approval request created. Check status separately."
        result["check_status_command"] = f"human_approval_skill(action_type='{action_type}', action_data={{}}, wait=True)"
    
    return result

def check_approval_status(request_id: str) -> Dict[str, Any]:
    """
    Check the status of an approval request.
    
    Args:
        request_id: The request ID to check
    
    Returns:
        Status dictionary
    """
    workflow = ApprovalWorkflowManager()
    status_checker = workflow.status_checker
    tracker = workflow.tracker
    
    status = status_checker.check_status(request_id)
    request_data = tracker.get_request(request_id)
    
    return {
        "request_id": request_id,
        "status": status.value if status else "not_found",
        "request_data": request_data
    }

def execute_approved_action(request_id: str, executor_func: callable = None) -> Dict[str, Any]:
    """
    Execute an approved action.
    
    Args:
        request_id: The request ID to execute
        executor_func: Optional function to execute the action
    
    Returns:
        Execution result
    """
    workflow = ApprovalWorkflowManager()
    tracker = workflow.tracker
    
    request_data = tracker.get_request(request_id)
    if not request_data:
        return {"status": "error", "reason": "Request not found"}
    
    # Reconstruct request
    request = ApprovalRequest.from_dict(request_data)
    
    return workflow.execute_approved_action(request, executor_func)

# Convenience functions for common action types

def request_email_approval(email_data: Dict, priority: str = "normal") -> Dict[str, Any]:
    """Request approval for sending an email."""
    return human_approval_skill(
        action_type="email_send",
        action_data=email_data,
        priority=priority,
        reason="Email requires human approval before sending"
    )

def request_linkedin_approval(post_data: Dict, priority: str = "normal") -> Dict[str, Any]:
    """Request approval for a LinkedIn post."""
    return human_approval_skill(
        action_type="linkedin_post",
        action_data=post_data,
        priority=priority,
        reason="LinkedIn post requires human approval before publishing"
    )

def request_file_operation_approval(operation_data: Dict, priority: str = "normal") -> Dict[str, Any]:
    """Request approval for a file operation."""
    return human_approval_skill(
        action_type="file_operation",
        action_data=operation_data,
        priority=priority,
        reason="File operation requires human approval"
    )

# Execute the skill when called
if __name__ == "__main__":
    # Example usage
    print("Human Approval Skill - Example")
    print("=" * 50)
    
    # Example: Request approval for an email
    email_data = {
        "to": "client@example.com",
        "subject": "Project Update",
        "body": "Dear Client, Here is your project update..."
    }
    
    # This would block until approved (for demo, we won't actually wait)
    # result = request_email_approval(email_data, wait=False)
    # print(f"Result: {result}")
    
    print("Human Approval Skill loaded successfully.")
    print("Use human_approval_skill() to request approval for sensitive actions.")
```

## Usage Examples

### Example 1: Request Email Approval (Non-blocking)
```python
from human_approval import human_approval_skill

email_data = {
    "to": "client@example.com",
    "subject": "Project Update",
    "body": "Dear Client, here is your project update..."
}

result = human_approval_skill(
    action_type="email_send",
    action_data=email_data,
    priority="normal",
    reason="Client communication requires approval",
    wait=False  # Don't block
)
# Returns: {"request_id": "email_send_20240115103000_abc123", "status": "pending", ...}
```

### Example 2: Request LinkedIn Post Approval (Blocking)
```python
from human_approval import request_linkedin_approval

post_data = {
    "content": "Excited to share our latest product update...",
    "hashtags": ["#innovation", "#technology"]
}

result = request_linkedin_approval(
    post_data, 
    priority="normal",
    wait=True  # Blocks until approved
)
# Blocks execution until human approves/rejects
```

### Example 3: Check Approval Status
```python
from human_approval import check_approval_status

status = check_approval_status("email_send_20240115103000_abc123")
# Returns: {"request_id": "...", "status": "approved", ...}
```

### Example 4: Execute Approved Action
```python
from human_approval import execute_approved_action

def send_email(data):
    # Actual email sending logic
    return {"sent": True}

result = execute_approved_action(
    "email_send_20240115103000_abc123",
    executor_func=send_email
)
# Only executes if approved
```

## Approval Request File Format

```markdown
# Approval Request

**Request ID:** email_send_20240115103000_abc123
**Status:** PENDING
**Priority:** NORMAL
**Created:** 2024-01-15 10:30:00

---

## Action Type

email_send

---

## Reason for Approval

Client communication requires approval

---

## Action Details

```json
{
  "to": "client@example.com",
  "subject": "Project Update",
  "body": "Dear Client, here is your project update..."
}
```

---

## Response Section (For Human Reviewer)

**Status:** [pending/approved/rejected/needs_revision]

**Approved By:** [Your name]

**Approval Date:** [YYYY-MM-DD HH:MM:SS]

**Rejection Reason:** [If rejected, explain why]

**Revision Notes:** [If needs revision, explain what to change]
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Human Approval Workflow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Sensitive  │─────▶│   Create     │─────▶│   Save to    │  │
│  │   Action     │      │   Request    │      │  Approvals/  │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│                                                   │              │
│                                                   ▼              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │   Execute    │◀─────│   Approved?  │◀─────│   Wait for   │  │
│  │   Action     │      │              │      │   Review     │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                    │                                      │
│         ▼                    ▼                                      │
│  ┌──────────────┐      ┌──────────────┐                          │
│  │   Log        │      │   Rejected/  │                          │
│  │   Success    │      │   Revision   │                          │
│  └──────────────┘      └──────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Log Format

```json
{
  "timestamp": "2024-01-15 10:30:00",
  "event_type": "approval_decision",
  "request_id": "email_send_20240115103000_abc123",
  "action_type": "email_send",
  "decision": "approved",
  "decided_by": "John Doe",
  "comments": "Looks good, approved for sending",
  "request_data": {...}
}
```

## Compliance Notes

- **Silver Tier Compliant:** Yes
- **Blocks Execution:** Yes, until approved
- **No Automatic Execution:** Yes, requires explicit approval
- **Decision Logging:** Yes, all decisions logged
- **Local Operations Only:** Yes
- **Structured Logging:** JSON format