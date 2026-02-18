# vault-watcher

## Description
A Claude Agent Skill that monitors multiple sources for new items and converts them into structured task reports. Provides modular detection and conversion without embedded business logic.

## Parameters
- `sources` (list, optional): List of sources to monitor. Default: ["local_inbox"]
- `check_interval` (int, optional): Seconds between checks. Default: 60
- `dry_run` (bool, optional): If True, only detect without creating reports. Default: False

## Functionality
When invoked, this skill:
1. Monitors configured sources (local Inbox folder, Gmail inbox via API placeholder)
2. Detects new items since last check
3. Generates structured markdown reports for new items
4. Saves reports to Needs_Action folder
5. Logs all detection events
6. Prevents duplicate processing through tracking
7. Complies with Silver Tier requirements

## Constraints
- Modular architecture - detection and conversion separated
- No business logic inside watcher
- Only detection + conversion responsibilities
- No external API calls (Gmail via placeholder)
- Local vault operations only
- Silver Tier compliant

## Sources

| Source | Type | Status |
|--------|------|--------|
| local_inbox | Folder | Active |
| gmail_inbox | API Placeholder | Configurable |

## Implementation
```python
import os
import json
import hashlib
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

# ============================================================================
# Configuration
# ============================================================================

VAULT_FOLDERS = {
    "inbox": "Inbox",
    "needs_action": "Needs_Action",
    "logs": "Logs"
}

DEFAULT_CHECK_INTERVAL = 60  # seconds
DEFAULT_SOURCES = ["local_inbox"]

# ============================================================================
# Data Models
# ============================================================================

class DetectedItem:
    """Represents a detected item from any source."""
    
    def __init__(self, source: str, item_id: str, title: str, 
                 content: str, metadata: Dict[str, Any], timestamp: datetime):
        self.source = source
        self.item_id = item_id
        self.title = title
        self.content = content
        self.metadata = metadata
        self.timestamp = timestamp
        self.unique_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate unique hash for duplicate prevention."""
        content = f"{self.source}:{self.item_id}:{self.title}:{self.content}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "source": self.source,
            "item_id": self.item_id,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "unique_hash": self.unique_hash
        }

# ============================================================================
# Detector Interface (Abstract Base Class)
# ============================================================================

class SourceDetector(ABC):
    """Abstract base class for all source detectors."""
    
    @abstractmethod
    def detect_new_items(self, last_check: Optional[datetime] = None) -> List[DetectedItem]:
        """
        Detect new items from the source.
        
        Args:
            last_check: Timestamp of last check for incremental detection
        
        Returns:
            List of newly detected items
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this source."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this source is available/configured."""
        pass

# ============================================================================
# Local Inbox Detector
# ============================================================================

class LocalInboxDetector(SourceDetector):
    """Detects new files in the local Inbox folder."""
    
    def __init__(self, inbox_path: str = None):
        self.inbox_path = inbox_path or VAULT_FOLDERS["inbox"]
        self._processed_files = set()
    
    def get_source_name(self) -> str:
        return "local_inbox"
    
    def is_available(self) -> bool:
        """Check if inbox folder exists or can be created."""
        return True  # Folder will be created if missing
    
    def detect_new_items(self, last_check: Optional[datetime] = None) -> List[DetectedItem]:
        """Detect new files in the inbox folder."""
        items = []
        
        # Ensure inbox folder exists
        if not os.path.exists(self.inbox_path):
            os.makedirs(self.inbox_path, exist_ok=True)
            return items  # Empty inbox
        
        # Scan for files
        try:
            for filename in os.listdir(self.inbox_path):
                filepath = os.path.join(self.inbox_path, filename)
                
                # Skip directories and already processed files
                if os.path.isdir(filepath):
                    continue
                
                if filepath in self._processed_files:
                    continue
                
                # Read file content
                content = self._read_file(filepath)
                
                # Create detected item
                item = DetectedItem(
                    source=self.get_source_name(),
                    item_id=filepath,
                    title=filename,
                    content=content,
                    metadata={
                        "filepath": filepath,
                        "filename": filename,
                        "size": os.path.getsize(filepath),
                        "modified": datetime.fromtimestamp(
                            os.path.getmtime(filepath)
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    },
                    timestamp=datetime.now()
                )
                
                items.append(item)
                self._processed_files.add(filepath)
        
        except PermissionError as e:
            # Log permission error but continue
            print(f"Permission denied accessing inbox: {str(e)}")
        except OSError as e:
            print(f"OS error accessing inbox: {str(e)}")
        
        return items
    
    def _read_file(self, filepath: str) -> str:
        """Read file content safely."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return "[Binary file - content not readable]"
        except Exception as e:
            return f"[Error reading file: {str(e)}]"

# ============================================================================
# Gmail Detector (API Placeholder)
# ============================================================================

class GmailDetector(SourceDetector):
    """
    Detects new emails from Gmail inbox.
    
    Note: This is a placeholder implementation.
    To enable Gmail monitoring, implement the _connect_to_gmail()
    and _fetch_emails() methods with actual Gmail API integration.
    """
    
    def __init__(self, api_config: Dict[str, str] = None):
        self.api_config = api_config or {}
        self._processed_emails = set()
        self._is_configured = bool(api_config.get('credentials'))
    
    def get_source_name(self) -> str:
        return "gmail_inbox"
    
    def is_available(self) -> bool:
        """Check if Gmail API is configured."""
        return self._is_configured
    
    def detect_new_items(self, last_check: Optional[datetime] = None) -> List[DetectedItem]:
        """Detect new emails from Gmail inbox."""
        items = []
        
        if not self.is_available():
            return items  # Gmail not configured
        
        try:
            # Connect to Gmail (placeholder)
            service = self._connect_to_gmail()
            
            # Fetch new emails
            emails = self._fetch_emails(service, last_check)
            
            for email in emails:
                # Skip already processed emails
                if email.get('id') in self._processed_emails:
                    continue
                
                # Create detected item
                item = DetectedItem(
                    source=self.get_source_name(),
                    item_id=email.get('id', ''),
                    title=email.get('subject', 'No Subject'),
                    content=email.get('body', ''),
                    metadata={
                        "from": email.get('from', ''),
                        "to": email.get('to', ''),
                        "date": email.get('date', ''),
                        "labels": email.get('labels', []),
                        "attachments": email.get('attachments', [])
                    },
                    timestamp=datetime.now()
                )
                
                items.append(item)
                self._processed_emails.add(email.get('id'))
        
        except NotImplementedError:
            # API not implemented - this is expected for placeholder
            pass
        except Exception as e:
            print(f"Gmail detection error: {str(e)}")
        
        return items
    
    def _connect_to_gmail(self):
        """
        Connect to Gmail API.
        
        TODO: Implement with actual Gmail API credentials.
        Required setup:
        1. Enable Gmail API in Google Cloud Console
        2. Download credentials.json
        3. Implement OAuth2 authentication
        """
        raise NotImplementedError(
            "Gmail API integration not implemented. "
            "Configure API credentials to enable Gmail monitoring."
        )
    
    def _fetch_emails(self, service, last_check: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch emails from Gmail.
        
        TODO: Implement with actual Gmail API calls.
        """
        raise NotImplementedError("Gmail API integration not implemented.")

# ============================================================================
# Report Generator (Converter)
# ============================================================================

class ReportGenerator:
    """Generates structured markdown reports from detected items."""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or VAULT_FOLDERS["needs_action"]
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_report(self, item: DetectedItem) -> str:
        """
        Generate a structured markdown report from a detected item.
        
        Args:
            item: The detected item to convert
        
        Returns:
            Path to the generated report file
        """
        # Generate filename
        timestamp = item.timestamp.strftime("%Y%m%d_%H%M%S")
        safe_title = self._sanitize_filename(item.title)
        filename = f"task_{item.source}_{timestamp}_{safe_title}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # Generate report content
        content = self._build_report_content(item, timestamp)
        
        # Write report
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _sanitize_filename(self, title: str) -> str:
        """Sanitize title for use in filename."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, '_')
        
        # Limit length
        return title[:50] if len(title) > 50 else title
    
    def _build_report_content(self, item: DetectedItem, timestamp: str) -> str:
        """Build the markdown report content."""
        content = f"""# New Task Detected

**Detected:** {item.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Source:** {item.source}
**Item ID:** {item.item_id}
**Unique Hash:** {item.unique_hash[:16]}...

---

## Title

{item.title}

---

## Content

{item.content}

---

## Metadata

| Field | Value |
|-------|-------|
"""
        
        # Add metadata rows
        for key, value in item.metadata.items():
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            content += f"| {key} | {value} |\n"
        
        content += f"""
---

## Action Items

- [ ] Review task details
- [ ] Determine priority and deadline
- [ ] Create action plan
- [ ] Execute required actions
- [ ] Mark as complete

---

## Notes

Add any additional context or notes here.

---

*Report generated automatically by vault-watcher skill.*
*Timestamp: {timestamp}*
"""
        
        return content

# ============================================================================
# Event Logger
# ============================================================================

class EventLogger:
    """Logs detection events in structured JSON format."""
    
    def __init__(self, logs_dir: str = None):
        self.logs_dir = logs_dir or VAULT_FOLDERS["logs"]
        self._ensure_logs_dir()
    
    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, exist_ok=True)
    
    def log_event(self, event_type: str, item: DetectedItem, 
                  report_path: str = None, status: str = "success"):
        """
        Log a detection event.
        
        Args:
            event_type: Type of event (detected, converted, error)
            item: The detected item
            report_path: Path to generated report (if applicable)
            status: Event status
        """
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": event_type,
            "item": item.to_dict(),
            "report_path": report_path,
            "status": status
        }
        
        self._write_log(log_entry)
    
    def log_error(self, error_type: str, message: str, details: Dict = None):
        """Log an error event."""
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "event_type": "error",
            "error_type": error_type,
            "message": message,
            "details": details or {},
            "status": "error"
        }
        
        self._write_log(log_entry)
    
    def _write_log(self, log_entry: Dict):
        """Write log entry to daily log file."""
        try:
            log_filename = f"vault_watcher_{datetime.now().strftime('%Y%m%d')}.json"
            log_filepath = os.path.join(self.logs_dir, log_filename)
            
            # Read existing logs
            existing_logs = []
            if os.path.exists(log_filepath):
                with open(log_filepath, 'r', encoding='utf-8') as f:
                    try:
                        existing_logs = json.load(f)
                    except json.JSONDecodeError:
                        existing_logs = []
            
            # Append new entry
            existing_logs.append(log_entry)
            
            # Write back
            with open(log_filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, indent=2, default=str)
        
        except Exception as e:
            print(f"Failed to write log: {str(e)}")

# ============================================================================
# Duplicate Tracker
# ============================================================================

class DuplicateTracker:
    """Tracks processed items to prevent duplicate processing."""
    
    def __init__(self, tracking_file: str = None):
        self.tracking_file = tracking_file or os.path.join(
            VAULT_FOLDERS["logs"], "vault_watcher_tracking.json"
        )
        self._processed_hashes = self._load_tracking_data()
    
    def _load_tracking_data(self) -> set:
        """Load previously processed item hashes."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('processed_hashes', []))
            except (json.JSONDecodeError, KeyError):
                pass
        return set()
    
    def is_processed(self, item_hash: str) -> bool:
        """Check if an item has already been processed."""
        return item_hash in self._processed_hashes
    
    def mark_processed(self, item_hash: str):
        """Mark an item as processed."""
        self._processed_hashes.add(item_hash)
        self._save_tracking_data()
    
    def _save_tracking_data(self):
        """Save tracking data to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
            
            data = {
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "processed_hashes": list(self._processed_hashes)
            }
            
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Failed to save tracking data: {str(e)}")

# ============================================================================
# Main Vault Watcher
# ============================================================================

class VaultWatcher:
    """Main vault watcher orchestrator."""
    
    def __init__(self, sources: List[str] = None, gmail_config: Dict = None):
        """
        Initialize the vault watcher.
        
        Args:
            sources: List of source names to monitor
            gmail_config: Gmail API configuration (optional)
        """
        self.sources = sources or DEFAULT_SOURCES
        self.detectors = self._initialize_detectors(gmail_config)
        self.report_generator = ReportGenerator()
        self.event_logger = EventLogger()
        self.duplicate_tracker = DuplicateTracker()
        self.last_check = datetime.now()
    
    def _initialize_detectors(self, gmail_config: Dict = None) -> Dict[str, SourceDetector]:
        """Initialize source detectors."""
        detectors = {}
        
        # Local inbox detector
        detectors["local_inbox"] = LocalInboxDetector()
        
        # Gmail detector (if configured)
        if gmail_config:
            detectors["gmail_inbox"] = GmailDetector(gmail_config)
        
        return detectors
    
    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run the vault watcher.
        
        Args:
            dry_run: If True, only detect without creating reports
        
        Returns:
            Summary of watcher execution
        """
        summary = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "sources_checked": [],
            "items_detected": 0,
            "reports_created": 0,
            "errors": []
        }
        
        for source_name in self.sources:
            detector = self.detectors.get(source_name)
            
            if not detector:
                summary["errors"].append(f"Unknown source: {source_name}")
                continue
            
            if not detector.is_available():
                summary["errors"].append(f"Source not available: {source_name}")
                continue
            
            summary["sources_checked"].append(source_name)
            
            # Detect new items
            try:
                items = detector.detect_new_items(self.last_check)
                summary["items_detected"] += len(items)
                
                # Process detected items
                for item in items:
                    # Check for duplicates
                    if self.duplicate_tracker.is_processed(item.unique_hash):
                        self.event_logger.log_event(
                            "duplicate_skipped", item, status="skipped"
                        )
                        continue
                    
                    if not dry_run:
                        # Generate report
                        try:
                            report_path = self.report_generator.generate_report(item)
                            summary["reports_created"] += 1
                            
                            # Log success
                            self.event_logger.log_event(
                                "item_converted", item, 
                                report_path=report_path, status="success"
                            )
                            
                            # Mark as processed
                            self.duplicate_tracker.mark_processed(item.unique_hash)
                        
                        except Exception as e:
                            self.event_logger.log_error(
                                "report_generation_error", str(e),
                                {"item": item.to_dict()}
                            )
                            summary["errors"].append(
                                f"Failed to generate report for {item.title}: {str(e)}"
                            )
                    else:
                        # Dry run - just log detection
                        self.event_logger.log_event(
                            "item_detected", item, status="dry_run"
                        )
            
            except Exception as e:
                self.event_logger.log_error(
                    "detection_error", str(e),
                    {"source": source_name}
                )
                summary["errors"].append(f"Detection error for {source_name}: {str(e)}")
        
        # Update last check time
        self.last_check = datetime.now()
        
        return summary

# ============================================================================
# Skill Entry Point
# ============================================================================

def vault_watcher_skill(sources: List[str] = None, 
                        gmail_config: Dict = None,
                        dry_run: bool = False) -> Dict[str, Any]:
    """
    Main entry point for the vault-watcher skill.
    
    Args:
        sources: List of sources to monitor (default: ["local_inbox"])
        gmail_config: Gmail API configuration (optional)
        dry_run: If True, only detect without creating reports
    
    Returns:
        Execution summary dictionary
    """
    watcher = VaultWatcher(sources=sources, gmail_config=gmail_config)
    return watcher.run(dry_run=dry_run)

# Convenience functions

def watch_local_inbox(dry_run: bool = False) -> Dict[str, Any]:
    """Watch only the local inbox folder."""
    return vault_watcher_skill(sources=["local_inbox"], dry_run=dry_run)

def watch_all_sources(gmail_config: Dict = None, 
                      dry_run: bool = False) -> Dict[str, Any]:
    """Watch all configured sources."""
    sources = ["local_inbox"]
    if gmail_config:
        sources.append("gmail_inbox")
    return vault_watcher_skill(sources=sources, gmail_config=gmail_config, dry_run=dry_run)

# Execute the skill when called
if __name__ == "__main__":
    # Example usage
    print("Vault Watcher - Monitoring Sources")
    print("=" * 50)
    
    # Run watcher
    summary = watch_local_inbox(dry_run=False)
    
    # Print summary
    print(f"Sources checked: {summary['sources_checked']}")
    print(f"Items detected: {summary['items_detected']}")
    print(f"Reports created: {summary['reports_created']}")
    
    if summary['errors']:
        print(f"Errors: {summary['errors']}")
```

