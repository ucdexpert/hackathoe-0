#!/usr/bin/env python3
"""
Error Recovery System - AI Employee Skill

Comprehensive error handling with:
- Automatic error logging to Logs/errors.log
- File quarantine to Errors/ directory
- Automatic retry after 5 minutes
- Error statistics and reporting

Usage:
    python error_recovery.py handle --message "Error" --type "FileNotFoundError"
    python error_recovery.py stats [--days 7]
    python error_recovery.py recent [--limit 10]
    python error_recovery.py clear [--days-old 30]
    python error_recovery.py test

Environment:
    VAULT_ROOT: Path to AI_Employee_Vault (default: parent of scripts directory)
"""

import os
import sys
import json
import shutil
import traceback
import time
import hashlib
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import threading


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration for error recovery system."""
    
    # Always use parent directory of this script as vault root
    VAULT_ROOT = Path(__file__).resolve().parent.parent
    
    ERRORS_DIR = VAULT_ROOT / "Errors"
    LOGS_DIR = VAULT_ROOT / "Logs"
    ERROR_LOG = LOGS_DIR / "errors.log"
    ERROR_INDEX = ERRORS_DIR / "error_index.json"
    
    # Retry configuration
    MAX_RETRIES = 1
    DEFAULT_RETRY_DELAY = 300  # 5 minutes
    
    # Ensure directories exist
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Error Recovery System
# ============================================================================

class ErrorRecoverySystem:
    """Comprehensive error handling and recovery system."""
    
    def __init__(self, vault_root: Path = None):
        """Initialize error recovery system."""
        self.vault_root = vault_root or Config.VAULT_ROOT
        
        # Define paths
        self.errors_dir = Config.ERRORS_DIR
        self.logs_dir = Config.LOGS_DIR
        self.error_log = Config.ERROR_LOG
        self.error_index = Config.ERROR_INDEX
        
        # Retry configuration
        self.max_retries = Config.MAX_RETRIES
        self.default_retry_delay = Config.DEFAULT_RETRY_DELAY
        
        # Thread safety
        self._lock = threading.Lock()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.errors_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create dated subdirectory
        today = datetime.now().strftime("%Y-%m-%d")
        (self.errors_dir / today).mkdir(exist_ok=True)
    
    def _generate_error_id(self, error_type: str, file_path: str = None) -> str:
        """Generate unique error ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_data = f"{timestamp}-{error_type}-{file_path or ''}"
        hash_suffix = hashlib.md5(unique_data.encode()).hexdigest()[:6].upper()
        return f"ERR-{timestamp}-{hash_suffix}"
    
    def _log_error(self, error_data: Dict):
        """Log error to errors.log in JSON Lines format."""
        with self._lock:
            try:
                self._ensure_directories()
                with open(self.error_log, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(error_data, default=str) + '\n')
            except Exception as e:
                print(f"[ERROR] Failed to log error: {str(e)}", file=sys.stderr)
    
    def _update_error_index(self, error_id: str, error_data: Dict):
        """Update error index for quick lookup."""
        with self._lock:
            index = {}
            
            # Load existing index
            if self.error_index.exists():
                try:
                    with open(self.error_index, 'r') as f:
                        index = json.load(f)
                except Exception:
                    index = {}
            
            # Update with new error
            index[error_id] = {
                "timestamp": error_data.get("timestamp"),
                "error_type": error_data.get("error_type"),
                "file_path": error_data.get("file_path"),
                "severity": error_data.get("severity"),
                "status": error_data.get("status"),
                "retry_count": error_data.get("retry_count", 0)
            }
            
            # Ensure directory exists
            self.error_index.parent.mkdir(parents=True, exist_ok=True)
            
            # Save index
            try:
                with open(self.error_index, 'w') as f:
                    json.dump(index, f, indent=2, default=str)
            except Exception as e:
                print(f"[ERROR] Failed to update error index: {str(e)}", file=sys.stderr)
    
    def _move_to_errors(self, file_path: str, error_id: str, error_data: Dict) -> Optional[str]:
        """Move failed file to Errors directory."""
        if not file_path or not Path(file_path).exists():
            return None
        
        try:
            self._ensure_directories()
            
            # Create dated subdirectory
            today = datetime.now().strftime("%Y-%m-%d")
            error_subdir = self.errors_dir / today
            error_subdir.mkdir(exist_ok=True)
            
            # Generate new filename
            original_name = Path(file_path).name
            base_name = Path(file_path).stem
            extension = Path(file_path).suffix
            new_filename = f"{base_name}_error_{error_id[:8]}{extension}"
            new_path = error_subdir / new_filename
            
            # Move file
            shutil.move(file_path, new_path)
            
            # Create metadata file
            meta_filename = f"{base_name}_error_{error_id[:8]}.meta.json"
            meta_path = error_subdir / meta_filename
            
            metadata = {
                "error_id": error_id,
                "original_path": str(file_path),
                "moved_path": str(new_path),
                "error_type": error_data.get("error_type"),
                "error_message": error_data.get("error_message"),
                "timestamp": error_data.get("timestamp"),
                "severity": error_data.get("severity"),
                "context": error_data.get("context", {})
            }
            
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            return str(new_path)
            
        except Exception as e:
            print(f"[ERROR] Failed to move file to errors: {str(e)}", file=sys.stderr)
            return None
    
    def _should_retry(self, error_type: str, severity: str) -> bool:
        """Determine if error should be retried."""
        # Don't retry certain error types
        no_retry_errors = [
            "PermissionError",
            "ValidationError",
            "ConfigurationError",
            "AuthenticationError"
        ]
        
        # Don't retry critical errors
        if severity == "critical":
            return False
        
        # Don't retry specific error types
        if error_type in no_retry_errors:
            return False
        
        return True
    
    def handle_error(self, error_message: str, error_type: str,
                    file_path: str = None, context: Dict = None,
                    retry_enabled: bool = True, retry_delay: int = None,
                    severity: str = "medium", retry_func: Callable = None) -> Dict:
        """
        Handle an error with logging, file movement, and retry logic.
        
        Args:
            error_message: Description of the error
            error_type: Type of error (e.g., "FileNotFoundError")
            file_path: Path to file that caused error
            context: Additional context information
            retry_enabled: Whether to enable retry
            retry_delay: Seconds to wait before retry
            severity: Error severity (low/medium/high/critical)
            retry_func: Optional function to retry
        
        Returns:
            Dict with error handling result
        """
        # Generate error ID
        error_id = self._generate_error_id(error_type, file_path)
        timestamp = datetime.now().isoformat()
        
        # Prepare error data
        error_data = {
            "error_id": error_id,
            "timestamp": timestamp,
            "error_type": error_type,
            "error_message": error_message,
            "file_path": file_path,
            "severity": severity,
            "context": context or {},
            "stack_trace": traceback.format_exc() if sys.exc_info()[2] else None,
            "retry_attempt": 0,
            "retry_count": 0,
            "status": "logged"
        }
        
        # Log error
        self._log_error(error_data)
        self._update_error_index(error_id, error_data)
        
        # Move file to errors directory
        if file_path:
            moved_path = self._move_to_errors(file_path, error_id, error_data)
            error_data["moved_path"] = moved_path
        
        # Determine if retry should be attempted
        should_retry = (
            retry_enabled and 
            self._should_retry(error_type, severity) and 
            retry_func is not None
        )
        
        result = {
            "success": False,
            "error_id": error_id,
            "error_type": error_type,
            "error_message": error_message,
            "file_moved_to": error_data.get("moved_path"),
            "retry_attempted": False,
            "retry_success": False
        }
        
        # Attempt retry if enabled
        if should_retry:
            actual_delay = retry_delay or self.default_retry_delay
            
            # Log retry scheduling
            retry_data = error_data.copy()
            retry_data["retry_attempt"] = 1
            retry_data["retry_delay"] = actual_delay
            retry_data["status"] = "retry_scheduled"
            self._log_error(retry_data)
            
            print(f"[RETRY] Waiting {actual_delay} seconds before retry...")
            time.sleep(actual_delay)
            
            try:
                # Execute retry function
                retry_result = retry_func()
                
                if retry_result:
                    # Retry succeeded
                    error_data["retry_count"] = 1
                    error_data["status"] = "recovered"
                    self._log_error(error_data)
                    self._update_error_index(error_id, error_data)
                    
                    result["retry_attempted"] = True
                    result["retry_success"] = True
                    result["success"] = True
                    result["message"] = "Operation recovered after retry"
                    
                    print(f"[OK] Operation recovered after retry!")
                    return result
                    
            except Exception as retry_error:
                # Retry failed
                retry_error_data = {
                    "error_id": error_id,
                    "timestamp": datetime.now().isoformat(),
                    "error_type": type(retry_error).__name__,
                    "error_message": str(retry_error),
                    "retry_attempt": 1,
                    "status": "retry_failed"
                }
                self._log_error(retry_error_data)
                self._update_error_index(error_id, error_data)
                
                result["retry_attempted"] = True
                result["retry_success"] = False
                result["message"] = "Retry failed after 5 minutes"
                print(f"[ERROR] Retry failed: {str(retry_error)}")
        
        # Update final status
        error_data["status"] = "failed"
        error_data["severity"] = "high" if severity != "critical" else "critical"
        self._log_error(error_data)
        self._update_error_index(error_id, error_data)
        
        if not result.get("message"):
            result["message"] = "Error logged and file moved to Errors directory"
        
        print(f"[ERROR] {error_type}: {error_message}")
        if error_data.get("moved_path"):
            print(f"       File moved to: {error_data['moved_path']}")
        
        return result
    
    def get_error_statistics(self, days: int = 7) -> Dict:
        """Get error statistics for the specified period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        stats = {
            "total_errors": 0,
            "by_type": {},
            "by_severity": {},
            "recovered": 0,
            "failed": 0,
            "period_days": days
        }
        
        if not self.error_log.exists():
            return stats
        
        try:
            with open(self.error_log, 'r') as f:
                for line in f:
                    try:
                        error = json.loads(line.strip())
                        error_date = datetime.fromisoformat(error.get("timestamp", ""))
                        
                        if error_date < cutoff_date:
                            continue
                        
                        stats["total_errors"] += 1
                        
                        # Count by type
                        error_type = error.get("error_type", "Unknown")
                        stats["by_type"][error_type] = stats["by_type"].get(error_type, 0) + 1
                        
                        # Count by severity
                        severity = error.get("severity", "unknown")
                        stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
                        
                        # Count recovery status
                        status = error.get("status", "")
                        if status == "recovered":
                            stats["recovered"] += 1
                        elif status in ["failed", "retry_failed"]:
                            stats["failed"] += 1
                            
                    except Exception:
                        continue
        except Exception as e:
            print(f"[ERROR] Failed to get statistics: {str(e)}")
        
        return stats
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get most recent errors."""
        errors = []
        
        if not self.error_log.exists():
            return errors
        
        try:
            with open(self.error_log, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-limit*2:]):
                    try:
                        error = json.loads(line.strip())
                        if error.get("retry_attempt", 0) == 0:
                            errors.append(error)
                            if len(errors) >= limit:
                                break
                    except Exception:
                        continue
        except Exception as e:
            print(f"[ERROR] Failed to get recent errors: {str(e)}")
        
        return errors
    
    def clear_old_errors(self, days_old: int = 30) -> Dict:
        """Clear errors older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleared = {"files": 0, "logs": 0}
        
        try:
            # Clear old error files
            if self.errors_dir.exists():
                for subdir in self.errors_dir.iterdir():
                    if subdir.is_dir():
                        try:
                            dir_date = datetime.strptime(subdir.name, "%Y-%m-%d")
                            if dir_date < cutoff_date:
                                shutil.rmtree(subdir)
                                cleared["files"] += 1
                                print(f"[OK] Cleared old directory: {subdir.name}")
                        except Exception:
                            continue
            
            # Clear old log entries
            if self.error_log.exists():
                new_lines = []
                with open(self.error_log, 'r') as f:
                    for line in f:
                        try:
                            error = json.loads(line.strip())
                            error_date = datetime.fromisoformat(error.get("timestamp", ""))
                            if error_date >= cutoff_date:
                                new_lines.append(line)
                                cleared["logs"] += 1
                        except Exception:
                            continue
                
                with open(self.error_log, 'w') as f:
                    f.writelines(new_lines)
                print(f"[OK] Cleared {cleared['logs']} old log entries")
                    
        except Exception as e:
            return {"error": str(e), "cleared": cleared}
        
        return {"success": True, "cleared": cleared}


# ============================================================================
# Decorator for Automatic Error Handling
# ============================================================================

def auto_handle_error(vault_root: Path = None, retry_delay: int = 300):
    """
    Decorator for automatic error handling.
    
    Usage:
        @auto_handle_error()
        def my_function(file_path):
            # Your code here
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            recovery = ErrorRecoverySystem(vault_root)
            
            # Extract file_path from args or kwargs if present
            file_path = kwargs.get('file_path')
            if not file_path and len(args) > 0:
                file_path = args[0] if isinstance(args[0], str) else None
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                result = recovery.handle_error(
                    error_message=str(e),
                    error_type=type(e).__name__,
                    file_path=file_path,
                    context={
                        "function": func.__name__,
                        "args": args,
                        "kwargs": kwargs
                    },
                    retry_delay=retry_delay,
                    retry_func=lambda: func(*args, **kwargs)
                )
                
                if not result["success"]:
                    raise Exception(f"Error after recovery attempt: {result['error_message']}")
                
                return result
        
        return wrapper
    return decorator


