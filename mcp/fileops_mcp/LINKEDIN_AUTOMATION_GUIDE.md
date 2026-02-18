# LinkedIn Automation Guide

Complete guide for automating LinkedIn posts using the FileOps MCP Server.

---

## Table of Contents

1. [Overview](#overview)
2. [First-Time Setup](#first-time-setup)
3. [Automated Posting](#automated-posting)
4. [Troubleshooting](#troubleshooting)
5. [Best Practices](#best-practices)

---

## Overview

The FileOps MCP Server provides automated LinkedIn posting through browser automation using Playwright.

### How It Works

1. **Persistent Browser Session**
   - First login is manual
   - Session (cookies) saved to `.browser_session/`
   - Future posts use saved session

2. **Automated Workflow**
   - Navigate to LinkedIn feed
   - Click "Start a post"
   - Fill message
   - Click "Post"
   - Screenshot for verification

3. **Safety Features**
   - Screenshot verification
   - Error handling
   - Session persistence

---

## First-Time Setup

### Step 1: Install Dependencies

```bash
# Install Playwright
pip install playwright
playwright install chromium
```

### Step 2: Configure Environment

Edit `.env` file:

```bash
BROWSER_TYPE=chromium
BROWSER_HEADLESS=false  # Set to false for first login
SESSION_DIR=D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/.browser_session
```

### Step 3: Manual Login (One-Time)

#### Option A: Interactive Browser

1. **Start server:**
   ```bash
   cd mcp/fileops_mcp
   python server.py
   ```

2. **Navigate to LinkedIn:**
   ```json
   {"method": "browser.navigate", "params": {"url": "https://www.linkedin.com/login"}}
   ```

3. **Wait for page to load** (check response title)

4. **Fill credentials:**
   ```json
   {"method": "browser.fill", "params": {"selector": "#username", "text": "your@email.com"}}
   {"method": "browser.fill", "params": {"selector": "#password", "text": "your-password"}}
   ```

5. **Click sign in:**
   ```json
   {"method": "browser.click", "params": {"selector": "button[type='submit']"}}
   ```

6. **Wait for navigation to feed**
   - Check URL changes to `linkedin.com/feed`
   - Session is now saved!

7. **Close browser** (Ctrl+C to stop server)

#### Option B: Headless with Script

Create a login script `login_linkedin.py`:

```python
import subprocess
import json
import time

def send_request(method, params):
    request = {"method": method, "params": params}
    result = subprocess.run(
        ['python', 'server.py'],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Navigate to login
print("Navigating to LinkedIn login...")
response = send_request('browser.navigate', {
    'url': 'https://www.linkedin.com/login'
})
print(f"Title: {response.get('result', {}).get('title')}")

print("\nPlease login manually in the browser window.")
print("After login, the session will be saved.")
print("\nPress Enter to exit...")
input()
```

Run it:
```bash
python login_linkedin.py
```

### Step 4: Verify Session

After login, verify session was saved:

```bash
# Check session directory
dir .browser_session\chromium

# Should contain:
# - Cookies
# - Local Storage
# - Other browser data
```

**DO NOT DELETE** the `.browser_session` folder - it contains your saved login!

---

## Automated Posting

### Basic Post

```json
{
  "method": "browser.linkedin_post",
  "params": {
    "message": "Excited to share our latest innovation! #automation #AI"
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
    "message": "Excited to share our latest innovation! #automation #AI"
  }
}
```

### Post with Hashtags

```json
{
  "method": "browser.linkedin_post",
  "params": {
    "message": "Just published a new article on AI automation!\n\nKey topics:\n- MCP servers\n- Browser automation\n- File operations\n\n#AI #Automation #Technology #Innovation"
  }
}
```

### Post from File Content

```bash
# Read content from file
echo '{"method": "file.read_file", "params": {"path": "Posts/draft.md"}}' | python server.py

# Then post
echo '{"method": "browser.linkedin_post", "params": {"message": "Content from file..."}}' | python server.py
```

### Verify Post

After posting:

1. **Check screenshot:**
   ```bash
   # Open screenshot
   start D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault\Screenshots\linkedin_post_*.png
   ```

2. **Verify on LinkedIn:**
   - Navigate to your profile
   - Check "Activity" section
   - Confirm post appears

---

## Troubleshooting

### Problem: "Not logged in" Error

**Symptom:**
```json
{
  "success": false,
  "error": "Not logged in to LinkedIn. Please login manually first.",
  "error_code": "NOT_LOGGED_IN"
}
```

**Solution:**

1. **Check session folder exists:**
   ```bash
   dir .browser_session\chromium
   ```

2. **If folder is empty or missing:**
   - Repeat first-time setup
   - Login manually
   - Verify session saved

3. **If folder exists but error persists:**
   - LinkedIn may have cleared session
   - Re-login manually
   - Check for LinkedIn security emails

### Problem: Browser Won't Launch

**Symptom:** Browser doesn't open or crashes

**Solution:**

1. **Reinstall Playwright:**
   ```bash
   pip install --upgrade playwright
   playwright install chromium
   ```

2. **Check system requirements:**
   - Windows 10/11
   - At least 2GB RAM free
   - Graphics drivers updated

3. **Try different browser:**
   ```bash
   # Edit .env
   BROWSER_TYPE=firefox  # or webkit
   ```

### Problem: Post Fails to Submit

**Symptom:** Timeout or "Failed to post" error

**Solution:**

1. **Check LinkedIn UI changes:**
   - LinkedIn may have updated selectors
   - Check server logs for details

2. **Increase timeout:**
   ```bash
   # Edit .env
   BROWSER_TIMEOUT=60  # Increase from 30
   ```

3. **Manual verification:**
   - Navigate to feed manually
   - Check "Start a post" button exists
   - Verify account not restricted

### Problem: Screenshot Not Saved

**Symptom:** Success response but no screenshot

**Solution:**

1. **Check Screenshots folder:**
   ```bash
   dir D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault\Screenshots
   ```

2. **Verify permissions:**
   - Ensure folder exists
   - Check write permissions

3. **Check disk space:**
   - Screenshots are ~500KB each
   - Clean old screenshots if needed

---

## Best Practices

### Posting Schedule

**Optimal Times:**
- Tuesday-Thursday: 9-11 AM
- Wednesday: Best day overall
- Avoid: Weekends, Mondays

**Frequency:**
- 2-3 posts per week
- Space posts 2-3 days apart
- Quality over quantity

### Content Guidelines

**Character Limits:**
- Posts: 3,000 characters max
- Optimal: 1,300-1,500 characters
- Headlines: 150 characters

**Hashtags:**
- Use 3-5 relevant hashtags
- Mix popular and niche tags
- Create branded hashtag

**Engagement:**
- Include call-to-action
- Ask questions
- Share insights, not just promotions

### Session Management

**Protect Your Session:**

1. **Backup session folder:**
   ```bash
   # Periodic backup
   xcopy /E /I .browser_session .browser_session_backup
   ```

2. **Don't share session files:**
   - Contains authentication cookies
   - Treat like password

3. **Rotate periodically:**
   - Every 3-6 months
   - Delete `.browser_session`
   - Re-login

### Error Recovery

**If Post Fails:**

1. **Check error code:**
   - `NOT_LOGGED_IN` → Re-login
   - `LINKEDIN_POST_FAILED` → Check UI/selectors
   - `SCREENSHOT_FAILED` → Check folder permissions

2. **Review logs:**
   ```bash
   type Logs\fileops_mcp.log
   ```

3. **Try manual post:**
   - Navigate to LinkedIn
   - Post manually
   - Check for account restrictions

### Security

**Protect Your Account:**

1. **Use strong password**
2. **Enable 2FA**
3. **Don't automate too frequently** (avoid spam detection)
4. **Monitor account activity**
5. **Review LinkedIn User Agreement**

---

## Advanced Usage

### Custom Selectors

If LinkedIn changes UI, update selectors in code:

```python
# In server.py, linkedin_post method:

# Current selectors (as of 2026-02)
self.page.click('button[aria-label="Start a post"]')
self.page.locator('div[role="textbox"]').first

# Alternative selectors
self.page.click('.share-box-feed-entry__trigger')
self.page.locator('.ProseMirror').first
```

### Batch Posting

Create a batch script `batch_posts.py`:

```python
import json
import subprocess
import time

posts = [
    "Post 1: Introduction to AI",
    "Post 2: Machine Learning Basics",
    "Post 3: Deep Learning Applications"
]

for i, post in enumerate(posts):
    request = {
        "method": "browser.linkedin_post",
        "params": {"message": post}
    }
    
    result = subprocess.run(
        ['python', 'server.py'],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    response = json.loads(result.stdout)
    print(f"Post {i+1}: {response.get('success')}")
    
    # Wait between posts
    if i < len(posts) - 1:
        time.sleep(300)  # 5 minutes
```

### Scheduled Posting

Use Windows Task Scheduler:

```batch
REM Run every Tuesday at 10 AM
schtasks /create /tn "LinkedIn_Post" /tr "python batch_posts.py" /sc weekly /d TUE /st 10:00
```

---

## API Reference

### browser.linkedin_post

**Parameters:**
- `message` (required): Post content (max 3000 chars)

**Returns:**
- `success`: Boolean
- `operation`: "browser.linkedin_post"
- `result.screenshot_path`: Path to verification screenshot
- `result.message`: Posted message (truncated)

**Error Codes:**
- `NOT_LOGGED_IN`: Session expired
- `LINKEDIN_POST_FAILED`: UI interaction failed
- `SCREENSHOT_FAILED`: Screenshot capture failed

---

## Support

**Logs Location:**
- Error log: `Logs/fileops_mcp.log`
- Audit log: `Logs/fileops_audit_YYYY-MM-DD.json`

**Session Location:**
- `.browser_session/chromium/`

**Screenshots:**
- `Screenshots/linkedin_post_*.png`

**Need Help?**

1. Check this guide first
2. Review error logs
3. Verify session exists
4. Try manual LinkedIn access

---

**Happy Posting! 🚀**
