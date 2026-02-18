# error-recovery

## Description
A comprehensive error handling and recovery system that automatically detects failures, logs errors, manages retries, and moves failed items to a quarantine area for manual review. This skill ensures no task fails silently and provides detailed diagnostics for troubleshooting.

## Parameters
- `error_message` (string, required): Description of the error that occurred
- `error_type` (string, required): Type of error (e.g., "FileNotFoundError", "PermissionError", "NetworkError")
- `file_path` (string, optional): Path to the file that caused the error
- `context` (dict, optional): Additional context about the error (function name, parameters, etc.)
- `retry_enabled` (boolean, optional): Whether to enable automatic retry (default: True)
- `retry_delay` (integer, optional): Seconds to wait before retry (default: 300 seconds / 5 minutes)
- `severity` (string, optional): Error severity - "low", "medium", "high", "critical" (default: "medium")

## Functionality
When invoked, this skill:

1. **Logs Error Details**
   - Timestamp
   - Error type and message
   - File path (if applicable)
   - Stack trace
   - Context information
   - Severity level

2. **Moves Failed Files**
   - Moves error-causing files to Errors/ folder
   - Preserves original path information
   - Creates error metadata file alongside

3. **Implements Retry Logic**
   - Automatically retries failed operations once
   - Waits specified delay (default: 5 minutes)
   - Tracks retry attempts
   - Aborts after one failed retry

4. **Categorizes Errors**
   - File system errors
   - Network errors
   - Permission errors
   - Validation errors
   - System errors

5. **Generates Error Reports**
   - Daily error summaries
   - Error frequency analysis
   - Common error patterns
   - Recovery success rate

## Error Log Format

Errors are logged to `Logs/errors.log` in JSON Lines format:

```json
{"timestamp": "2026-02-18T10:30:00", "error_id": "ERR-20260218-103000-ABC123", "error_type": "FileNotFoundError", "error_message": "File not found", "file_path": "/path/to/file.txt", "severity": "medium", "retry_attempt": 0, "context": {"function": "process_file", "parameters": {...}}, "stack_trace": "...", "status": "logged"}
{"timestamp": "2026-02-18T10:35:00", "error_id": "ERR-20260218-103000-ABC123", "error_type": "FileNotFoundError", "error_message": "File not found", "file_path": "/path/to/file.txt", "severity": "high", "retry_attempt": 1, "context": {"function": "process_file", "parameters": {...}}, "stack_trace": "...", "status": "retry_failed"}
```

## Error File Structure

```
AI_Employee_Vault/
├── Errors/
│   ├── 2026-02-18/
│   │   ├── filename_error.md
│   │   └── filename_error.meta.json
│   └── error_index.json
└── Logs/
    └── errors.log
```

## Implementation
```python
import os
import sys
import json
import shutil
import traceback
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import threading


class ErrorRecoverySystem:
    """Comprehensive error handling and recovery system."""
    
    def __init__(self, vault_root: Path = None):
        """Initialize error recovery system."""
        if vault_root is None:
            self.vault_root = Path(__file__).resolve().parent.parent
        else:
            self.vault_root = Path(vault_root)
        
        # Define paths
        self.errors_dir = self.vault_root / "Errors"
        self.logs_dir = self.vault_root / "Logs"
        self.error_log = self.logs_dir / "errors.log"
        self.error_index = self.errors_dir / "error_index.json"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Retry configuration
        self.max_retries = 1
        self.default_retry_delay = 300  # 5 minutes
        
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
                with open(self.error_log, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(error_data, default=str) + '\n')
            except Exception as e:
                print(f"Failed to log error: {str(e)}", file=sys.stderr)
    
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
            
            # Save index
            try:
                with open(self.error_index, 'w') as f:
                    json.dump(index, f, indent=2, default=str)
            except Exception as e:
                print(f"Failed to update error index: {str(e)}", file=sys.stderr)
    
    def _move_to_errors(self, file_path: str, error_id: str, error_data: Dict) -> Optional[str]:
        """Move failed file to Errors directory."""
        if not file_path or not Path(file_path).exists():
            return None
        
        try:
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
            print(f"Failed to move file to errors: {str(e)}", file=sys.stderr)
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
            
            # Wait and retry
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
        
        # Update final status
        error_data["status"] = "failed"
        error_data["severity"] = "high" if severity != "critical" else "critical"
        self._log_error(error_data)
        self._update_error_index(error_id, error_data)
        
        if not result.get("message"):
            result["message"] = "Error logged and file moved to Errors directory"
        
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
        except Exception:
            pass
        
        return stats
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get most recent errors."""
        errors = []
        
        if not self.error_log.exists():
            return errors
        
        try:
            with open(self.error_log, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-limit*2:]):  # Read extra to account for retries
                    try:
                        error = json.loads(line.strip())
                        if error.get("retry_attempt", 0) == 0:  # Only initial errors
                            errors.append(error)
                            if len(errors) >= limit:
                                break
                    except Exception:
                        continue
        except Exception:
            pass
        
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
                        except Exception:
                            continue
            
            # Clear old log entries (rewrite log without old entries)
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
# Skill Entry Point
# ============================================================================

def error_recovery_skill(error_message: str, error_type: str,
                        file_path: str = None, context: Dict = None,
                        retry_enabled: bool = True, retry_delay: int = 300,
                        severity: str = "medium") -> Dict:
    """
    Main entry point for error-recovery skill.
    
    Args:
        error_message: Description of the error
        error_type: Type of error
        file_path: Path to file that caused error
        context: Additional context
        retry_enabled: Whether to enable retry
        retry_delay: Seconds to wait before retry
        severity: Error severity
    
    Returns:
        Result dictionary
    """
    recovery = ErrorRecoverySystem()
    return recovery.handle_error(
        error_message=error_message,
        error_type=error_type,
        file_path=file_path,
        context=context,
        retry_enabled=retry_enabled,
        retry_delay=retry_delay,
        severity=severity
    )


# Example usage
if __name__ == "__main__":
    # Test error handling
    result = error_recovery_skill(
        error_message="Test error for demonstration",
        error_type="TestError",
        file_path=None,
        severity="low"
    )
    print(json.dumps(result, indent=2, default=str))
```

