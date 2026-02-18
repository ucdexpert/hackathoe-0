# SKILL_email_handler

## Description
Manages email processing for the AI Employee, including categorization, drafting replies, determining when to request approval, and using appropriate templates.

## Parameters
None

## Functionality
When invoked, this skill enables the AI Employee to:
1. Categorize incoming emails (urgent/normal/low priority)
2. Draft appropriate replies based on email content
3. Determine when to request human approval before sending
4. Apply appropriate email templates based on context
5. Log email processing activities

## Implementation
```python
import os
import json
from datetime import datetime

def email_handler_skill():
    """
    Processes incoming emails for the AI Employee.
    """
    # Define folder paths
    inbox_dir = "Email_Inbox"  # Assumed to be a separate email inbox
    drafts_dir = "Email_Drafts"
    sent_dir = "Email_Sent"
    needs_approval_dir = "Needs_Approval"
    logs_dir = "Logs"
    
    # Ensure directories exist
    for directory in [drafts_dir, sent_dir, needs_approval_dir, logs_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Scan for emails in the inbox
    emails = scan_email_inbox(inbox_dir)
    
    processed_count = 0
    activity_entries = []
    
    for email_file in emails:
        email_content = read_email(email_file)
        
        # 1. Categorize the email
        category = categorize_email(email_content)
        
        # 2. Determine if approval is needed
        requires_approval = should_require_approval(email_content, category)
        
        if requires_approval:
            # 3. Create approval request
            approval_result = create_email_approval_request(email_file, email_content, category)
            activity_entries.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'Approval Requested',
                'item': os.path.basename(email_file),
                'category': category,
                'details': 'Requires human approval before sending'
            })
        else:
            # 4. Draft reply using appropriate template
            draft_result = draft_reply(email_content, category)
            
            # Save draft
            draft_filename = f"draft_{os.path.splitext(os.path.basename(email_file))[0]}.md"
            draft_path = os.path.join(drafts_dir, draft_filename)
            
            with open(draft_path, 'w', encoding='utf-8') as f:
                f.write(draft_result)
            
            # Move email to sent (simulated)
            sent_filename = f"sent_{os.path.basename(email_file)}"
            sent_path = os.path.join(sent_dir, sent_filename)
            # In a real system, we would move the email after sending
            # For simulation, we'll just copy it
            with open(email_file, 'r', encoding='utf-8') as src, \
                 open(sent_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            
            activity_entries.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'Email Processed',
                'item': os.path.basename(email_file),
                'category': category,
                'details': f'Drafted reply: {draft_filename}'
            })
        
        processed_count += 1
    
    # Log all activities
    log_email_activities(logs_dir, activity_entries, processed_count)
    
    return f"Email processing completed. Processed {processed_count} email(s)."

def scan_email_inbox(inbox_dir):
    """
    Scans the email inbox for new messages.
    """
    if not os.path.exists(inbox_dir):
        # Create sample inbox if it doesn't exist for demonstration
        os.makedirs(inbox_dir, exist_ok=True)
        # Create a sample email for testing
        sample_email = os.path.join(inbox_dir, "sample_email.txt")
        with open(sample_email, 'w', encoding='utf-8') as f:
            f.write("""From: client@example.com
To: company@business.com
Subject: Project Inquiry
Date: 2023-06-15

Hi,

I'm interested in your services for a new project. Could you please provide more information about your offerings?

Best regards,
Client Name""")
        return [sample_email]
    
    email_files = []
    for filename in os.listdir(inbox_dir):
        if filename.lower().endswith(('.txt', '.eml', '.msg')):
            filepath = os.path.join(inbox_dir, filename)
            if os.path.isfile(filepath):
                email_files.append(filepath)
    
    return email_files

def read_email(email_file):
    """
    Reads the content of an email file.
    """
    with open(email_file, 'r', encoding='utf-8') as f:
        return f.read()

def categorize_email(email_content):
    """
    Categorizes an email as urgent, normal, or low priority.
    """
    email_lower = email_content.lower()
    
    # Keywords indicating urgency
    urgent_keywords = [
        'urgent', 'asap', 'immediately', 'critical', 'emergency', 
        'today', 'deadline', 'important', 'attention required'
    ]
    
    # Keywords indicating low priority
    low_keywords = [
        'newsletter', 'promotion', 'marketing', 'advertisement', 
        'unsubscribe', 'spam', 'offer'
    ]
    
    # Check for urgent indicators
    for keyword in urgent_keywords:
        if keyword in email_lower:
            return 'urgent'
    
    # Check for low priority indicators
    for keyword in low_keywords:
        if keyword in email_lower:
            return 'low'
    
    # Default to normal priority
    return 'normal'

def should_require_approval(email_content, category):
    """
    Determines if an email requires human approval before sending a response.
    """
    email_lower = email_content.lower()
    
    # Always require approval for urgent emails
    if category == 'urgent':
        return True
    
    # Keywords that require approval
    approval_keywords = [
        'contract', 'agreement', 'payment', 'financial', 'budget',
        'legal', 'complaint', 'problem', 'issue', 'refund', 'compliance',
        'sensitive', 'confidential', 'personal data', 'security'
    ]
    
    for keyword in approval_keywords:
        if keyword in email_lower:
            return True
    
    return False

def create_email_approval_request(email_file, email_content, category):
    """
    Creates an approval request for an email that requires human oversight.
    """
    needs_approval_dir = "Needs_Approval"
    if not os.path.exists(needs_approval_dir):
        os.makedirs(needs_approval_dir)
    
    email_name = os.path.basename(email_file)
    approval_filename = f"email_approval_{os.path.splitext(email_name)[0]}.md"
    approval_filepath = os.path.join(needs_approval_dir, approval_filename)
    
    # Draft a suggested response
    suggested_response = draft_reply(email_content, category)
    
    approval_content = f"""# Email Response Approval Request

## Original Email
{email_content}

## Suggested Response
{suggested_response}

## Category
{category}

## Justification for Approval
This email contains sensitive topics requiring human oversight.

## Action Required
Please review the suggested response and approve, modify, or reject.
"""

    with open(approval_filepath, 'w', encoding='utf-8') as f:
        f.write(approval_content)
    
    return True

def draft_reply(email_content, category):
    """
    Drafts an appropriate reply based on email content and category.
    """
    # Extract subject and sender from email content
    subject_line = ""
    sender = ""
    
    lines = email_content.split('\n')
    for line in lines:
        if line.startswith('Subject:'):
            subject_line = line.replace('Subject:', '').strip()
        elif line.startswith('From:'):
            sender = line.replace('From:', '').strip()
    
    # Select template based on category
    if category == 'urgent':
        template = get_urgent_template(subject_line, sender)
    elif category == 'low':
        template = get_low_priority_template(subject_line, sender)
    else:
        template = get_normal_template(subject_line, sender)
    
    return template

def get_urgent_template(subject, sender):
    """
    Returns a template for urgent emails.
    """
    return f"""From: ai.employee@company.com
To: {sender}
Subject: RE: {subject}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Dear Sender,

Thank you for your urgent message regarding "{subject}". We acknowledge receipt and are prioritizing your request. 

Our team is currently reviewing your inquiry and will provide a detailed response within 24 hours. If this matter requires immediate attention beyond that timeframe, please contact our emergency line at [emergency contact].

Best regards,
AI Employee Assistant
Company Name"""

def get_normal_template(subject, sender):
    """
    Returns a template for normal priority emails.
    """
    return f"""From: ai.employee@company.com
To: {sender}
Subject: RE: {subject}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Dear Sender,

Thank you for your message regarding "{subject}". We have received your inquiry and will review it carefully.

We typically respond to inquiries of this nature within 1-2 business days. If you have not received a response by then, please feel free to follow up.

Best regards,
AI Employee Assistant
Company Name"""

def get_low_priority_template(subject, sender):
    """
    Returns a template for low priority emails.
    """
    return f"""From: ai.employee@company.com
To: {sender}
Subject: RE: {subject}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Thank you for your message regarding "{subject}". 

This inquiry has been logged in our system and will be addressed in our regular processing cycle. 

Best regards,
AI Employee Assistant
Company Name"""

def log_email_activities(logs_dir, activity_entries, processed_count):
    """
    Logs email processing activities in JSON format.
    """
    log_entry = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "operation": "email_processing",
        "processed_count": processed_count,
        "activities": activity_entries,
        "status": "completed"
    }
    
    log_file = os.path.join(logs_dir, f"email_processing_{datetime.now().strftime('%Y%m%d')}.json")
    
    # Read existing logs if file exists
    existing_logs = []
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                existing_logs = json.load(f)
            except json.JSONDecodeError:
                existing_logs = []
    
    # Append new log entry
    existing_logs.append(log_entry)
    
    # Write back to file
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, indent=2)

# Execute the skill when called
result = email_handler_skill()
result
```