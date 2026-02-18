#!/usr/bin/env python3
"""
Browser + File Operations MCP Server - Production Ready

A unified MCP server combining browser automation (Playwright) and file operations.
Uses stdin/stdout JSON protocol for communication.

Browser Capabilities (Playwright):
- navigate(url)
- click(selector)
- fill(selector, text)
- get_text(selector)
- screenshot(path)
- linkedin_post(message)

File Capabilities:
- read_file(path)
- write_file(path, content)
- move_file(source, dest)
- delete_file(path, require_approval=True)
- list_files(directory, pattern)
- parse_csv(path)
- parse_json(path)

Protocol:
- Read JSON requests from stdin (one per line)
- Write JSON responses to stdout
- Flush stdout after each response
- Log errors to /Logs/fileops_mcp.log (not stdout)

Usage:
    python server.py
"""

import sys
import os
import json
import time
import shutil
import csv
import fnmatch
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Server configuration from environment variables."""
    
    def __init__(self):
        """Load configuration from environment."""
        self._load_env()
        
        # Browser configuration
        self.BROWSER_TYPE = os.environ.get('BROWSER_TYPE', 'chromium')
        self.BROWSER_HEADLESS = os.environ.get('BROWSER_HEADLESS', 'true').lower() == 'true'
        self.BROWSER_TIMEOUT = int(os.environ.get('BROWSER_TIMEOUT', '30'))
        
        # Session directory for persistent browser sessions
        self.SESSION_DIR = Path(os.environ.get('SESSION_DIR', ''))
        if not self.SESSION_DIR.exists():
            self.SESSION_DIR = Path(__file__).resolve().parent.parent.parent / ".browser_session"
        self.SESSION_DIR.mkdir(parents=True, exist_ok=True)
        
        # Vault configuration
        self.VAULT_PATH = Path(os.environ.get('VAULT_PATH', ''))
        if not self.VAULT_PATH.exists():
            self.VAULT_PATH = Path(__file__).resolve().parent.parent.parent
        
        # Allowed directories for file operations (security whitelist)
        allowed_dirs = os.environ.get('ALLOWED_DIRECTORIES', str(self.VAULT_PATH))
        self.ALLOWED_DIRECTORIES = [Path(d.strip()) for d in allowed_dirs.split(',')]
        
        # Paths
        self.LOGS_DIR = self.VAULT_PATH / "Logs"
        self.SCREENSHOTS_DIR = self.VAULT_PATH / "Screenshots"
        
        # Ensure directories exist
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_env(self):
        """Load .env file if it exists."""
        env_files = [
            Path(__file__).parent / ".env",
            Path(__file__).parent.parent.parent / ".env",
        ]
        
        for env_file in env_files:
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                os.environ[key.strip()] = value.strip()
                except Exception:
                    pass
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        try:
            path = path.resolve()
            for allowed_dir in self.ALLOWED_DIRECTORIES:
                allowed_dir = allowed_dir.resolve()
                # Check if path is within or equal to allowed directory
                if str(path).startswith(str(allowed_dir)) or path == allowed_dir:
                    return True
            return False
        except Exception:
            return False


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """Structured audit logging for file and browser operations."""
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self.log_file = None
        self._rotate_log()
    
    def _rotate_log(self):
        """Rotate log file daily."""
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.logs_dir / f"fileops_audit_{today}.json"
        
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log(self, operation_type: str, operation: str, details: Dict[str, Any], success: bool):
        """Log an operation."""
        try:
            self._rotate_log()
            
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            entry = {
                'timestamp': datetime.now().isoformat(),
                'operation_type': operation_type,  # 'browser' or 'file'
                'operation': operation,
                'success': success,
                'details': details
            }
            logs.append(entry)
            
            # Keep last 1000 entries
            logs = logs[-1000:]
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
                
        except Exception as e:
            self._log_error(f"Audit logging failed: {str(e)}")
    
    def _log_error(self, message: str):
        """Log error to error log."""
        error_file = self.logs_dir / "fileops_mcp.log"
        try:
            with open(error_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {message}\n")
        except Exception:
            pass


# ============================================================================
# Browser Manager (Playwright)
# ============================================================================

class BrowserManager:
    """Manages browser automation with Playwright."""
    
    def __init__(self, config: Config, audit_logger: AuditLogger):
        self.config = config
        self.audit_logger = audit_logger
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
    
    def _ensure_playwright(self):
        """Ensure Playwright is imported and initialized."""
        if self.playwright is None:
            try:
                from playwright.sync_api import sync_playwright
                self.playwright = sync_playwright().start()
            except ImportError:
                raise Exception("Playwright not installed. Run: pip install playwright && playwright install")
    
    def _ensure_browser(self):
        """Ensure browser is launched."""
        if self.browser is None:
            self._ensure_playwright()
            
            if self.config.BROWSER_TYPE == 'chromium':
                browser_launcher = self.playwright.chromium
            elif self.config.BROWSER_TYPE == 'firefox':
                browser_launcher = self.playwright.firefox
            else:
                browser_launcher = self.playwright.webkit
            
            # Load persistent context if exists
            user_data_dir = self.config.SESSION_DIR / self.config.BROWSER_TYPE
            
            self.context = browser_launcher.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=self.config.BROWSER_HEADLESS,
                viewport={'width': 1920, 'height': 1080},
                timeout=self.config.BROWSER_TIMEOUT * 1000
            )
            
            self.browser = self.context
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.page.set_default_timeout(self.config.BROWSER_TIMEOUT * 1000)
    
    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        start_time = datetime.now()
        
        try:
            self._ensure_browser()
            self.page.goto(url, wait_until='networkidle')
            
            self.audit_logger.log('browser', 'navigate', {
                'url': url,
                'title': self.page.title(),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'browser.navigate',
                'result': {
                    'url': url,
                    'title': self.page.title()
                }
            }
            
        except Exception as e:
            self.audit_logger.log('browser', 'navigate', {
                'url': url,
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'browser.navigate',
                'error': f'Failed to navigate: {str(e)}',
                'error_code': 'NAVIGATION_FAILED'
            }
    
    def click(self, selector: str) -> Dict[str, Any]:
        """Click an element."""
        start_time = datetime.now()
        
        try:
            self._ensure_browser()
            self.page.click(selector)
            
            self.audit_logger.log('browser', 'click', {
                'selector': selector,
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'browser.click',
                'result': {
                    'selector': selector
                }
            }
            
        except Exception as e:
            self.audit_logger.log('browser', 'click', {
                'selector': selector,
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'browser.click',
                'error': f'Failed to click: {str(e)}',
                'error_code': 'CLICK_FAILED'
            }
    
    def fill(self, selector: str, text: str) -> Dict[str, Any]:
        """Fill text into an input field."""
        start_time = datetime.now()
        
        try:
            self._ensure_browser()
            self.page.fill(selector, text)
            
            self.audit_logger.log('browser', 'fill', {
                'selector': selector,
                'text_length': len(text),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'browser.fill',
                'result': {
                    'selector': selector,
                    'text': text
                }
            }
            
        except Exception as e:
            self.audit_logger.log('browser', 'fill', {
                'selector': selector,
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'browser.fill',
                'error': f'Failed to fill: {str(e)}',
                'error_code': 'FILL_FAILED'
            }
    
    def get_text(self, selector: str) -> Dict[str, Any]:
        """Get text content from an element."""
        start_time = datetime.now()
        
        try:
            self._ensure_browser()
            text = self.page.text_content(selector)
            
            self.audit_logger.log('browser', 'get_text', {
                'selector': selector,
                'text_length': len(text) if text else 0,
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'browser.get_text',
                'result': {
                    'selector': selector,
                    'text': text
                }
            }
            
        except Exception as e:
            self.audit_logger.log('browser', 'get_text', {
                'selector': selector,
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'browser.get_text',
                'error': f'Failed to get text: {str(e)}',
                'error_code': 'GET_TEXT_FAILED'
            }
    
    def screenshot(self, path: str = None) -> Dict[str, Any]:
        """Take a screenshot."""
        start_time = datetime.now()
        
        try:
            self._ensure_browser()
            
            if path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                path = str(self.config.SCREENSHOTS_DIR / f"screenshot_{timestamp}.png")
            
            self.page.screenshot(path=path, full_page=True)
            
            self.audit_logger.log('browser', 'screenshot', {
                'path': path,
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'browser.screenshot',
                'result': {
                    'path': path
                }
            }
            
        except Exception as e:
            self.audit_logger.log('browser', 'screenshot', {
                'path': path,
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'browser.screenshot',
                'error': f'Failed to take screenshot: {str(e)}',
                'error_code': 'SCREENSHOT_FAILED'
            }
    
    def linkedin_post(self, message: str) -> Dict[str, Any]:
        """Post to LinkedIn."""
        start_time = datetime.now()
        
        try:
            self._ensure_browser()
            
            # Navigate to LinkedIn
            self.page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
            time.sleep(2)  # Wait for page to load
            
            # Check if logged in (look for feed)
            if 'login' in self.page.url.lower():
                return {
                    'success': False,
                    'operation': 'browser.linkedin_post',
                    'error': 'Not logged in to LinkedIn. Please login manually first.',
                    'error_code': 'NOT_LOGGED_IN'
                }
            
            # Click "Start a post"
            try:
                self.page.click('button[aria-label="Start a post"]', timeout=5000)
                time.sleep(1)
            except Exception:
                # Try alternative selector
                self.page.click('.share-box-feed-entry__trigger', timeout=5000)
                time.sleep(1)
            
            # Fill message
            text_editor = self.page.locator('div[role="textbox"]').first
            text_editor.fill(message)
            time.sleep(0.5)
            
            # Click "Post" button
            self.page.click('button:has-text("Post")', timeout=10000)
            time.sleep(2)
            
            # Take screenshot for verification
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = str(self.config.SCREENSHOTS_DIR / f"linkedin_post_{timestamp}.png")
            self.page.screenshot(path=screenshot_path, full_page=True)
            
            self.audit_logger.log('browser', 'linkedin_post', {
                'message_length': len(message),
                'screenshot': screenshot_path,
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'browser.linkedin_post',
                'result': {
                    'screenshot_path': screenshot_path,
                    'message': message[:100] + '...' if len(message) > 100 else message
                }
            }
            
        except Exception as e:
            self.audit_logger.log('browser', 'linkedin_post', {
                'message': message[:100],
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'browser.linkedin_post',
                'error': f'Failed to post to LinkedIn: {str(e)}',
                'error_code': 'LINKEDIN_POST_FAILED'
            }
    
    def close(self):
        """Close browser."""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            self.browser = None
            self.context = None
            self.page = None
        except Exception:
            pass


# ============================================================================
# File Operations Manager
# ============================================================================

class FileOperationsManager:
    """Manages file operations with safety checks."""
    
    def __init__(self, config: Config, audit_logger: AuditLogger):
        self.config = config
        self.audit_logger = audit_logger
    
    def _validate_path(self, path: Path, operation: str) -> Dict[str, Any]:
        """Validate path is within allowed directories."""
        if not self.config.is_path_allowed(path):
            return {
                'success': False,
                'operation': operation,
                'error': f'Access denied: Path outside allowed directories',
                'error_code': 'ACCESS_DENIED',
                'path': str(path)
            }
        return None
    
    def read_file(self, path: str) -> Dict[str, Any]:
        """Read file content."""
        start_time = datetime.now()
        path = Path(path)
        
        # Validate path
        error = self._validate_path(path, 'file.read_file')
        if error:
            return error
        
        try:
            if not path.exists():
                return {
                    'success': False,
                    'operation': 'file.read_file',
                    'error': f'File not found: {path}',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.audit_logger.log('file', 'read_file', {
                'path': str(path),
                'size_bytes': len(content),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'file.read_file',
                'result': {
                    'path': str(path),
                    'content': content,
                    'size_bytes': len(content)
                }
            }
            
        except Exception as e:
            self.audit_logger.log('file', 'read_file', {
                'path': str(path),
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'file.read_file',
                'error': f'Failed to read file: {str(e)}',
                'error_code': 'READ_FAILED'
            }
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to file."""
        start_time = datetime.now()
        path = Path(path)
        
        # Validate path
        error = self._validate_path(path, 'file.write_file')
        if error:
            return error
        
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.audit_logger.log('file', 'write_file', {
                'path': str(path),
                'size_bytes': len(content),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'file.write_file',
                'result': {
                    'path': str(path),
                    'size_bytes': len(content)
                }
            }
            
        except Exception as e:
            self.audit_logger.log('file', 'write_file', {
                'path': str(path),
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'file.write_file',
                'error': f'Failed to write file: {str(e)}',
                'error_code': 'WRITE_FAILED'
            }
    
    def move_file(self, source: str, dest: str) -> Dict[str, Any]:
        """Move file from source to destination."""
        start_time = datetime.now()
        source_path = Path(source)
        dest_path = Path(dest)
        
        # Validate paths
        error = self._validate_path(source_path, 'file.move_file')
        if error:
            return error
        
        error = self._validate_path(dest_path, 'file.move_file')
        if error:
            return error
        
        try:
            if not source_path.exists():
                return {
                    'success': False,
                    'operation': 'file.move_file',
                    'error': f'Source file not found: {source_path}',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(dest_path))
            
            self.audit_logger.log('file', 'move_file', {
                'source': str(source_path),
                'destination': str(dest_path),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'file.move_file',
                'result': {
                    'source': str(source_path),
                    'destination': str(dest_path)
                }
            }
            
        except Exception as e:
            self.audit_logger.log('file', 'move_file', {
                'source': str(source_path),
                'destination': str(dest_path),
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'file.move_file',
                'error': f'Failed to move file: {str(e)}',
                'error_code': 'MOVE_FAILED'
            }
    
    def delete_file(self, path: str, require_approval: bool = True) -> Dict[str, Any]:
        """Delete file (requires approval by default)."""
        path_obj = Path(path)
        
        # Validate path
        error = self._validate_path(path_obj, 'file.delete_file')
        if error:
            return error
        
        try:
            if not path_obj.exists():
                return {
                    'success': False,
                    'operation': 'file.delete_file',
                    'error': f'File not found: {path_obj}',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            if require_approval:
                # Return approval request instead of deleting
                return {
                    'success': True,
                    'operation': 'file.delete_file',
                    'requires_approval': True,
                    'message': 'Deletion requires approval',
                    'result': {
                        'path': str(path_obj),
                        'action': 'pending_approval'
                    }
                }
            
            # Actually delete (if approved)
            path_obj.unlink()
            
            self.audit_logger.log('file', 'delete_file', {
                'path': str(path_obj),
                'approved': not require_approval,
                'duration_ms': 0
            }, success=True)
            
            return {
                'success': True,
                'operation': 'file.delete_file',
                'result': {
                    'path': str(path_obj),
                    'deleted': True
                }
            }
            
        except Exception as e:
            self.audit_logger.log('file', 'delete_file', {
                'path': str(path_obj),
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'file.delete_file',
                'error': f'Failed to delete file: {str(e)}',
                'error_code': 'DELETE_FAILED'
            }
    
    def list_files(self, directory: str, pattern: str = '*') -> Dict[str, Any]:
        """List files in directory matching pattern."""
        start_time = datetime.now()
        dir_path = Path(directory)
        
        # Validate path
        error = self._validate_path(dir_path, 'file.list_files')
        if error:
            return error
        
        try:
            if not dir_path.exists():
                return {
                    'success': False,
                    'operation': 'file.list_files',
                    'error': f'Directory not found: {dir_path}',
                    'error_code': 'DIRECTORY_NOT_FOUND'
                }
            
            if not dir_path.is_dir():
                return {
                    'success': False,
                    'operation': 'file.list_files',
                    'error': f'Not a directory: {dir_path}',
                    'error_code': 'NOT_A_DIRECTORY'
                }
            
            files = []
            for item in dir_path.glob(pattern):
                files.append({
                    'name': item.name,
                    'path': str(item),
                    'is_file': item.is_file(),
                    'is_dir': item.is_dir(),
                    'size_bytes': item.stat().st_size if item.is_file() else 0
                })
            
            self.audit_logger.log('file', 'list_files', {
                'directory': str(dir_path),
                'pattern': pattern,
                'count': len(files),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'file.list_files',
                'result': {
                    'directory': str(dir_path),
                    'pattern': pattern,
                    'files': files,
                    'count': len(files)
                }
            }
            
        except Exception as e:
            self.audit_logger.log('file', 'list_files', {
                'directory': str(dir_path),
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'file.list_files',
                'error': f'Failed to list files: {str(e)}',
                'error_code': 'LIST_FAILED'
            }
    
    def parse_csv(self, path: str) -> Dict[str, Any]:
        """Parse CSV file."""
        start_time = datetime.now()
        path_obj = Path(path)
        
        # Validate path
        error = self._validate_path(path_obj, 'file.parse_csv')
        if error:
            return error
        
        try:
            if not path_obj.exists():
                return {
                    'success': False,
                    'operation': 'file.parse_csv',
                    'error': f'File not found: {path_obj}',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            rows = []
            with open(path_obj, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            
            self.audit_logger.log('file', 'parse_csv', {
                'path': str(path_obj),
                'rows': len(rows),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'file.parse_csv',
                'result': {
                    'path': str(path_obj),
                    'rows': rows,
                    'count': len(rows)
                }
            }
            
        except Exception as e:
            self.audit_logger.log('file', 'parse_csv', {
                'path': str(path_obj),
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'file.parse_csv',
                'error': f'Failed to parse CSV: {str(e)}',
                'error_code': 'PARSE_FAILED'
            }
    
    def parse_json(self, path: str) -> Dict[str, Any]:
        """Parse JSON file."""
        start_time = datetime.now()
        path_obj = Path(path)
        
        # Validate path
        error = self._validate_path(path_obj, 'file.parse_json')
        if error:
            return error
        
        try:
            if not path_obj.exists():
                return {
                    'success': False,
                    'operation': 'file.parse_json',
                    'error': f'File not found: {path_obj}',
                    'error_code': 'FILE_NOT_FOUND'
                }
            
            with open(path_obj, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.audit_logger.log('file', 'parse_json', {
                'path': str(path_obj),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }, success=True)
            
            return {
                'success': True,
                'operation': 'file.parse_json',
                'result': {
                    'path': str(path_obj),
                    'data': data
                }
            }
            
        except Exception as e:
            self.audit_logger.log('file', 'parse_json', {
                'path': str(path_obj),
                'error': str(e)
            }, success=False)
            
            return {
                'success': False,
                'operation': 'file.parse_json',
                'error': f'Failed to parse JSON: {str(e)}',
                'error_code': 'PARSE_FAILED'
            }


# ============================================================================
# MCP Server
# ============================================================================

class FileOpsMCPServer:
    """MCP server for browser and file operations."""
    
    def __init__(self):
        """Initialize MCP server."""
        self.config = Config()
        self.audit_logger = AuditLogger(self.config.LOGS_DIR)
        self.browser_manager = BrowserManager(self.config, self.audit_logger)
        self.file_manager = FileOperationsManager(self.config, self.audit_logger)
        self.error_logger = self.config.LOGS_DIR / "fileops_mcp.log"
    
    def _log_error(self, message: str):
        """Log error to file (never to stdout)."""
        try:
            with open(self.error_logger, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {message}\n")
        except Exception:
            pass
    
    def _create_response(self, success: bool, **kwargs) -> Dict[str, Any]:
        """Create a standard response."""
        response = {
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        response.update(kwargs)
        return response
    
    def _handle_browser_method(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle browser.* methods."""
        try:
            if method == 'navigate':
                return self.browser_manager.navigate(params.get('url', ''))
            elif method == 'click':
                return self.browser_manager.click(params.get('selector', ''))
            elif method == 'fill':
                return self.browser_manager.fill(params.get('selector', ''), params.get('text', ''))
            elif method == 'get_text':
                return self.browser_manager.get_text(params.get('selector', ''))
            elif method == 'screenshot':
                return self.browser_manager.screenshot(params.get('path'))
            elif method == 'linkedin_post':
                return self.browser_manager.linkedin_post(params.get('message', ''))
            else:
                return self._create_response(
                    success=False,
                    error=f'Unknown browser method: {method}',
                    error_code='UNKNOWN_METHOD'
                )
        except Exception as e:
            self._log_error(f"Browser method error: {str(e)}\n{traceback.format_exc()}")
            return self._create_response(
                success=False,
                error=f'Browser method error: {str(e)}',
                error_code='BROWSER_ERROR'
            )
    
    def _handle_file_method(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file.* methods."""
        try:
            if method == 'read_file':
                return self.file_manager.read_file(params.get('path', ''))
            elif method == 'write_file':
                return self.file_manager.write_file(params.get('path', ''), params.get('content', ''))
            elif method == 'move_file':
                return self.file_manager.move_file(params.get('source', ''), params.get('dest', ''))
            elif method == 'delete_file':
                return self.file_manager.delete_file(
                    params.get('path', ''),
                    params.get('require_approval', True)
                )
            elif method == 'list_files':
                return self.file_manager.list_files(
                    params.get('directory', '.'),
                    params.get('pattern', '*')
                )
            elif method == 'parse_csv':
                return self.file_manager.parse_csv(params.get('path', ''))
            elif method == 'parse_json':
                return self.file_manager.parse_json(params.get('path', ''))
            else:
                return self._create_response(
                    success=False,
                    error=f'Unknown file method: {method}',
                    error_code='UNKNOWN_METHOD'
                )
        except Exception as e:
            self._log_error(f"File method error: {str(e)}\n{traceback.format_exc()}")
            return self._create_response(
                success=False,
                error=f'File method error: {str(e)}',
                error_code='FILE_ERROR'
            )
    
    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            
            # Parse method namespace
            if '.' in method:
                namespace, method_name = method.split('.', 1)
                
                if namespace == 'browser':
                    return self._handle_browser_method(method_name, params)
                elif namespace == 'file':
                    return self._handle_file_method(method_name, params)
                else:
                    return self._create_response(
                        success=False,
                        error=f'Unknown namespace: {namespace}',
                        error_code='UNKNOWN_NAMESPACE'
                    )
            else:
                return self._create_response(
                    success=False,
                    error='Method must include namespace (browser.* or file.*)',
                    error_code='MISSING_NAMESPACE'
                )
                
        except Exception as e:
            self._log_error(f"Request handling error: {str(e)}\n{traceback.format_exc()}")
            return self._create_response(
                success=False,
                error=f'Request handling error: {str(e)}',
                error_code='REQUEST_ERROR'
            )
    
    def run(self):
        """Run MCP server (stdin/stdout protocol)."""
        try:
            self._log_error("FileOps MCP Server starting...")
            
            for line in sys.stdin:
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse request
                    request = json.loads(line)
                    
                    # Handle request
                    response = self._handle_request(request)
                    
                    # Write response
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    response = self._create_response(
                        success=False,
                        error=f'Invalid JSON: {str(e)}',
                        error_code='INVALID_JSON'
                    )
                    print(json.dumps(response), flush=True)
                    self._log_error(f"Invalid JSON request: {line[:100]}")
                    
                except Exception as e:
                    response = self._create_response(
                        success=False,
                        error=f'Unexpected error: {str(e)}',
                        error_code='UNEXPECTED_ERROR'
                    )
                    print(json.dumps(response), flush=True)
                    self._log_error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
                    
        except KeyboardInterrupt:
            self._log_error("Server stopped by user")
            self.browser_manager.close()
        except Exception as e:
            self._log_error(f"Server error: {str(e)}\n{traceback.format_exc()}")
            self.browser_manager.close()
            try:
                response = self._create_response(
                    success=False,
                    error=f'Server error: {str(e)}',
                    error_code='SERVER_ERROR'
                )
                print(json.dumps(response), flush=True)
            except Exception:
                pass
    
    def shutdown(self):
        """Shutdown server gracefully."""
        self._log_error("Shutting down server...")
        self.browser_manager.close()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point."""
    server = FileOpsMCPServer()
    server.run()


if __name__ == '__main__':
    main()