## Usage Examples

### Example 1: Watch Local Inbox
```python
from vault_watcher import watch_local_inbox

result = watch_local_inbox()
# Returns: {"timestamp": "...", "sources_checked": ["local_inbox"], 
#           "items_detected": 2, "reports_created": 2, "errors": []}
```

### Example 2: Dry Run (Detection Only)
```python
from vault_watcher import watch_local_inbox

result = watch_local_inbox(dry_run=True)
# Detects items but doesn't create reports
```

### Example 3: Watch All Sources (with Gmail)
```python
from vault_watcher import watch_all_sources

gmail_config = {
    "credentials": "path/to/credentials.json",
    "token": "path/to/token.json"
}

result = watch_all_sources(gmail_config=gmail_config)
```

### Example 4: Custom Sources
```python
from vault_watcher import vault_watcher_skill

result = vault_watcher_skill(sources=["local_inbox"])
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Vault Watcher                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Detectors     │    │   Converters    │                │
│  │  (Detection)    │───▶│  (Conversion)   │                │
│  │                 │    │                 │                │
│  │ - LocalInbox    │    │ - ReportGen     │                │
│  │ - Gmail (API)   │    │ - Markdown      │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                     │                          │
│           ▼                     ▼                          │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  Duplicate      │    │   Event         │                │
│  │  Tracker        │    │   Logger        │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Generated Report Format

```markdown
# New Task Detected

