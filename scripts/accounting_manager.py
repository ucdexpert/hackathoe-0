#!/usr/bin/env python3
"""
Accounting Manager - AI Employee Skill

Manages accounting records for the AI Employee including:
- Logging income and expenses
- Maintaining Current_Month.md
- Generating weekly/monthly summaries
- Category-wise breakdown

Usage:
    python accounting_manager.py log --type income --amount 5000 --desc "Sales" --category sales
    python accounting_manager.py list [--type income]
    python accounting_manager.py summary
    python accounting_manager.py weekly-report [--offset 0]
    python accounting_manager.py monthly-report

Environment:
    VAULT_ROOT: Path to AI_Employee_Vault (default: parent of scripts directory)
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from tabulate import tabulate


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration for accounting manager."""
    
    # Always use parent directory of this script as vault root
    VAULT_ROOT = Path(__file__).resolve().parent.parent
    
    ACCOUNTING_DIR = VAULT_ROOT / "Accounting"
    LOGS_DIR = ACCOUNTING_DIR / "logs"
    BACKUPS_DIR = ACCOUNTING_DIR / "backups"
    CURRENT_FILE = ACCOUNTING_DIR / "Current_Month.md"
    
    # Categories
    INCOME_CATEGORIES = ['sales', 'services', 'consulting', 'investments', 'other']
    EXPENSE_CATEGORIES = ['salary', 'rent', 'utilities', 'supplies', 'marketing', 'travel', 'other']


# ============================================================================
# Accounting Manager
# ============================================================================

