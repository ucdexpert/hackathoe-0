# vault-file-manager

## Description
Manage task workflow by moving files between vault folders. Handles Inbox → Needs_Action → Done pipeline.

## Folder Structure
```
AI_Employee_Vault/
├── Inbox/          # New files arrive here
├── Needs_Action/   # Files requiring attention
├── Plans/          # Generated action plans
└── Done/           # Completed items
```

## Usage
```bash
python .claude/skills/vault-file-manager/scripts/move_task.py --file document.pdf --to Needs_Action
python .claude/skills/vault-file-manager/scripts/move_task.py --file task.md --to Done
python .claude/skills/vault-file-manager/scripts/move_task.py --list Inbox
```

## Inputs
- `--file`: File to move (required for move operations)
- `--to`: Destination folder (Inbox/Needs_Action/Done)
- `--from`: Source folder (optional, auto-detected)
- `--list`: List files in a folder

## Output
```
SUCCESS: Moved document.pdf from Inbox to Needs_Action
Destination: AI_Employee_Vault/Needs_Action/document.pdf
```

## Operations
- `move`: Move file between folders
- `list`: List files in folder
- `status`: Show file count in each folder

## Error Handling
- File not found → ERROR: File not found
- Invalid folder → ERROR: Invalid destination folder
- File exists → ERROR: Destination file already exists
