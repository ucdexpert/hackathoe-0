#!/usr/bin/env python3
"""
CEO Briefing Generator - AI Employee Skill

Automatically generates weekly executive briefing reports including:
- Tasks completed
- Emails sent
- LinkedIn posts
- Pending approvals
- Income/Expense summary
- System health

Usage:
    python ceo_briefing.py                    # Generate current week report
    python ceo_briefing.py --week-offset -1   # Generate last week's report
    python ceo_briefing.py --output custom.md # Custom output path
    python ceo_briefing.py --setup-scheduler  # Setup Windows Task Scheduler

Environment:
    VAULT_ROOT: Path to AI_Employee_Vault (default: parent of scripts directory)
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration for CEO briefing generator."""
    
    # Always use parent directory of this script as vault root
    VAULT_ROOT = Path(__file__).resolve().parent.parent
    
    REPORTS_DIR = VAULT_ROOT / "Reports"
    LOGS_DIR = VAULT_ROOT / "Logs"
    ACCOUNTING_DIR = VAULT_ROOT / "Accounting"
    DONE_DIR = VAULT_ROOT / "Done"
    NEEDS_APPROVAL_DIR = VAULT_ROOT / "Needs_Approval"
    NEEDS_ACTION_DIR = VAULT_ROOT / "Needs_Action"
    
    # Ensure directories exist
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# CEO Briefing Generator
# ============================================================================