# ============================================================================
# CLI Functions
# ============================================================================

def cmd_handle(args, recovery: ErrorRecoverySystem):
    """Handle an error."""
    result = recovery.handle_error(
        error_message=args.message,
        error_type=args.type,
        file_path=args.file if hasattr(args, 'file') else None,
        severity=args.severity if hasattr(args, 'severity') else 'medium',
        retry_enabled=not args.no_retry if hasattr(args, 'no_retry') else True
    )
    
    print(f"\n[RESULT]")
    print(f"  Error ID: {result['error_id']}")
    print(f"  Status: {result['message']}")
    if result.get('file_moved_to'):
        print(f"  File moved to: {result['file_moved_to']}")


def cmd_stats(args, recovery: ErrorRecoverySystem):
    """Show error statistics."""
    stats = recovery.get_error_statistics(days=args.days if hasattr(args, 'days') else 7)
    
    print(f"\n{'='*60}")
    print(f"Error Statistics (Last {stats['period_days']} days)")
    print(f"{'='*60}")
    print(f"\nTotal Errors: {stats['total_errors']}")
    print(f"Recovered: {stats['recovered']}")
    print(f"Failed: {stats['failed']}")
    
    if stats['by_type']:
        print(f"\nBy Type:")
        for error_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count}")
    
    if stats['by_severity']:
        print(f"\nBy Severity:")
        for severity, count in sorted(stats['by_severity'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {severity}: {count}")
    
    print(f"\n{'='*60}")


def cmd_recent(args, recovery: ErrorRecoverySystem):
    """Show recent errors."""
    errors = recovery.get_recent_errors(limit=args.limit if hasattr(args, 'limit') else 10)
    
    if not errors:
        print("\n[INFO] No recent errors found.")
        return
    
    print(f"\n{'='*60}")
    print(f"Recent Errors ({len(errors)} shown)")
    print(f"{'='*60}")
    
    for error in errors:
        print(f"\n[{error.get('severity', 'unknown').upper()}] {error.get('error_type', 'Unknown')}")
        print(f"  Time: {error.get('timestamp', 'Unknown')}")
        print(f"  Message: {error.get('error_message', 'N/A')}")
        if error.get('file_path'):
            print(f"  File: {error.get('file_path')}")
        print(f"  Status: {error.get('status', 'unknown')}")
    
    print(f"\n{'='*60}")


def cmd_clear(args, recovery: ErrorRecoverySystem):
    """Clear old errors."""
    result = recovery.clear_old_errors(days_old=args.days_old if hasattr(args, 'days_old') else 30)
    
    if result.get('success'):
        print(f"\n[OK] Successfully cleared old errors!")
        print(f"  Directories cleared: {result['cleared'].get('files', 0)}")
        print(f"  Log entries cleared: {result['cleared'].get('logs', 0)}")
    else:
        print(f"\n[ERROR] Failed to clear old errors: {result.get('error', 'Unknown error')}")


def cmd_test(args, recovery: ErrorRecoverySystem):
    """Test error handling system."""
    print("\n[TEST] Testing error recovery system...")
    
    # Test 1: Log a test error
    print("\n[Test 1] Logging test error...")
    result = recovery.handle_error(
        error_message="This is a test error",
        error_type="TestError",
        severity="low",
        retry_enabled=False
    )
    print(f"  Result: {result['message']}")
    print(f"  Error ID: {result['error_id']}")
    
    # Test 2: Get statistics
    print("\n[Test 2] Getting statistics...")
    stats = recovery.get_error_statistics(days=1)
    print(f"  Total errors in last 24h: {stats['total_errors']}")
    
    # Test 3: Get recent errors
    print("\n[Test 3] Getting recent errors...")
    errors = recovery.get_recent_errors(limit=5)
    print(f"  Recent errors found: {len(errors)}")
    
    print(f"\n[OK] All tests completed!")
    print(f"  Error log: {recovery.error_log}")
    print(f"  Error index: {recovery.error_index}")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Error Recovery System - Automatic Error Handling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Handle an error:
    python error_recovery.py handle --message "File not found" --type "FileNotFoundError"
  
  Handle error with file:
    python error_recovery.py handle --message "Error" --type "Error" --file path/to/file.txt
  
  Show statistics:
    python error_recovery.py stats --days 7
  
  Show recent errors:
    python error_recovery.py recent --limit 10
  
  Clear old errors:
    python error_recovery.py clear --days-old 30
  
  Test error handling:
    python error_recovery.py test
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Handle command
    handle_parser = subparsers.add_parser('handle', help='Handle an error')
    handle_parser.add_argument('--message', '-m', required=True, help='Error message')
    handle_parser.add_argument('--type', '-t', required=True, help='Error type')
    handle_parser.add_argument('--file', '-f', help='File path that caused error')
    handle_parser.add_argument('--severity', '-s', default='medium',
                              choices=['low', 'medium', 'high', 'critical'],
                              help='Error severity')
    handle_parser.add_argument('--no-retry', action='store_true', help='Disable retry')
    handle_parser.set_defaults(func=cmd_handle)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show error statistics')
    stats_parser.add_argument('--days', '-d', type=int, default=7, help='Number of days')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Recent command
    recent_parser = subparsers.add_parser('recent', help='Show recent errors')
    recent_parser.add_argument('--limit', '-l', type=int, default=10, help='Number of errors')
    recent_parser.set_defaults(func=cmd_recent)
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear old errors')
    clear_parser.add_argument('--days-old', type=int, default=30, help='Days old threshold')
    clear_parser.set_defaults(func=cmd_clear)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test error handling')
    test_parser.set_defaults(func=cmd_test)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Create recovery system and execute command
    recovery = ErrorRecoverySystem()
    args.func(args, recovery)


if __name__ == '__main__':
    main()
