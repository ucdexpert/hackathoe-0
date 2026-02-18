# Business MCP Server - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to MCP directory
cd D:\hackathons-Q-4\hackthon-0\AI_Employee_Vault\mcp\business_mcp

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright (optional, for real LinkedIn posting)
playwright install
```

### Step 2: Configure Email (1 minute)

1. Open the root `.env` file or create one in this directory
2. Add your Gmail credentials:

```bash
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your-app-password
```

**Get Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable **2-Factor Authentication**
3. Go to https://myaccount.google.com/apppasswords
4. Create app password for "Mail"
5. Copy the 16-character password to `.env`

### Step 3: Test the Server (1 minute)

```bash
# Check server status
python server.py --status

# Test email (simulation)
python server.py --test-email

# Test LinkedIn (simulation)
python server.py --test-linkedin
```

### Step 4: Run the Server (1 minute)

```bash
# Run with stdio transport (for Claude Code)
python server.py

# Or run with HTTP transport
python server.py --port 8080
```

---

## 🔗 Integration with Claude Desktop

### Option 1: Automatic Setup

Run this command to automatically configure Claude Desktop:

```bash
python configure_claude.py
```

### Option 2: Manual Configuration

1. Open Claude Desktop configuration:
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add the business-mcp server:

```json
{
  "mcpServers": {
    "business-mcp": {
      "command": "python",
      "args": [
        "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/mcp/business_mcp/server.py"
      ],
      "env": {
        "EMAIL_ADDRESS": "your.email@gmail.com",
        "EMAIL_PASSWORD": "your-app-password"
      }
    }
  }
}
```

3. Restart Claude Desktop

---

## 📋 Available Tools

Once connected, Claude can use these tools:

### 1. Send Email
```
Send an email to client@example.com about the project update
```

### 2. Post to LinkedIn
```
Create a LinkedIn post about our new product launch
```

### 3. Log Activity
```
Log that we completed the quarterly review meeting
```

---

## 🧪 Testing

```bash
# Run all tests
pytest test_server.py -v

# Run with coverage
pytest test_server.py --cov=. --cov-report=term-missing

# Test specific functionality
python server.py --test-email
python server.py --test-linkedin
```

---

## 📁 Project Structure

```
mcp/business_mcp/
├── server.py              # Main MCP server
├── requirements.txt       # Python dependencies
├── README.md             # Full documentation
├── QUICKSTART.md         # This file
├── test_server.py        # Unit tests
├── claude_desktop_config.json  # Claude Desktop config template
└── setup_task_scheduler.bat    # Windows Task Scheduler setup
```

---

## 🔧 Troubleshooting

### Server Won't Start

```bash
# Check Python version (need 3.8+)
python --version

# Check MCP installation
pip show mcp

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Email Not Working

1. Verify you're using an **App Password**, not regular password
2. Check 2FA is enabled on Gmail
3. Test with: `python server.py --test-email`

### LinkedIn Not Posting

- Without Playwright: Posts run in **simulation mode** (logged but not posted)
- With Playwright: Set `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD`
- Test with: `python server.py --test-linkedin`

---

## 📊 View Logs

All activities are logged to `Logs/business.log`:

```bash
# View recent logs (Windows PowerShell)
Get-Content ..\..\Logs\business.log -Tail 20

# View recent logs (Linux/Mac)
tail -20 ../../Logs/business.log

# View in real-time (Windows)
powershell -Command "Get-Content ..\..\Logs\business.log -Wait -Tail 10"
```

---

## 🎯 Next Steps

1. ✅ Test email sending
2. ✅ Test LinkedIn posting
3. ✅ Configure Claude Desktop
4. ✅ Set up Windows Task Scheduler (optional)
5. ✅ Start using with Claude!

---

## 📞 Support

- **Full Documentation:** See `README.md`
- **Tests:** Run `pytest test_server.py -v`
- **Logs:** Check `Logs/business.log`
- **Status:** Run `python server.py --status`

---

**Happy Automating! 🚀**
