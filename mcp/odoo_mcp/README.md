# Odoo MCP Server

A production-ready Model Context Protocol (MCP) server for Odoo ERP integration. Provides capabilities for invoice management, payment recording, and accounting summaries via Odoo's JSON-RPC API.

## Features

- **Invoice Management**: Create and list invoices in Odoo
- **Payment Recording**: Record payments against invoices
- **Accounting Summaries**: Get real-time accounting data
- **Partner Search**: Search for customers and vendors
- **Approval Workflow**: Human approval required for write operations
- **Comprehensive Logging**: All operations logged to `Logs/odoo.log`

## Installation

1. Navigate to the Odoo MCP directory:
```bash
cd mcp/odoo_mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the environment template and configure:
```bash
cp .env.example .env
```

4. Edit `.env` and fill in your Odoo credentials:
```
ODOO_URL=https://mycompany.odoo.com
ODOO_DB=my_database
ODOO_USERNAME=user@company.com
ODOO_PASSWORD=your_password_or_api_key
ODOO_PORT=80
```

## Usage

### Run as MCP Server (stdio transport)

```bash
python server.py
```

### Run with HTTP Transport

```bash
python server.py --port 8080
```

### Check Configuration

```bash
python server.py --check-config
```

### Test Connection

```bash
python server.py --test-connection
```

## MCP Tools

### create_invoice

Create a new invoice in Odoo. Requires human approval before execution.

**Parameters:**
- `partner_id` (required): Customer/partner ID in Odoo
- `invoice_type` (optional): Type of invoice (default: `out_invoice`)
  - `out_invoice`: Customer invoice
  - `in_invoice`: Vendor bill
  - `out_refund`: Customer credit note
  - `in_refund`: Vendor credit note
- `lines` (optional): Invoice line items
  - `product_id`: Product ID
  - `quantity`: Quantity (default: 1)
  - `price_unit`: Unit price (default: 0)
  - `name`: Line description
- `invoice_date` (optional): Invoice date (YYYY-MM-DD)
- `due_date` (optional): Due date (YYYY-MM-DD)
- `narration` (optional): Additional notes

**Example:**
```json
{
  "partner_id": 123,
  "invoice_type": "out_invoice",
  "lines": [
    {
      "product_id": 456,
      "quantity": 2,
      "price_unit": 100.00,
      "name": "Product A"
    }
  ],
  "invoice_date": "2026-02-20",
  "narration": "Thank you for your business"
}
```

**Response:**
```json
{
  "success": true,
  "invoice_id": 789,
  "approval_request_id": "create_invoice_20260220_123456",
  "state": "draft"
}
```

### list_invoices

List invoices from Odoo with optional filters.

**Parameters:**
- `partner_id` (optional): Filter by partner ID
- `state` (optional): Filter by state (`draft`, `posted`, `cancel`)
- `limit` (optional): Maximum number of results (default: 100)
- `offset` (optional): Offset for pagination (default: 0)

**Example:**
```json
{
  "state": "posted",
  "limit": 10
}
```

### record_payment

Record a payment against an invoice. Requires human approval before execution.

**Parameters:**
- `invoice_id` (required): Invoice ID
- `amount` (required): Payment amount
- `payment_date` (optional): Payment date (YYYY-MM-DD, default: today)
- `reference` (optional): Payment reference

**Example:**
```json
{
  "invoice_id": 789,
  "amount": 200.00,
  "payment_date": "2026-02-20",
  "reference": "PAY-001"
}
```

### get_account_summary

Get accounting summary from Odoo.

**Parameters:**
- `partner_id` (optional): Partner ID for customer-specific summary

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_receivable": 15000.00,
    "total_payable": 5000.00,
    "invoices_count": 25,
    "bills_count": 10,
    "draft_invoices": 3,
    "posted_invoices": 22,
    "currency": "USD",
    "as_of": "2026-02-20T10:30:00"
  }
}
```

### search_partner

Search for partners (customers/vendors) in Odoo.

**Parameters:**
- `search_term` (required): Search string (name or email)
- `limit` (optional): Maximum results (default: 10)

**Example:**
```json
{
  "search_term": "Acme",
  "limit": 5
}
```

## Approval Workflow

Write operations (`create_invoice`, `record_payment`) require human approval:

1. **Request Created**: Server creates approval request file in `Pending_Approval/`
2. **Pending Status**: Initial response includes `approval_request_id` and `requires_approval: true`
3. **Human Review**: Operator reviews and approves/rejects the request file
4. **Status Check**: Server polls for approval status change
5. **Execution**: If approved, operation is executed; if rejected, operation is cancelled

**Approval File Format:**
```markdown
# Odoo Action Approval Request

**Request ID:** create_invoice_20260220_123456
**Created:** 2026-02-20 12:34:56
**Action:** create_invoice

---

## Action Details

{
  "partner_id": 123,
  "amount": 500.00,
  ...
}

---

## Approval Status

**Status:** [PENDING/APPROVED/REJECTED]

**Approved By:** _______________

**Date:** _______________
```

## Logging

All operations are logged to `Logs/odoo.log` in JSON Lines format:

```json
{"timestamp": "2026-02-20T12:34:56", "action_type": "invoice", "message": "Invoice created: 789", "status": "success", "details": {...}}
```

## Error Handling

The server handles various error conditions:

| Error | Description | Response |
|-------|-------------|----------|
| `NOT_CONFIGURED` | Odoo credentials missing | `error: "Odoo credentials not configured"` |
| `AUTH_FAILED` | Authentication failed | `error: "Authentication failed: ..."` |
| `CONNECTION_ERROR` | Network/connection issue | `error: "Failed to connect to Odoo: ..."` |
| `APPROVAL_PENDING` | Awaiting human approval | `requires_approval: true` |
| `APPROVAL_REJECTED` | Approval was rejected | `error: "Approval rejected"` |

## Testing

Run the test suite:

```bash
python test_server.py
```

## Architecture

```
mcp/odoo_mcp/
├── server.py          # Main MCP server with tool definitions
├── odoo_client.py     # Odoo JSON-RPC client class
├── config.py          # Configuration management
├── requirements.txt   # Python dependencies
├── README.md         # This file
├── .env.example      # Environment variable template
└── test_server.py    # Test suite
```

## Security

- **Never commit credentials**: `.env` is in `.gitignore`
- **Use API keys**: Prefer API keys over passwords when possible
- **HTTPS only**: Always use HTTPS for Odoo URLs
- **Least privilege**: Use Odoo user with minimal required permissions

## Troubleshooting

### Connection Failed

1. Verify Odoo URL is correct (include `https://` or `http://`)
2. Check Odoo server is running and accessible
3. Verify firewall allows connections to Odoo port

### Authentication Failed

1. Verify username and password are correct
2. Check user has API access enabled in Odoo
3. Try generating a new API key in Odoo

### MCP Library Not Found

```bash
pip install mcp
```

### Approval Not Working

1. Ensure `Pending_Approval/` directory exists and is writable
2. Check approval file status field is exactly `APPROVED` or `REJECTED`

## License

MIT License - See main project LICENSE file.
