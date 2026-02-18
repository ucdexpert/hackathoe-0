# SKILL_core_operations

## Description
Defines the core operational behavior of the AI Employee, including how to read company policies, process tasks, create plans, update dashboards, log actions, and determine when to seek approval.

## Parameters
None

## Functionality
When invoked, this skill enables the AI Employee to:
1. Read and interpret Company_Handbook.md
2. Process tasks from the Needs_Action folder
3. Create structured plans for task completion
4. Update the Dashboard with progress
5. Log all actions appropriately
6. Determine when to request human approval

## Implementation
```python
import os
import json
from datetime import datetime

def core_operations_skill():
    """
    Executes core operations for the AI Employee.
    """
    # Define folder paths
    handbook_file = "Company_Handbook.md"
    needs_action_dir = "Needs_Action"
    plans_dir = "Plans"
    logs_dir = "Logs"
    dashboard_file = "Dashboard.md"
    
    # Ensure directories exist
    for directory in [plans_dir, logs_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # 1. Read Company_Handbook.md
    handbook_content = read_company_handbook(handbook_file)
    
    # 2. Process tasks from Needs_Action
    tasks = scan_needs_action_folder(needs_action_dir)
    
    processed_count = 0
    activity_entries = []
    
    for task_file in tasks:
        task_content = read_task_file(task_file)
        
        # 3. Create plans based on handbook guidance
        plan_result = create_plan_from_task(task_file, task_content, handbook_content)
        
        if plan_result['requires_approval']:
            # Create approval request
            approval_needed = create_approval_request(task_file, plan_result['plan_details'])
            if approval_needed:
                activity_entries.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'action': 'Approval Requested',
                    'item': os.path.basename(task_file),
                    'details': 'Human approval required for sensitive task'
                })
            continue  # Skip processing until approval is granted
        
        # Execute the plan
        execution_result = execute_plan(plan_result['plan_filepath'], plan_result['tasks'])
        
        # Update dashboard
        activity_entries.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'Task Processed',
            'item': os.path.basename(task_file),
            'details': f"Created plan: {os.path.basename(plan_result['plan_filepath'])}"
        })
        
        processed_count += 1
    
    # 4. Update Dashboard with recent activity
    if activity_entries:
        update_dashboard_with_activities(dashboard_file, activity_entries)
    
    # 5. Log all actions
    log_core_operations(logs_dir, activity_entries, processed_count)
    
    return f"Core operations completed. Processed {processed_count} task(s). See Dashboard for details."

def read_company_handbook(handbook_file):
    """
    Reads and interprets the Company_Handbook.md file.
    """
    if not os.path.exists(handbook_file):
        return "Company handbook not found. Proceeding with default policies."
    
    with open(handbook_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def scan_needs_action_folder(needs_action_dir):
    """
    Scans the Needs_Action folder for task files.
    """
    if not os.path.exists(needs_action_dir):
        return []
    
    task_files = []
    for filename in os.listdir(needs_action_dir):
        if filename.lower().endswith(('.md', '.txt')):
            filepath = os.path.join(needs_action_dir, filename)
            if os.path.isfile(filepath):
                task_files.append(filepath)
    
    return task_files

def read_task_file(task_file):
    """
    Reads the content of a task file.
    """
    with open(task_file, 'r', encoding='utf-8') as f:
        return f.read()

def create_plan_from_task(task_file, task_content, handbook_content):
    """
    Creates a structured plan based on the task and company handbook.
    Determines if approval is needed based on handbook policies.
    """
    import re
    
    task_name = os.path.basename(task_file)
    plan_filename = f"plan_{os.path.splitext(task_name)[0]}.md"
    plan_filepath = os.path.join("Plans", plan_filename)
    
    # Determine if approval is needed based on keywords in handbook and task
    requires_approval = False
    approval_keywords = [
        'approval', 'authorize', 'permission', 'sensitive', 'confidential', 
        'financial', 'budget', 'contract', 'legal', 'customer data'
    ]
    
    handbook_lower = handbook_content.lower()
    task_lower = task_content.lower()
    
    for keyword in approval_keywords:
        if keyword in handbook_lower or keyword in task_lower:
            requires_approval = True
            break
    
    # Create plan content
    plan_content = f"""# Plan for {task_name}

## Original Task
{task_content}

## Action Steps
1. Analyze requirements
2. Gather necessary resources
3. Execute primary action
4. Verify completion
5. Document results

## Timeline
- Priority: Normal
- Estimated completion: 1-2 business days

## Resources Needed
- Access to relevant systems
- Reference materials
- Potential team collaboration

## Success Criteria
- Task completed as specified
- Quality standards met
- Proper documentation maintained
"""

    # Write the plan file
    with open(plan_filepath, 'w', encoding='utf-8') as f:
        f.write(plan_content)
    
    return {
        'plan_filepath': plan_filepath,
        'plan_details': plan_content,
        'requires_approval': requires_approval,
        'tasks': ['analyze', 'gather', 'execute', 'verify', 'document']
    }

def create_approval_request(task_file, plan_details):
    """
    Creates an approval request file when needed.
    """
    approval_dir = "Needs_Approval"
    if not os.path.exists(approval_dir):
        os.makedirs(approval_dir)
    
    task_name = os.path.basename(task_file)
    approval_filename = f"approval_{os.path.splitext(task_name)[0]}.md"
    approval_filepath = os.path.join(approval_dir, approval_filename)
    
    approval_content = f"""# Approval Request

## Task Requiring Approval
{task_file}

## Proposed Plan
{plan_details}

## Justification
This task involves sensitive operations requiring human oversight.

## Action Required
Please review the proposed plan and approve or modify as needed.
"""

    with open(approval_filepath, 'w', encoding='utf-8') as f:
        f.write(approval_content)
    
    return True

def execute_plan(plan_filepath, tasks):
    """
    Simulates execution of the plan steps.
    """
    # In a real implementation, this would execute the actual tasks
    # For now, we'll just return a success indicator
    return {'status': 'completed', 'executed_tasks': tasks}

def update_dashboard_with_activities(dashboard_file, activity_entries):
    """
    Updates the Dashboard.md file with recent activities.
    """
    # Create dashboard content if it doesn't exist
    if not os.path.exists(dashboard_file):
        initial_content = "# Dashboard\n\n## Recent Activity\n\n"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(initial_content)

    # Read current dashboard content
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the position to insert recent activity
    activity_section_marker = "## Recent Activity"
    if activity_section_marker in content:
        # Find the position after the activity section marker
        pos = content.find(activity_section_marker) + len(activity_section_marker)

        # Prepare new activity entries
        new_activity = "\n"
        for entry in activity_entries:
            new_activity += f"- {entry['timestamp']}: {entry['action']} - {entry['item']} ({entry['details']})\n"

        # Insert new activity entries after the marker
        updated_content = content[:pos] + new_activity + content[pos:]
    else:
        # If no activity section exists, add it
        updated_content = content + f"\n## Recent Activity\n"
        for entry in activity_entries:
            updated_content += f"- {entry['timestamp']}: {entry['action']} - {entry['item']} ({entry['details']})\n"

    # Write updated content back to dashboard
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def log_core_operations(logs_dir, activity_entries, processed_count):
    """
    Logs core operations in JSON format.
    """
    log_entry = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "operation": "core_operations",
        "processed_count": processed_count,
        "activities": activity_entries,
        "status": "completed"
    }
    
    log_file = os.path.join(logs_dir, f"core_operations_{datetime.now().strftime('%Y%m%d')}.json")
    
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
result = core_operations_skill()
result
```