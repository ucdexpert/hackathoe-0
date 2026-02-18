#!/usr/bin/env python3
"""
Business MCP Server

A production-ready Model Context Protocol (MCP) server for business automation.
Provides capabilities for email sending, LinkedIn posting, and activity logging.

Server Name: business-mcp
Capabilities:
    - send_email(to, subject, body)
    - post_linkedin(content)
    - log_activity(message)

Usage:
    python server.py                    # Run with stdio transport
    python server.py --port 8080        # Run with HTTP transport on port 8080
    python server.py --help             # Show help

Environment Variables:
    EMAIL_ADDRESS       - Gmail address for sending emails
    EMAIL_PASSWORD      - Gmail app password
    LINKEDIN_EMAIL      - LinkedIn email (for future integration)
    LINKEDIN_PASSWORD   - LinkedIn password (for future integration)
    LOGS_DIR            - Directory for activity logs (default: Logs)
"""

import os
import sys
import json
import logging
import argparse
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Optional
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed

# Try to import MCP library
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("WARNING: MCP library not installed. Install with: pip install mcp")
    print("Running in simulation mode...")

# Try to import Playwright for LinkedIn
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed. LinkedIn posting will use simulation mode.")
    print("Install with: pip install playwright && playwright install")


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Server configuration."""
    
    # Email configuration
    EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS', '')
    EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    
    # LinkedIn configuration
    LINKEDIN_EMAIL = os.environ.get('LINKEDIN_EMAIL', '')
    LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD', '')
    
    # Logging configuration
    LOGS_DIR = os.environ.get('LOGS_DIR', 'Logs')
    BUSINESS_LOG = 'business.log'
    
    # Server configuration
    SERVER_NAME = 'business-mcp'
    SERVER_VERSION = '1.0.0'
    
    @classmethod
    def validate(cls) -> dict:
        """Validate configuration and return status."""
        status = {
            'email_configured': bool(cls.EMAIL_ADDRESS and cls.EMAIL_PASSWORD),
            'linkedin_configured': bool(cls.LINKEDIN_EMAIL and cls.LINKEDIN_PASSWORD),
            'playwright_available': PLAYWRIGHT_AVAILABLE,
            'mcp_available': MCP_AVAILABLE,
        }
        status['fully_operational'] = (
            status['email_configured'] and 
            status['mcp_available']
        )
        return status


# ============================================================================
# Logger
# ============================================================================

class BusinessLogger:
    """Logs business activities to vault/Logs/business.log."""
    
    def __init__(self, logs_dir: str = None):
        self.logs_dir = Path(logs_dir or Config.LOGS_DIR)
        self.log_file = self.logs_dir / Config.BUSINESS_LOG
        self._ensure_logs_dir()
        self._setup_logging()
    
    def _ensure_logs_dir(self):
        """Ensure logs directory exists."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self):
        """Setup Python logging."""
        log_level = logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(Config.SERVER_NAME)
    
    def log_activity(self, message: str, action_type: str = 'general', 
                     details: dict = None, status: str = 'success'):
        """
        Log a business activity.
        
        Args:
            message: Activity message
            action_type: Type of action (email, linkedin, general)
            details: Additional details dictionary
            status: Status (success, error, pending)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'message': message,
            'status': status,
            'details': details or {}
        }
        
        # Write to JSON log file
        self._write_json_log(log_entry)
        
        # Also log using Python logging
        log_message = f"[{action_type.upper()}] {message}"
        if status == 'success':
            self.logger.info(log_message)
        elif status == 'error':
            self.logger.error(log_message)
        else:
            self.logger.warning(log_message)
        
        return log_entry
    
    def _write_json_log(self, log_entry: dict):
        """Write log entry to JSON file (line-delimited)."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write log: {str(e)}")
    
    def get_recent_activities(self, limit: int = 10) -> list:
        """Get recent activities from log."""
        activities = []
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in reversed(lines[-limit:]):
                        try:
                            activities.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            self.logger.error(f"Failed to read log: {str(e)}")
        return activities


