# vault-file-manager

## Description
A Claude Agent Skill for safely managing local vault file operations. Handles file movements between vault folders with comprehensive safety measures, duplicate prevention, and structured JSON logging.

## Parameters
- `source_path` (string, required): The source file path or folder name
- `destination_path` (string, required): The destination file path or folder name
- `operation` (string, optional): The operation type (move, copy, create_folder). Default: "move"

## Functionality
When invoked, this skill:
1. Moves files between vault folders (Inbox, Needs_Action, Plans, Done, Logs, Approvals)
2. Creates folders if they don't exist
3. Prevents file overwriting with safe duplicate handling
4. Prevents any file deletion operations
5. Logs all actions in structured JSON format
6. Complies with Silver Tier requirements

## Constraints
- No external API calls
- No file deletion allowed (ever)
- Must handle duplicate filenames safely
- Local vault operations only
- Silver Tier compliant

## Vault Folders
```
AI_Employee_Vault/
├── Inbox/           # Incoming files
├── Needs_Action/    # Files requiring action
├── Plans/          # Plan files
├── Done/           # Completed tasks
├── Logs/           # Operation logs
└── Approvals/      # Pending approvals
```

## Implementation
```python
import os
import json
import shutil
from datetime import datetime

# Define vault folder paths
VAULT_FOLDERS = [
    "Inbox",
    "Needs_Action",
    "Plans",
    "Done",
    "Logs",
    "Approvals"
]

def vault_file_manager_skill(source_path, destination_path, operation="move"):
    """
    Safely manages local vault file operations.
    
    Args:
        source_path (str): Source file path or folder name
        destination_path (str): Destination file path or folder name
        operation (str): Operation type - "move", "copy", or "create_folder"
    
    Returns:
        dict: Operation result with status and details
    """
    logs_dir = "Logs"
    
    # Ensure Logs directory exists
    ensure_folders_exist([logs_dir])
    
    result = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "operation": operation,
        "source": source_path,
        "destination": destination_path,
        "status": "pending",
        "details": ""
    }
    
    try:
        # Validate folders
        source_folder, source_file = parse_path(source_path)
        dest_folder, dest_file = parse_path(destination_path)
        
        # Validate folder names
        if source_folder and source_folder not in VAULT_FOLDERS:
            raise ValueError(f"Invalid source folder: {source_folder}")
        if dest_folder and dest_folder not in VAULT_FOLDERS:
            raise ValueError(f"Invalid destination folder: {dest_folder}")
        
        # Ensure destination folder exists
        if dest_folder:
            ensure_folders_exist([dest_folder])
        
        # Execute operation
        if operation == "create_folder":
            result = execute_create_folder(dest_folder, dest_file, result, logs_dir)
        elif operation == "move":
            result = execute_move(source_path, destination_path, result, logs_dir)
        elif operation == "copy":
            result = execute_copy(source_path, destination_path, result, logs_dir)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
    except Exception as e:
        result["status"] = "error"
        result["details"] = str(e)
        result["error"] = str(e)
    
    # Log the operation
    log_operation(logs_dir, result)
    
    return result

def parse_path(path):
    """
    Parses a path into folder and file components.
    
    Args:
        path (str): Path to parse
    
    Returns:
        tuple: (folder_name, file_name)
    """
    if not path:
        return None, None
    
    # Check if path contains a folder separator
    if os.sep in path:
        parts = path.split(os.sep)
        if len(parts) == 2:
            return parts[0], parts[1]
        elif len(parts) > 2:
            return parts[-2], parts[-1]
    
    # Check if it's a folder name
    if path in VAULT_FOLDERS:
        return path, None
    
    # Assume it's a filename
    return None, path

def ensure_folders_exist(folders):
    """
    Creates folders if they don't exist.
    
    Args:
        folders (list): List of folder names to create
    """
    for folder in folders:
        if folder and folder in VAULT_FOLDERS:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)

def execute_create_folder(folder_name, subfolder, result, logs_dir):
    """
    Executes a folder creation operation.
    
    Args:
        folder_name (str): Parent folder name
        subfolder (str): Subfolder to create
        result (dict): Result dictionary to update
        logs_dir (str): Logs directory path
    
    Returns:
        dict: Updated result dictionary
    """
    if not folder_name:
        raise ValueError("Folder name is required for create_folder operation")
    
    # Ensure parent folder exists
    ensure_folders_exist([folder_name])
    
    # Create subfolder if specified
    if subfolder:
        folder_path = os.path.join(folder_name, subfolder)
    else:
        folder_path = folder_name
    
    if os.path.exists(folder_path):
        result["status"] = "success"
        result["details"] = f"Folder already exists: {folder_path}"
        result["warning"] = "Folder already exists - no action taken"
    else:
        os.makedirs(folder_path, exist_ok=True)
        result["status"] = "success"
        result["details"] = f"Folder created: {folder_path}"
    
    return result

def execute_move(source_path, destination_path, result, logs_dir):
    """
    Executes a file move operation with safety checks.
    
    Args:
        source_path (str): Source file path
        destination_path (str): Destination file path
        result (dict): Result dictionary to update
        logs_dir (str): Logs directory path
    
    Returns:
        dict: Updated result dictionary
    """
    # Check if source exists
    if not os.path.exists(source_path):
        # Try with folder prefix
        source_folder, source_file = parse_path(source_path)
        if source_folder and source_file:
            full_source = os.path.join(source_folder, source_file)
            if os.path.exists(full_source):
                source_path = full_source
            else:
                raise FileNotFoundError(f"Source file not found: {source_path}")
        else:
            raise FileNotFoundError(f"Source file not found: {source_path}")
    
    # Check if source is a file (not a directory)
    if os.path.isdir(source_path):
        raise ValueError("Cannot move directories - only files are supported")
    
    # Determine destination
    dest_folder, dest_file = parse_path(destination_path)
    
    if dest_folder:
        # Ensure destination folder exists
        ensure_folders_exist([dest_folder])
        
        if dest_file:
            destination = os.path.join(dest_folder, dest_file)
        else:
            # Move to folder with same filename
            filename = os.path.basename(source_path)
            destination = os.path.join(dest_folder, filename)
    else:
        destination = destination_path
    
    # Handle duplicate filenames safely
    if os.path.exists(destination):
        destination = generate_safe_filename(destination)
        result["warning"] = "Duplicate filename detected - renamed to prevent overwrite"
    
    # Move the file
    shutil.move(source_path, destination)
    
    result["status"] = "success"
    result["details"] = f"File moved from {source_path} to {destination}"
    result["destination"] = destination
    
    return result

def execute_copy(source_path, destination_path, result, logs_dir):
    """
    Executes a file copy operation with safety checks.
    
    Args:
        source_path (str): Source file path
        destination_path (str): Destination file path
        result (dict): Result dictionary to update
        logs_dir (str): Logs directory path
    
    Returns:
        dict: Updated result dictionary
    """
    # Check if source exists
    if not os.path.exists(source_path):
        # Try with folder prefix
        source_folder, source_file = parse_path(source_path)
        if source_folder and source_file:
            full_source = os.path.join(source_folder, source_file)
            if os.path.exists(full_source):
                source_path = full_source
            else:
                raise FileNotFoundError(f"Source file not found: {source_path}")
        else:
            raise FileNotFoundError(f"Source file not found: {source_path}")
    
    # Check if source is a file (not a directory)
    if os.path.isdir(source_path):
        raise ValueError("Cannot copy directories - only files are supported")
    
    # Determine destination
    dest_folder, dest_file = parse_path(destination_path)
    
    if dest_folder:
        # Ensure destination folder exists
        ensure_folders_exist([dest_folder])
        
        if dest_file:
            destination = os.path.join(dest_folder, dest_file)
        else:
            # Copy to folder with same filename
            filename = os.path.basename(source_path)
            destination = os.path.join(dest_folder, filename)
    else:
        destination = destination_path
    
    # Handle duplicate filenames safely
    if os.path.exists(destination):
        destination = generate_safe_filename(destination)
        result["warning"] = "Duplicate filename detected - renamed to prevent overwrite"
    
    # Copy the file
    shutil.copy2(source_path, destination)
    
    result["status"] = "success"
    result["details"] = f"File copied from {source_path} to {destination}"
    result["destination"] = destination
    
    return result

def generate_safe_filename(filepath):
    """
    Generates a safe filename to prevent overwriting.
    
    Args:
        filepath (str): Original filepath
    
    Returns:
        str: New filepath with unique filename
    """
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)
    
    # Generate timestamp-based unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    new_filename = f"{name}_copy_{timestamp}{ext}"
    
    return os.path.join(directory, new_filename)

def log_operation(logs_dir, operation_data):
    """
    Logs an operation in structured JSON format.
    
    Args:
        logs_dir (str): Directory for log files
        operation_data (dict): Operation data to log
    """
    try:
        # Ensure logs directory exists
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Create daily log file
        log_filename = f"vault_file_manager_{datetime.now().strftime('%Y%m%d')}.json"
        log_filepath = os.path.join(logs_dir, log_filename)
        
        # Read existing logs
        existing_logs = []
        if os.path.exists(log_filepath):
            with open(log_filepath, 'r', encoding='utf-8') as f:
                try:
                    existing_logs = json.load(f)
                except json.JSONDecodeError:
                    existing_logs = []
        
        # Append new log entry
        existing_logs.append(operation_data)
        
        # Write back to file
        with open(log_filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_logs, f, indent=2, default=str)
    
    except Exception as e:
        # If logging fails, print error but don't fail the operation
        print(f"Warning: Failed to log operation: {str(e)}")

# Convenience functions for common operations

def move_from_inbox_to_needs_action(filename):
    """
    Moves a file from Inbox to Needs_Action.
    
    Args:
        filename (str): Name of the file in Inbox
    
    Returns:
        dict: Operation result
    """
    source = os.path.join("Inbox", filename)
    return vault_file_manager_skill(source, "Needs_Action", operation="move")

def move_from_needs_action_to_plans(filename):
    """
    Moves a file from Needs_Action to Plans.
    
    Args:
        filename (str): Name of the file in Needs_Action
    
    Returns:
        dict: Operation result
    """
    source = os.path.join("Needs_Action", filename)
    return vault_file_manager_skill(source, "Plans", operation="move")

def move_from_needs_action_to_done(filename):
    """
    Moves a file from Needs_Action to Done.
    
    Args:
        filename (str): Name of the file in Needs_Action
    
    Returns:
        dict: Operation result
    """
    source = os.path.join("Needs_Action", filename)
    return vault_file_manager_skill(source, "Done", operation="move")

def move_to_approvals(filename):
    """
    Moves a file to the Approvals folder.
    
    Args:
        filename (str): Name of the file to move
    
    Returns:
        dict: Operation result
    """
    source = filename if os.path.exists(filename) else os.path.join("Needs_Action", filename)
    return vault_file_manager_skill(source, "Approvals", operation="move")

def create_approval_subfolder(folder_name):
    """
    Creates a subfolder in the Approvals folder.
    
    Args:
        folder_name (str): Name of the subfolder to create
    
    Returns:
        dict: Operation result
    """
    return vault_file_manager_skill(None, f"Approvals/{folder_name}", operation="create_folder")

# Execute the skill when called
if __name__ == "__main__":
    # Example usage
    print("Vault File Manager - Example Operations")
    print("=" * 50)
    
    # Example 1: Move file from Inbox to Needs_Action
    # result = move_from_inbox_to_needs_action("test_file.txt")
    # print(f"Move result: {result}")
    
    # Example 2: Create a folder
    # result = vault_file_manager_skill(None, "Approvals", operation="create_folder")
    # print(f"Create folder result: {result}")
    
    # Example 3: Copy a file
    # result = vault_file_manager_skill("Inbox/test.txt", "Plans/test_copy.txt", operation="copy")
    # print(f"Copy result: {result}")
    
    print("Vault File Manager skill loaded successfully.")
    print("Available vault folders:", VAULT_FOLDERS)
```

