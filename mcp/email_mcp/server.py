#!/usr/bin/env python3
"""
Email MCP Server - Production Ready

A production-ready MCP (Model Context Protocol) server for email operations.
Uses stdin/stdout JSON protocol for communication.

Capabilities:
1. send_email(to, subject, body, html=False)
2. draft_email(to, subject, body) - saves to Pending_Approval
3. validate_email(email) - check if valid

Protocol:
- Read JSON requests from stdin (one per line)
- Write JSON responses to stdout
- Flush stdout after each response
- Log errors to /Logs/email_mcp.log (not stdout)

Usage:
    python server.py

Environment Variables (from .env):
    EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, VAULT_PATH
"""

import sys
import os
import json
import smtplib
import time
import re
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import traceback
import random


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Server configuration from environment variables."""
    
    def __init__(self):
        """Load configuration from environment."""
        # Try to load .env file
        self._load_env()
        
        # Email configuration
        self.EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', '')
        self.EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
        self.SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
        
        # Vault configuration
        self.VAULT_PATH = Path(os.environ.get('VAULT_PATH', ''))
        if not self.VAULT_PATH.exists():
            # Default to parent directory
            self.VAULT_PATH = Path(__file__).resolve().parent.parent.parent
        
        # Rate limiting
        self.MAX_EMAILS_PER_HOUR = int(os.environ.get('MAX_EMAILS_PER_HOUR', '50'))
        
        # Retry configuration
        self.MAX_RETRIES = 3
        self.BASE_DELAY = 1.0  # seconds
        
        # Paths
        self.LOGS_DIR = self.VAULT_PATH / "Logs"
        self.PENDING_APPROVAL_DIR = self.VAULT_PATH / "Pending_Approval"
        
        # Ensure directories exist
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.PENDING_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    
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
                    pass  # Ignore errors, use environment variables
    
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.EMAIL_ADDRESS and self.EMAIL_PASSWORD)


# ============================================================================
# Rate Limiter
# ============================================================================

class RateLimiter:
    """Rate limiter for email sending."""
    
    def __init__(self, max_per_hour: int):
        self.max_per_hour = max_per_hour
        self.sent_times = []
        self._load_state()
    
    def _load_state(self):
        """Load rate limit state from file."""
        state_file = Config().LOGS_DIR / "email_rate_limit.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    # Convert timestamps back to datetime
                    self.sent_times = [
                        datetime.fromisoformat(ts) 
                        for ts in data.get('sent_times', [])
                    ]
            except Exception:
                self.sent_times = []
    
    def _save_state(self):
        """Save rate limit state to file."""
        state_file = Config().LOGS_DIR / "email_rate_limit.json"
        try:
            with open(state_file, 'w') as f:
                json.dump({
                    'sent_times': [ts.isoformat() for ts in self.sent_times[-self.max_per_hour:]]
                }, f, indent=2)
        except Exception:
            pass
    
    def can_send(self) -> bool:
        """Check if we can send an email."""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Remove old timestamps
        self.sent_times = [ts for ts in self.sent_times if ts > one_hour_ago]
        
        # Check limit
        return len(self.sent_times) < self.max_per_hour
    
    def record_send(self):
        """Record that an email was sent."""
        self.sent_times.append(datetime.now())
        self._save_state()
    
    def get_remaining(self) -> int:
        """Get remaining emails for this hour."""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        self.sent_times = [ts for ts in self.sent_times if ts > one_hour_ago]
        return max(0, self.max_per_hour - len(self.sent_times))


# Import timedelta here to avoid circular import
from datetime import timedelta


# ============================================================================
# Email Validator
# ============================================================================

class EmailValidator:
    """Email address validation."""
    
    # RFC 5322 compliant email regex (simplified)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Common disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.com', 'throwaway.com', 'guerrillamail.com',
        'mailinator.com', '10minutemail.com'
    }
    
    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Check if email address is valid."""
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip()
        
        # Check basic format
        if not cls.EMAIL_REGEX.match(email):
            return False
        
        # Check length
        if len(email) > 254:
            return False
        
        # Check local part length
        local_part = email.split('@')[0]
        if len(local_part) > 64:
            return False
        
        # Check for disposable domains
        domain = email.split('@')[1].lower()
        if domain in cls.DISPOSABLE_DOMAINS:
            return False
        
        return True
    
    @classmethod
    def normalize(cls, email: str) -> str:
        """Normalize email address."""
        if not email:
            return ''
        
        email = email.strip().lower()
        
        # Remove dots from Gmail addresses
        if '@gmail.com' in email:
            local, domain = email.split('@')
            local = local.replace('.', '')
            # Remove everything after +
            if '+' in local:
                local = local.split('+')[0]
            email = f"{local}@{domain}"
        
        return email


