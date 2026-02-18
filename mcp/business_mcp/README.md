# Business MCP Server

A production-ready Model Context Protocol (MCP) server for business automation.

## Features

- **Send Email** - Send emails via Gmail SMTP with attachments support
- **Create LinkedIn Post** - Post to LinkedIn (simulation or real via Playwright)
- **Log Business Activity** - Log all activities to `vault/Logs/business.log`

## Installation

### 1. Install Dependencies

```bash
# Navigate to MCP directory
cd mcp/business_mcp

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright (optional, for real LinkedIn posting)
playwright install
```

### 2. Configure Environment Variables

Copy the root `.env` file or set these environment variables:

```bash
# Required for email functionality
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Optional for LinkedIn (uses simulation if not set)
LINKEDIN_EMAIL=your.linkedin@email.com
LINKEDIN_PASSWORD=your-password

# Optional logging configuration
LOGS_DIR=Logs
```

### 3. Gmail App Password Setup

To send emails, you need a Gmail App Password:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Factor Authentication**
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create a new app password for "Mail"
5. Copy the 16-character password to your `.env` file

## Usage

### Run Server

```bash
# Run with stdio transport (for Claude Code integration)
python server.py

# Run with HTTP transport on port 8080
python server.py --port 8080

# Show server status
python server.py --status

# Test email functionality
python server.py --test-email

# Test LinkedIn functionality
python server.py --test-linkedin
```

### Available Tools

#### 1. `send_email`

Send an email via Gmail SMTP.

**Parameters:**
- `to` (required): Recipient email address
- `subject` (required): Email subject
- `body` (required): Email body (supports HTML)
- `cc` (optional): CC recipient
- `attachments` (optional): List of file paths to attach

**Example:**
```json
{
  "to": "client@example.com",
  "subject": "Project Update",
  "body": "<h1>Project Status</h1><p>All tasks completed on schedule.</p>",
  "cc": "manager@example.com"
}
```

#### 2. `post_linkedin`

Create a LinkedIn post.

**Parameters:**
- `content` (required): Post content (max 3000 characters)
- `topic` (optional): Topic or hashtag

**Example:**
```json
{
  "content": "Excited to announce our new product launch! #innovation #business",
  "topic": "Product Launch"
}
```

#### 3. `log_activity`

Log a business activity to the vault.

**Parameters:**
- `message` (required): Activity message
- `action_type` (optional): Type of action (email, linkedin, meeting, call, general)
- `details` (optional): Additional details dictionary
- `status` (optional): Status (success, error, pending, completed)

**Example:**
```json
{
  "message": "Client meeting completed",
  "action_type": "meeting",
  "details": {
    "client": "Acme Corp",
    "attendees": ["John", "Jane"],
    "outcome": "Deal signed"
  },
  "status": "completed"
}
```

## Integration with Claude Code

### Claude Desktop Configuration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "business-mcp": {
      "command": "python",
      "args": ["D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/mcp/business_mcp/server.py"],
      "env": {
        "EMAIL_ADDRESS": "your.email@gmail.com",
        "EMAIL_PASSWORD": "your-app-password"
      }
    }
  }
}
```

### Using with Claude

Once configured, Claude can:
- Send emails on your behalf
- Create LinkedIn posts
- Log all business activities automatically

## Log File Format

Activities are logged to `Logs/business.log` in line-delimited JSON format:

```json
{"timestamp": "2026-02-18T14:30:00", "action_type": "email", "message": "Email sent to client@example.com", "status": "success", "details": {"to": "client@example.com", "subject": "Project Update"}}
{"timestamp": "2026-02-18T14:35:00", "action_type": "linkedin", "message": "LinkedIn post created", "status": "success", "details": {"post_id": "urn:li:share:20260218143500"}}
```

## API Reference

### Email Service

```python
from server import EmailService, BusinessLogger

logger = BusinessLogger()
email = EmailService(logger)

result = email.send_email(
    to="client@example.com",
    subject="Hello",
    body="<h1>Hi!</h1>",
    cc="team@example.com",
    attachments=["/path/to/file.pdf"]
)

print(result)
# {'success': True, 'message_id': '<20260218143000@gmail.com>', 'error': None}
```

### LinkedIn Service

```python
from server import LinkedInService, BusinessLogger

logger = BusinessLogger()
linkedin = LinkedInService(logger)

result = linkedin.post_linkedin(
    content="Great news! #business",
    topic="Announcement"
)

print(result)
# {'success': True, 'post_id': 'urn:li:share:20260218143500', 'post_url': 'https://...'}
```

### Business Logger

```python
from server import BusinessLogger

logger = BusinessLogger()

logger.log_activity(
    message="Quarterly review completed",
    action_type="meeting",
    details={"quarter": "Q1", "year": 2026},
    status="completed"
)

# Get recent activities
activities = logger.get_recent_activities(limit=10)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Test email only
python server.py --test-email

# Test LinkedIn only
python server.py --test-linkedin

# Check server status
python server.py --status
```

## Troubleshooting

### Email Not Sending

1. Verify `EMAIL_ADDRESS` and `EMAIL_PASSWORD` are set correctly
2. Ensure you're using an **App Password**, not your regular Gmail password
3. Check that 2-Factor Authentication is enabled
4. Verify SMTP server settings (default: `smtp.gmail.com:587`)

### LinkedIn Posting Fails

1. If Playwright is not installed, posts run in simulation mode (still logged)
2. Install Playwright: `pip install playwright && playwright install`
3. Set `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` environment variables
4. Note: Browser automation may violate LinkedIn Terms of Service

### MCP Server Not Starting

1. Ensure MCP library is installed: `pip install mcp`
2. Check Python version (3.8+ required)
3. Verify all dependencies in `requirements.txt` are installed

## Security Best Practices

- **Never commit `.env` file** - It contains sensitive credentials
- **Use App Passwords** - Never use your regular Gmail password
- **Restrict file permissions** - Ensure `.env` is only readable by your user
- **Review logs regularly** - Monitor `Logs/business.log` for unauthorized activity

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `Logs/business.log`
3. Run `python server.py --status` to verify configuration