class AccountingManager:
    """Manages accounting records for the AI Employee."""
    
    def __init__(self, vault_root: Path = None):
        """Initialize accounting manager."""
        self.vault_root = vault_root or Config.VAULT_ROOT
        self.accounting_dir = self.vault_root / "Accounting"
        self.logs_dir = self.accounting_dir / "logs"
        self.backups_dir = self.accounting_dir / "backups"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Get current month file
        self.current_file = Config.CURRENT_FILE
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        for directory in [self.accounting_dir, self.logs_dir, self.backups_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _create_backup(self, filepath: Path) -> Optional[Path]:
        """Create backup of a file."""
        if not filepath.exists():
            return None
        
        backup_name = f"{filepath.name}.backup"
        backup_path = self.backups_dir / backup_name
        
        # If backup exists, create timestamped version
        if backup_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{filepath.name}.{timestamp}.backup"
            backup_path = self.backups_dir / backup_name
        
        try:
            shutil.copy2(filepath, backup_path)
            self._log_operation("backup_created", {"file": str(backup_path)})
            return backup_path
        except Exception as e:
            self._log_operation("backup_failed", {"error": str(e)}, "error")
            return None
    
    def _log_operation(self, operation: str, details: Dict = None, status: str = "success"):
        """Log an accounting operation."""
        log_file = self.logs_dir / "accounting.log"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details or {},
            "status": status
        }
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Failed to log operation: {str(e)}", file=sys.stderr)
    
    def _parse_transactions(self, content: str) -> List[Dict]:
        """Parse transactions from markdown content."""
        transactions = []
        in_table = False
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Detect table start
            if line.startswith('| Date |'):
                in_table = True
                continue
            
            # Detect table end
            if in_table and line.startswith('|---'):
                continue
            
            # Parse table row
            if in_table and line.startswith('|') and line.endswith('|'):
                if '|---|' in line:
                    continue
                
                # Parse columns
                parts = line.split('|')
                parts = [p.strip() for p in parts if p.strip()]
                
                if len(parts) >= 5:
                    try:
                        transaction = {
                            "date": parts[0],
                            "type": parts[1],
                            "category": parts[2],
                            "amount": float(parts[3].replace('$', '').replace(',', '')),
                            "description": parts[4]
                        }
                        transactions.append(transaction)
                    except (ValueError, IndexError):
                        continue
            
            # Exit table
            if in_table and (not line or line.startswith('---')):
                in_table = False
        
        return transactions
    
    def _generate_summary(self, transactions: List[Dict]) -> Dict:
        """Generate summary from transactions."""
        summary = {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "net_profit": 0.0,
            "profit_margin": 0.0,
            "income_by_category": {},
            "expense_by_category": {}
        }
        
        for txn in transactions:
            amount = txn["amount"]
            txn_type = txn["type"].lower()
            category = txn.get("category", "general")
            
            if txn_type == "income":
                summary["total_income"] += amount
                summary["income_by_category"][category] = \
                    summary["income_by_category"].get(category, 0.0) + amount
            elif txn_type == "expense":
                summary["total_expenses"] += amount
                summary["expense_by_category"][category] = \
                    summary["expense_by_category"].get(category, 0.0) + amount
        
        summary["net_profit"] = summary["total_income"] - summary["total_expenses"]
        if summary["total_income"] > 0:
            summary["profit_margin"] = (summary["net_profit"] / summary["total_income"]) * 100
        
        return summary
    
    def _generate_markdown(self, transactions: List[Dict], summary: Dict = None) -> str:
        """Generate markdown content for accounting file."""
        now = datetime.now()
        month_name = now.strftime("%B")
        year = now.year
        
        content = f"""# Accounting Records - {month_name} {year}

**Month:** {month_name}  
**Year:** {year}  
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Transactions

| Date | Type | Category | Amount | Description |
|------|------|----------|--------|-------------|
"""
        
        # Add transactions (sorted by date, newest first)
        for txn in sorted(transactions, key=lambda x: x["date"], reverse=True):
            content += f"| {txn['date']} | {txn['type']} | {txn.get('category', 'general')} | ${txn['amount']:,.2f} | {txn['description']} |\n"
        
        if summary is None:
            summary = self._generate_summary(transactions)
        
        content += f"""
---

## Summary

| Metric | Amount |
|--------|--------|
| Total Income | ${summary['total_income']:,.2f} |
| Total Expenses | ${summary['total_expenses']:,.2f} |
| Net Profit | ${summary['net_profit']:,.2f} |
| Profit Margin | {summary['profit_margin']:.1f}% |

---

## Category Breakdown

### Income by Category
| Category | Amount | Percentage |
|----------|--------|------------|
"""
        
        # Income categories
        if summary["income_by_category"]:
            for category, amount in sorted(summary["income_by_category"].items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / summary["total_income"] * 100) if summary["total_income"] > 0 else 0
                content += f"| {category} | ${amount:,.2f} | {percentage:.1f}% |\n"
        else:
            content += "| No income recorded | - | - |\n"
        
        content += """
### Expenses by Category
| Category | Amount | Percentage |
|----------|--------|------------|
"""
        
        # Expense categories
        if summary["expense_by_category"]:
            for category, amount in sorted(summary["expense_by_category"].items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / summary["total_expenses"] * 100) if summary["total_expenses"] > 0 else 0
                content += f"| {category} | ${amount:,.2f} | {percentage:.1f}% |\n"
        else:
            content += "| No expenses recorded | - | - |\n"
        
        content += "\n---\n\n*Generated by accounting-manager skill*\n"
        
        return content
    
    def log_transaction(self, transaction_type: str, amount: float, 
                       description: str, date: str = None, 
                       category: str = "general") -> Dict:
        """
        Log a new transaction.
        
        Args:
            transaction_type: "income" or "expense"
            amount: Amount (positive number)
            description: Transaction description
            date: Date in YYYY-MM-DD format (default: today)
            category: Category (default: "general")
        
        Returns:
            Dict with status and transaction details
        """
        result = {
            "success": False,
            "message": "",
            "transaction": None,
            "summary": None
        }
        
        # Validate transaction type
        if transaction_type.lower() not in ["income", "expense"]:
            result["message"] = "Invalid transaction type. Must be 'income' or 'expense'."
            return result
        
        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                result["message"] = "Amount must be a positive number."
                return result
        except (ValueError, TypeError):
            result["message"] = "Amount must be a valid number."
            return result
        
        # Set date
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                result["message"] = "Invalid date format. Use YYYY-MM-DD."
                return result
        
        # Create backup
        if self.current_file.exists():
            self._create_backup(self.current_file)
        
        # Read existing transactions
        transactions = []
        if self.current_file.exists():
            try:
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    transactions = self._parse_transactions(content)
            except Exception as e:
                self._log_operation("read_error", {"error": str(e)}, "error")
        
        # Add new transaction
        transaction = {
            "date": date,
            "type": transaction_type.lower(),
            "category": category,
            "amount": amount,
            "description": description
        }
        transactions.append(transaction)
        
        # Generate summary and content
        summary = self._generate_summary(transactions)
        content = self._generate_markdown(transactions, summary)
        
        # Write file
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            result["success"] = True
            result["message"] = f"[OK] Transaction logged: {transaction_type.upper()} ${amount:,.2f}"
            result["transaction"] = transaction
            result["summary"] = {
                "total_income": summary["total_income"],
                "total_expenses": summary["total_expenses"],
                "net_profit": summary["net_profit"]
            }
            
            self._log_operation("transaction_logged", {
                "type": transaction_type,
                "amount": amount,
                "date": date,
                "category": category
            })
            
        except Exception as e:
            result["message"] = f"Failed to write file: {str(e)}"
            self._log_operation("write_error", {"error": str(e)}, "error")
        
        return result
    
    def list_transactions(self, transaction_type: str = None, 
                         start_date: str = None, 
                         end_date: str = None) -> List[Dict]:
        """List transactions with optional filters."""
        if not self.current_file.exists():
            return []
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                content = f.read()
                transactions = self._parse_transactions(content)
        except Exception as e:
            self._log_operation("read_error", {"error": str(e)}, "error")
            return []
        
        # Apply filters
        filtered = []
        for txn in transactions:
            if transaction_type and txn["type"].lower() != transaction_type.lower():
                continue
            if start_date and txn["date"] < start_date:
                continue
            if end_date and txn["date"] > end_date:
                continue
            filtered.append(txn)
        
        self._log_operation("transactions_listed", {"count": len(filtered)})
        
        return filtered
    
    def get_summary(self) -> Dict:
        """Get current month's summary."""
        transactions = self.list_transactions()
        summary = self._generate_summary(transactions)
        
        summary["transaction_count"] = len(transactions)
        summary["income_count"] = len([t for t in transactions if t["type"] == "income"])
        summary["expense_count"] = len([t for t in transactions if t["type"] == "expense"])
        summary["period"] = datetime.now().strftime("%B %Y")
        
        self._log_operation("summary_generated", summary)
        
        return summary
    
    def get_weekly_report(self, week_offset: int = 0) -> Dict:
        """Generate weekly report."""
        now = datetime.now()
        
        # Calculate week boundaries (week starts on Monday)
        days_since_monday = now.weekday()
        start_of_week = now - timedelta(days=days_since_monday)
        start_of_week = start_of_week + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=6)
        
        start_date = start_of_week.strftime("%Y-%m-%d")
        end_date = end_of_week.strftime("%Y-%m-%d")
        
        transactions = self.list_transactions(start_date=start_date, end_date=end_date)
        summary = self._generate_summary(transactions)
        
        summary["week_start"] = start_date
        summary["week_end"] = end_date
        summary["transaction_count"] = len(transactions)
        summary["week_number"] = start_of_week.isocalendar()[1]
        summary["period"] = f"Week {summary['week_number']} ({start_date} to {end_date})"
        
        self._log_operation("weekly_report_generated", summary)
        
        return summary
    
    def get_monthly_report(self, month: int = None, year: int = None) -> Dict:
        """Generate monthly report."""
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year
        
        if month == datetime.now().month and year == datetime.now().year:
            summary = self.get_summary()
            summary["month"] = month
            summary["year"] = year
            return summary
        
        return {
            "month": month,
            "year": year,
            "note": "Historical month reports require archived file access"
        }
    
    def display_summary(self, summary: Dict):
        """Display summary in a formatted way."""
        # Use ASCII-safe characters for Windows compatibility
        print("\n" + "="*60)
        print(f"Accounting Summary - {summary.get('period', 'Current Month')}")
        print("="*60)
        
        # Key metrics
        print(f"\n[METRICS] Key Metrics")
        print(f"{'Total Income:':<20} ${summary['total_income']:>12,.2f}")
        print(f"{'Total Expenses:':<20} ${summary['total_expenses']:>12,.2f}")
        print(f"{'Net Profit:':<20} ${summary['net_profit']:>12,.2f}")
        print(f"{'Profit Margin:':<20} {summary['profit_margin']:>11.1f}%")
        
        # Transaction counts
        print(f"\n[TRANSACTIONS] Transactions")
        print(f"{'Total:':<20} {summary.get('transaction_count', 0):>12}")
        print(f"{'Income:':<20} {summary.get('income_count', 0):>12}")
        print(f"{'Expenses:':<20} {summary.get('expense_count', 0):>12}")
        
        # Category breakdown
        if summary.get('income_by_category'):
            print(f"\n[INCOME] Income by Category")
            for category, amount in sorted(summary['income_by_category'].items(), key=lambda x: x[1], reverse=True):
                pct = (amount / summary['total_income'] * 100) if summary['total_income'] > 0 else 0
                print(f"{category:<20} ${amount:>10,.2f} ({pct:>5.1f}%)")
        
        if summary.get('expense_by_category'):
            print(f"\n[EXPENSES] Expenses by Category")
            for category, amount in sorted(summary['expense_by_category'].items(), key=lambda x: x[1], reverse=True):
                pct = (amount / summary['total_expenses'] * 100) if summary['total_expenses'] > 0 else 0
                print(f"{category:<20} ${amount:>10,.2f} ({pct:>5.1f}%)")
        
        print("\n" + "="*60)


