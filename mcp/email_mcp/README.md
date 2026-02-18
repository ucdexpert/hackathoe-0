# Email MCP Server

A production-ready MCP (Model Context Protocol) server for email operations using the stdin/stdout JSON protocol.

## Features

- ✅ **Send Email** - Send emails via Gmail SMTP with retry and rate limiting
- ✅ **Draft Email** - Create email drafts requiring human approval
- ✅ **Validate Email** - Validate email addresses (RFC 5322 compliant)
- ✅ **Retry Logic** - Exponential backoff (1s, 2s, 4s) with max 3 attempts
- ✅ **Rate Limiting** - Configurable emails per hour (default: 50)
- ✅ **Audit Logging** - Structured JSON audit logs
- ✅ **Error Handling** - Never crashes, always returns valid JSON
- ✅ **HTML Support** - Send both plain text and HTML emails

## MCP Protocol Explanation

This server implements the **Model Context Protocol (MCP)** using stdin/stdout:

### Protocol Flow

1. **Client writes JSON request to stdin** (one JSON object per line)
2. **Server reads from stdin** (line by line)
3. **Server processes request**
4. **Server writes JSON response to stdout**
5. **Server flushes stdout**

### Request Format

```json
{
  "method": "send_email",
  "params": {
    "to": "client@example.com",
    "subject": "Invoice #123",
    "body": "Please find attached...",
    "html": false
  }
}
```

### Response Format

```json
{
  "success": true,
  "message": "Email sent successfully",
  "timestamp": "2026-02-19T10:30:00Z",
  "message_id": "<20260219103000@gmail.com>"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Invalid recipient email address",
  "error_code": "INVALID_EMAIL",
  "timestamp": "2026-02-19T10:30:00Z"
}
```

## Installation

### 1. Install Dependencies

```bash
cd mcp/email_mcp
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# See "Gmail App Password Setup" below
```

### 3. Test the Server

```bash
# Start server (interactive mode)
python server.py

# In another terminal, send test requests:
echo '{"method": "validate_email", "params": {"email": "test@example.com"}}' | python server.py
```

## Gmail App Password Setup

To send emails via Gmail, you need an **App Password** (not your regular password):

### Step 1: Enable 2-Factor Authentication

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **2-Step Verification**
3. Follow the setup process

### Step 2: Generate App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Under "App", select **Mail**
3. Under "Device", select **Other (Custom name)**
4. Enter: `AI Employee Vault`
5. Click **Generate**
6. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)
7. Paste it in your `.env` file (without spaces): `EMAIL_PASSWORD=abcdefghijklmnop`

### Step 3: Update .env

```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop  # Your 16-character app password
```

## Configuration in claude_desktop_config.json

To use this MCP server with Claude Desktop:

### Windows

Edit: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": [
        "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/mcp/email_mcp/server.py"
      ],
      "env": {
        "EMAIL_ADDRESS": "your.email@gmail.com",
        "EMAIL_PASSWORD": "your-app-password",
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "VAULT_PATH": "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault",
        "MAX_EMAILS_PER_HOUR": "50"
      }
    }
  }
}
```

### macOS/Linux

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python3",
      "args": [
        "/path/to/AI_Employee_Vault/mcp/email_mcp/server.py"
      ],
      "env": {
        "EMAIL_ADDRESS": "your.email@gmail.com",
        "EMAIL_PASSWORD": "your-app-password"
      }
    }
  }
}
```

**Restart Claude Desktop** after editing the configuration.

## Available Methods

### 1. send_email

Send an email via Gmail SMTP.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject
- `body` (required): Email body
- `html` (optional): Whether body is HTML (default: false)
- `cc` (optional): CC recipients
- `bcc` (optional): BCC recipients
- `attachments` (optional): List of file paths

