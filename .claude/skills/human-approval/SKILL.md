# human-approval

## Description
Human-in-the-loop approval for sensitive actions. Creates approval request files and waits for APPROVED/REJECTED status.

## Usage
```bash
python .claude/skills/human-approval/scripts/request_approval.py --action email --data '{"to":"user@example.com"}'
python .claude/skills/human-approval/scripts/request_approval.py --request-id email_20260218_123456 --check
```

## Inputs
- `--action`: Action type (email/linkedin/file_operation)
- `--data`: JSON action data
- `--request-id`: Existing request ID to check
- `--check`: Check status of existing request
- `--timeout`: Timeout in minutes (default: 60)

## Output
```
SUCCESS: Action approved
Request ID: email_20260218_123456
Status: APPROVED
```

## Workflow
1. Creates file in `Needs_Approval/`
2. Human edits file: `status: APPROVED` or `status: REJECTED`
3. Script polls for status change
4. Returns result, moves file to Approved/Rejected

## Timeout
Default 60 minutes. Timed-out requests move to `Needs_Action/`.