# ============================================================================
# CLI Functions
# ============================================================================

def cmd_log(args, manager: AccountingManager):
    """Handle log command."""
    result = manager.log_transaction(
        transaction_type=args.type,
        amount=args.amount,
        description=args.desc,
        date=args.date,
        category=args.category
    )
    
    if result["success"]:
        print(f"\n[OK] {result['message']}")
        if result.get('summary'):
            print(f"   Running Total - Income: ${result['summary']['total_income']:,.2f}, "
                  f"Expenses: ${result['summary']['total_expenses']:,.2f}, "
                  f"Profit: ${result['summary']['net_profit']:,.2f}")
    else:
        print(f"\n[ERROR] {result['message']}")
        sys.exit(1)


def cmd_list(args, manager: AccountingManager):
    """Handle list command."""
    transactions = manager.list_transactions(
        transaction_type=args.type if hasattr(args, 'type') else None
    )
    
    if not transactions:
        print("\n[INFO] No transactions found.")
        return
    
    print(f"\n[LIST] Transactions ({len(transactions)} found)\n")
    
    # Prepare table data
    table_data = []
    for txn in transactions:
        amount_str = f"${txn['amount']:,.2f}"
        table_data.append([
            txn['date'],
            txn['type'].upper(),
            txn.get('category', 'general'),
            amount_str,
            txn['description'][:40] + '...' if len(txn['description']) > 40 else txn['description']
        ])
    
    # Display table
    print(tabulate(table_data, 
                   headers=['Date', 'Type', 'Category', 'Amount', 'Description'],
                   tablefmt='grid'))


