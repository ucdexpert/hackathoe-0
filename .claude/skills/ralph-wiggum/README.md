# Ralph Wiggum Autonomous Loop - Quick Start Guide

## 🚀 Overview

The **Ralph Wiggum Autonomous Loop** automatically executes tasks with persistent step-by-step processing:

1. **Analyzes** the task
2. **Creates** a Plan.md
3. **Executes** first step
4. **Checks** result
5. **Continues** to next step
6. **Repeats** until completed
7. **Moves** task to Done

**Safety Features:**
- ✅ Max 5 iterations (configurable)
- ✅ Human approval for risky actions
- ✅ Dry run mode for testing
- ✅ Comprehensive error logging

## 📁 How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Ralph Wiggum Autonomous Loop                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Analyze Task ←────────────────────────────┐        │
│     ↓                                         │        │
│  2. Create Plan.md                            │        │
│     ↓                                         │        │
│  3. Execute First Step                        │        │
│     ↓                                         │        │
│  4. Check Result                              │        │
│     ↓                                         │        │
│  5. Continue Next Step                        │        │
│     ↓                                         │        │
│  6. More Steps? ──Yes──→ Step 3               │        │
│     ↓ No                                      │        │
│  7. Move to Done                              │        │
│     ↓                                         │        │
│  8. Complete ─────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Quick Start

### Process Next Available Task

```bash
cd D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault\scripts
python ralph_wiggum.py run
```

### Process Specific Task

```bash
python ralph_wiggum.py run --task Needs_Action/email_request.md
```

### Test Mode (Dry Run)

```bash
python ralph_wiggum.py run --dry-run
```

### Custom Settings

```bash
python ralph_wiggum.py run --max-iterations 3 --no-approval
```

## ⏰ Automatic Scheduling

### Windows - One-Click Setup

```batch
# Run from scripts directory
setup_ralph_wiggum_scheduler.bat install
```

This sets up automatic execution:
- **When:** Every hour
- **Where:** Task Scheduler
- **Task Name:** Ralph_Wiggum_Autonomous_Loop

### Manual Windows Setup

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **"Create Basic Task..."**
3. Name: `Ralph Wiggum Autonomous Loop`
4. Trigger: **Hourly**
5. Action: **Start a program**
6. Program: `C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe`
7. Arguments: `"D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault\scripts\ralph_wiggum.py" run`

### Linux/Mac - Cron Setup

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths)
0 * * * * cd /path/to/vault && python scripts/ralph_wiggum.py run
```

## 📊 Command Reference

| Command | Description |
|---------|-------------|
| `run` | Process next task |
| `run --task file.md` | Process specific task |
| `run --dry-run` | Test without changes |
| `run --max-iterations 3` | Custom iteration limit |
| `stats` | Show execution statistics |
| `setup-scheduler` | Setup Windows Task Scheduler |
| `test` | Test loop (dry run) |

## 🔍 Task Detection

The loop automatically detects task types:

| Keywords | Task Type | Risk Level | Approval Required |
|----------|-----------|------------|-------------------|
| email, send, recipient | Email | Medium | ✅ Yes |
| linkedin, post, social | Social Media | Medium | ✅ Yes |
| payment, money, transfer | Financial | High | ✅ Yes |
| delete, remove, destroy | Destructive | High | ✅ Yes |
| (other) | General | Low | ❌ No |

## 📋 Plan.md Structure

Generated plans include:

```markdown
# Execution Plan: task_name.md

**Created:** 2026-02-18 10:00:00
**Task Type:** email
**Risk Level:** medium
**Max Iterations:** 5

## Steps
- [ ] Step 1: Analyze email content
- [ ] Step 2: Validate recipient
- [ ] Step 3: Prepare draft
- [ ] Step 4: Request approval
- [ ] Step 5: Send email
- [ ] Step 6: Log activity

## Execution Log
| Iteration | Step | Status | Timestamp |
|-----------|------|--------|-----------|
| 1 | 1 | completed | 10:00:01 |
```

## 🛡️ Safety Features

### 1. Iteration Limit
- **Default:** 5 iterations maximum
- **Purpose:** Prevents infinite loops
- **Custom:** `--max-iterations 3`

### 2. Human Approval
- **Required for:** Risky operations (email, financial, destructive)
- **Process:** Creates approval request in `Needs_Approval/`
- **Disable:** `--no-approval` (not recommended)

### 3. Dry Run Mode
- **Test:** `--dry-run`
- **Effect:** Simulates without making changes
- **Use:** Testing and validation

### 4. Error Handling
- All errors logged to `Logs/ralph_wiggum.log`
- Failed tasks remain in `Needs_Action`
- Detailed execution tracking

## 📈 Monitoring

### View Statistics

```bash
python ralph_wiggum.py stats
```

**Output:**
```
============================================================
Ralph Wiggum Statistics
============================================================
Total Executions: 10
Successful: 8
Failed: 2
Total Iterations: 45
Average Iterations: 4.5
============================================================
```

### View Execution Logs

```bash
# Windows PowerShell
Get-Content ..\Logs\ralph_wiggum.log -Tail 20

# Linux/Mac
tail -20 ../Logs/ralph_wiggum.log
```

### Check Task Status

```bash
# Check what's in Needs_Action
dir ..\Needs_Action

# Check recent completions
dir ..\Done
```

## 🔗 Integration with Other Skills

Ralph Wiggum works with:

| Skill | Integration |
|-------|-------------|
| `error-recovery` | Automatic error handling |
| `ceo-briefing` | Reports task completion |
| `accounting-manager` | Processes financial tasks |
| `mcp/business_mcp` | Executes email/LinkedIn tasks |

## 🎯 Best Practices

1. **Review Plans** - Check generated Plan.md files
2. **Monitor Logs** - Review ralph_wiggum.log regularly
3. **Start with Dry Run** - Test new task types first
4. **Keep Approval Enabled** - Safety first!
5. **Clear Completed** - Archive Done folder periodically

## 🔍 Troubleshooting

**No tasks processed:**
- Check Needs_Action folder has .md files
- Ensure files don't start with "Plan_"
- Verify file permissions

**Max iterations reached:**
- Task may be too complex
- Increase with `--max-iterations 10`
- Review task for issues

**Approval requests piling up:**
- Review Needs_Approval folder
- Approve or reject pending requests
- Consider adjusting risk detection

**Loop not running automatically:**
- Check Task Scheduler status
- Verify Python path in task
- Review ralph_wiggum.log for errors

## 📞 Support

**View Help:**
```bash
python ralph_wiggum.py --help
```

**Test System:**
```bash
python ralph_wiggum.py test
```

**Check Scheduler:**
```bash
setup_ralph_wiggum_scheduler.bat status
```

**Remove Scheduler:**
```bash
setup_ralph_wiggum_scheduler.bat uninstall
```

## 🔗 Claude Integration

Once installed in `.claude/skills/ralph-wiggum/`, Claude can:

- Run autonomous loop on demand
- Explain task execution progress
- Generate execution reports
- Adjust loop parameters
- Analyze execution logs

**Example Claude Requests:**
- "Process the next task in Needs_Action"
- "How many iterations did the last task take?"
- "Show me the execution plan for task X"
- "Run Ralph Wiggum in dry run mode"

---

**Your Ralph Wiggum Autonomous Loop is ready!** 🎉

Run `python ralph_wiggum.py run` to start autonomous task execution.
