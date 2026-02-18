import os
import time
from datetime import datetime
import logging
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileCreatedHandler(FileSystemEventHandler):
    """Handles file creation events in the watched directory."""
    
    def __init__(self, inbox_dir, needs_action_dir):
        self.inbox_dir = inbox_dir
        self.needs_action_dir = needs_action_dir
        self.processed_files = set()  # Track processed files to prevent duplicates
        
    def on_created(self, event):
        """Called when a file is created in the watched directory."""
        if not event.is_directory:
            # Process the newly created file
            self.process_new_file(event.src_path)
    
    def process_new_file(self, file_path):
        """Process a new file by creating a markdown report."""
        try:
            # Check if file was already processed to prevent duplicates
            abs_path = os.path.abspath(file_path)
            if abs_path in self.processed_files:
                logging.info(f"File {file_path} already processed, skipping duplicate.")
                return
                
            # Get file information
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create markdown content
            markdown_content = f"""# New File Detected

**Filename:** {filename}
**File Size:** {file_size} bytes
**Timestamp:** {timestamp}
**Status:** pending
"""
            
            # Create markdown file in Needs_Action directory
            markdown_filename = f"{os.path.splitext(filename)[0]}_report.md"
            markdown_path = os.path.join(self.needs_action_dir, markdown_filename)
            
            # Write the markdown file
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
                
            # Mark file as processed
            self.processed_files.add(abs_path)
            
            # Log the operation in JSON format
            log_entry = {
                "timestamp": timestamp,
                "event_type": "file_processed",
                "original_file": file_path,
                "created_report": markdown_path,
                "file_size": file_size,
                "status": "success"
            }
            self.log_json_operation(log_entry)
            
            logging.info(f"Created report for '{filename}' in Needs_Action folder")
            
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
        except PermissionError:
            logging.error(f"Permission denied when processing file: {file_path}")
        except OSError as e:
            logging.error(f"OS error when processing file {file_path}: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error processing file {file_path}: {str(e)}")
    
    def log_json_operation(self, log_entry):
        """Log operation in JSON format to a dedicated log file."""
        try:
            logs_dir = "Logs"
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            log_file = os.path.join(logs_dir, f"filesystem_watcher_{datetime.now().strftime('%Y%m%d')}.json")
            
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
                
        except Exception as e:
            logging.error(f"Failed to write JSON log: {str(e)}")


def ensure_directories_exist(inbox_dir, needs_action_dir):
    """Ensure that required directories exist, create if missing."""
    directories = [inbox_dir, needs_action_dir]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Created directory: {directory}")


def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('filesystem_watcher.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main function to start the file system watcher."""
    # Define directory paths
    inbox_dir = "Inbox"
    needs_action_dir = "Needs_Action"
    
    # Setup logging
    setup_logging()
    
    # Ensure directories exist
    ensure_directories_exist(inbox_dir, needs_action_dir)
    
    # Create event handler
    event_handler = FileCreatedHandler(inbox_dir, needs_action_dir)
    
    # Create observer
    observer = Observer()
    observer.schedule(event_handler, inbox_dir, recursive=False)
    
    # Start the observer
    observer.start()
    logging.info("File system watcher started. Monitoring 'Inbox' folder...")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("File system watcher stopped by user.")
    
    observer.join()


if __name__ == "__main__":
    main()