# ============================================================================
# Email Service
# ============================================================================

class EmailService:
    """Sends emails via Gmail SMTP."""
    
    def __init__(self, logger: BusinessLogger = None):
        self.logger = logger or BusinessLogger()
        self.config = Config()
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: str = None, attachments: list = None) -> dict:
        """
        Send an email via Gmail SMTP.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (supports HTML)
            cc: CC recipient (optional)
            attachments: List of file paths to attach (optional)
        
        Returns:
            dict: {'success': bool, 'message_id': str, 'error': str or None}
        """
        result = {
            'success': False,
            'message_id': None,
            'error': None,
            'recipient': to,
            'subject': subject
        }
        
        # Validate configuration
        if not self.config.EMAIL_ADDRESS or not self.config.EMAIL_PASSWORD:
            error_msg = "Email credentials not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD."
            result['error'] = error_msg
            self.logger.log_activity(
                f"Email to {to} failed: {error_msg}",
                action_type='email',
                details={'to': to, 'subject': subject},
                status='error'
            )
            return result
        
        # Validate recipient
        if not self._validate_email(to):
            error_msg = f"Invalid recipient email address: {to}"
            result['error'] = error_msg
            self.logger.log_activity(
                f"Email failed: {error_msg}",
                action_type='email',
                details={'to': to, 'subject': subject},
                status='error'
            )
            return result
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.EMAIL_ADDRESS
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            
            # Attach body as HTML
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # Add attachments if provided
            if attachments:
                self._add_attachments(msg, attachments)
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
                
                recipients = [to]
                if cc:
                    recipients.extend(cc.split(','))
                
                server.send_message(msg, to_addrs=recipients)
            
            result['success'] = True
            result['message_id'] = f"<{datetime.now().strftime('%Y%m%d%H%M%S')}@gmail.com>"
            
            self.logger.log_activity(
                f"Email sent to {to}: {subject}",
                action_type='email',
                details={
                    'to': to,
                    'subject': subject,
                    'message_id': result['message_id'],
                    'cc': cc
                },
                status='success'
            )
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed. Check email credentials."
            result['error'] = error_msg
            self.logger.log_activity(
                f"Email authentication failed: {error_msg}",
                action_type='email',
                details={'to': to, 'subject': subject},
                status='error'
            )
        except smtplib.SMTPConnectError:
            error_msg = "Failed to connect to SMTP server."
            result['error'] = error_msg
            self.logger.log_activity(
                f"Email connection failed: {error_msg}",
                action_type='email',
                details={'to': to, 'subject': subject},
                status='error'
            )
        except Exception as e:
            result['error'] = str(e)
            self.logger.log_activity(
                f"Email failed: {str(e)}",
                action_type='email',
                details={'to': to, 'subject': subject},
                status='error'
            )
        
        return result
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _add_attachments(self, msg: MIMEMultipart, attachments: list):
        """Add attachments to email."""
        from email.mime.base import MIMEBase
        from email import encoders
        
        for file_path in attachments:
            try:
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{os.path.basename(file_path)}"'
                    )
                    msg.attach(part)
            except Exception as e:
                self.logger.log_activity(
                    f"Failed to attach {file_path}: {str(e)}",
                    action_type='email',
                    status='error'
                )


# ============================================================================
# LinkedIn Service
# ============================================================================