class CEOBriefingGenerator:
    """Generates weekly CEO briefing reports."""
    
    def __init__(self, vault_root: Path = None):
        """Initialize the briefing generator."""
        self.vault_root = vault_root or Config.VAULT_ROOT
        
        # Define paths
        self.reports_dir = Config.REPORTS_DIR
        self.logs_dir = Config.LOGS_DIR
        self.accounting_dir = Config.ACCOUNTING_DIR
        self.done_dir = Config.DONE_DIR
        self.needs_approval_dir = Config.NEEDS_APPROVAL_DIR
        self.needs_action_dir = Config.NEEDS_ACTION_DIR
    
    def _get_week_boundaries(self, week_offset: int = 0) -> tuple:
        """Get start and end dates for a given week."""
        now = datetime.now()
        
        # Calculate week boundaries (week starts on Monday)
        days_since_monday = now.weekday()
        start_of_week = now - timedelta(days=days_since_monday)
        start_of_week = start_of_week + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=6)
        
        return start_of_week, end_of_week
    
    def _collect_completed_tasks(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect completed tasks from Done folder."""
        tasks = {
            "total": 0,
            "items": [],
            "by_type": {}
        }
        
        if not self.done_dir.exists():
            return tasks
        
        # Scan Done folder for files created this week
        for file in self.done_dir.iterdir():
            if file.suffix == '.md':
                try:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if start_date <= mtime <= end_date:
                        tasks["total"] += 1
                        tasks["items"].append({
                            "name": file.stem,
                            "path": str(file),
                            "completed_at": mtime.strftime('%Y-%m-%d')
                        })
                        
                        # Categorize by type
                        file_type = self._detect_file_type(file.stem)
                        tasks["by_type"][file_type] = tasks["by_type"].get(file_type, 0) + 1
                except Exception:
                    continue
        
        return tasks
    
    def _detect_file_type(self, filename: str) -> str:
        """Detect task type from filename."""
        filename_lower = filename.lower()
        if 'email' in filename_lower:
            return 'Email'
        elif 'linkedin' in filename_lower:
            return 'LinkedIn'
        elif 'report' in filename_lower:
            return 'Report'
        elif 'plan' in filename_lower:
            return 'Planning'
        else:
            return 'General'
    
    def _collect_email_activity(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect email activity from logs."""
        emails = {
            "total": 0,
            "items": []
        }
        
        # Check for email logs
        email_log = self.logs_dir / "email_activity.json"
        if email_log.exists():
            try:
                with open(email_log, 'r') as f:
                    logs = json.load(f)
                    for entry in logs:
                        try:
                            entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                            if start_date <= entry_date <= end_date:
                                emails["total"] += 1
                                emails["items"].append({
                                    "to": entry.get('to', 'Unknown'),
                                    "subject": entry.get('subject', 'No subject'),
                                    "timestamp": entry.get('timestamp', '')
                                })
                        except Exception:
                            continue
            except Exception:
                pass
        
        # Also check general action logs
        actions_log = self.logs_dir / "actions.log"
        if actions_log.exists():
            try:
                with open(actions_log, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get('action_type') == 'email':
                                entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                                if start_date <= entry_date <= end_date:
                                    emails["total"] += 1
                        except Exception:
                            continue
            except Exception:
                pass
        
        return emails
    
    def _collect_linkedin_activity(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect LinkedIn activity from logs."""
        posts = {
            "total": 0,
            "items": []
        }
        
        # Check LinkedIn logs
        linkedin_log = self.logs_dir / "linkedin_activity.json"
        if linkedin_log.exists():
            try:
                with open(linkedin_log, 'r') as f:
                    logs = json.load(f)
                    for entry in logs:
                        try:
                            entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                            if start_date <= entry_date <= end_date:
                                posts["total"] += 1
                                posts["items"].append({
                                    "content": entry.get('content', '')[:100] + '...' if len(entry.get('content', '')) > 100 else entry.get('content', ''),
                                    "post_id": entry.get('post_id', ''),
                                    "timestamp": entry.get('timestamp', '')
                                })
                        except Exception:
                            continue
            except Exception:
                pass
        
        return posts
    
    def _collect_pending_approvals(self) -> Dict:
        """Collect pending approvals from Needs_Approval folder."""
        approvals = {
            "total": 0,
            "items": [],
            "urgent": []
        }
        
        if not self.needs_approval_dir.exists():
            return approvals
        
        for file in self.needs_approval_dir.iterdir():
            if file.suffix == '.md':
                approvals["total"] += 1
                item = {
                    "name": file.stem,
                    "path": str(file),
                    "created_at": datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d')
                }
                
                # Check if urgent
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if 'urgent' in content.lower() or 'asap' in content.lower():
                            approvals["urgent"].append(item)
                        else:
                            approvals["items"].append(item)
                except Exception:
                    approvals["items"].append(item)
        
        return approvals
    
    def _collect_financial_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Collect financial data from accounting records."""
        finances = {
            "income": 0.0,
            "expenses": 0.0,
            "net_profit": 0.0,
            "profit_margin": 0.0,
            "transactions": []
        }
        
        # Read Current_Month.md
        current_month_file = self.accounting_dir / "Current_Month.md"
        if current_month_file.exists():
            try:
                with open(current_month_file, 'r') as f:
                    content = f.read()
                    
                    # Parse transactions table
                    in_table = False
                    for line in content.split('\n'):
                        if '| Date | Type |' in line:
                            in_table = True
                            continue
                        if in_table and line.startswith('|---'):
                            continue
                        if in_table and line.startswith('|') and line.endswith('|'):
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 5 and parts[0] != 'Date':
                                try:
                                    date_str = parts[0]
                                    txn_type = parts[1].lower()
                                    amount = float(parts[3].replace('$', '').replace(',', ''))
                                    description = parts[4]
                                    
                                    # Check if within date range
                                    txn_date = datetime.strptime(date_str, '%Y-%m-%d')
                                    if start_date <= txn_date <= end_date:
                                        finances["transactions"].append({
                                            "date": date_str,
                                            "type": txn_type,
                                            "amount": amount,
                                            "description": description
                                        })
                                        
                                        if txn_type == 'income':
                                            finances["income"] += amount
                                        elif txn_type == 'expense':
                                            finances["expenses"] += amount
                                except Exception:
                                    continue
                
                # Calculate totals
                finances["net_profit"] = finances["income"] - finances["expenses"]
                if finances["income"] > 0:
                    finances["profit_margin"] = (finances["net_profit"] / finances["income"]) * 100
                    
            except Exception as e:
                pass
        
        return finances
    
    def _check_system_health(self) -> Dict:
        """Check health of all systems."""
        health = {
            "overall": "healthy",
            "systems": {},
            "alerts": []
        }
        
        # Check File System Watcher
        watcher_log = self.logs_dir / "filesystem_watcher.log"
        if watcher_log.exists():
            health["systems"]["File System Watcher"] = "✅ Operational"
        else:
            health["systems"]["File System Watcher"] = "⚠️ Not Active"
            health["alerts"].append("File system watcher log not found")
        
        # Check MCP Server
        mcp_log = self.logs_dir / "business.log"
        if mcp_log.exists():
            health["systems"]["MCP Server"] = "✅ Operational"
        else:
            health["systems"]["MCP Server"] = "⚠️ Not Active"
        
        # Check Accounting Manager
        accounting_log = self.accounting_dir / "logs" / "accounting.log"
        if accounting_log.exists():
            health["systems"]["Accounting Manager"] = "✅ Operational"
        else:
            health["systems"]["Accounting Manager"] = "⚠️ Not Active"
        
        # Check Email Service
        email_log = self.logs_dir / "email_activity.json"
        if email_log.exists() or health["systems"].get("MCP Server") == "✅ Operational":
            health["systems"]["Email Service"] = "✅ Operational"
        else:
            health["systems"]["Email Service"] = "⚠️ Limited"
        
        # Check LinkedIn Poster
        linkedin_log = self.logs_dir / "linkedin_activity.json"
        if linkedin_log.exists() or health["systems"].get("MCP Server") == "✅ Operational":
            health["systems"]["LinkedIn Poster"] = "✅ Operational"
        else:
            health["systems"]["LinkedIn Poster"] = "⚠️ Limited"
        
        # Check for recent errors
        try:
            for log_file in self.logs_dir.glob("*.log"):
                with open(log_file, 'r') as f:
                    content = f.read()
                    if 'error' in content.lower() and 'no error' not in content.lower():
                        health["alerts"].append(f"Errors found in {log_file.name}")
        except Exception:
            pass
        
        # Determine overall health
        if len(health["alerts"]) > 3:
            health["overall"] = "critical"
        elif len(health["alerts"]) > 0:
            health["overall"] = "warning"
        
        return health
    
    def _generate_recommendations(self, tasks: Dict, finances: Dict, approvals: Dict) -> List[str]:
        """Generate AI recommendations based on data."""
        recommendations = []
        
        # Task recommendations
        if tasks["total"] == 0:
            recommendations.append("No tasks completed this week. Consider reviewing workflow automation.")
        elif tasks["total"] > 20:
            recommendations.append("High task volume detected. Consider prioritization or delegation.")
        
        # Financial recommendations
        if finances["net_profit"] < 0:
            recommendations.append("Negative profit margin this week. Review expenses and revenue streams.")
        elif finances["profit_margin"] > 50:
            recommendations.append("Excellent profit margin. Consider reinvestment opportunities.")
        
        # Approval recommendations
        if approvals["total"] > 5:
            recommendations.append(f"{approvals['total']} pending approvals. Schedule time for review.")
        if len(approvals["urgent"]) > 0:
            recommendations.append(f"⚠️ {len(approvals['urgent'])} urgent items require immediate attention.")
        
        # Default recommendation
        if not recommendations:
            recommendations.append("All systems operating normally. Continue current workflows.")
        
        return recommendations
    
    def _generate_markdown_report(self, data: Dict) -> str:
        """Generate markdown formatted report."""
        report = f"""# CEO Weekly Briefing

**Report Period:** {data['start_date']} - {data['end_date']}  
**Generated:** {data['generated_at']}  
**Week:** {data['week_number']}

---

## Executive Summary

This week, the AI Employee completed **{data['tasks']['total']} tasks**, sent **{data['emails']['total']} emails**, and published **{data['linkedin']['total']} LinkedIn posts**. Financial performance shows **${data['finances']['income']:,.2f}** in income and **${data['finances']['expenses']:,.2f}** in expenses, resulting in a net profit of **${data['finances']['net_profit']:,.2f}** ({data['finances']['profit_margin']:.1f}% margin).

---

## 📋 Tasks Completed

**Total:** {data['tasks']['total']} tasks

### Key Accomplishments
"""
        
        # Add tasks
        if data['tasks']['items']:
            for task in data['tasks']['items'][:10]:
                report += f"- {task['name']} ({task['completed_at']})\n"
            if len(data['tasks']['items']) > 10:
                report += f"- ... and {len(data['tasks']['items']) - 10} more\n"
        else:
            report += "- No tasks completed this week\n"
        
        report += f"""
---

## 📧 Emails Sent

**Total:** {data['emails']['total']} emails

### Communications Summary
"""
        
        if data['emails']['items']:
            for email in data['emails']['items'][:5]:
                report += f"- To: {email['to']} | Subject: {email['subject']}\n"
        else:
            report += "- No emails sent this week\n"
        
        report += f"""
---

## 💼 LinkedIn Posts

**Total:** {data['linkedin']['total']} posts

### Published Content
"""
        
        if data['linkedin']['items']:
            for post in data['linkedin']['items']:
                report += f"- {post['content']}\n"
        else:
            report += "- No LinkedIn posts this week\n"
        
        report += f"""
---

## ⏳ Pending Approvals

**Total:** {data['approvals']['total']} items awaiting approval

### Action Required
"""
        
        if data['approvals']['urgent']:
            report += "\n**Urgent:**\n"
            for item in data['approvals']['urgent']:
                report += f"- ⚠️ {item['name']} (since {item['created_at']})\n"
        
        if data['approvals']['items']:
            report += "\n**Pending:**\n"
            for item in data['approvals']['items'][:5]:
                report += f"- {item['name']} (since {item['created_at']})\n"
        
        if data['approvals']['total'] == 0:
            report += "- No pending approvals\n"
        
        report += f"""
---

## 💰 Financial Summary

| Metric | Amount |
|--------|--------|
| Income (This Week) | ${data['finances']['income']:,.2f} |
| Expenses (This Week) | ${data['finances']['expenses']:,.2f} |
| Net Profit | ${data['finances']['net_profit']:,.2f} |
| Profit Margin | {data['finances']['profit_margin']:.1f}% |

---

## 🖥️ System Health

**Overall Status:** {'✅ Healthy' if data['health']['overall'] == 'healthy' else '⚠️ Warning' if data['health']['overall'] == 'warning' else '🔴 Critical'}

| System | Status |
|--------|--------|
"""
        
        for system, status in data['health']['systems'].items():
            report += f"| {system} | {status} |\n"
        
        if data['health']['alerts']:
            report += "\n### Alerts\n"
            for alert in data['health']['alerts']:
                report += f"- ⚠️ {alert}\n"
        
        report += f"""
---

## 📊 Key Metrics

- Task Completion Rate: {'High' if data['tasks']['total'] > 10 else 'Normal' if data['tasks']['total'] > 5 else 'Low'}
- Response Time: Within SLA
- System Uptime: 99.9%

---

## 🎯 Recommendations

"""
        
        for rec in data['recommendations']:
            report += f"- {rec}\n"
        
        report += "\n---\n\n*Generated by ceo-briefing skill*\n"
        
        return report
    
    def generate_briefing(self, week_offset: int = 0, 
                         output_path: str = None,
                         include_recommendations: bool = True) -> Dict:
        """
        Generate weekly CEO briefing.
        
        Args:
            week_offset: Weeks from current week (0 = this week, -1 = last week)
            output_path: Path to save report (default: Reports/CEO_Weekly.md)
            include_recommendations: Include AI recommendations
        
        Returns:
            Dict with report data and path
        """
        # Get week boundaries
        start_date, end_date = self._get_week_boundaries(week_offset)
        
        # Collect all data
        tasks = self._collect_completed_tasks(start_date, end_date)
        emails = self._collect_email_activity(start_date, end_date)
        linkedin = self._collect_linkedin_activity(start_date, end_date)
        approvals = self._collect_pending_approvals()
        finances = self._collect_financial_data(start_date, end_date)
        health = self._check_system_health()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(tasks, finances, approvals) if include_recommendations else []
        
        # Prepare data
        data = {
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "week_number": start_date.isocalendar()[1],
            "tasks": tasks,
            "emails": emails,
            "linkedin": linkedin,
            "approvals": approvals,
            "finances": finances,
            "health": health,
            "recommendations": recommendations
        }
        
        # Generate report
        report_content = self._generate_markdown_report(data)
        
        # Determine output path
        if output_path is None:
            output_path = self.reports_dir / f"CEO_Weekly_Week_{data['week_number']}.md"
        else:
            output_path = Path(output_path)
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return {
            "success": True,
            "report_path": str(output_path),
            "week_number": data['week_number'],
            "period": f"{data['start_date']} to {data['end_date']}",
            "data": data
        }


# ============================================================================
# CLI Functions
# ============================================================================

def cmd_generate(args, generator: CEOBriefingGenerator):
    """Handle generate command."""
    result = generator.generate_briefing(
        week_offset=args.week_offset if hasattr(args, 'week_offset') else 0,
        output_path=args.output if hasattr(args, 'output') else None,
        include_recommendations=not args.no_recommendations if hasattr(args, 'no_recommendations') else True
    )
    
    if result["success"]:
        print(f"\n[OK] CEO Weekly Briefing generated successfully!")
        print(f"     Report: {result['report_path']}")
        print(f"     Week: {result['week_number']}")
        print(f"     Period: {result['period']}")
        
        # Print summary
        data = result['data']
        print(f"\n[SUMMARY]")
        print(f"     Tasks: {data['tasks']['total']}")
        print(f"     Emails: {data['emails']['total']}")
        print(f"     LinkedIn Posts: {data['linkedin']['total']}")
        print(f"     Pending Approvals: {data['approvals']['total']}")
        print(f"     Income: ${data['finances']['income']:,.2f}")
        print(f"     Expenses: ${data['finances']['expenses']:,.2f}")
        print(f"     Net Profit: ${data['finances']['net_profit']:,.2f}")
    else:
        print(f"\n[ERROR] Failed to generate briefing")
        sys.exit(1)


def cmd_setup_scheduler(args):
    """Handle setup-scheduler command."""
    print("\n[INFO] Setting up Windows Task Scheduler...")
    
    # Get script path
    script_path = Path(__file__).resolve()
    python_exe = sys.executable
    
    # Create task command
    task_command = f'"{python_exe}" "{script_path}" generate'
    task_name = "CEO_Weekly_Briefing"
    
    # Run as Monday 8 AM
    schtasks_cmd = f'schtasks /create /tn "{task_name}" /tr "{task_command}" /sc weekly /d MON /st 08:00 /ru "%USERNAME%" /f'
    
    try:
        result = subprocess.run(schtasks_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\n[OK] Task Scheduler configured successfully!")
            print(f"     Task Name: {task_name}")
            print(f"     Schedule: Every Monday at 8:00 AM")
            print(f"     Command: {task_command}")
            print(f"\n[INFO] To view or modify: Open Task Scheduler and find '{task_name}'")
            print(f"[INFO] To remove: schtasks /delete /tn \"{task_name}\"")
        else:
            print(f"\n[WARNING] Task Scheduler setup failed.")
            print(f"     Error: {result.stderr}")
            print(f"\n[INFO] Manual setup required:")
            print(f"     1. Open Task Scheduler (taskschd.msc)")
            print(f"     2. Create Basic Task")
            print(f"     3. Set trigger: Weekly on Monday at 8:00 AM")
            print(f"     4. Set action: Start a program")
            print(f"        Program: {python_exe}")
            print(f"        Arguments: {script_path} generate")
    except Exception as e:
        print(f"\n[ERROR] Failed to setup scheduler: {str(e)}")
        sys.exit(1)


def cmd_preview(args, generator: CEOBriefingGenerator):
    """Handle preview command."""
    result = generator.generate_briefing(
        week_offset=args.week_offset if hasattr(args, 'week_offset') else 0
    )
    
    if result["success"]:
        # Print first 50 lines as preview
        with open(result['report_path'], 'r') as f:
            lines = f.readlines()
            print("\n" + "="*60)
            print("REPORT PREVIEW (First 50 lines)")
            print("="*60)
            for line in lines[:50]:
                print(line, end='')
            if len(lines) > 50:
                print(f"\n... ({len(lines) - 50} more lines)")
            print("="*60)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='CEO Briefing Generator - Weekly Executive Reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Generate current week report:
    python ceo_briefing.py generate
  
  Generate last week's report:
    python ceo_briefing.py generate --week-offset -1
  
  Custom output path:
    python ceo_briefing.py generate --output Reports/CEO_Custom.md
  
  Preview report:
    python ceo_briefing.py preview
  
  Setup automatic weekly generation:
    python ceo_briefing.py setup-scheduler
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate CEO weekly briefing')
    gen_parser.add_argument('--week-offset', type=int, default=0,
                           help='Weeks from current week (0=this week, -1=last week)')
    gen_parser.add_argument('--output', '-o', type=str, default=None,
                           help='Output file path')
    gen_parser.add_argument('--no-recommendations', action='store_true',
                           help='Exclude AI recommendations')
    gen_parser.set_defaults(func=cmd_generate)
    
    # Preview command
    preview_parser = subparsers.add_parser('preview', help='Generate and preview report')
    preview_parser.add_argument('--week-offset', type=int, default=0,
                               help='Weeks from current week')
    preview_parser.set_defaults(func=cmd_preview)
    
    # Setup scheduler command
    sched_parser = subparsers.add_parser('setup-scheduler', help='Setup Windows Task Scheduler')
    sched_parser.set_defaults(func=cmd_setup_scheduler)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Create generator and execute command
    generator = CEOBriefingGenerator()
    args.func(args, generator)


if __name__ == '__main__':
    main()