# ============================================================================
# Audit Logger
# ============================================================================

class AuditLogger:
    """Structured audit logging for email operations."""
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self.log_file = None
        self._rotate_log()
    
    def _rotate_log(self):
        """Rotate log file daily."""
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_file = self.logs_dir / f"email_audit_{today}.json"
        
        # Create file if doesn't exist
        if not self.log_file.exists():
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def log(self, operation: str, details: Dict[str, Any], success: bool):
        """Log an email operation."""
        try:
            # Check if we need to rotate
            self._rotate_log()
            
            # Load existing logs
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            # Add new entry
            entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'success': success,
                'details': details
            }
            logs.append(entry)
            
            # Save (keep last 1000 entries)
            logs = logs[-1000:]
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
                
        except Exception as e:
            # Never fail on logging errors
            self._log_error(f"Audit logging failed: {str(e)}")
    
    def _log_error(self, message: str):
        """Log error to error log."""
        error_file = self.logs_dir / "email_mcp.log"
        try:
            with open(error_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {message}\n")
        except Exception:
            pass


# ============================================================================
# Email Service
# ============================================================================

class EmailService:
    """Email sending service with retry and rate limiting."""
    
    def __init__(self, config: Config):
        self.config = config
        self.rate_limiter = RateLimiter(config.MAX_EMAILS_PER_HOUR)
        self.audit_logger = AuditLogger(config.LOGS_DIR)
    
    def send_email(self, to: str, subject: str, body: str, 
                   html: bool = False, cc: str = None, 
                   bcc: str = None, attachments: list = None) -> Dict[str, Any]:
        """
        Send an email with retry and exponential backoff.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            html: Whether body is HTML
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach
        
        Returns:
            Dict with success status and details
        """
        start_time = datetime.now()
        
        # Validate recipient
        if not EmailValidator.is_valid(to):
            return {
                'success': False,
                'error': f'Invalid recipient email address: {to}',
                'error_code': 'INVALID_EMAIL'
            }
        
        # Check rate limit
        if not self.rate_limiter.can_send():
            return {
                'success': False,
                'error': f'Rate limit exceeded. Try again in 1 hour.',
                'error_code': 'RATE_LIMIT_EXCEEDED',
                'remaining': 0
            }
        
        # Check configuration
        if not self.config.is_configured():
            return {
                'success': False,
                'error': 'Email credentials not configured',
                'error_code': 'NOT_CONFIGURED'
            }
        
        # Retry with exponential backoff
        last_error = None
        for attempt in range(1, self.config.MAX_RETRIES + 1):
            try:
                # Send email
                result = self._send_smtp_email(
                    to=to, subject=subject, body=body,
                    html=html, cc=cc, bcc=bcc,
                    attachments=attachments
                )
                
                if result['success']:
                    # Record successful send
                    self.rate_limiter.record_send()
                    
                    # Audit log
                    self.audit_logger.log('send_email', {
                        'to': to,
                        'subject': subject,
                        'html': html,
                        'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
                    }, success=True)
                    
                    return {
                        'success': True,
                        'message': 'Email sent successfully',
                        'message_id': result.get('message_id'),
                        'attempts': attempt
                    }
                
                last_error = result.get('error', 'Unknown error')
                
            except Exception as e:
                last_error = str(e)
            
            # Wait before retry (exponential backoff)
            if attempt < self.config.MAX_RETRIES:
                delay = self.config.BASE_DELAY * (2 ** (attempt - 1))
                # Add jitter
                delay = delay + random.uniform(0, 0.5 * delay)
                time.sleep(delay)
        
        # All retries failed
        self.audit_logger.log('send_email', {
            'to': to,
            'subject': subject,
            'error': last_error,
            'attempts': self.config.MAX_RETRIES
        }, success=False)
        
        return {
            'success': False,
            'error': f'Failed to send email after {self.config.MAX_RETRIES} attempts: {last_error}',
            'error_code': 'SEND_FAILED',
            'attempts': self.config.MAX_RETRIES
        }
    
    def _send_smtp_email(self, to: str, subject: str, body: str,
                         html: bool = False, cc: str = None,
                         bcc: str = None, attachments: list = None) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.EMAIL_ADDRESS
            msg['To'] = to
            
            if cc:
                msg['Cc'] = cc
            
            # Attach body
            mime_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_type, 'utf-8'))
            
            # Add attachments
            if attachments:
                from email.mime.base import MIMEBase
                from email import encoders
                
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = Path(file_path).name
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{filename}"'
                            )
                            msg.attach(part)
                    except Exception as e:
                        raise Exception(f"Failed to attach {file_path}: {str(e)}")
            
            # Send via SMTP
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
                
                # Get all recipients
                recipients = [to]
                if cc:
                    recipients.extend(cc.split(','))
                if bcc:
                    recipients.extend(bcc.split(','))
                
                server.send_message(msg, to_addrs=recipients)
            
            return {
                'success': True,
                'message_id': msg.get('Message-ID', '')
            }
            
        except smtplib.SMTPAuthenticationError:
            return {
                'success': False,
                'error': 'SMTP authentication failed. Check email credentials.',
                'error_code': 'AUTH_FAILED'
            }
        except smtplib.SMTPConnectError:
            return {
                'success': False,
                'error': 'Failed to connect to SMTP server.',
                'error_code': 'CONNECTION_FAILED'
            }
        except smtplib.SMTPException as e:
            return {
                'success': False,
                'error': f'SMTP error: {str(e)}',
                'error_code': 'SMTP_ERROR'
            }
    
    def draft_email(self, to: str, subject: str, body: str,
                    html: bool = False) -> Dict[str, Any]:
        """
        Create a draft email in Pending_Approval folder.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            html: Whether body is HTML
        
        Returns:
            Dict with draft file path
        """
        timestamp = datetime.now()
        
        # Validate recipient
        if not EmailValidator.is_valid(to):
            return {
                'success': False,
                'error': f'Invalid recipient email address: {to}'
            }
        
        # Generate filename
        filename = f"draft_{timestamp.strftime('%Y%m%d_%H%M%S')}_{subject[:20]}.md"
        draft_path = self.config.PENDING_APPROVAL_DIR / filename
        
        # Create draft content
        content = f"""# Email Draft

**To:** {to}
**Subject:** {subject}
**Created:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Format:** {'HTML' if html else 'Plain Text'}

---

## Content

{body}

---

## Instructions

This draft requires approval before sending.

### To Approve:
1. Review the email content
2. Change status below to "approved"
3. Add your name as approver

### To Reject:
1. Change status to "rejected"
2. Provide rejection reason

---

## Approval Status

**Status:** [pending/approved/rejected]

**Approved By:** [Name]

**Date:** [YYYY-MM-DD]

**Comments:** [Optional]
"""
        
        try:
            # Write draft file
            with open(draft_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Audit log
            self.audit_logger.log('draft_email', {
                'to': to,
                'subject': subject,
                'draft_path': str(draft_path)
            }, success=True)
            
            return {
                'success': True,
                'message': 'Draft created successfully',
                'draft_path': str(draft_path),
                'requires_approval': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create draft: {str(e)}'
            }


# ============================================================================
# MCP Server
# ============================================================================

class EmailMCPServer:
    """MCP server for email operations."""
    
    def __init__(self):
        """Initialize MCP server."""
        self.config = Config()
        self.email_service = EmailService(self.config)
        self.error_logger = self.config.LOGS_DIR / "email_mcp.log"
    
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
    
    def _handle_send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send_email request."""
        try:
            # Extract parameters
            to = params.get('to', '')
            subject = params.get('subject', '')
            body = params.get('body', '')
            html = params.get('html', False)
            cc = params.get('cc')
            bcc = params.get('bcc')
            attachments = params.get('attachments')
            
            # Validate required fields
            if not to:
                return self._create_response(
                    success=False,
                    error='Recipient email address is required',
                    error_code='MISSING_TO'
                )
            
            if not subject:
                return self._create_response(
                    success=False,
                    error='Email subject is required',
                    error_code='MISSING_SUBJECT'
                )
            
            if not body:
                return self._create_response(
                    success=False,
                    error='Email body is required',
                    error_code='MISSING_BODY'
                )
            
            # Send email
            result = self.email_service.send_email(
                to=to, subject=subject, body=body,
                html=html, cc=cc, bcc=bcc,
                attachments=attachments
            )
            
            return self._create_response(**result)
            
        except Exception as e:
            self._log_error(f"send_email error: {str(e)}\n{traceback.format_exc()}")
            return self._create_response(
                success=False,
                error=f'Internal error: {str(e)}',
                error_code='INTERNAL_ERROR'
            )
    
    def _handle_draft_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle draft_email request."""
        try:
            # Extract parameters
            to = params.get('to', '')
            subject = params.get('subject', '')
            body = params.get('body', '')
            html = params.get('html', False)
            
            # Validate required fields
            if not to:
                return self._create_response(
                    success=False,
                    error='Recipient email address is required',
                    error_code='MISSING_TO'
                )
            
            if not subject:
                return self._create_response(
                    success=False,
                    error='Email subject is required',
                    error_code='MISSING_SUBJECT'
                )
            
            if not body:
                return self._create_response(
                    success=False,
                    error='Email body is required',
                    error_code='MISSING_BODY'
                )
            
            # Create draft
            result = self.email_service.draft_email(
                to=to, subject=subject, body=body, html=html
            )
            
            return self._create_response(**result)
            
        except Exception as e:
            self._log_error(f"draft_email error: {str(e)}\n{traceback.format_exc()}")
            return self._create_response(
                success=False,
                error=f'Internal error: {str(e)}',
                error_code='INTERNAL_ERROR'
            )
    
    def _handle_validate_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validate_email request."""
        try:
            # Extract email
            email = params.get('email', '')
            
            if not email:
                return self._create_response(
                    success=False,
                    error='Email address is required',
                    error_code='MISSING_EMAIL'
                )
            
            # Validate
            is_valid = EmailValidator.is_valid(email)
            normalized = EmailValidator.normalize(email) if is_valid else email
            
            return self._create_response(
                success=True,
                valid=is_valid,
                email=email,
                normalized=normalized,
                message='Email is valid' if is_valid else 'Email is invalid'
            )
            
        except Exception as e:
            self._log_error(f"validate_email error: {str(e)}\n{traceback.format_exc()}")
            return self._create_response(
                success=False,
                error=f'Internal error: {str(e)}',
                error_code='INTERNAL_ERROR'
            )
    
    def _handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        try:
            method = request.get('method', '')
            params = request.get('params', {})
            
            if method == 'send_email':
                return self._handle_send_email(params)
            elif method == 'draft_email':
                return self._handle_draft_email(params)
            elif method == 'validate_email':
                return self._handle_validate_email(params)
            else:
                return self._create_response(
                    success=False,
                    error=f'Unknown method: {method}',
                    error_code='UNKNOWN_METHOD'
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
            # Log startup
            self._log_error("Email MCP Server starting...")
            
            # Process requests
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
                    # Invalid JSON - return error response
                    response = self._create_response(
                        success=False,
                        error=f'Invalid JSON: {str(e)}',
                        error_code='INVALID_JSON'
                    )
                    print(json.dumps(response), flush=True)
                    self._log_error(f"Invalid JSON request: {line[:100]}")
                    
                except Exception as e:
                    # Unexpected error - return error response
                    response = self._create_response(
                        success=False,
                        error=f'Unexpected error: {str(e)}',
                        error_code='UNEXPECTED_ERROR'
                    )
                    print(json.dumps(response), flush=True)
                    self._log_error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
                    
        except KeyboardInterrupt:
            self._log_error("Server stopped by user")
        except Exception as e:
            self._log_error(f"Server error: {str(e)}\n{traceback.format_exc()}")
            # Still try to return error response
            try:
                response = self._create_response(
                    success=False,
                    error=f'Server error: {str(e)}',
                    error_code='SERVER_ERROR'
                )
                print(json.dumps(response), flush=True)
            except Exception:
                pass


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point."""
    server = EmailMCPServer()
    server.run()


if __name__ == '__main__':
    main()
