# FileOps MCP Server

A unified production-ready MCP (Model Context Protocol) server combining browser automation (Playwright) and file operations with comprehensive safety features.

## Features

### Browser Automation (Playwright)
- ✅ **navigate(url)** - Navigate to any URL
- ✅ **click(selector)** - Click elements
- ✅ **fill(selector, text)** - Fill text inputs
- ✅ **get_text(selector)** - Extract text from elements
- ✅ **screenshot(path)** - Capture screenshots
- ✅ **linkedin_post(message)** - Automated LinkedIn posting

### File Operations
- ✅ **read_file(path)** - Read file content
- ✅ **write_file(path, content)** - Write content to files
- ✅ **move_file(source, dest)** - Move/rename files
- ✅ **delete_file(path, require_approval)** - Delete files (with approval)
- ✅ **list_files(directory, pattern)** - List directory contents
- ✅ **parse_csv(path)** - Parse CSV files
- ✅ **parse_json(path)** - Parse JSON files

### Safety Features
- ✅ Directory whitelist for file operations
- ✅ Approval required for deletions
- ✅ Comprehensive audit logging
- ✅ Persistent browser sessions (save LinkedIn login)
- ✅ Screenshot verification for LinkedIn posts

## MCP Protocol Explanation

This server implements the **Model Context Protocol (MCP)** using stdin/stdout:

### Protocol Flow

1. **Client writes JSON request to stdin** (one JSON object per line)
2. **Server reads from stdin** (line by line)
3. **Server processes request**
4. **Server writes JSON response to stdout**
5. **Server flushes stdout**

### Request Format (Browser)

```json
{
  "method": "browser.linkedin_post",
  "params": {
    "message": "Excited to share our new product! #innovation"
  }
}
```

### Request Format (File)

```json
{
  "method": "file.read_file",
  "params": {
    "path": "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/Dashboard.md"
  }
}
```

### Response Format

```json
{
  "success": true,
  "operation": "browser.linkedin_post",
  "result": {
    "screenshot_path": "/Screenshots/linkedin_post_123.png"
  },
  "timestamp": "2026-02-19T10:30:00Z"
}
```

## Installation

### 1. Install Dependencies

```bash
cd mcp/fileops_mcp
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your paths
```

### 3. Test the Server

```bash
# Start server (interactive mode)
python server.py

# Send test requests:
echo '{"method": "file.list_files", "params": {"directory": ".", "pattern": "*.md"}}' | python server.py
```

## Configuration in claude_desktop_config.json

### Windows

