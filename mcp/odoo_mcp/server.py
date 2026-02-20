#!/usr/bin/env python3
"""
Odoo MCP Server

A production-ready Model Context Protocol (MCP) server for Odoo ERP integration.
Provides capabilities for invoice management, payment recording, and accounting summaries.

Server Name: odoo-mcp
Capabilities:
    - create_invoice(partner_id, invoice_type, lines, invoice_date, due_date, narration)
    - list_invoices(partner_id, state, limit, offset)
    - record_payment(invoice_id, amount, payment_date, reference)
    - get_account_summary(partner_id)

Usage:
    python server.py                    # Run with stdio transport
    python server.py --port 8080        # Run with HTTP transport on port 8080
    python server.py --help             # Show help

Environment Variables:
    ODOO_URL            - Odoo server URL (e.g., https://mycompany.odoo.com)
    ODOO_DB             - Odoo database name
    ODOO_USERNAME       - Odoo username/email
    ODOO_PASSWORD       - Odoo password or API key
    ODOO_PORT           - Odoo port (default: 80)
    VAULT_PATH          - Path to vault root directory
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

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

# Import local modules
from config import Config, get_config
from odoo_client import OdooClient, OdooClientError, OdooAuthenticationError, OdooConnectionError


# ============================================================================
# Logger
# ============================================================================

class OdooLogger:
    """Logs Odoo activities to vault/Logs/odoo.log."""

    def __init__(self, logs_dir: Path = None):
        config = get_config()
        self.logs_dir = logs_dir or config.LOGS_DIR
        self.log_file = self.logs_dir / config.ODOO_LOG
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
        self.logger = logging.getLogger('odoo-mcp')

    def log_activity(self, message: str, action_type: str = 'general',
                     details: dict = None, status: str = 'success'):
        """
        Log an Odoo activity.

        Args:
            message: Activity message
            action_type: Type of action (invoice, payment, summary)
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

        # Write to JSON log file (line-delimited JSON)
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
# Approval Manager
# ============================================================================

class ApprovalManager:
    """Manages approval workflow for sensitive Odoo operations."""

    def __init__(self, pending_approval_dir: Path):
        self.pending_approval_dir = pending_approval_dir
        self.pending_approval_dir.mkdir(parents=True, exist_ok=True)

    def create_approval_request(self, action: str, details: Dict) -> Dict:
        """
        Create an approval request file.

        Args:
            action: Action requiring approval
            details: Action details

        Returns:
            Dict with request ID and file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        request_id = f"{action}_{timestamp}"

        filename = f"odoo_{request_id}.md"
        filepath = self.pending_approval_dir / filename

        content = f"""# Odoo Action Approval Request

**Request ID:** {request_id}
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Action:** {action}

---

## Action Details

```json
{json.dumps(details, indent=2, default=str)}
```

---

## Approval Status

**Status:** [PENDING/APPROVED/REJECTED]

**Approved By:** _______________

**Date:** _______________

**Comments:** _______________

---