**Detected:** 2024-01-15 10:30:00
**Source:** local_inbox
**Item ID:** Inbox/task.txt
**Unique Hash:** a1b2c3d4e5f6...

---

## Title

task.txt

---

## Content

[File content here]

---

## Metadata

| Field | Value |
|-------|-------|
| filepath | Inbox/task.txt |
| filename | task.txt |
| size | 1024 |
| modified | 2024-01-15 10:00:00 |

---

## Action Items

- [ ] Review task details
- [ ] Determine priority and deadline
- [ ] Create action plan
- [ ] Execute required actions
- [ ] Mark as complete

---

*Report generated automatically by vault-watcher skill.*
```

## Log Format

```json
{
  "timestamp": "2024-01-15 10:30:00",
  "event_type": "item_converted",
  "item": {
    "source": "local_inbox",
    "item_id": "Inbox/task.txt",
    "title": "task.txt",
    "unique_hash": "a1b2c3d4e5f6..."
  },
  "report_path": "Needs_Action/task_local_inbox_20240115_103000_task.txt.md",
  "status": "success"
}
```

## Compliance Notes

- **Silver Tier Compliant:** Yes
- **Modular Architecture:** Yes (detectors, converters, loggers separated)
- **No Business Logic:** Only detection + conversion
- **Duplicate Prevention:** Hash-based tracking
- **External API Calls:** None (Gmail via placeholder)
- **Local Operations Only:** Yes
- **Structured Logging:** JSON format