import os
import json
import shutil
from datetime import datetime
import time


def scan_needs_action_folder(needs_action_dir):
    """Scan the Needs_Action folder for markdown files."""
    markdown_files = []

    if not os.path.exists(needs_action_dir):
        print(f"Directory {needs_action_dir} does not exist.")
        return markdown_files

    for filename in os.listdir(needs_action_dir):
        if filename.lower().endswith('.md'):
            filepath = os.path.join(needs_action_dir, filename)
            if os.path.isfile(filepath):
                markdown_files.append(filepath)

    return markdown_files


def create_plan_file(plan_filepath, original_filename):
    """Create a plan file in the Plans folder with checklist steps."""
    plan_content = f"""# Action Plan for {original_filename}

## Checklist
- [ ] Review item
- [ ] Decide action
- [ ] Mark complete

## Notes
Add your notes here about the required actions.
"""

    try:
        with open(plan_filepath, 'w', encoding='utf-8') as f:
            f.write(plan_content)
    except PermissionError:
        raise Exception(f"Permission denied when creating plan file: {plan_filepath}")
    except OSError as e:
        raise Exception(f"OS error when creating plan file {plan_filepath}: {str(e)}")


def move_to_done(done_dir, source_file):
    """Move the processed file to the Done folder."""
    try:
        if not os.path.exists(done_dir):
            os.makedirs(done_dir)

        filename = os.path.basename(source_file)
        destination = os.path.join(done_dir, filename)

        shutil.move(source_file, destination)
        return destination
    except PermissionError:
        raise Exception(f"Permission denied when moving file to Done: {source_file}")
    except OSError as e:
        raise Exception(f"OS error when moving file {source_file} to Done: {str(e)}")


def log_operation(logs_dir, operation_data):
    """Log the operation in JSON format to the Logs folder."""
    try:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_filename = f"log_{timestamp}.json"
        log_filepath = os.path.join(logs_dir, log_filename)

        with open(log_filepath, 'w', encoding='utf-8') as f:
            json.dump(operation_data, f, indent=2, default=str)
    except PermissionError:
        print(f"Permission denied when writing log file: {log_filepath}")
    except OSError as e:
        print(f"OS error when writing log file {log_filepath}: {str(e)}")


def safe_update_dashboard(dashboard_file, activity_entries):
    """Safely update the Dashboard.md file with recent activity."""
    try:
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
            
    except PermissionError:
        raise Exception(f"Permission denied when updating dashboard: {dashboard_file}")
    except OSError as e:
        raise Exception(f"OS error when updating dashboard {dashboard_file}: {str(e)}")


def process_needs_action_files():
    """Main function to process files in Needs_Action folder."""
    needs_action_dir = "Needs_Action"
    plans_dir = "Plans"
    done_dir = "Done"
    logs_dir = "Logs"
    dashboard_file = "Dashboard.md"

    # Create directories if they don't exist
    for directory in [plans_dir, done_dir, logs_dir]:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                print(f"Error creating directory {directory}: {str(e)}")
                return

    # Track processed files to prevent duplicates
    processed_files = set()
    
    # Scan for markdown files in Needs_Action folder
    try:
        markdown_files = scan_needs_action_folder(needs_action_dir)
    except OSError as e:
        print(f"Error scanning {needs_action_dir}: {str(e)}")
        return

    if not markdown_files:
        print("No markdown files found in Needs_Action folder.")
        return

    print(f"Found {len(markdown_files)} markdown file(s) to process.")

    # Collect activity entries for dashboard update
    all_activity_entries = []
    
    for filepath in markdown_files:
        try:
            original_filename = os.path.basename(filepath)
            abs_path = os.path.abspath(filepath)
            
            # Check if file was already processed to prevent duplicates
            if abs_path in processed_files:
                print(f"File {original_filename} already processed, skipping duplicate.")
                continue
                
            print(f"Processing: {original_filename}")

            # Create plan file in Plans folder
            plan_filename = f"plan_{os.path.splitext(original_filename)[0]}.md"
            plan_filepath = os.path.join(plans_dir, plan_filename)
            create_plan_file(plan_filepath, original_filename)

            # Move original file to Done folder
            moved_file_path = move_to_done(done_dir, filepath)

            # Record activity for dashboard
            activity_entry = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'Processed file',
                'item': original_filename
            }
            all_activity_entries.append(activity_entry)
            
            # Mark file as processed
            processed_files.add(abs_path)

            # Log the operation
            log_data = {
                "timestamp": datetime.now(),
                "operation": "process_needs_action",
                "original_file": original_filename,
                "plan_file": plan_filename,
                "moved_to": moved_file_path,
                "status": "success"
            }
            log_operation(logs_dir, log_data)

            print(f"Completed processing: {original_filename}")

        except Exception as e:
            # Log error if something goes wrong
            error_log_data = {
                "timestamp": datetime.now(),
                "operation": "process_needs_action",
                "original_file": original_filename if 'original_filename' in locals() else 'unknown',
                "error": str(e),
                "status": "error"
            }
            log_operation(logs_dir, error_log_data)
            print(f"Error processing file: {str(e)}")

    # Update dashboard with all activities
    if all_activity_entries:
        try:
            safe_update_dashboard(dashboard_file, all_activity_entries)
            print(f"Dashboard updated with {len(all_activity_entries)} activity entries.")
        except Exception as e:
            print(f"Error updating dashboard: {str(e)}")


def main():
    """Main function to run the orchestrator."""
    print("Starting Orchestrator...")
    print("Scanning Needs_Action folder for markdown files...")

    process_needs_action_files()

    print("Orchestrator completed.")


if __name__ == "__main__":
    main()