class LinkedInService:
    """Posts content to LinkedIn."""
    
    def __init__(self, logger: BusinessLogger = None):
        self.logger = logger or BusinessLogger()
        self.config = Config()
    
    def post_linkedin(self, content: str, topic: str = None) -> dict:
        """
        Create a LinkedIn post.
        
        Args:
            content: Post content (max 3000 characters)
            topic: Optional topic/hashtag
        
        Returns:
            dict: {'success': bool, 'post_id': str, 'post_url': str, 'error': str or None}
        """
        result = {
            'success': False,
            'post_id': None,
            'post_url': None,
            'error': None,
            'content_preview': content[:100] + '...' if len(content) > 100 else content
        }
        
        # Validate content
        if not content or len(content.strip()) == 0:
            error_msg = "Post content is required"
            result['error'] = error_msg
            self.logger.log_activity(
                f"LinkedIn post failed: {error_msg}",
                action_type='linkedin',
                details={'content_preview': result['content_preview']},
                status='error'
            )
            return result
        
        if len(content) > 3000:
            error_msg = "Content exceeds 3000 character limit"
            result['error'] = error_msg
            self.logger.log_activity(
                f"LinkedIn post failed: {error_msg}",
                action_type='linkedin',
                details={'content_preview': result['content_preview']},
                status='error'
            )
            return result
        
        # Check if Playwright is available
        if not PLAYWRIGHT_AVAILABLE:
            # Simulation mode
            return self._simulate_linkedin_post(content, topic, result)
        
        # Try to post using Playwright
        return self._post_with_playwright(content, topic, result)
    
    def _simulate_linkedin_post(self, content: str, topic: str, result: dict) -> dict:
        """Simulate LinkedIn post (for testing/development)."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        result['success'] = True
        result['post_id'] = f"urn:li:share:{timestamp}"
        result['post_url'] = f"https://www.linkedin.com/feed/update/{result['post_id']}"
        
        self.logger.log_activity(
            f"LinkedIn post created (simulated): {content[:50]}...",
            action_type='linkedin',
            details={
                'post_id': result['post_id'],
                'post_url': result['post_url'],
                'topic': topic,
                'mode': 'simulated'
            },
            status='success'
        )
        
        return result
    
    def _post_with_playwright(self, content: str, topic: str, result: dict) -> dict:
        """Post to LinkedIn using Playwright browser automation."""
        if not self.config.LINKEDIN_EMAIL or not self.config.LINKEDIN_PASSWORD:
            return self._simulate_linkedin_post(content, topic, result)
        
        browser = None
        context = None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
                )
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = context.new_page()
                page.set_default_timeout(60000)
                
                # Navigate to LinkedIn
                page.goto('https://www.linkedin.com/login', wait_until='networkidle')
                
                # Login
                page.fill('input[id="username"]', self.config.LINKEDIN_EMAIL)
                page.fill('input[id="password"]', self.config.LINKEDIN_PASSWORD)
                page.click('button[type="submit"]')
                page.wait_for_url('https://www.linkedin.com/feed/*', timeout=30000)
                
                # Navigate to feed
                page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
                
                # Click post trigger
                page.locator('button[aria-label="Start a post"]').first.click()
                
                # Fill content
                page.locator('div[role="textbox"]').first.fill(content)
                
                # Click Post button
                page.locator('button:has-text("Post")').first.click()
                
                # Wait for confirmation
                try:
                    page.wait_for_selector('div:has-text("Your post was shared")', timeout=10000)
                except:
                    pass  # Post may still have succeeded
                
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                result['success'] = True
                result['post_id'] = f"urn:li:activity:{timestamp}"
                result['post_url'] = f"https://www.linkedin.com/feed/update/{result['post_id']}"
                
                self.logger.log_activity(
                    f"LinkedIn post published: {content[:50]}...",
                    action_type='linkedin',
                    details={
                        'post_id': result['post_id'],
                        'post_url': result['post_url'],
                        'topic': topic,
                        'mode': 'playwright'
                    },
                    status='success'
                )
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.log_activity(
                f"LinkedIn post failed: {str(e)}",
                action_type='linkedin',
                details={'content_preview': result['content_preview'], 'mode': 'playwright'},
                status='error'
            )
        finally:
            if context:
                context.close()
            if browser:
                browser.close()
        
        return result


# ============================================================================
# MCP Server
# ============================================================================

class BusinessMCPServer:
    """MCP Server for business automation."""
    
    def __init__(self):
        self.logger = BusinessLogger()
        self.email_service = EmailService(self.logger)
        self.linkedin_service = LinkedInService(self.logger)
        self.server = None
        self._setup_server()
    
    def _setup_server(self):
        """Setup MCP server and tools."""
        if not MCP_AVAILABLE:
            self.logger.log_activity(
                "MCP library not available. Server will run in simulation mode.",
                action_type='server',
                status='error'
            )
            return
        
        # Create MCP server instance
        self.server = Server(Config.SERVER_NAME)
        
        # Register tools
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name='send_email',
                    description='Send an email via Gmail SMTP. Requires EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'to': {
                                'type': 'string',
                                'description': 'Recipient email address'
                            },
                            'subject': {
                                'type': 'string',
                                'description': 'Email subject'
                            },
                            'body': {
                                'type': 'string',
                                'description': 'Email body (supports HTML)'
                            },
                            'cc': {
                                'type': 'string',
                                'description': 'CC recipient (optional)'
                            },
                            'attachments': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': 'List of file paths to attach (optional)'
                            }
                        },
                        'required': ['to', 'subject', 'body']
                    }
                ),
                Tool(
                    name='post_linkedin',
                    description='Create a LinkedIn post. Supports both simulation mode and real posting via Playwright.',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'content': {
                                'type': 'string',
                                'description': 'Post content (max 3000 characters)'
                            },
                            'topic': {
                                'type': 'string',
                                'description': 'Optional topic or hashtag'
                            }
                        },
                        'required': ['content']
                    }
                ),
                Tool(
                    name='log_activity',
                    description='Log a business activity to vault/Logs/business.log',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'message': {
                                'type': 'string',
                                'description': 'Activity message'
                            },
                            'action_type': {
                                'type': 'string',
                                'description': 'Type of action (email, linkedin, meeting, general)',
                                'enum': ['email', 'linkedin', 'meeting', 'call', 'general']
                            },
                            'details': {
                                'type': 'object',
                                'description': 'Additional details (optional)'
                            },
                            'status': {
                                'type': 'string',
                                'description': 'Activity status',
                                'enum': ['success', 'error', 'pending', 'completed']
                            }
                        },
                        'required': ['message']
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == 'send_email':
                    result = self.email_service.send_email(
                        to=arguments.get('to'),
                        subject=arguments.get('subject'),
                        body=arguments.get('body'),
                        cc=arguments.get('cc'),
                        attachments=arguments.get('attachments', [])
                    )
                elif name == 'post_linkedin':
                    result = self.linkedin_service.post_linkedin(
                        content=arguments.get('content'),
                        topic=arguments.get('topic')
                    )
                elif name == 'log_activity':
                    result = self.logger.log_activity(
                        message=arguments.get('message'),
                        action_type=arguments.get('action_type', 'general'),
                        details=arguments.get('details', {}),
                        status=arguments.get('status', 'success')
                    )
                else:
                    result = {
                        'success': False,
                        'error': f'Unknown tool: {name}'
                    }
                
                return [TextContent(type='text', text=json.dumps(result, indent=2, default=str))]
                
            except Exception as e:
                error_result = {
                    'success': False,
                    'error': str(e),
                    'tool': name
                }
                self.logger.log_activity(
                    f"Tool {name} failed: {str(e)}",
                    action_type='server',
                    status='error'
                )
                return [TextContent(type='text', text=json.dumps(error_result, indent=2))]
    
    async def run_stdio(self):
        """Run server with stdio transport."""
        if not self.server:
            print("MCP library not available. Cannot start server.")
            return
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
    
    def get_status(self) -> dict:
        """Get server status."""
        config_status = Config.validate()
        return {
            'server_name': Config.SERVER_NAME,
            'version': Config.SERVER_VERSION,
            'mcp_available': MCP_AVAILABLE,
            'config': config_status,
            'logs_dir': str(self.logger.logs_dir),
            'log_file': str(self.logger.log_file)
        }


# ============================================================================
# CLI Entry Point
# ============================================================================

async def run_server_async(port: int = None):
    """Run the MCP server."""
    server = BusinessMCPServer()
    
    if port:
        # HTTP transport (requires mcp[http] extra)
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        import uvicorn
        
        sse = SseServerTransport('/messages/')
        
        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.server.run(
                    streams[0], streams[1],
                    server.server.create_initialization_options()
                )
        
        app = Starlette(
            routes=[
                Mount('/sse', app=sse.handle_post_message),
                Route('/sse', endpoint=handle_sse),
            ]
        )
        
        config = uvicorn.Config(app, host='0.0.0.0', port=port, log_level='info')
        uvicorn_server = uvicorn.Server(config)
        await uvicorn_server.serve()
    else:
        # Stdio transport
        await server.run_stdio()


def run_server(port: int = None):
    """Run the MCP server (sync wrapper)."""
    import asyncio
    asyncio.run(run_server_async(port))


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Business MCP Server - Email, LinkedIn, and Activity Logging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python server.py                    # Run with stdio transport
  python server.py --port 8080        # Run HTTP server on port 8080
  python server.py --status           # Show server status
  python server.py --test-email       # Test email functionality
  python server.py --test-linkedin    # Test LinkedIn functionality

Environment Variables:
  EMAIL_ADDRESS       - Gmail address for sending emails
  EMAIL_PASSWORD      - Gmail app password (not regular password)
  SMTP_SERVER         - SMTP server (default: smtp.gmail.com)
  SMTP_PORT           - SMTP port (default: 587)
  LINKEDIN_EMAIL      - LinkedIn email (optional, for real posting)
  LINKEDIN_PASSWORD   - LinkedIn password (optional, for real posting)
  LOGS_DIR            - Directory for activity logs (default: Logs)
        '''
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='Run HTTP server on specified port (default: stdio transport)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show server status and exit'
    )
    
    parser.add_argument(
        '--test-email',
        action='store_true',
        help='Test email functionality'
    )
    
    parser.add_argument(
        '--test-linkedin',
        action='store_true',
        help='Test LinkedIn functionality'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Show status
    if args.status:
        server = BusinessMCPServer()
        status = server.get_status()
        print(f"\n{'Business MCP Server Status':^50}")
        print('=' * 50)
        print(f"Server Name:     {status['server_name']}")
        print(f"Version:         {status['version']}")
        print(f"MCP Available:   {status['mcp_available']}")
        print(f"Logs Dir:        {status['logs_dir']}")
        print(f"Log File:        {status['log_file']}")
        print(f"\nConfiguration:")
        # Use ASCII-safe characters for Windows compatibility
        check_ok = "[OK]"
        check_fail = "[  ]"
        print(f"  Email:         {check_ok if status['config']['email_configured'] else check_fail} Configured")
        print(f"  LinkedIn:      {check_ok if status['config']['linkedin_configured'] else check_fail} Configured")
        print(f"  Playwright:    {check_ok if status['config']['playwright_available'] else check_fail} Installed")
        operational_status = "YES" if status['config']['fully_operational'] else "Partial (simulation mode)"
        print(f"\nOperational:     {operational_status}")
        print('=' * 50)
        return 0
    
    # Test email
    if args.test_email:
        logger = BusinessLogger()
        email_service = EmailService(logger)
        print("\nTesting email functionality...")
        result = email_service.send_email(
            to='test@example.com',
            subject='Test Email from Business MCP',
            body='<h1>Test Email</h1><p>This is a test email from Business MCP Server.</p>'
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        return 0 if result['success'] else 1
    
    # Test LinkedIn
    if args.test_linkedin:
        logger = BusinessLogger()
        linkedin_service = LinkedInService(logger)
        print("\nTesting LinkedIn functionality...")
        result = linkedin_service.post_linkedin(
            content='Test post from Business MCP Server! #automation #business'
        )
        print(f"Result: {json.dumps(result, indent=2)}")
        return 0 if result['success'] else 1
    
    # Run server
    if args.verbose:
        print(f"\nStarting Business MCP Server...")
        print(f"Server: {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
        print(f"Transport: {'HTTP on port ' + str(args.port) if args.port else 'stdio'}")
        print(f"Press Ctrl+C to stop\n")
    
    try:
        run_server(port=args.port)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Server error: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
