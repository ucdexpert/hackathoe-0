# gmail-send

## Description
Send real emails via Gmail SMTP. Uses environment variables for credentials. Requires human approval for production use.

## Environment Variables
```
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Usage
```bash
python .claude/skills/gmail-send/scripts/send_email.py --to recipient@example.com --subject "Subject" --body "Message body"
```

## Inputs
- `--to`: Recipient email address (required)
- `--subject`: Email subject (required)
- `--body`: Email body text (required)
- `--cc`: CC recipient (optional)
- `--attachments`: Comma-separated file paths (optional)

## Output
```
SUCCESS: Email sent to recipient@example.com
Message-ID: <abc123@gmail.com>
```

## Error Handling
- Invalid email format → ERROR: Invalid email address
- SMTP auth failure → ERROR: Authentication failed
- Network error → ERROR: Connection failed

## Security
- Use Gmail App Passwords, not main password
- Enable 2FA on Gmail account
- Never commit credentials to version control
