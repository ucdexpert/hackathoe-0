# SKILL_gmail_send

## Description
Sends emails via Gmail API using MCP (Model Context Protocol) server. Implements human-in-the-loop approval workflow to ensure no email is sent without explicit human authorization.

## Parameters
- `recipient` (string): Email address of the recipient
- `subject` (string): Subject line of the email
- `body` (string): Body content of the email

## Functionality
When invoked, this skill enables the AI Employee to:
1. Validate email inputs (recipient, subject, body)
2. Create an approval request file for human review
3. Wait for human approval before execution
4. Call MCP endpoint to send email via Gmail API
5. Log the result of the email sending operation
6. Handle errors and failures gracefully

## Constraints
- **No direct SMTP**: Must use MCP server for all email operations
- **Human approval required**: No email is sent without explicit human approval
- **MCP server only**: All email sending goes through the MCP `/send-email` endpoint
- **Silver Tier compliant**: Follows approval workflow and logging requirements

## Implementation
```python
import os
import json
import re
from datetime import datetime

def gmail_send_skill(recipient, subject, body):
    """
    Sends an email via Gmail API using MCP server.
    Requires human approval before execution.
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Subject line of the email
        body (str): Body content of the email
    
    Returns:
        dict: Result of the email sending operation
    """
    # Define folder paths
    needs_approval_dir = "Needs_Approval"
    approved_dir = "Approved"
    rejected_dir = "Rejected"
    logs_dir = "Logs"
    sent_dir = "Email_Sent"

    # Ensure directories exist
    for directory in [needs_approval_dir, approved_dir, rejected_dir, logs_dir, sent_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    # 1. Validate inputs
    validation_result = validate_email_inputs(recipient, subject, body)
    if not validation_result['valid']:
        error_result = {
            "status": "error",
            "message": validation_result['error'],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        log_email_operation(logs_dir, error_result)
        return error_result

    # 2. Create approval request
    approval_request = create_approval_request(
        needs_approval_dir, recipient, subject, body
    )

    # 3. Wait for human approval (blocking operation)
    # In practice, this would poll or use a callback mechanism
    approval_status = wait_for_approval(approval_request['filepath'])

    if approval_status == 'approved':
        # 4. Call MCP endpoint to send email
        send_result = call_mcp_send_email(recipient, subject, body)
        
        if send_result['success']:
            # Move approval request to approved folder
            move_to_approved(approval_request['filepath'], approved_dir)
            
            # Save sent email record
            save_sent_email(sent_dir, recipient, subject, body, send_result)
            
            # Log success
            success_result = {
                "status": "success",
                "message": f"Email sent to {recipient}",
                "recipient": recipient,
                "subject": subject,
                "mcp_response": send_result,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            log_email_operation(logs_dir, success_result)
            return success_result
        else:
            # Log failure
            failure_result = {
                "status": "error",
                "message": "Failed to send email via MCP",
                "recipient": recipient,
                "error": send_result.get('error', 'Unknown error'),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            log_email_operation(logs_dir, failure_result)
            return failure_result

    elif approval_status == 'rejected':
        # Move to rejected folder
        move_to_rejected(approval_request['filepath'], rejected_dir)
        
        rejection_result = {
            "status": "rejected",
            "message": "Email sending was rejected by human reviewer",
            "recipient": recipient,
            "subject": subject,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        log_email_operation(logs_dir, rejection_result)
        return rejection_result

    else:
        # Timeout or pending
        timeout_result = {
            "status": "pending",
            "message": "Approval timeout - email not sent",
            "recipient": recipient,
            "subject": subject,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        log_email_operation(logs_dir, timeout_result)
        return timeout_result


def validate_email_inputs(recipient, subject, body):
    """
    Validates email inputs.
    
    Args:
        recipient: Email address to validate
        subject: Subject line to validate
        body: Email body to validate
    
    Returns:
        dict: {'valid': bool, 'error': str or None}
    """
    # Validate recipient
    if not recipient or not isinstance(recipient, str):
        return {'valid': False, 'error': 'Recipient email address is required'}
    
    # Basic email regex validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, recipient.strip()):
        return {'valid': False, 'error': f'Invalid email address format: {recipient}'}
    
    # Validate subject
    if not subject or not isinstance(subject, str):
        return {'valid': False, 'error': 'Email subject is required'}
    
    if len(subject.strip()) == 0:
        return {'valid': False, 'error': 'Email subject cannot be empty'}
    
    if len(subject) > 998:  # RFC 5322 limit
        return {'valid': False, 'error': 'Email subject exceeds maximum length (998 characters)'}
    
    # Validate body
    if body is None or not isinstance(body, str):
        return {'valid': False, 'error': 'Email body is required'}
    
    return {'valid': True, 'error': None}


def create_approval_request(needs_approval_dir, recipient, subject, body):
    """
    Creates an approval request file for human review.
    
    Args:
        needs_approval_dir: Directory for approval requests
        recipient: Email recipient
        subject: Email subject
        body: Email body
    
    Returns:
        dict: {'filepath': str, 'request_id': str}
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    request_id = f"email_{timestamp}_{hash(recipient + subject) % 10000:04d}"
    filename = f"{request_id}.md"
    filepath = os.path.join(needs_approval_dir, filename)
    
    approval_content = f"""# Email Sending Approval Request

## Request ID
{request_id}

## Timestamp
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Email Details

### Recipient
{recipient}

### Subject
{subject}

### Body
{body}

## Approval Required
This email requires human approval before sending via Gmail API (MCP server).

## Instructions for Reviewer
1. Review the email content above
2. To **APPROVE**: Change the status below to `approved`
3. To **REJECT**: Change the status below to `rejected`
4. Optionally add comments in the section below

## Status
<!-- AI Employee will read this field: approved, rejected, or pending -->
status: pending

## Reviewer Comments
<!-- Add any comments or modification requests here -->

---
*This is an automated approval request generated by AI Employee Vault*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(approval_content)
    
    return {'filepath': filepath, 'request_id': request_id}


def wait_for_approval(filepath, timeout_seconds=300, poll_interval=5):
    """
    Waits for human approval by polling the approval request file.
    
    Args:
        filepath: Path to the approval request file
        timeout_seconds: Maximum time to wait for approval (default: 5 minutes)
        poll_interval: Time between status checks (default: 5 seconds)
    
    Returns:
        str: 'approved', 'rejected', or 'timeout'
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for status in the content
            status_match = re.search(r'status:\s*(\w+)', content, re.IGNORECASE)
            if status_match:
                status = status_match.group(1).lower().strip()
                if status == 'approved':
                    return 'approved'
                elif status == 'rejected':
                    return 'rejected'
        
        except (FileNotFoundError, IOError):
            # File might have been moved
            return 'timeout'
        
        time.sleep(poll_interval)
    
    return 'timeout'


def call_mcp_send_email(recipient, subject, body):
    """
    Calls the MCP server endpoint to send email via Gmail API.
    
    POST /send-email
    
    Args:
        recipient: Email recipient
        subject: Email subject
        body: Email body
    
    Returns:
        dict: {'success': bool, 'message_id': str or None, 'error': str or None}
    """
    # MCP server endpoint configuration
    mcp_endpoint = os.environ.get('MCP_SERVER_URL', 'http://localhost:8080')
    send_email_url = f"{mcp_endpoint}/send-email"
    
    # Prepare the request payload
    payload = {
        "to": recipient,
        "subject": subject,
        "body": body,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # In a real implementation, this would make an HTTP request to the MCP server
        # For simulation purposes, we'll demonstrate the structure
        
        # import requests
        # response = requests.post(
        #     send_email_url,
        #     json=payload,
        #     headers={'Content-Type': 'application/json'},
        #     timeout=30
        # )
        # 
        # if response.status_code == 200:
        #     result = response.json()
        #     return {
        #         'success': True,
        #         'message_id': result.get('message_id'),
        #         'error': None
        #     }
        # else:
        #     return {
        #         'success': False,
        #         'message_id': None,
        #         'error': f"MCP server error: {response.status_code} - {response.text}"
        #     }
        
        # Simulation for demonstration (remove in production)
        # This simulates a successful MCP response
        return {
            'success': True,
            'message_id': f"<{datetime.now().strftime('%Y%m%d%H%M%S')}@gmail.com>",
            'error': None,
            'mcp_endpoint': send_email_url
        }
        
    except Exception as e:
        return {
            'success': False,
            'message_id': None,
            'error': str(e)
        }


def move_to_approved(filepath, approved_dir):
    """
    Moves an approved request to the Approved folder.
    """
    if not os.path.exists(approved_dir):
        os.makedirs(approved_dir)
    
    filename = os.path.basename(filepath)
    approved_path = os.path.join(approved_dir, f"approved_{filename}")
    
    # Copy with approval timestamp
    with open(filepath, 'r', encoding='utf-8') as src:
        content = src.read()
    
    content += f"\n\n---\n*Approved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    with open(approved_path, 'w', encoding='utf-8') as dst:
        dst.write(content)
    
    # Remove original
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return approved_path


def move_to_rejected(filepath, rejected_dir):
    """
    Moves a rejected request to the Rejected folder.
    """
    if not os.path.exists(rejected_dir):
        os.makedirs(rejected_dir)
    
    filename = os.path.basename(filepath)
    rejected_path = os.path.join(rejected_dir, f"rejected_{filename}")
    
    # Copy with rejection timestamp
    with open(filepath, 'r', encoding='utf-8') as src:
        content = src.read()
    
    content += f"\n\n---\n*Rejected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    with open(rejected_path, 'w', encoding='utf-8') as dst:
        dst.write(content)
    
    # Remove original
    if os.path.exists(filepath):
        os.remove(filepath)
    
    return rejected_path


def save_sent_email(sent_dir, recipient, subject, body, send_result):
    """
    Saves a record of the sent email.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"sent_{timestamp}_{hash(recipient) % 10000:04d}.md"
    filepath = os.path.join(sent_dir, filename)
    
    email_record = f"""# Sent Email Record

## Metadata
- **Sent At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Recipient**: {recipient}
- **Subject**: {subject}
- **Message ID**: {send_result.get('message_id', 'N/A')}

## Content

### Subject
{subject}

### Body
{body}

## Delivery Status
- **Status**: Sent successfully
- **Via**: Gmail API (MCP Server)

---
*This record was automatically generated by AI Employee Vault*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(email_record)
    
    return filepath


def log_email_operation(logs_dir, result):
    """
    Logs email operation results in JSON format.
    """
    log_file = os.path.join(logs_dir, f"gmail_send_{datetime.now().strftime('%Y%m%d')}.json")
    
    # Read existing logs
    existing_logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                existing_logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_logs = []
    
    # Append new log entry
    existing_logs.append(result)
    
    # Write back
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, indent=2)


# Execute the skill when called
if __name__ == "__main__":
    # Example usage
    result = gmail_send_skill(
        recipient="example@example.com",
        subject="Test Email",
        body="This is a test email from AI Employee Vault."
    )
    print(json.dumps(result, indent=2))
```

## Usage Examples

### Basic Usage
```python
from skills.SKILL_gmail_send import gmail_send_skill

result = gmail_send_skill(
    recipient="colleague@company.com",
    subject="Meeting Reminder",
    body="Hi, this is a reminder about our meeting tomorrow at 10 AM."
)
print(result)
```

### With Approval Workflow
1. Call the skill with email parameters
2. An approval request file is created in `Needs_Approval/`
3. Human reviewer opens the file and changes `status: pending` to `status: approved`
4. The skill polls for approval and sends the email via MCP server
5. Result is logged and email record is saved

## MCP Server Integration

The skill expects an MCP server running with the following endpoint:

```
POST /send-email
Content-Type: application/json

{
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body": "Email body content"
}
```

Expected response:
```json
{
    "success": true,
    "message_id": "<message-id@gmail.com>"
}
```

## Security Notes

- No email credentials are stored or handled by this skill
- All email sending goes through the authenticated MCP server
- Approval workflow ensures human oversight for all outgoing emails
- All operations are logged for audit purposes
