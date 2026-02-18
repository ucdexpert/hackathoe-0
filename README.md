# AI Employee Vault System

A comprehensive file management system that automates task processing and workflow management using a folder-based approach.

## Overview

The AI Employee Vault System consists of three main components:

1. **Filesystem Watcher** - Monitors the Inbox folder and creates reports for new files
2. **Orchestrator** - Processes files in the Needs_Action folder and manages workflows
3. **Process Tasks Skill** - A Claude Agent skill for manual task processing

## Prerequisites

- Python 3.7 or higher
- `watchdog` library (for filesystem monitoring)

## Installation

1. Clone or download this repository to your local machine
2. Install the required dependencies:

```bash
pip install watchdog
```

## Components

### 1. Filesystem Watcher (`filesystem_watcher.py`)

Monitors the `Inbox` folder for new files and automatically creates markdown reports in the `Needs_Action` folder.

**Features:**
- Watches for new files in the Inbox folder
- Creates detailed reports with filename, size, timestamp, and status
- Automatic folder creation if missing
- Basic logging functionality
- Error handling to prevent crashes

**To run:**
```bash
python filesystem_watcher.py
```

The script will continuously monitor the Inbox folder. Press `Ctrl+C` to stop the watcher.

### 2. Orchestrator (`orchestrator.py`)

Processes markdown files in the `Needs_Action` folder by creating plan files, updating the dashboard, and moving processed files to the `Done` folder.

**Features:**
- Scans Needs_Action folder for markdown files
- Creates plan files in the Plans folder with checklist steps
- Moves processed files to the Done folder
- Logs all operations in JSON format to the Logs folder
- Updates Dashboard.md with recent activity

**To run:**
```bash
python orchestrator.py
```

### 3. Process Tasks Skill (`process_tasks_skill.md`)

A Claude Agent skill that provides the same functionality as the orchestrator but designed for integration with Claude.

**Features:**
- Reads all files inside the Needs_Action folder
- Creates Plan files inside the Plans folder
- Updates Dashboard.md with new entries under Recent Activity
- Moves completed tasks to Done folder
- Includes safety measures to prevent duplicate processing

**To use:**
Copy the Python code from the Implementation section in `process_tasks_skill.md` and integrate it with Claude as a custom skill.

## Folder Structure

The system uses the following folder structure:

```
AI_Employee_Vault/
├── Inbox/              # Files placed here trigger automatic reports
├── Needs_Action/       # Files requiring action (reports created by watcher)
├── Plans/             # Generated action plans
├── Done/              # Completed tasks
├── Logs/              # Operation logs in JSON format
├── Dashboard.md       # Dashboard with recent activity
├── Company_Handbook.md # Company policies and procedures
├── filesystem_watcher.py
├── orchestrator.py
├── process_tasks_skill.md
└── README.md          # This file
```

## How to Use

### Basic Workflow

1. Place files in the `Inbox` folder
2. Run `filesystem_watcher.py` to generate reports in `Needs_Action`
3. Run `orchestrator.py` to process files and create plans
4. Monitor progress in `Dashboard.md`

### Step-by-Step Example

1. **Start the filesystem watcher:**
   ```bash
   python filesystem_watcher.py
   ```

2. **Place a new file in the `Inbox` folder** - the watcher will automatically detect it and create a report in `Needs_Action`

3. **Stop the watcher** (Ctrl+C) and run the orchestrator:
   ```bash
   python orchestrator.py
   ```

4. **Check the results:**
   - Plan files will appear in the `Plans` folder
   - Processed files will move to the `Done` folder
   - Activity will be logged in `Logs` folder
   - Dashboard will update with recent activity

## Safety Features

- No files are deleted - they are moved between folders
- Duplicate processing prevention
- Comprehensive error handling
- Safe dashboard updates with backup mechanism
- Structured JSON logging

## Troubleshooting

- If the watcher doesn't detect new files, ensure the `Inbox` folder exists
- Check the log files in the `Logs` folder for error details
- Make sure you have write permissions for all folders
- If Dashboard.md becomes corrupted, you can safely delete it and it will be recreated

## License

This project is available for use under the terms of the MIT License.