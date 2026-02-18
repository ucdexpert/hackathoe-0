# CEO Briefing Skill - Quick Start Guide

## 🚀 Overview

The **CEO Briefing Skill** automatically generates comprehensive weekly executive reports that include:

- ✅ Tasks completed
- ✅ Emails sent
- ✅ LinkedIn posts published
- ✅ Pending approvals
- ✅ Income/Expense summary
- ✅ System health status
- ✅ AI-generated recommendations

## 📁 Output Location

Reports are saved to: `AI_Employee_Vault/Reports/CEO_Weekly.md`

## 🎯 Quick Start

### Generate Current Week's Report

```bash
cd D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault\scripts
python ceo_briefing.py generate
```

### Generate Last Week's Report

```bash
python ceo_briefing.py generate --week-offset -1
```

### Preview Report

```bash
python ceo_briefing.py preview
```

## ⏰ Automatic Scheduling

### Windows - One-Click Setup

```batch
# Run from scripts directory
setup_ceo_briefing_scheduler.bat install
```

This sets up automatic report generation:
- **When:** Every Monday at 8:00 AM
- **Where:** Task Scheduler
- **Task Name:** CEO_Weekly_Briefing

### Manual Windows Setup

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **"Create Basic Task..."**
3. Name: `CEO Weekly Briefing`
4. Trigger: **Weekly**
5. Day: **Monday**
6. Time: **8:00 AM**
7. Action: **Start a program**
8. Program: `C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe`
9. Arguments: `"D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault\scripts\ceo_briefing.py" generate`

### Linux/Mac - Cron Setup

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths)
0 8 * * 1 cd /path/to/vault && python scripts/ceo_briefing.py generate
```

## 📊 Sample Report Structure

```markdown
# CEO Weekly Briefing

**Report Period:** 2026-02-16 - 2026-02-22
**Week:** 8

## Executive Summary
- Tasks completed: 8
- Emails sent: 0
- LinkedIn posts: 0
- Financial performance summary

## Tasks Completed
- List of all completed tasks

## Emails Sent
- Email activity summary

## LinkedIn Posts
- Published content

## Pending Approvals
- Items requiring attention

## Financial Summary
| Metric | Amount |
|--------|--------|
| Income | $X,XXX |
| Expenses | $X,XXX |
| Net Profit | $X,XXX |
| Profit Margin | XX.X% |

## System Health
- Status of all subsystems
- Alerts and warnings

## Recommendations
- AI-generated action items
```

## 🔧 Command Reference

| Command | Description |
|---------|-------------|
| `generate` | Generate weekly briefing |
| `generate --week-offset -1` | Generate last week's report |
| `generate -o custom.md` | Custom output path |
| `preview` | Generate and preview |
| `setup-scheduler` | Setup Windows Task Scheduler |

## 📈 Integration with Other Skills

The CEO Briefing automatically collects data from:

| Source | Data Collected |
|--------|---------------|
| `Done/` folder | Completed tasks |
| `Logs/` folder | Email & LinkedIn activity |
| `Accounting/Current_Month.md` | Financial data |
| `Needs_Approval/` folder | Pending approvals |
| System logs | Health status |

## 🎯 Best Practices

1. **Review Every Monday** - Check reports at start of week
2. **Track Trends** - Compare week-over-week metrics
3. **Act on Recommendations** - Follow up on AI suggestions
4. **Archive Reports** - Keep for historical analysis
5. **Share with Team** - Distribute to stakeholders

## 🔍 Troubleshooting

### No Tasks Shown
- Ensure tasks are being moved to `Done/` folder
- Check file timestamps are correct

### No Financial Data
- Verify `Accounting/Current_Month.md` exists
- Ensure transactions are logged with dates

### System Health Warnings
- Check that all subsystems are running
- Review log files for errors

### Report Not Generating
- Verify Python is installed
- Check script permissions
- Ensure `Reports/` directory exists

## 📞 Support

**View Help:**
```bash
python ceo_briefing.py --help
```

**Check Status:**
```bash
setup_ceo_briefing_scheduler.bat status
```

**Remove Scheduler:**
```bash
setup_ceo_briefing_scheduler.bat uninstall
```

## 🔗 Claude Integration

Once installed in `.claude/skills/ceo-briefing/`, Claude can:

- Generate reports on demand
- Answer questions about business performance
- Provide executive summaries
- Track trends over time
- Explain metrics and recommendations

**Example Claude Requests:**
- "Generate this week's CEO briefing"
- "What was our profit margin last week?"
- "How many tasks were completed this week?"
- "Show me pending approvals"

---

**Your CEO Briefing skill is ready to use!** 🎉

Run `python ceo_briefing.py generate` to create your first report.
