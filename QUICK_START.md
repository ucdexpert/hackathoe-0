# AI Employee Vault - Quick Start Guide

**Status:** ✅ Silver Tier Complete (100%) | ⚠️ Gold Tier 56% Complete  
**Last Tested:** 2026-02-18 18:45:00  
**Grade:** A- (82%)

---

## 1-Minute Status Check

✅ **Working:**
- All 12 folders (Inbox, Needs_Action, Plans, Done, Logs, etc.)
- Dashboard.md & Company_Handbook.md
- 13 Agent Skills in .claude/skills/
- 4 MCP servers (business, email, social, fileops)
- 18 Python scripts
- Task workflow (create → plan → execute → complete)
- Logging system
- Claude Desktop configuration

⚠️ **Needs Configuration:**
- API credentials (11 total - all currently template values)
- Python dependencies (run install script)
- Playwright browsers (for LinkedIn automation)

❌ **Missing:**
- Odoo accounting integration (optional, 30-40 hours to implement)

---

## Quick Start (15 minutes)

### Step 1: Install Dependencies (5 minutes)

```bash
# Navigate to project
cd D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault

# Run installation script
install_all_mcps.bat

# Install Playwright browsers
playwright install chromium
```

### Step 2: Configure Credentials (5 minutes)

```bash
# Edit .env file
notepad .env
```

**Minimum Required (for email):**
```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

**Get Gmail App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Enable 2-Factor Authentication
3. Generate App Password for "Mail"
4. Copy 16-character password to .env

**Optional (for social media):**
- Twitter: developer.twitter.com
- Facebook: developers.facebook.com
- Instagram: Link to Facebook Page

### Step 3: Configure Claude Desktop (2 minutes)

```bash
# Copy config to Claude Desktop
copy claude_desktop_config.json %APPDATA%\Claude\

# Restart Claude Desktop
```

### Step 4: Test Basic Functionality (3 minutes)

```bash
# Test Email MCP
cd mcp\email_mcp
echo {"method": "validate_email", "params": {"email": "test@example.com"}} | python server.py

# Test FileOps MCP
cd mcp\fileops_mcp
echo {"method": "file.list_files", "params": {"directory": ".", "pattern": "*.md"}} | python server.py

# Test core workflow
cd D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault
python scripts\ralph_wiggum.py run
```

---

## Detailed Setup

### Core Components

**1. Filesystem Watcher** (Monitors Inbox)
```bash
python filesystem_watcher.py
# Runs continuously, watches Inbox/ folder
# Press Ctrl+C to stop
```

**2. Ralph Wiggum Autonomous Loop** (Processes tasks)
```bash
python scripts\ralph_wiggum.py run
# Processes tasks from Needs_Action/
# Creates plans, executes steps, moves to Done
```

**3. CEO Briefing** (Weekly reports)
```bash
python scripts\ceo_briefing.py generate
# Generates comprehensive weekly report
# Saves to Reports/CEO_Weekly.md
```

**4. Accounting Manager** (Track finances)
```bash
# Log income
python scripts\accounting_manager.py log -t income -a 5000 -d "Product sales" -c sales

# Log expense
python scripts\accounting_manager.py log -t expense -a 2000 -d "Office rent" -c rent

# View summary
python scripts\accounting_manager.py summary
```

### MCP Servers

**Business MCP** (Email + LinkedIn)
```bash
cd mcp\business_mcp
python server.py --status
```

**Email MCP** (Production email)
```bash
cd mcp\email_mcp
python test_server.py
```

**Social MCP** (Twitter/FB/Instagram)
```bash
cd mcp\social_mcp
python test_server.py
```

**FileOps MCP** (Browser + File ops)
```bash
cd mcp\fileops_mcp
python test_server.py
```

---

## Daily Operations

### Morning Routine (5 minutes)

```bash
# 1. Check Dashboard
type Dashboard.md

# 2. Check pending approvals
dir Needs_Approval

# 3. Run Ralph Wiggum
python scripts\ralph_wiggum.py run

# 4. Check errors
python scripts\error_recovery.py recent
```

### Weekly Routine (15 minutes - Monday)

```bash
# 1. Generate CEO Briefing
python scripts\ceo_briefing.py generate

# 2. Review Social Log
type Reports\Social_Log.md

# 3. Review Accounting
python scripts\accounting_manager.py summary

# 4. Clear old errors
python scripts\error_recovery.py clear --days-old 30
```

---

## Troubleshooting

### "NOT_CONFIGURED" Error

**Problem:** MCP servers report credentials not configured

**Solution:**
1. Edit .env file with actual credentials
2. Restart MCP server
3. Test again

### Playwright Not Working

**Problem:** Browser automation fails

**Solution:**
```bash
pip install --upgrade playwright
playwright install chromium
```

### File Access Denied

**Problem:** Cannot access files outside vault

**Solution:**
- Files must be within ALLOWED_DIRECTORIES
- Default: D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault
- Add directories to .env if needed

### Rate Limit Exceeded

**Problem:** Email or social media rate limit hit

**Solution:**
- Wait for limit to reset (next hour/day)
- Check Logs/*_rate_limit.json
- Increase limits in .env (within platform guidelines)

---

## Verification Checklist

After setup, verify everything works:

- [ ] All folders exist (Inbox, Needs_Action, Plans, Done, Logs, etc.)
- [ ] Dashboard.md exists and updates
- [ ] Company_Handbook.md exists
- [ ] .env file configured with at least Gmail credentials
- [ ] claude_desktop_config.json in %APPDATA%\Claude\
- [ ] Dependencies installed (run install_all_mcps.bat)
- [ ] Playwright browsers installed
- [ ] Test task can be created and processed
- [ ] MCP servers respond to test requests
- [ ] Logs are being created in Logs/ folder

**Test Command:**
```bash
# Create test task
echo "# Test Task" > Needs_Action\test_[timestamp].md

# Process it
python scripts\ralph_wiggum.py run

# Verify plan created
dir Plans\Plan_test_*

# Verify dashboard updated
type Dashboard.md | findstr "test"

# Verify task moved
dir Done\test_*
```

---

## Current Status Summary

### ✅ Complete (Bronze + Silver)

- 13 Agent Skills
- 4 MCP Servers
- 18 Python Scripts
- Full folder structure
- Task workflow
- Approval system
- Scheduling
- Error recovery
- Audit logging
- CEO Briefing
- Ralph Wiggum loop

### ⚠️ Needs Credentials

- Gmail (for email MCP)
- Twitter API (for social MCP)
- Facebook (for social MCP)
- Instagram (for social MCP)
- LinkedIn (for browser automation - or use manual login)

### ❌ Missing (Optional for Gold)

- Odoo accounting integration (30-40 hours)

---

## Next Steps

**For Silver Tier Submission:**
✅ **READY NOW** - No additional work needed!

**For Gold Tier Completion:**
1. Configure all API credentials (1-2 hours)
2. Implement Odoo accounting (30-40 hours)

---

**Questions?** See documentation:
- RUNNING_GUIDE.md - Complete running instructions
- MCP_SETUP_GUIDE.md - MCP server configuration
- PROJECT_AUDIT.md - Detailed tier assessment
- TEST_REPORT_20260218_184500.md - Latest test results

**Happy Automating! 🤖**
