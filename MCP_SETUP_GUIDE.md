# MCP Servers Setup Guide

Complete guide for configuring and running all 4 MCP servers in your AI Employee Vault.

---

## Quick Start

### 1. Install All MCPs

```bash
# Run the installation script
install_all_mcps.bat
```

This will:
- Install Email MCP dependencies
- Install Social MCP dependencies
- Install FileOps MCP dependencies
- Install Playwright browsers (Chromium)

**Time:** 5-10 minutes

### 2. Configure Credentials

```bash
# Copy template
copy .env.example .env

# Edit .env with your credentials
# See "Getting API Credentials" section below
```

### 3. Configure Claude Desktop

The `claude_desktop_config.json` file has been created with all 4 MCP servers.

**Location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- The file in vault root is a template - copy it to Claude Desktop config location

**Restart Claude Desktop** after configuration.

### 4. Test MCP Servers

```bash
# Test Email MCP
cd mcp\email_mcp
python test_server.py

# Test Social MCP
cd mcp\social_mcp
python test_server.py

# Test FileOps MCP
cd mcp\fileops_mcp
python test_server.py
```

---

## MCP Servers Overview

### 1. Business MCP (`mcp/business_mcp/`)

**Purpose:** Core business operations

**Capabilities:**
- `send_email` - Send emails via Gmail SMTP
- `post_linkedin` - Post to LinkedIn
- `log_activity` - Log business activities

**Configuration:**
```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

**Test:**
```bash
cd mcp/business_mcp
python server.py --status
```

### 2. Email MCP (`mcp/email_mcp/`)

**Purpose:** Production-ready email sending

**Capabilities:**
- `send_email` - Send with retry and rate limiting
- `draft_email` - Create drafts for approval
- `validate_email` - Validate email addresses

**Features:**
- Exponential backoff retry (1s, 2s, 4s)
- Rate limiting (50/hour default)
- Audit logging
- HTML email support

**Configuration:**
```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
MAX_EMAILS_PER_HOUR=50
```

**Test:**
```bash
cd mcp/email_mcp
echo '{"method": "validate_email", "params": {"email": "test@example.com"}}' | python server.py
```

### 3. Social MCP (`mcp/social_mcp/`)

**Purpose:** Unified social media management

**Capabilities:**
- **Twitter:** `post_tweet`, `get_mentions`
- **Facebook:** `post_to_page`, `get_page_insights`
- **Instagram:** `post_image`, `get_recent_media`
- **General:** `create_post_draft`

**Rate Limits:**
- Twitter: 50 posts/day
- Instagram: 25 posts/day
- Facebook: API default

**Configuration:**
```bash
# Twitter
TWITTER_BEARER_TOKEN=your_token
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret

# Facebook
FACEBOOK_ACCESS_TOKEN=your_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
```

**Test:**
```bash
cd mcp/social_mcp
echo '{"method": "create_post_draft", "params": {"platform": "twitter", "content": "Test"}}' | python server.py
```

### 4. FileOps MCP (`mcp/fileops_mcp/`)

**Purpose:** Browser automation + File operations

**Browser Capabilities:**
- `browser.navigate` - Navigate to URLs
- `browser.click` - Click elements
- `browser.fill` - Fill text inputs
- `browser.get_text` - Extract text
- `browser.screenshot` - Take screenshots
- `browser.linkedin_post` - Automated LinkedIn posting

**File Capabilities:**
- `file.read_file` - Read files
- `file.write_file` - Write files
- `file.move_file` - Move/rename files
- `file.delete_file` - Delete (with approval)
- `file.list_files` - List directory
- `file.parse_csv` - Parse CSV
- `file.parse_json` - Parse JSON

**Safety Features:**
- Directory whitelist
- Deletion approval required
- Comprehensive audit logging
- Persistent browser sessions

**Configuration:**
```bash
BROWSER_TYPE=chromium
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30
SESSION_DIR=D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/.browser_session
VAULT_PATH=D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault
ALLOWED_DIRECTORIES=D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault
```

**Test:**
```bash
cd mcp/fileops_mcp
echo '{"method": "file.list_files", "params": {"directory": ".", "pattern": "*.md"}}' | python server.py
```

---

## Getting API Credentials

### Gmail App Password

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Factor Authentication**
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create app password for "Mail"
5. Copy 16-character password to `.env`

**Detailed guide:** `mcp/email_mcp/README.md`

### Twitter API

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create developer account
3. Create project and app
4. Generate Bearer Token
5. Get API Key and Secret

**Detailed guide:** `mcp/social_mcp/API_SETUP_GUIDE.md`

### Facebook API

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create developer account
3. Create Business app
4. Add Facebook Login product
5. Generate Page Access Token
6. Get Page ID

**Detailed guide:** `mcp/social_mcp/API_SETUP_GUIDE.md`

### Instagram API

1. Convert to Business/Creator account
2. Link to Facebook Page
3. Get Business Account ID via Graph API
4. Use same Access Token as Facebook

**Detailed guide:** `mcp/social_mcp/API_SETUP_GUIDE.md`

### LinkedIn (Browser Automation)

1. No API credentials needed
2. First login is manual via browser
3. Session saved to `.browser_session/`
4. Future posts automatic

**Detailed guide:** `mcp/fileops_mcp/LINKEDIN_AUTOMATION_GUIDE.md`

---

## Configuration Files

### .env (Vault Root)

Contains all API credentials. **NEVER commit to git.**

```bash
# Email
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_app_password