Edit: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fileops-mcp": {
      "command": "python",
      "args": [
        "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/mcp/fileops_mcp/server.py"
      ],
      "env": {
        "BROWSER_TYPE": "chromium",
        "BROWSER_HEADLESS": "true",
        "SESSION_DIR": "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/.browser_session",
        "VAULT_PATH": "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault",
        "ALLOWED_DIRECTORIES": "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault"
      }
    }
  }
}
```

**Restart Claude Desktop** after editing the configuration.

## Available Methods

### Browser Methods

#### 1. browser.navigate

Navigate to a URL.

**Parameters:**
- `url` (required): URL to navigate to

**Example:**
```json
{
  "method": "browser.navigate",
  "params": {
    "url": "https://www.linkedin.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "operation": "browser.navigate",
  "result": {
    "url": "https://www.linkedin.com",
    "title": "LinkedIn: Log In or Sign Up"
  }
}
```

#### 2. browser.click

Click an element matching selector.

**Parameters:**
- `selector` (required): CSS selector for element

**Example:**
```json
{
  "method": "browser.click",
  "params": {
    "selector": "button:has-text('Sign In')"
  }
}
```

#### 3. browser.fill

Fill text into an input field.

**Parameters:**
- `selector` (required): CSS selector for input
- `text` (required): Text to fill

**Example:**
```json
{
  "method": "browser.fill",
  "params": {
    "selector": "input#email",
    "text": "user@example.com"
  }
}
```

#### 4. browser.get_text

Get text content from an element.

**Parameters:**
- `selector` (required): CSS selector for element

**Example:**
```json
{
  "method": "browser.get_text",
  "params": {
    "selector": "h1.page-title"
  }
}
```

#### 5. browser.screenshot

Take a screenshot.

**Parameters:**
- `path` (optional): Path to save screenshot (default: auto-generated)

**Example:**
```json
{
  "method": "browser.screenshot",
  "params": {
    "path": "D:/.../Screenshots/page.png"
  }
}
```

#### 6. browser.linkedin_post ⭐

Post to LinkedIn with automated browser.

**Parameters:**
- `message` (required): Post message

**Example:**
```json
{
  "method": "browser.linkedin_post",
  "params": {
    "message": "Excited to announce our new product launch! #innovation #business"
  }
}
```

**Response:**
```json
{
  "success": true,
  "operation": "browser.linkedin_post",
  "result": {
    "screenshot_path": "D:/.../Screenshots/linkedin_post_20260219_103000.png",
    "message": "Excited to announce our new product launch! #innovation #business"
  }
}
```

### File Methods

#### 7. file.read_file

Read file content.

**Parameters:**
- `path` (required): Path to file

**Example:**
```json
{
  "method": "file.read_file",
  "params": {
    "path": "D:/.../Vault/Dashboard.md"
  }
}
```

#### 8. file.write_file

Write content to file.

**Parameters:**
- `path` (required): Path to file
- `content` (required): Content to write

**Example:**
```json
{
  "method": "file.write_file",
  "params": {
    "path": "D:/.../Vault/Notes.md",
    "content": "# Notes\n\nThis is a note."
  }
}
```

#### 9. file.move_file

Move file from source to destination.

**Parameters:**
- `source` (required): Source file path
- `dest` (required): Destination path

**Example:**
```json
{
  "method": "file.move_file",
  "params": {
    "source": "D:/.../Inbox/file.md",
    "dest": "D:/.../Done/file.md"
  }
}
```

#### 10. file.delete_file

Delete file (requires approval by default).

**Parameters:**
- `path` (required): Path to file
- `require_approval` (optional): Whether to require approval (default: true)

**Example:**
```json
{
  "method": "file.delete_file",
  "params": {
    "path": "D:/.../Vault/temp.txt",
    "require_approval": true
  }
}
```

**Response (pending approval):**
```json
{
  "success": true,
  "operation": "file.delete_file",
  "requires_approval": true,
  "message": "Deletion requires approval",
  "result": {
    "path": "D:/.../Vault/temp.txt",
    "action": "pending_approval"
  }
}
```

#### 11. file.list_files

List files in directory.

**Parameters:**
- `directory` (required): Directory to list
- `pattern` (optional): Glob pattern (default: '*')

**Example:**
```json
{
  "method": "file.list_files",
  "params": {
    "directory": "D:/.../Vault",
    "pattern": "*.md"
  }
}
```

#### 12. file.parse_csv

Parse CSV file.

**Parameters:**
- `path` (required): Path to CSV file

**Example:**
```json
{
  "method": "file.parse_csv",
  "params": {
    "path": "D:/.../Vault/data.csv"
  }
}
```

#### 13. file.parse_json

Parse JSON file.

**Parameters:**
- `path` (required): Path to JSON file

**Example:**
```json
{
  "method": "file.parse_json",
  "params": {
    "path": "D:/.../Vault/config.json"
  }
}
```

## Browser Session Setup (First-Time Login)

### LinkedIn Automation Setup

The browser uses **persistent sessions** - your LinkedIn login is saved for reuse.

### First-Time Setup

1. **Start the server in interactive mode:**
   ```bash
   python server.py
   ```

2. **Manually login to LinkedIn:**
   ```json
   {"method": "browser.navigate", "params": {"url": "https://linkedin.com/login"}}
   ```

3. **Use browser.fill and browser.click to login:**
   ```json
   {"method": "browser.fill", "params": {"selector": "#username", "text": "your@email.com"}}
   {"method": "browser.fill", "params": {"selector": "#password", "text": "your-password"}}
   {"method": "browser.click", "params": {"selector": "button[type='submit']"}}
   ```

4. **Wait for login to complete** (check URL changes to feed)

5. **Session is saved!** Future `linkedin_post` calls will use saved session.

### Session Location

Sessions are stored in: `D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/.browser_session/`

**DO NOT DELETE** this folder - it contains your saved LinkedIn login.

## File Operations Safety Features

### 1. Directory Whitelist

Only files within `ALLOWED_DIRECTORIES` can be accessed.

**Configuration:**
```bash
ALLOWED_DIRECTORIES=D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault
```

**Multiple directories:**
```bash
ALLOWED_DIRECTORIES=D:/vault,D:/documents,D:/work
```

### 2. Deletion Approval

All deletions require explicit approval by default:

```json
{
  "method": "file.delete_file",
  "params": {
    "path": "D:/.../file.txt",
    "require_approval": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "requires_approval": true,
  "message": "Deletion requires approval"
}
```

### 3. Audit Logging

All operations logged to `Logs/fileops_audit_YYYY-MM-DD.json`:

```json
[
  {
    "timestamp": "2026-02-19T10:30:00",
    "operation_type": "file",
    "operation": "read_file",
    "success": true,
    "details": {
      "path": "D:/.../Dashboard.md",
      "size_bytes": 1024,
      "duration_ms": 5.2
    }
  }
]
```

## Testing Instructions

### Test File Operations

```bash
# List files
echo '{"method": "file.list_files", "params": {"directory": ".", "pattern": "*.md"}}' | python server.py

# Read file
echo '{"method": "file.read_file", "params": {"path": "Dashboard.md"}}' | python server.py

# Write file
echo '{"method": "file.write_file", "params": {"path": "test.txt", "content": "Hello"}}' | python server.py
```

### Test Browser Operations

```bash
# Navigate
echo '{"method": "browser.navigate", "params": {"url": "https://example.com"}}' | python server.py

# Screenshot
echo '{"method": "browser.screenshot", "params": {}}' | python server.py

# LinkedIn post (requires login)
echo '{"method": "browser.linkedin_post", "params": {"message": "Test post"}}' | python server.py
```

## Troubleshooting

### Playwright Not Installed

**Symptom:** `ImportError: No module named 'playwright'`

**Solution:**
```bash
pip install playwright
playwright install chromium
```

### Browser Won't Launch

**Symptom:** Browser launch fails

**Solution:**
```bash
# Reinstall browsers
playwright install chromium

# Check permissions
ls -la ~/.cache/ms-playwright/
```

### LinkedIn Not Logged In

**Symptom:** `NOT_LOGGED_IN` error

**Solution:**
1. Navigate to LinkedIn login manually
2. Login through browser
3. Session will be saved for future use

### File Access Denied

**Symptom:** `ACCESS_DENIED` error

**Solution:**
- Check file is within `ALLOWED_DIRECTORIES`
- Add directory to whitelist in `.env`

## File Structure

```
mcp/fileops_mcp/
├── server.py              # Main MCP server
├── README.md              # This file
├── LINKEDIN_AUTOMATION_GUIDE.md  # LinkedIn setup guide
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── .env                  # Your configuration (DO NOT COMMIT)

# Generated files:
../Logs/
├── fileops_mcp.log                    # Error logs
├── fileops_audit_YYYY-MM-DD.json      # Daily audit logs

../Screenshots/
└── screenshot_*.png                   # Browser screenshots

../.browser_session/
└── chromium/                          # Persistent browser session
```

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│    (Client)     │
└────────┬────────┘
         │ JSON via stdin/stdout
         ▼
┌─────────────────┐
│  FileOps MCP    │
│  Server         │
├─────────────────┤
│  Browser Mgr    │
│  (Playwright)   │
├─────────────────┤
│  File Ops Mgr   │
│  (Safe I/O)     │
├─────────────────┤
│  Audit Logger   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│LinkedIn│ │File System│
└───────┘ └──────────┘
```

## Security Best Practices

1. **Never commit `.env`** - Contains paths and configuration
2. **Use directory whitelist** - Restrict file access
3. **Require deletion approval** - Prevent accidental data loss
4. **Review audit logs** - Monitor for unusual activity
5. **Secure session folder** - Protect saved LinkedIn login

## License

MIT License - See project LICENSE file.

## Support

For LinkedIn automation issues, see `LINKEDIN_AUTOMATION_GUIDE.md`.
For general troubleshooting, check `Logs/fileops_mcp.log`.
