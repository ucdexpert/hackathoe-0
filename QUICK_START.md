# 🚀 AI Employee Vault - Quick Start Card

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
pip install watchdog playwright python-dotenv tabulate
playwright install
```

### 2. Configure Credentials
Edit `.env` file:
```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-app-password
LINKEDIN_EMAIL=your.linkedin@email.com
LINKEDIN_PASSWORD=your-password
```

### 3. Start Core Services
```bash
# Terminal 1: Filesystem Watcher
python filesystem_watcher.py

# Terminal 2: Ralph Wiggum (Autonomous Loop)
python scripts/ralph_wiggum.py run

# Terminal 3: MCP Server
cd mcp/business_mcp && python server.py
```

---

## 📋 Common Commands

### Task Processing
```bash
# Process next task autonomously
python scripts/ralph_wiggum.py run

# Process specific task
python scripts/ralph_wiggum.py run --task Needs_Action/email.md

# Manual orchestration
python orchestrator.py
```

### Email
```bash
# Send email
python scripts/send_email.py --to client@example.com --subject "Hello" --body "Message"

# Via MCP
cd mcp/business_mcp
python server.py --test-email
```

### LinkedIn
```bash
# Post to LinkedIn
python scripts/post_linkedin.py --content "Business update #innovation"

# Log to social summary
python scripts/social_summary.py log -p linkedin -c "Post content" --engagement "{\"likes\": 50}"
```

### Accounting
```bash
# Log income
python scripts/accounting_manager.py log -t income -a 5000 -d "Product sales" -c sales

# Log expense
python scripts/accounting_manager.py log -t expense -a 2000 -d "Office rent" -c rent

# View summary
python scripts/accounting_manager.py summary
```

### Reports
```bash
# Generate CEO Weekly Briefing
python scripts/ceo_briefing.py generate

# View social media summary
python scripts/social_summary.py summary --days 7

# View recent social posts
python scripts/social_summary.py recent --limit 10
```

### Error Handling
```bash
# View recent errors
python scripts/error_recovery.py recent

# View error statistics
python scripts/error_recovery.py stats --days 7

# Clear old errors
python scripts/error_recovery.py clear --days-old 30
```

---

## ⏰ Setup Automatic Scheduling

### Windows Task Scheduler
```bash
# CEO Briefing - Every Monday 8 AM
python scripts/ceo_briefing.py setup-scheduler

# Ralph Wiggum - Every hour
python scripts/ralph_wiggum.py setup-scheduler

# Or use batch files
scripts\setup_ceo_briefing_scheduler.bat install
scripts\setup_ralph_wiggum_scheduler.bat install
```

### Linux/Mac Cron
```bash
crontab -e
# CEO Briefing - Every Monday 8 AM
0 8 * * 1 cd /path/to/vault && python scripts/ceo_briefing.py generate

# Ralph Wiggum - Every hour
0 * * * * cd /path/to/vault && python scripts/ralph_wiggum.py run
```

---

## 📊 Monitoring Commands

### Check System Status
```bash
# View Dashboard
cat Dashboard.md

# Check pending tasks
dir Needs_Action

# Check pending approvals
dir Needs_Approval

# View recent completions
dir Done
```

### View Logs
```bash
# Error logs
Get-Content Logs\errors.log -Tail 20

# Ralph Wiggum execution
Get-Content Logs\ralph_wiggum.log -Tail 20

# Business activities
Get-Content Logs\business.log -Tail 20

# Accounting
Get-Content Accounting\logs\accounting.log -Tail 20
```

### Statistics
```bash
# Ralph Wiggum stats
python scripts/ralph_wiggum.py stats

# Social media summary
python scripts/social_summary.py summary --days 7

# Error statistics
python scripts/error_recovery.py stats
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Test Individual Components
```bash
# Filesystem Watcher
pytest tests/test_filesystem_watcher.py -v

# MCP Executor
pytest tests/test_mcp_executor.py -v

# Orchestrator
pytest tests/test_orchestrator.py -v

# Send Email
pytest tests/test_send_email.py -v
```

### Test Scripts
```bash
# Error recovery test
python scripts/error_recovery.py test

# Ralph Wiggum test (dry run)
python scripts/ralph_wiggum.py test

# MCP Server test
cd mcp/business_mcp
python server.py --status
```

---

## 📁 Important Files & Folders

### Configuration
- `.env` - Your credentials (DO NOT COMMIT)
- `requirements.txt` - Python dependencies
- `claude_desktop_config.json` - Claude Desktop MCP config