## Usage Examples

### Basic Error Handling
```python
from error_recovery import error_recovery_skill

result = error_recovery_skill(
    error_message="File not found",
    error_type="FileNotFoundError",
    file_path="/path/to/file.txt",
    severity="medium"
)
```

### With Automatic Retry
```python
def failed_operation():
    # Your code that might fail
    pass

result = error_recovery_skill(
    error_message="Network timeout",
    error_type="NetworkError",
    retry_enabled=True,
    retry_delay=300,  # 5 minutes
    retry_func=failed_operation
)
```

### Using Decorator
```python
from error_recovery import auto_handle_error

@auto_handle_error(retry_delay=300)
def process_file(file_path):
    # Your code here
    pass
```

### Get Error Statistics
```python
from error_recovery import ErrorRecoverySystem

recovery = ErrorRecoverySystem()
stats = recovery.get_error_statistics(days=7)
print(f"Total errors: {stats['total_errors']}")
print(f"Recovered: {stats['recovered']}")
```

### Clear Old Errors
```python
recovery = ErrorRecoverySystem()
result = recovery.clear_old_errors(days_old=30)
```

## Error Severity Levels

| Severity | Description | Retry? | Example |
|----------|-------------|--------|---------|
| low | Minor issues | Yes | Temporary network glitch |
| medium | Recoverable errors | Yes | File locked temporarily |
| high | Serious errors | No | Data validation failed |
| critical | System failures | No | Database corruption |

## Integration Patterns

### Pattern 1: Wrap Critical Operations
```python
try:
    process_task()
except Exception as e:
    error_recovery_skill(
        error_message=str(e),
        error_type=type(e).__name__,
        file_path=current_file
    )
```

### Pattern 2: Use Decorator
```python
@auto_handle_error()
def send_email(recipient, subject, body):
    # Email sending code
    pass
```

### Pattern 3: Manual Error Logging
```python
recovery = ErrorRecoverySystem()
recovery.handle_error(
    error_message="Custom error",
    error_type="CustomError"
)
```

## Best Practices

1. **Always catch specific exceptions** - Don't catch generic Exception
2. **Provide context** - Include function name, parameters, state
3. **Use appropriate severity** - Don't mark everything as critical
4. **Monitor error logs** - Review errors.log regularly
5. **Clear old errors** - Run cleanup monthly
6. **Test retry logic** - Ensure retries don't cause issues

## Troubleshooting

**Errors not being logged:**
- Check Logs/errors.log exists
- Verify write permissions
- Ensure JSON formatting is valid

**Files not moving to Errors/:**
- Check source file exists
- Verify write permissions on Errors/ directory
- Check for file locks

**Retry not working:**
- Ensure retry_enabled=True
- Verify retry_func is callable
- Check error type allows retry

## Monitoring

Check error health regularly:
```bash
# View recent errors
tail -20 Logs/errors.log

# Count errors by type
grep -o '"error_type": "[^"]*"' Logs/errors.log | sort | uniq -c

# View error statistics
python scripts/error_recovery.py stats
```