# Twitter
TWITTER_BEARER_TOKEN=...
TWITTER_API_KEY=...
TWITTER_API_SECRET=...

# Facebook
FACEBOOK_ACCESS_TOKEN=...
FACEBOOK_PAGE_ID=...

# Instagram
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...

# Paths
VAULT_PATH=D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault
```

### claude_desktop_config.json

**Windows Location:** `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "business": {
      "command": "python",
      "args": ["D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/mcp/business_mcp/server.py"],
      "env": {...}
    },
    "email": {...},
    "social": {...},
    "fileops": {...}
  }
}
```

### .gitignore

Already configured to exclude:
- `.env` files
- Log files
- Browser sessions
- Python cache
- Credentials

---

## Troubleshooting

### MCP Not Showing in Claude Desktop

**Solution:**
1. Verify `claude_desktop_config.json` syntax (use JSON validator)
2. Check file paths are absolute and correct
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

### "NOT_CONFIGURED" Error

**Solution:**
1. Verify `.env` file exists in vault root
2. Check all credentials are filled in
3. Restart MCP server
4. Test manually: `python server.py`

### Playwright Not Working

**Solution:**
```bash
# Reinstall Playwright
pip install --upgrade playwright
playwright install chromium

# Verify installation
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### Rate Limit Exceeded

**Solution:**
- Wait for limit to reset (next day/hour)
- Check `Logs/*_rate_limit.json` for current usage
- Increase limits in `.env` (within platform guidelines)

### File Access Denied

**Solution:**
- Check file is within `ALLOWED_DIRECTORIES`
- Add directory to whitelist in `.env`
- Verify path uses forward slashes or escaped backslashes

---

## Testing All MCPs

### Quick Test Script

Create `test_all_mcps.bat`:

```batch
@echo off
echo Testing Email MCP...
cd mcp\email_mcp
python test_server.py

echo.
echo Testing Social MCP...
cd mcp\social_mcp
python test_server.py

echo.
echo Testing FileOps MCP...
cd mcp\fileops_mcp
python test_server.py

echo.
echo All tests complete!
pause
```

### Manual Testing

```bash
# Email MCP - Validate email
echo '{"method": "validate_email", "params": {"email": "test@example.com"}}' | python server.py

# Social MCP - Create draft
echo '{"method": "create_post_draft", "params": {"platform": "twitter", "content": "Test"}}' | python server.py

# FileOps MCP - List files
echo '{"method": "file.list_files", "params": {"directory": ".", "pattern": "*.md"}}' | python server.py

# Business MCP - Check status
python server.py --status
```

---

## Maintenance

### Update Dependencies

```bash
# Run installation script again
install_all_mcps.bat

# Or manually
cd mcp/email_mcp && pip install -r requirements.txt --upgrade
cd mcp/social_mcp && pip install -r requirements.txt --upgrade
cd mcp/fileops_mcp && pip install -r requirements.txt --upgrade
```

### Rotate Credentials

**Recommended:** Every 90 days

1. Generate new tokens in respective developer portals
2. Update `.env` file
3. Restart Claude Desktop
4. Test all MCPs

### Clear Old Logs

```bash
# Clear logs older than 30 days
python scripts/error_recovery.py clear --days-old 30

# Or manually delete old log files
del Logs\email_audit_*.json
del Logs\social_audit_*.json
del Logs\fileops_audit_*.json
```

---

## Security Best Practices

1. **Never commit `.env`** - Contains API credentials
2. **Use App Passwords** - Never use regular passwords
3. **Rotate credentials** - Every 90 days
4. **Review audit logs** - Check `Logs/` regularly
5. **Restrict file access** - Use `ALLOWED_DIRECTORIES`
6. **Secure session folder** - Protect `.browser_session/`

---

## Support

### Documentation

- **Email MCP:** `mcp/email_mcp/README.md`
- **Social MCP:** `mcp/social_mcp/API_SETUP_GUIDE.md`
- **FileOps MCP:** `mcp/fileops_mcp/LINKEDIN_AUTOMATION_GUIDE.md`
- **Business MCP:** `mcp/business_mcp/README.md`

### Logs

- **Email:** `Logs/email_mcp.log`, `Logs/email_audit_*.json`
- **Social:** `Logs/social_mcp.log`, `Logs/social_audit_*.json`
- **FileOps:** `Logs/fileops_mcp.log`, `Logs/fileops_audit_*.json`
- **Business:** `Logs/business.log`

### Test Commands

```bash
# Test each MCP
cd mcp/email_mcp && python test_server.py
cd mcp/social_mcp && python test_server.py
cd mcp/fileops_mcp && python test_server.py
cd mcp/business_mcp && python server.py --status
```

---

**All MCPs configured and ready! 🎉**