## Usage Examples

### Example 1: Move File from Inbox to Needs_Action
```python
result = vault_file_manager_skill(
    source_path="Inbox/new_task.txt",
    destination_path="Needs_Action",
    operation="move"
)
# Returns: {"status": "success", "details": "File moved from Inbox/new_task.txt to Needs_Action/new_task.txt"}
```

### Example 2: Copy File to Plans
```python
result = vault_file_manager_skill(
    source_path="Needs_Action/task.md",
    destination_path="Plans/task_plan.md",
    operation="copy"
)
# Returns: {"status": "success", "details": "File copied from Needs_Action/task.md to Plans/task_plan.md"}
```

### Example 3: Create Subfolder
```python
result = vault_file_manager_skill(
    source_path=None,
    destination_path="Approvals/pending_reviews",
    operation="create_folder"
)
# Returns: {"status": "success", "details": "Folder created: Approvals/pending_reviews"}
```

### Example 4: Handle Duplicate Filename
```python
# If Plans/report.md already exists
result = vault_file_manager_skill(
    source_path="Inbox/report.md",
    destination_path="Plans/report.md",
    operation="move"
)
# Returns: {"status": "success", "details": "...", "warning": "Duplicate filename detected - renamed to prevent overwrite"}
# File will be saved as: Plans/report_copy_20240115_103000_123456.md
```

## Safety Features

| Feature | Implementation |
|---------|---------------|
| No File Deletion | Only move/copy operations - files are never deleted |
| Duplicate Prevention | Automatic filename generation with timestamp |
| Folder Creation | Auto-creates missing vault folders |
| Validation | Validates folder names against allowed list |
| Logging | All operations logged in structured JSON |
| Error Handling | Comprehensive try/except blocks |

## Log Format
```json
{
  "timestamp": "2024-01-15 10:30:00",
  "operation": "move",
  "source": "Inbox/task.txt",
  "destination": "Needs_Action/task.txt",
  "status": "success",
  "details": "File moved from Inbox/task.txt to Needs_Action/task.txt"
}
```

## Compliance Notes

- **Silver Tier Compliant:** Yes
- **External API Calls:** None
- **File Deletion:** Never performed
- **Duplicate Handling:** Safe timestamp-based renaming
- **Local Operations Only:** Yes
- **Structured Logging:** JSON format with timestamps