**Example:**
```json
{
  "method": "send_email",
  "params": {
    "to": "client@example.com",
    "subject": "Meeting Tomorrow",
    "body": "Hi,\n\nJust confirming our meeting tomorrow at 2 PM.\n\nBest regards",
    "html": false
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully",
  "message_id": "<20260219103000@gmail.com>",
  "attempts": 1,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

### 2. draft_email

Create a draft email that requires human approval before sending.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject
- `body` (required): Email body
- `html` (optional): Whether body is HTML

**Example:**
```json
{
  "method": "draft_email",
  "params": {
    "to": "client@example.com",
    "subject": "Proposal",
    "body": "Please review the attached proposal..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Draft created successfully",
  "draft_path": "D:/.../Pending_Approval/draft_20260219_103000_Proposal.md",
  "requires_approval": true,
  "timestamp": "2026-02-19T10:30:00Z"
}
```

### 3. validate_email

Validate an email address format.

**Parameters:**
- `email` (required): Email address to validate

**Example:**
```json
{
  "method": "validate_email",
  "params": {
    "email": "client@example.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "email": "client@example.com",
  "normalized": "client@example.com",
  "message": "Email is valid",
  "timestamp": "2026-02-19T10:30:00Z"
}
```

## Testing Instructions

### Interactive Testing

```bash
# Start server
python server.py

# Send test requests (one per line):
{"method": "validate_email", "params": {"email": "test@example.com"}}
{"method": "send_email", "params": {"to": "test@example.com", "subject": "Test", "body": "Hello"}}
{"method": "draft_email", "params": {"to": "test@example.com", "subject": "Draft", "body": "Draft body"}}
```

### Automated Testing

```bash
# Test validate_email
echo '{"method": "validate_email", "params": {"email": "valid@example.com"}}' | python server.py

# Test send_email (will fail if not configured)
echo '{"method": "send_email", "params": {"to": "test@example.com", "subject": "Test", "body": "Hello"}}' | python server.py

# Test invalid email
echo '{"method": "validate_email", "params": {"email": "invalid-email"}}' | python server.py

# Test unknown method
echo '{"method": "unknown_method", "params": {}}' | python server.py
```

### Test Rate Limiting

```python
import subprocess
import json

for i in range(55):
    request = {
        "method": "send_email",
        "params": {
            "to": f"test{i}@example.com",
            "subject": f"Test {i}",
            "body": f"Test email {i}"
        }
    }
    
    result = subprocess.run(
        ['python', 'server.py'],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    response = json.loads(result.stdout)
    print(f"Email {i}: {response['success']} - {response.get('error', 'OK')}")
```

## Troubleshooting

### Server Won't Start

**Symptom:** Server exits immediately

**Solution:**
```bash
# Check Python version (need 3.8+)
python --version

# Check dependencies
pip install -r requirements.txt

# Check for syntax errors
python -m py_compile server.py
```

### Authentication Failed

**Symptom:** `SMTP authentication failed`

**Solution:**
1. Verify you're using an **App Password**, not your regular Gmail password
2. Ensure 2-Factor Authentication is enabled
3. Check `.env` file has correct credentials
4. Test credentials manually:
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your.email@gmail.com', 'your-app-password')
   ```

### Rate Limit Exceeded

**Symptom:** `Rate limit exceeded. Try again in 1 hour.`

**Solution:**
- Wait 1 hour for the limit to reset
- Check `Logs/email_rate_limit.json` for current usage
- Increase `MAX_EMAILS_PER_HOUR` in `.env` (Gmail limit: 500 free, 2000 Workspace)

### Invalid JSON Response

**Symptom:** Client receives invalid JSON

**Solution:**
- Check `Logs/email_mcp.log` for server errors
- Ensure no debug prints to stdout (only JSON responses)
- Verify request is valid JSON

### Emails Not Sending

**Symptom:** `Failed to send email after 3 attempts`

**Solution:**
1. Check internet connection
2. Verify SMTP server settings
3. Check firewall (port 587 must be open)
4. Review `Logs/email_audit_YYYY-MM-DD.json` for details
5. Check `Logs/email_mcp.log` for errors

### Claude Desktop Integration Issues

**Symptom:** Claude can't use email MCP server

**Solution:**
1. Verify `claude_desktop_config.json` syntax (use JSON validator)
2. Check file paths are absolute and correct
3. Restart Claude Desktop completely
4. Test server manually first: `python server.py`
5. Check Claude Desktop logs for errors

## File Structure

```
mcp/email_mcp/
├── server.py              # Main MCP server
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── .env                  # Your configuration (DO NOT COMMIT)

# Generated files:
../Logs/
├── email_mcp.log                    # Error logs
├── email_audit_YYYY-MM-DD.json      # Daily audit logs
└── email_rate_limit.json            # Rate limit state

../Pending_Approval/
└── draft_*.md                       # Email drafts
```

## Security Best Practices

1. **Never commit `.env`** - Contains sensitive credentials
2. **Use App Passwords** - Never use regular Gmail password
3. **Restrict file permissions** - `.env` readable only by your user
4. **Enable 2FA** - Required for Gmail app passwords
5. **Review audit logs** - Monitor `Logs/email_audit_*.json` regularly
6. **Rate limiting** - Prevents accidental spam

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│    (Client)     │
└────────┬────────┘
         │ JSON via stdin/stdout
         ▼
┌─────────────────┐
│  Email MCP      │
│  Server         │
├─────────────────┤
│  Rate Limiter   │
│  Email Service  │
│  Validator      │
│  Audit Logger   │
└────────┬────────┘
         │ SMTP
         ▼
┌─────────────────┐
│  Gmail SMTP     │
│  Server         │
└─────────────────┘
```

## License

MIT License - See project LICENSE file.

## Support

For issues:
1. Check this README
2. Review `Logs/email_mcp.log`
3. Test with manual requests
4. Verify configuration
