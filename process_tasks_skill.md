# process_tasks

## Description
A skill that processes tasks in the Needs_Action folder by creating plan files, updating the dashboard, and moving completed tasks to the Done folder.

## Parameters
None

## Functionality
When invoked, this skill will:

1. Read all files inside the Needs_Action folder
2. Create Plan files inside the Plans folder
3. Update Dashboard.md with a new entry under Recent Activity
4. Move completed tasks to the Done folder

## Constraints
- Only performs local vault operations
- Does not perform external actions, payments, or email sending
- Complies with Bronze Tier limitations
- No file deletion operations
- Includes error handling and duplicate prevention

## Implementation
```python
import os
import shutil
import json
from datetime import datetime

def process_tasks_skill():
    """
    Main function for the process_tasks skill.
    Processes tasks from Needs_Action, creates plans, updates dashboard, and moves to Done.
    """
    # Define folder paths
    needs_action_dir = "Needs_Action"
    plans_dir = "Plans"
    done_dir = "Done"
    dashboard_file = "Dashboard.md"
    logs_dir = "Logs"

    # Create directories if they don't exist
    for directory in [needs_action_dir, plans_dir, done_dir, logs_dir]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                return f"Error creating directory {directory}: {str(e)}"

    # Read all files in Needs_Action
    if not os.path.exists(needs_action_dir):
        return f"The {needs_action_dir} directory does not exist."

    try:
        files = os.listdir(needs_action_dir)
    except OSError as e:
        return f"Error reading directory {needs_action_dir}: {str(e)}"

    if not files:
        return f"No files found in {needs_action_dir} directory."

    processed_count = 0
    activity_entries = []
    processed_files = set()  # Track processed files to prevent duplicates

    for filename in files:
        filepath = os.path.join(needs_action_dir, filename)

        # Skip directories, only process files
        if os.path.isfile(filepath):
            abs_path = os.path.abspath(filepath)
            
            # Check if file was already processed to prevent duplicates
            if abs_path in processed_files:
                continue
            
            try:
                # Create a plan file in Plans folder
                plan_filename = f"plan_{os.path.splitext(filename)[0]}.md"
                plan_filepath = os.path.join(plans_dir, plan_filename)

                with open(filepath, 'r', encoding='utf-8') as source_file:
                    content = source_file.read()

                # Create plan content based on the original file
                plan_content = f"""# Plan for {filename}

## Original Content
{content}

## Action Items
- [ ] Review the content
- [ ] Determine next steps
- [ ] Execute planned actions
- [ ] Mark as complete

## Notes
Add any additional notes or considerations here.
"""

                with open(plan_filepath, 'w', encoding='utf-8') as plan_file:
                    plan_file.write(plan_content)

                # Record activity for dashboard
                activity_entries.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'action': 'Created plan',
                    'item': plan_filename
                })

                # Move the original file to Done folder
                done_filepath = os.path.join(done_dir, filename)
                shutil.move(filepath, done_filepath)

                # Mark file as processed
                processed_files.add(abs_path)

                processed_count += 1
                
                # Log the operation in JSON format
                log_entry = {
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "operation": "process_task",
                    "original_file": filename,
                    "created_plan": plan_filename,
                    "moved_to": done_filepath,
                    "status": "success"
                }
                log_json_operation(logs_dir, log_entry)

            except FileNotFoundError:
                error_msg = f"File not found: {filepath}"
                log_error(logs_dir, "process_task", filename, error_msg)
                continue
            except PermissionError:
                error_msg = f"Permission denied when processing: {filepath}"
                log_error(logs_dir, "process_task", filename, error_msg)
                continue
            except OSError as e:
                error_msg = f"OS error when processing {filepath}: {str(e)}"
                log_error(logs_dir, "process_task", filename, error_msg)
                continue
            except Exception as e:
                error_msg = f"Unexpected error when processing {filepath}: {str(e)}"
                log_error(logs_dir, "process_task", filename, error_msg)
                continue

    # Update Dashboard.md with recent activity if there are entries
    if activity_entries:
        try:
            update_dashboard_safely(dashboard_file, activity_entries)
        except Exception as e:
            error_msg = f"Error updating dashboard: {str(e)}"
            log_error(logs_dir, "update_dashboard", "Dashboard.md", error_msg)

    return f"Processed {processed_count} file(s). Created corresponding plan(s) in Plans folder and moved original file(s) to Done folder."

def update_dashboard_safely(dashboard_file, activity_entries):
    """
    Safely updates the Dashboard.md file with recent activity entries.
    Creates a backup before updating and removes it after successful update.
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
            new_activity += f"- {entry['timestamp']}: {entry['action']} - {entry['item']}\n"

        # Insert new activity entries after the marker
        updated_content = content[:pos] + new_activity + content[pos:]
    else:
        # If no activity section exists, add it
        updated_content = content + f"\n## Recent Activity\n"
        for entry in activity_entries:
            updated_content += f"- {entry['timestamp']}: {entry['action']} - {entry['item']}\n"

    # Write updated content back to dashboard with backup
    backup_file = f"{dashboard_file}.backup"
    if os.path.exists(dashboard_file):
        shutil.copy2(dashboard_file, backup_file)
    
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
        
    # Remove backup after successful write
    if os.path.exists(backup_file):
        os.remove(backup_file)

def log_json_operation(logs_dir, log_entry):
    """
    Log operation in JSON format to a dedicated log file.
    """
    try:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        log_file = os.path.join(logs_dir, f"skill_process_tasks_{datetime.now().strftime('%Y%m%d')}.json")
        
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
    except Exception:
        # If logging fails, we don't want to stop the main operation
        pass

def log_error(logs_dir, operation, filename, error_msg):
    """
    Log error in JSON format.
    """
    try:
        error_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "operation": operation,
            "file": filename,
            "error": error_msg,
            "status": "error"
        }
        log_json_operation(logs_dir, error_entry)
    except Exception:
        # If logging fails, we don't want to stop the main operation
        pass

# Execute the skill when called
result = process_tasks_skill()
result
```