*This action requires human approval before execution.*
*Change status to APPROVED or REJECTED and save this file.*
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            'request_id': request_id,
            'filepath': str(filepath),
            'status': 'PENDING'
        }

    def check_approval_status(self, request_id: str) -> str:
        """
        Check the approval status of a request.

        Args:
            request_id: Request ID to check

        Returns:
            Status string (PENDING, APPROVED, REJECTED)
        """
        # Search for the request file
        for filepath in self.pending_approval_dir.glob(f"odoo_{request_id}*.md"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '**Status:** APPROVED' in content or '**Status:** [APPROVED' in content:
                        return 'APPROVED'
                    elif '**Status:** REJECTED' in content or '**Status:** [REJECTED' in content:
                        return 'REJECTED'
            except Exception:
                pass
        return 'PENDING'


# ============================================================================
# Odoo Service
# ============================================================================

class OdooService:
    """High-level Odoo service with approval workflow."""

    def __init__(self, logger: OdooLogger = None):
        self.logger = logger or OdooLogger()
        self.config = get_config()
        self.client: Optional[OdooClient] = None
        self.approval_manager = ApprovalManager(self.config.PENDING_APPROVAL_DIR)

    def _get_client(self) -> OdooClient:
        """Get or create Odoo client."""
        if self.client is None:
            self.client = OdooClient(self.config)
        return self.client

    def create_invoice(self, partner_id: int, invoice_type: str = 'out_invoice',
                       lines: List[Dict] = None, invoice_date: str = None,
                       due_date: str = None, narration: str = None,
                       skip_approval: bool = False) -> Dict:
        """
        Create an invoice (requires approval).

        Args:
            partner_id: Customer/partner ID
            invoice_type: Type of invoice
            lines: Invoice line items
            invoice_date: Invoice date
            due_date: Due date
            narration: Additional notes
            skip_approval: Skip approval workflow (for testing)

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'invoice_id': None,
            'error': None,
            'approval_request_id': None
        }

        # Check configuration
        if not self.config.is_configured():
            error_msg = "Odoo credentials not configured"
            result['error'] = error_msg
            self.logger.log_activity(
                f"Create invoice failed: {error_msg}",
                action_type='invoice',
                status='error'
            )
            return result

        # Create approval request
        approval_details = {
            'action': 'create_invoice',
            'partner_id': partner_id,
            'invoice_type': invoice_type,
            'lines': lines,
            'invoice_date': invoice_date,
            'due_date': due_date,
            'narration': narration
        }

        approval = self.approval_manager.create_approval_request('create_invoice', approval_details)
        result['approval_request_id'] = approval['request_id']

        if not skip_approval:
            # Check approval status
            status = self.approval_manager.check_approval_status(approval['request_id'])
            if status == 'PENDING':
                result['error'] = 'Approval pending'
                result['requires_approval'] = True
                self.logger.log_activity(
                    f"Create invoice pending approval: {approval['request_id']}",
                    action_type='invoice',
                    details=approval_details,
                    status='pending'
                )
                return result
            elif status == 'REJECTED':
                result['error'] = 'Approval rejected'
                self.logger.log_activity(
                    f"Create invoice rejected: {approval['request_id']}",
                    action_type='invoice',
                    status='error'
                )
                return result

        # Execute the action
        try:
            client = self._get_client()
            invoice_result = client.create_invoice(
                partner_id=partner_id,
                invoice_type=invoice_type,
                lines=lines,
                invoice_date=invoice_date,
                due_date=due_date,
                narration=narration
            )

            result['success'] = True
            result['invoice_id'] = invoice_result['invoice_id']
            result.update(invoice_result)

            self.logger.log_activity(
                f"Invoice created: {invoice_result['invoice_id']}",
                action_type='invoice',
                details=invoice_result,
                status='success'
            )

        except (OdooClientError, OdooAuthenticationError, OdooConnectionError) as e:
            result['error'] = str(e)
            self.logger.log_activity(
                f"Create invoice failed: {str(e)}",
                action_type='invoice',
                details=approval_details,
                status='error'
            )

        return result

    def list_invoices(self, partner_id: int = None, state: str = None,
                      limit: int = 100, offset: int = 0) -> Dict:
        """
        List invoices from Odoo.

        Args:
            partner_id: Filter by partner
            state: Filter by state
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            Dict with invoice list
        """
        result = {
            'success': False,
            'invoices': [],
            'count': 0,
            'error': None
        }

        if not self.config.is_configured():
            result['error'] = "Odoo credentials not configured"
            return result

        try:
            client = self._get_client()
            invoices = client.list_invoices(
                partner_id=partner_id,
                state=state,
                limit=limit,
                offset=offset
            )

            result['success'] = True
            result['invoices'] = invoices
            result['count'] = len(invoices)

            self.logger.log_activity(
                f"Listed {len(invoices)} invoices",
                action_type='invoice',
                details={'partner_id': partner_id, 'state': state},
                status='success'
            )

        except (OdooClientError, OdooAuthenticationError, OdooConnectionError) as e:
            result['error'] = str(e)
            self.logger.log_activity(
                f"List invoices failed: {str(e)}",
                action_type='invoice',
                status='error'
            )

        return result

    def record_payment(self, invoice_id: int, amount: float,
                       payment_date: str = None, reference: str = None,
                       skip_approval: bool = False) -> Dict:
        """
        Record a payment (requires approval).

        Args:
            invoice_id: Invoice ID
            amount: Payment amount
            payment_date: Payment date
            reference: Payment reference
            skip_approval: Skip approval workflow

        Returns:
            Dict with result
        """
        result = {
            'success': False,
            'payment_id': None,
            'error': None,
            'approval_request_id': None
        }

        if not self.config.is_configured():
            result['error'] = "Odoo credentials not configured"
            return result

        # Create approval request
        approval_details = {
            'action': 'record_payment',
            'invoice_id': invoice_id,
            'amount': amount,
            'payment_date': payment_date,
            'reference': reference
        }

        approval = self.approval_manager.create_approval_request('record_payment', approval_details)
        result['approval_request_id'] = approval['request_id']

        if not skip_approval:
            status = self.approval_manager.check_approval_status(approval['request_id'])
            if status == 'PENDING':
                result['error'] = 'Approval pending'
                result['requires_approval'] = True
                self.logger.log_activity(
                    f"Record payment pending approval: {approval['request_id']}",
                    action_type='payment',
                    details=approval_details,
                    status='pending'
                )
                return result
            elif status == 'REJECTED':
                result['error'] = 'Approval rejected'
                self.logger.log_activity(
                    f"Record payment rejected: {approval['request_id']}",
                    action_type='payment',
                    status='error'
                )
                return result

        # Execute the action
        try:
            client = self._get_client()
            payment_result = client.record_payment(
                invoice_id=invoice_id,
                amount=amount,
                payment_date=payment_date,
                reference=reference
            )

            result['success'] = True
            result.update(payment_result)

            self.logger.log_activity(
                f"Payment recorded for invoice {invoice_id}: {amount}",
                action_type='payment',
                details=payment_result,
                status='success'
            )

        except (OdooClientError, OdooAuthenticationError, OdooConnectionError) as e:
            result['error'] = str(e)
            self.logger.log_activity(
                f"Record payment failed: {str(e)}",
                action_type='payment',
                details=approval_details,
                status='error'
            )

        return result

    def get_account_summary(self, partner_id: int = None) -> Dict:
        """
        Get accounting summary.

        Args:
            partner_id: Optional partner ID

        Returns:
            Dict with summary
        """
        result = {
            'success': False,
            'summary': {},
            'error': None
        }

        if not self.config.is_configured():
            result['error'] = "Odoo credentials not configured"
            return result

        try:
            client = self._get_client()
            summary = client.get_account_summary(partner_id=partner_id)

            result['success'] = True
            result['summary'] = summary

            self.logger.log_activity(
                "Account summary retrieved",
                action_type='summary',
                details=summary,
                status='success'
            )

        except (OdooClientError, OdooAuthenticationError, OdooConnectionError) as e:
            result['error'] = str(e)
            self.logger.log_activity(
                f"Get account summary failed: {str(e)}",
                action_type='summary',
                status='error'
            )

        return result

    def search_partner(self, search_term: str, limit: int = 10) -> Dict:
        """
        Search for partners.

        Args:
            search_term: Search string
            limit: Maximum results

        Returns:
            Dict with partner list
        """
        result = {
            'success': False,
            'partners': [],
            'error': None
        }

        if not self.config.is_configured():
            result['error'] = "Odoo credentials not configured"
            return result

        try:
            client = self._get_client()
            partners = client.search_partner(search_term, limit)

            result['success'] = True
            result['partners'] = partners

            self.logger.log_activity(
                f"Found {len(partners)} partners for '{search_term}'",
                action_type='partner',
                status='success'
            )

        except (OdooClientError, OdooAuthenticationError, OdooConnectionError) as e:
            result['error'] = str(e)
            self.logger.log_activity(
                f"Search partner failed: {str(e)}",
                action_type='partner',
                status='error'
            )

        return result


# ============================================================================
# MCP Server
# ============================================================================

class OdooMCPServer:
    """MCP Server for Odoo ERP integration."""

    def __init__(self):
        self.logger = OdooLogger()
        self.service = OdooService(self.logger)
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
                    name='create_invoice',
                    description='Create a new invoice in Odoo. Requires human approval before execution. Returns approval_request_id for tracking.',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'partner_id': {
                                'type': 'integer',
                                'description': 'Customer/partner ID in Odoo'
                            },
                            'invoice_type': {
                                'type': 'string',
                                'description': 'Invoice type: out_invoice, in_invoice, out_refund, in_refund',
                                'default': 'out_invoice'
                            },
                            'lines': {
                                'type': 'array',
                                'description': 'Invoice line items',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'product_id': {'type': 'integer', 'description': 'Product ID'},
                                        'quantity': {'type': 'number', 'description': 'Quantity', 'default': 1},
                                        'price_unit': {'type': 'number', 'description': 'Unit price', 'default': 0},
                                        'name': {'type': 'string', 'description': 'Line description'}
                                    }
                                }
                            },
                            'invoice_date': {
                                'type': 'string',
                                'description': 'Invoice date (YYYY-MM-DD)'
                            },
                            'due_date': {
                                'type': 'string',
                                'description': 'Due date (YYYY-MM-DD)'
                            },
                            'narration': {
                                'type': 'string',
                                'description': 'Additional notes'
                            }
                        },
                        'required': ['partner_id']
                    }
                ),
                Tool(
                    name='list_invoices',
                    description='List invoices from Odoo with optional filters',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'partner_id': {
                                'type': 'integer',
                                'description': 'Filter by partner ID'
                            },
                            'state': {
                                'type': 'string',
                                'description': 'Filter by state: draft, posted, cancel',
                                'enum': ['draft', 'posted', 'cancel']
                            },
                            'limit': {
                                'type': 'integer',
                                'description': 'Maximum number of results',
                                'default': 100
                            },
                            'offset': {
                                'type': 'integer',
                                'description': 'Offset for pagination',
                                'default': 0
                            }
                        }
                    }
                ),
                Tool(
                    name='record_payment',
                    description='Record a payment against an invoice. Requires human approval before execution.',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'invoice_id': {
                                'type': 'integer',
                                'description': 'Invoice ID'
                            },
                            'amount': {
                                'type': 'number',
                                'description': 'Payment amount'
                            },
                            'payment_date': {
                                'type': 'string',
                                'description': 'Payment date (YYYY-MM-DD)'
                            },
                            'reference': {
                                'type': 'string',
                                'description': 'Payment reference'
                            }
                        },
                        'required': ['invoice_id', 'amount']
                    }
                ),
                Tool(
                    name='get_account_summary',
                    description='Get accounting summary from Odoo',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'partner_id': {
                                'type': 'integer',
                                'description': 'Optional partner ID for customer-specific summary'
                            }
                        }
                    }
                ),
                Tool(
                    name='search_partner',
                    description='Search for partners (customers/vendors) in Odoo',
                    inputSchema={
                        'type': 'object',
                        'properties': {
                            'search_term': {
                                'type': 'string',
                                'description': 'Search string (name or email)'
                            },
                            'limit': {
                                'type': 'integer',
                                'description': 'Maximum results',
                                'default': 10
                            }
                        },
                        'required': ['search_term']
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == 'create_invoice':
                    result = self.service.create_invoice(
                        partner_id=arguments.get('partner_id'),
                        invoice_type=arguments.get('invoice_type', 'out_invoice'),
                        lines=arguments.get('lines'),
                        invoice_date=arguments.get('invoice_date'),
                        due_date=arguments.get('due_date'),
                        narration=arguments.get('narration')
                    )
                elif name == 'list_invoices':
                    result = self.service.list_invoices(
                        partner_id=arguments.get('partner_id'),
                        state=arguments.get('state'),
                        limit=arguments.get('limit', 100),
                        offset=arguments.get('offset', 0)
                    )
                elif name == 'record_payment':
                    result = self.service.record_payment(
                        invoice_id=arguments.get('invoice_id'),
                        amount=arguments.get('amount'),
                        payment_date=arguments.get('payment_date'),
                        reference=arguments.get('reference')
                    )
                elif name == 'get_account_summary':
                    result = self.service.get_account_summary(
                        partner_id=arguments.get('partner_id')
                    )
                elif name == 'search_partner':
                    result = self.service.search_partner(
                        search_term=arguments.get('search_term'),
                        limit=arguments.get('limit', 10)
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
            print("MCP library not available. Cannot run server.")
            return 1

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

        return 0

    async def run_http(self, port: int = 8080):
        """Run server with HTTP transport."""
        if not self.server:
            print("MCP library not available. Cannot run server.")
            return 1

        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.server.run(
                    streams[0], streams[1],
                    self.server.create_initialization_options()
                )

        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
            ]
        )

        config = uvicorn.Config(app, host="0.0.0.0", port=port)
        server = uvicorn.Server(config)
        await server.serve()

        return 0


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """Command-line interface for Odoo MCP Server."""
    parser = argparse.ArgumentParser(
        description='Odoo MCP Server - ERP integration via JSON-RPC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Environment Variables:
    ODOO_URL            Odoo server URL (e.g., https://mycompany.odoo.com)
    ODOO_DB             Odoo database name
    ODOO_USERNAME       Odoo username/email
    ODOO_PASSWORD       Odoo password or API key
    ODOO_PORT           Odoo port (default: 80)

Examples:
    python server.py                    # Run with stdio transport
    python server.py --port 8080        # Run with HTTP transport
    python server.py --check-config     # Check configuration
        '''
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=None,
        help='HTTP port (default: stdio transport)'
    )
    parser.add_argument(
        '--check-config',
        action='store_true',
        help='Check configuration and exit'
    )
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test Odoo connection and exit'
    )

    args = parser.parse_args()

    # Check configuration
    if args.check_config:
        config = get_config()
        status = Config.validate()
        print(json.dumps(status, indent=2))
        sys.exit(0 if status['fully_operational'] else 1)

    # Test connection
    if args.test_connection:
        config = get_config()
        if not config.is_configured():
            print("ERROR: Odoo credentials not configured")
            sys.exit(1)

        try:
            client = OdooClient(config)
            uid = client.authenticate()
            print(f"SUCCESS: Connected to Odoo as user ID {uid}")
            client.close()
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: Connection failed: {str(e)}")
            sys.exit(1)

    # Create and run server
    server = OdooMCPServer()

    if args.port:
        import asyncio
        asyncio.run(server.run_http(args.port))
    else:
        import asyncio
        asyncio.run(server.run_stdio())


if __name__ == '__main__':
    main()