def cmd_summary(args, manager: AccountingManager):
    """Handle summary command."""
    summary = manager.get_summary()
    manager.display_summary(summary)


def cmd_weekly_report(args, manager: AccountingManager):
    """Handle weekly-report command."""
    report = manager.get_weekly_report(week_offset=args.offset if hasattr(args, 'offset') else 0)
    
    print(f"\n📊 Weekly Report - {report['period']}")
    print("="*60)
    print(f"\nTotal Income:   ${report['total_income']:>12,.2f}")
    print(f"Total Expenses: ${report['total_expenses']:>12,.2f}")
    print(f"Net Profit:     ${report['net_profit']:>12,.2f}")
    print(f"Profit Margin:  {report['profit_margin']:>11.1f}%")
    print(f"\nTransactions:   {report['transaction_count']:>12}")
    print("="*60)


def cmd_monthly_report(args, manager: AccountingManager):
    """Handle monthly-report command."""
    report = manager.get_monthly_report(
        month=args.month if hasattr(args, 'month') else None,
        year=args.year if hasattr(args, 'year') else None
    )
    
    print(f"\n📊 Monthly Report")
    print("="*60)
    print(f"\nTotal Income:   ${report['total_income']:>12,.2f}")
    print(f"Total Expenses: ${report['total_expenses']:>12,.2f}")
    print(f"Net Profit:     ${report['net_profit']:>12,.2f}")
    print(f"Profit Margin:  {report['profit_margin']:>11.1f}%")
    print(f"\nTransactions:   {report['transaction_count']:>12}")
    print("="*60)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Accounting Manager - AI Employee Skill',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Log income:
    python accounting_manager.py log --type income --amount 5000 --desc "Product sales" --category sales
  
  Log expense:
    python accounting_manager.py log --type expense --amount 2000 --desc "Office rent" --category rent
  
  List transactions:
    python accounting_manager.py list
    python accounting_manager.py list --type income
  
  Get summary:
    python accounting_manager.py summary
  
  Weekly report:
    python accounting_manager.py weekly-report
    python accounting_manager.py weekly-report --offset -1  (last week)
  
  Monthly report:
    python accounting_manager.py monthly-report
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Log a transaction')
    log_parser.add_argument('--type', '-t', required=True, choices=['income', 'expense'],
                           help='Transaction type')
    log_parser.add_argument('--amount', '-a', type=float, required=True,
                           help='Amount (positive number)')
    log_parser.add_argument('--desc', '-d', required=True,
                           help='Description')
    log_parser.add_argument('--date', default=None,
                           help='Date (YYYY-MM-DD, default: today)')
    log_parser.add_argument('--category', '-c', default='general',
                           help='Category')
    log_parser.set_defaults(func=cmd_log)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List transactions')
    list_parser.add_argument('--type', '-t', choices=['income', 'expense'],
                            help='Filter by type')
    list_parser.set_defaults(func=cmd_list)
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show summary')
    summary_parser.set_defaults(func=cmd_summary)
    
    # Weekly report command
    weekly_parser = subparsers.add_parser('weekly-report', help='Weekly report')
    weekly_parser.add_argument('--offset', type=int, default=0,
                              help='Weeks offset (0=this week, -1=last week)')
    weekly_parser.set_defaults(func=cmd_weekly_report)
    
    # Monthly report command
    monthly_parser = subparsers.add_parser('monthly-report', help='Monthly report')
    monthly_parser.add_argument('--month', type=int, help='Month (1-12)')
    monthly_parser.add_argument('--year', type=int, help='Year')
    monthly_parser.set_defaults(func=cmd_monthly_report)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Create manager and execute command
    manager = AccountingManager()
    args.func(args, manager)


if __name__ == '__main__':
    main()