### Core Scripts
- `filesystem_watcher.py` - Monitors Inbox
- `orchestrator.py` - Processes tasks
- `scripts/ralph_wiggum.py` - Autonomous loop
- `scripts/ceo_briefing.py` - Weekly reports
- `mcp/business_mcp/server.py` - MCP server

### Skills (14 Total)
Located in `.claude/skills/`:
- accounting-manager
- ceo-briefing
- error-recovery
- human-approval
- linkedin-post
- mcp-executor
- ralph-wiggum
- social-summary
- task-planner
- vault-file-manager
- vault-watcher
- ...and 3 more

### Data Folders
- `Inbox/` - New files trigger processing
- `Needs_Action/` - Tasks pending action
- `Plans/` - Generated execution plans
- `Done/` - Completed tasks
- `Needs_Approval/` - Pending approvals
- `Approved/` - Approved items
- `Rejected/` - Rejected items
- `Errors/` - Quarantined files
- `Accounting/` - Financial records
- `Reports/` - Generated reports
- `Logs/` - Audit logs

### Key Reports
- `Dashboard.md` - Main dashboard
- `Reports/CEO_Weekly_Week_X.md` - Weekly executive reports
- `Reports/Social_Log.md` - Social media activity log
- `Accounting/Current_Month.md` - Monthly financial records

---

## 🔧 Troubleshooting

### Watcher Not Detecting Files
```bash
# Check Inbox folder exists
dir Inbox

# Check watcher log
Get-Content filesystem_watcher.log -Tail 20

# Restart watcher
python filesystem_watcher.py
```

### Tasks Not Processing
```bash
# Check Needs_Action folder
dir Needs_Action

# Run Ralph Wiggum manually
python scripts/ralph_wiggum.py run

# Check execution log
Get-Content Logs\ralph_wiggum.log -Tail 20
```

### MCP Server Not Starting
```bash
# Check MCP installed
pip show mcp

# Check server status
cd mcp/business_mcp
python server.py --status

# Check logs
Get-Content ..\..\Logs\business.log -Tail 20
```

### Email Not Sending
```bash
# Verify .env credentials
cat .env | findstr EMAIL

# Test email
python scripts/send_email.py --test

# Check SMTP settings
# EMAIL_ADDRESS must be Gmail
# EMAIL_PASSWORD must be App Password (not regular password)
```

### LinkedIn Not Posting
```bash
# Check Playwright installed
playwright install

# Test posting
python scripts/post_linkedin.py --content "Test"

# Check credentials in .env
```

---

## 📞 Quick Help

### View Help
```bash
# General help
python scripts/ralph_wiggum.py --help

# Specific command help
python scripts/ceo_briefing.py --help
```

### Project Documentation
- `README.md` - Project overview
- `PROJECT_AUDIT.md` - Complete audit and status
- `TEST_REPORT.md` - Test results
- `mcp/business_mcp/README.md` - MCP server docs

### Skill Documentation
Each skill has documentation in `.claude/skills/[skill-name]/`:
- `SKILL.md` - Full skill documentation
- Usage examples
- Parameters and return values

---

## 🎯 Daily Workflow

### Morning (5 minutes)
```bash
# 1. Check Dashboard
cat Dashboard.md

# 2. Check pending approvals
dir Needs_Approval

# 3. Run Ralph Wiggum
python scripts/ralph_wiggum.py run
```

### Weekly (15 minutes - Monday)
```bash
# 1. Generate CEO Briefing
python scripts/ceo_briefing.py generate

# 2. Review Social Log
cat Reports\Social_Log.md

# 3. Review Accounting
python scripts/accounting_manager.py summary

# 4. Clear old errors
python scripts/error_recovery.py clear --days-old 30
```

### Monthly (30 minutes)
```bash
# 1. Review all logs
Get-Content Logs\errors.log | Measure-Object -Line

# 2. Archive old reports
# Move old Reports/ to archive folder

# 3. Update credentials if needed
# Edit .env file
```

---

## ✅ Project Status

**Bronze Tier:** ✅ 100% COMPLETE  
**Silver Tier:** ✅ 100% COMPLETE  
**Gold Tier:** ⚠️ 56% COMPLETE (5/9 features)

**Overall:** 82% Complete (18/22 requirements)

See `PROJECT_AUDIT.md` for detailed status.

---

**Happy Automating! 🤖**
