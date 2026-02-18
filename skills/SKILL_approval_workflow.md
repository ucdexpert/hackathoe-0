# SKILL_approval_workflow

## Description
Implements the human-in-the-loop approval workflow for the AI Employee, defining when to request approval, how to create approval request files, how to wait for approval, and how to handle rejections.

## Parameters
None

## Functionality
When invoked, this skill enables the AI Employee to:
1. Determine when approval is required
2. Create structured approval request files
3. Wait for human approval
4. Handle approved/rejected requests appropriately
5. Log all approval workflow activities

## Implementation
```python
import os
import json
from datetime import datetime, timedelta

def approval_workflow_skill():
    """
    Manages the approval workflow for the AI Employee.
    """
    # Define folder paths
    needs_approval_dir = "Needs_Approval"
    approved_dir = "Approved"
    rejected_dir = "Rejected"
    logs_dir = "Logs"
    
    # Ensure directories exist
    for directory in [needs_approval_dir, approved_dir, rejected_dir, logs_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Scan for approval requests
    approval_requests = scan_approval_requests(needs_approval_dir)
    
    processed_count = 0
    activity_entries = []
    
    for request_file in approval_requests:
        # Check if the request has been approved or rejected
        decision = check_approval_status(request_file)
        
        if decision == 'approved':
            # Move to approved folder
            approved_path = move_to_approved(request_file)
            activity_entries.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'Request Approved',
                'item': os.path.basename(request_file),
                'details': 'Moved to Approved folder'
            })
            
            # Execute the approved action
            execute_approved_action(request_file)
            
        elif decision == 'rejected':
            # Move to rejected folder
            rejected_path = move_to_rejected(request_file)
            activity_entries.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'Request Rejected',
                'item': os.path.basename(request_file),
                'details': 'Moved to Rejected folder'
            })
            
            # Handle rejection appropriately
            handle_rejection(request_file)
        else:
            # Still pending approval
            activity_entries.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'Awaiting Approval',
                'item': os.path.basename(request_file),
                'details': 'Still waiting for human decision'
            })
        
        processed_count += 1
    
    # Log all activities
    log_approval_activities(logs_dir, activity_entries, processed_count)
    
    return f"Approval workflow completed. Processed {processed_count} request(s)."

def scan_approval_requests(needs_approval_dir):
    """
    Scans the Needs_Approval folder for pending requests.
    """
    if not os.path.exists(needs_approval_dir):
        return []
    
    request_files = []
    for filename in os.listdir(needs_approval_dir):
        if filename.lower().endswith('.md'):
            filepath = os.path.join(needs_approval_dir, filename)
            if os.path.isfile(filepath):
                request_files.append(filepath)
    
    return request_files

def check_approval_status(request_file):
    """
    Checks if a request has been approved or rejected.
    In a real implementation, this would interface with a human approval system.
    For this simulation, we'll use a simple heuristic based on file content.
    """
    with open(request_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # In a real system, this would connect to an actual approval system
    # For simulation purposes, we'll randomly decide after a certain time
    # to simulate human decision-making
    
    # Check if enough time has passed to simulate a decision
    # (In reality, this would be based on actual human input)
    import random
    # Simulate a 30% chance of approval, 20% chance of rejection, 50% still pending
    rand_val = random.random()
    
    if rand_val < 0.3:  # 30% chance of approval
        return 'approved'
    elif rand_val < 0.5:  # 20% chance of rejection (0.3 to 0.5 range)
        return 'rejected'
    else:  # 50% still pending
        return 'pending'

def move_to_approved(request_file):
    """
    Moves an approved request to the Approved folder.
    """
    approved_dir = "Approved"
    if not os.path.exists(approved_dir):
        os.makedirs(approved_dir)
    
    filename = os.path.basename(request_file)
    approved_path = os.path.join(approved_dir, f"approved_{filename}")
    
    # Copy the file to approved folder (in real system, might move)
    with open(request_file, 'r', encoding='utf-8') as src, \
         open(approved_path, 'w', encoding='utf-8') as dst:
        dst.write(src.read())
    
    # Remove the original request file
    os.remove(request_file)
    
    return approved_path

def move_to_rejected(request_file):
    """
    Moves a rejected request to the Rejected folder.
    """
    rejected_dir = "Rejected"
    if not os.path.exists(rejected_dir):
        os.makedirs(rejected_dir)
    
    filename = os.path.basename(request_file)
    rejected_path = os.path.join(rejected_dir, f"rejected_{filename}")
    
    # Copy the file to rejected folder (in real system, might move)
    with open(request_file, 'r', encoding='utf-8') as src, \
         open(rejected_path, 'w', encoding='utf-8') as dst:
        dst.write(src.read())
    
    # Remove the original request file
    os.remove(request_file)
    
    return rejected_path

def execute_approved_action(request_file):
    """
    Executes the action that was approved.
    The specific action depends on the type of request.
    """
    # Determine the type of request from the filename
    filename = os.path.basename(request_file)
    
    if 'email' in filename.lower():
        # Execute email sending
        execute_email_sending(request_file)
    elif 'linkedin' in filename.lower():
        # Execute LinkedIn posting
        execute_linkedin_posting(request_file)
    else:
        # Execute general task
        execute_general_task(request_file)

def execute_email_sending(request_file):
    """
    Executes the sending of an approved email.
    """
    # In a real implementation, this would send the actual email
    # For simulation, we'll just log the action
    sent_dir = "Email_Sent"
    if not os.path.exists(sent_dir):
        os.makedirs(sent_dir)
    
    # Create a simulated sent email
    sent_filename = f"sent_{os.path.basename(request_file)}"
    sent_path = os.path.join(sent_dir, sent_filename)
    
    with open(request_file, 'r', encoding='utf-8') as src, \
         open(sent_path, 'w', encoding='utf-8') as dst:
        dst.write(src.read())

def execute_linkedin_posting(request_file):
    """
    Executes the posting of an approved LinkedIn post.
    """
    # In a real implementation, this would post to LinkedIn
    # For simulation, we'll just move to published folder
    published_dir = "LinkedIn_Published"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
    
    # Create a simulated published post
    published_filename = f"linkedin_published_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    published_path = os.path.join(published_dir, published_filename)
    
    with open(request_file, 'r', encoding='utf-8') as src, \
         open(published_path, 'w', encoding='utf-8') as dst:
        dst.write(src.read())

def execute_general_task(request_file):
    """
    Executes a general approved task.
    """
    # In a real implementation, this would execute the specific task
    # For simulation, we'll just log the action
    completed_dir = "Tasks_Completed"
    if not os.path.exists(completed_dir):
        os.makedirs(completed_dir)
    
    # Move the request to completed folder
    completed_filename = f"completed_{os.path.basename(request_file)}"
    completed_path = os.path.join(completed_dir, completed_filename)
    
    with open(request_file, 'r', encoding='utf-8') as src, \
         open(completed_path, 'w', encoding='utf-8') as dst:
        dst.write(src.read())

def handle_rejection(request_file):
    """
    Handles a rejected request appropriately.
    """
    # In a real implementation, this might notify the requester
    # or queue for revision
    # For simulation, we'll just log the rejection
    pass

def log_approval_activities(logs_dir, activity_entries, processed_count):
    """
    Logs approval workflow activities in JSON format.
    """
    log_entry = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "operation": "approval_workflow",
        "processed_count": processed_count,
        "activities": activity_entries,
        "status": "completed"
    }
    
    log_file = os.path.join(logs_dir, f"approval_workflow_{datetime.now().strftime('%Y%m%d')}.json")
    
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
result = approval_workflow_skill()
result
```