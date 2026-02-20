#!/usr/bin/env python3
"""
Odoo JSON-RPC Client

Client for communicating with Odoo ERP via JSON-RPC API.
Supports Odoo 16+ (tested with Odoo 19).
"""

import json
import logging
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime

from config import Config, get_config


class OdooClientError(Exception):
    """Base exception for Odoo client errors."""
    pass


class OdooAuthenticationError(OdooClientError):
    """Authentication failed."""
    pass


class OdooConnectionError(OdooClientError):
    """Connection to Odoo failed."""
    pass


class OdooClient:
    """
    Odoo JSON-RPC API client.

    Implements the standard Odoo JSON-RPC protocol for:
    - Authentication
    - Model operations (read, write, create, unlink)
    - Method calls
    """

    def __init__(self, config: Config = None):
        """
        Initialize Odoo client.

        Args:
            config: Configuration object (uses singleton if not provided)
        """
        self.config = config or get_config()
        self.uid: Optional[int] = None
        self.session = requests.Session()
        self.logger = logging.getLogger(self.config.SERVER_NAME)

        # JSON-RPC settings
        self.jsonrpc_url = self.config.get_jsonrpc_url()
        self.headers = {
            'Content-Type': 'application/json',
        }

    def authenticate(self) -> int:
        """
        Authenticate with Odoo and get user ID.

        Returns:
            int: User ID (uid)

        Raises:
            OdooAuthenticationError: If authentication fails
            OdooConnectionError: If connection fails
        """
        if not self.config.is_configured():
            raise OdooAuthenticationError("Odoo credentials not configured")

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [
                    self.config.ODOO_DB,
                    self.config.ODOO_USERNAME,
                    self.config.ODOO_PASSWORD,
                    {}
                ]
            },
            "id": 1
        }

        try:
            response = self.session.post(
                self.jsonrpc_url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if 'error' in result:
                error = result['error']
                raise OdooAuthenticationError(
                    f"Authentication failed: {error.get('data', {}).get('message', str(error))}"
                )

            self.uid = result.get('result')

            if not self.uid:
                raise OdooAuthenticationError("Authentication returned empty user ID")

            self.logger.info(f"Authenticated with Odoo as user ID: {self.uid}")
            return self.uid

        except requests.exceptions.RequestException as e:
            raise OdooConnectionError(f"Failed to connect to Odoo: {str(e)}")

    def _ensure_authenticated(self):
        """Ensure client is authenticated."""
        if self.uid is None:
            self.authenticate()

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Execute a method on an Odoo model.

        Args:
            model: Model name (e.g., 'account.move')
            method: Method name (e.g., 'create', 'read', 'write')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Any: Method result
        """
        self._ensure_authenticated()

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.config.ODOO_DB,
                    self.uid,
                    self.config.ODOO_PASSWORD,
                    model,
                    method,
                    list(args),
                    kwargs
                ]
            },
            "id": 2
        }

        try:
            response = self.session.post(
                self.jsonrpc_url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if 'error' in result:
                error = result['error']
                raise OdooClientError(
                    f"Odoo error: {error.get('data', {}).get('message', str(error))}"
                )

            return result.get('result')

        except requests.exceptions.RequestException as e:
            raise OdooConnectionError(f"Failed to execute {method} on {model}: {str(e)}")

    # ========================================================================
    # Invoice Operations
    # ========================================================================

    def create_invoice(self, partner_id: int, invoice_type: str = 'out_invoice',
                       invoice_date: str = None, due_date: str = None,
                       lines: List[Dict] = None, narration: str = None) -> Dict[str, Any]:
        """
        Create a new invoice in Odoo.

        Args:
            partner_id: Customer/partner ID
            invoice_type: Type (out_invoice, in_invoice, out_refund, in_refund)
            invoice_date: Invoice date (YYYY-MM-DD)
            due_date: Due date (YYYY-MM-DD)
            lines: Invoice line items [{'product_id': int, 'quantity': float, 'price_unit': float}]
            narration: Additional notes

        Returns:
            Dict with invoice ID and details
        """
        self._ensure_authenticated()

        invoice_vals = {
            'partner_id': partner_id,
            'move_type': invoice_type,
        }

        if invoice_date:
            invoice_vals['invoice_date'] = invoice_date

        if due_date:
            invoice_vals['invoice_date_due'] = due_date

        if narration:
            invoice_vals['narration'] = narration

        # Add invoice lines if provided
        if lines:
            invoice_lines = []
            for line in lines:
                invoice_lines.append((0, 0, {
                    'product_id': line.get('product_id'),
                    'quantity': line.get('quantity', 1),
                    'price_unit': line.get('price_unit', 0),
                    'name': line.get('name', 'Invoice line')
                }))
            invoice_vals['invoice_line_ids'] = invoice_lines

        invoice_id = self.execute('account.move', 'create', invoice_vals)

        return {
            'success': True,
            'invoice_id': invoice_id,
            'partner_id': partner_id,
            'type': invoice_type,
            'state': 'draft'
        }

    def list_invoices(self, partner_id: int = None, state: str = None,
                      limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        List invoices from Odoo.

        Args:
            partner_id: Filter by partner ID
            state: Filter by state (draft, posted, cancel)
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            List of invoice dictionaries
        """
        self._ensure_authenticated()

        domain = []

        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        if state:
            domain.append(('state', '=', state))

        # Search for invoices
        invoice_ids = self.execute(
            'account.move', 'search', domain,
            limit=limit, offset=offset,
            order='invoice_date DESC'
        )

        if not invoice_ids:
            return []

        # Read invoice details
        fields = [
            'id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
            'amount_total', 'amount_untaxed', 'amount_tax', 'state',
            'move_type', 'payment_state', 'ref'
        ]

        invoices = self.execute('account.move', 'read', invoice_ids, fields)

        # Format partner_id (it's a tuple [id, name])
        for invoice in invoices:
            if isinstance(invoice.get('partner_id'), (list, tuple)):
                invoice['partner_id'] = {
                    'id': invoice['partner_id'][0],
                    'name': invoice['partner_id'][1] if len(invoice['partner_id']) > 1 else ''
                }

        return invoices

    def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """
        Get a single invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice dictionary or None
        """
        self._ensure_authenticated()

        fields = [
            'id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
            'amount_total', 'amount_untaxed', 'amount_tax', 'state',
            'move_type', 'payment_state', 'ref', 'narration',
            'invoice_line_ids', 'invoice_origin'
        ]

        invoices = self.execute('account.move', 'read', [invoice_id], fields)

        if not invoices:
            return None

        invoice = invoices[0]

        # Format partner_id
        if isinstance(invoice.get('partner_id'), (list, tuple)):
            invoice['partner_id'] = {
                'id': invoice['partner_id'][0],
                'name': invoice['partner_id'][1] if len(invoice['partner_id']) > 1 else ''
            }

        return invoice

    def record_payment(self, invoice_id: int, amount: float,
                       payment_date: str = None,
                       payment_method: str = None,
                       reference: str = None) -> Dict[str, Any]:
        """
        Record a payment against an invoice.

        Args:
            invoice_id: Invoice ID
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            payment_method: Payment method name
            reference: Payment reference

        Returns:
            Dict with payment details
        """
        self._ensure_authenticated()

        if payment_date is None:
            payment_date = datetime.now().strftime('%Y-%m-%d')

        # Get the invoice to determine journal
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            raise OdooClientError(f"Invoice {invoice_id} not found")

        # Create payment through Odoo's payment registration
        payment_vals = {
            'amount': amount,
            'payment_date': payment_date,
        }

        if reference:
            payment_vals['payment_reference'] = reference

        # Use Odoo's payment registration wizard approach
        # This registers a payment directly on the invoice
        try:
            # Try to use the _register_payment method
            result = self.execute(
                'account.move', '_register_payment',
                [invoice_id],
                payment_vals=payment_vals
            )
        except OdooClientError:
            # Fallback: Create payment record directly
            # Find appropriate journal
            journals = self.execute(
                'account.journal', 'search_read',
                [('type', 'in', ['bank', 'cash'])],
                ['id', 'name'],
                limit=1
            )

            journal_id = journals[0]['id'] if journals else None

            if journal_id:
                payment_vals['journal_id'] = journal_id
                payment_vals['partner_id'] = invoice['partner_id']['id'] if isinstance(invoice['partner_id'], dict) else invoice['partner_id']
                payment_vals['payment_type'] = 'inbound' if invoice['move_type'] in ['out_invoice', 'out_refund'] else 'outbound'

                payment_id = self.execute('account.payment', 'create', payment_vals)
                self.execute('account.payment', 'action_post', [payment_id])

                result = {'payment_id': payment_id}
            else:
                raise OdooClientError("No payment journal found")

        return {
            'success': True,
            'invoice_id': invoice_id,
            'amount': amount,
            'payment_date': payment_date,
            'reference': reference,
            'result': result
        }

    # ========================================================================
    # Account Summary Operations
    # ========================================================================

    def get_account_summary(self, partner_id: int = None) -> Dict[str, Any]:
        """
        Get accounting summary.

        Args:
            partner_id: Optional partner ID for customer-specific summary

        Returns:
            Dict with accounting summary
        """
        self._ensure_authenticated()

        summary = {
            'total_receivable': 0.0,
            'total_payable': 0.0,
            'invoices_count': 0,
            'bills_count': 0,
            'draft_invoices': 0,
            'posted_invoices': 0
        }

        try:
            # Get invoice counts and amounts
            domain = []
            if partner_id:
                domain.append(('partner_id', '=', partner_id))

            # Count invoices by type
            invoice_count = self.execute('account.move', 'search_count', [
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ] + domain)

            bill_count = self.execute('account.move', 'search_count', [
                ('move_type', 'in', ['in_invoice', 'in_refund'])
            ] + domain)

            # Count by state
            draft_count = self.execute('account.move', 'search_count', [
                ('state', '=', 'draft')
            ] + domain)

            posted_count = self.execute('account.move', 'search_count', [
                ('state', '=', 'posted')
            ] + domain)

            # Get total amounts from posted invoices
            posted_invoices = self.execute(
                'account.move', 'search_read',
                [('state', '=', 'posted'), ('move_type', '=', 'out_invoice')] + domain,
                ['amount_total', 'amount_residual'],
                limit=1000
            )

            total_receivable = sum(inv.get('amount_residual', 0) for inv in posted_invoices)

            summary.update({
                'invoices_count': invoice_count,
                'bills_count': bill_count,
                'draft_invoices': draft_count,
                'posted_invoices': posted_count,
                'total_receivable': total_receivable
            })

        except OdooClientError as e:
            self.logger.warning(f"Error getting account summary: {e}")

        summary['currency'] = 'USD'  # Default, could be fetched from Odoo
        summary['as_of'] = datetime.now().isoformat()

        return summary

    def search_partner(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search for partners (customers/vendors).

        Args:
            search_term: Search string
            limit: Maximum results

        Returns:
            List of partner dictionaries
        """
        self._ensure_authenticated()

        domain = [
            '|',
            ('name', 'ilike', search_term),
            ('email', 'ilike', search_term)
        ]

        partners = self.execute(
            'res.partner', 'search_read',
            domain,
            ['id', 'name', 'email', 'phone', 'customer_rank', 'supplier_rank'],
            limit=limit
        )

        return partners

    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
