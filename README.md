# AI Employee Vault System

A comprehensive file management system that automates task processing and workflow management using a folder-based approach. Now includes Gold Tier integrations for ERP, social media, and personal productivity.

## Overview

The AI Employee Vault System consists of multiple tiers of components:

### Core Components
1. **Filesystem Watcher** - Monitors the Inbox folder and creates reports for new files
2. **Orchestrator** - Processes files in the Needs_Action folder and manages workflows
3. **Process Tasks Skill** - A Claude Agent skill for manual task processing

### Gold Tier Integrations (New)
4. **Odoo MCP Server** - ERP integration for invoice and accounting management
5. **Twitter Post Skill** - Twitter API integration for automated posting
6. **Social Meta Skill** - Facebook and Instagram posting via Graph API
7. **Personal Task Handler** - Personal productivity management (tasks, habits, goals, journal)

## Prerequisites

- Python 3.10 or higher
- `watchdog` library (for filesystem monitoring)
- Additional dependencies for Gold Tier features (see Installation)

## Installation

### Core Installation
```bash
pip install watchdog
```

### Gold Tier Installation
```bash
# Odoo MCP Server
pip install requests python-dotenv mcp

# Twitter Skill
pip install tweepy python-dotenv

# Social Meta Skill
pip install requests python-dotenv

# All at once
pip install watchdog requests python-dotenv mcp tweepy
```

### Environment Configuration
```bash
# Copy the environment template
cp .env.example .env

# Edit .env and fill in your credentials
```

## Components

### Core Components

#### 1. Filesystem Watcher (`filesystem_watcher.py`)

Monitors the `Inbox` folder for new files and automatically creates markdown reports in the `Needs_Action` folder.

**Features:**
- Watches for new files in the Inbox folder
- Creates detailed reports with filename, size, timestamp, and status
- Automatic folder creation if missing
- Basic logging functionality
- Error handling to prevent crashes

**To run:**
```bash
python filesystem_watcher.py
```

#### 2. Orchestrator (`orchestrator.py`)

Processes markdown files in the `Needs_Action` folder by creating plan files, updating the dashboard, and moving processed files to the `Done` folder.

**To run:**
```bash
python orchestrator.py
```

#### 3. Process Tasks Skill

A Claude Agent skill for manual task processing. See `process_tasks_skill.md` for details.

---

### Gold Tier Components

#### 4. Odoo MCP Server (`mcp/odoo_mcp/`)

Production-ready MCP server for Odoo ERP integration via JSON-RPC API.

**Capabilities:**
- `create_invoice` - Create invoices in Odoo (requires approval)
- `list_invoices` - List invoices with filters
- `record_payment` - Record payments against invoices (requires approval)
- `get_account_summary` - Get accounting summaries
- `search_partner` - Search for customers/vendors

**Setup:**
```bash
cd mcp/odoo_mcp
pip install -r requirements.txt
# Configure .env with Odoo credentials
python server.py --check-config
python server.py --test-connection
```

**Usage:**
```bash
# Run as MCP server (stdio)
python server.py

# Run with HTTP transport
python server.py --port 8080
```

**Documentation:** See `mcp/odoo_mcp/README.md`

---

#### 5. Twitter Post Skill (`.claude/skills/twitter-post/`)

Twitter API integration for automated tweet posting and history retrieval.

**Capabilities:**
- `post_tweet` - Post tweets with content and hashtags
- `get_tweet_history` - Retrieve recent tweets
- `delete_tweet` - Delete tweets by ID
- Automatic logging to `Reports/twitter_log.md`

**Setup:**
```bash
# Install dependencies
pip install tweepy

# Configure Twitter credentials in .env
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_SECRET=
TWITTER_BEARER_TOKEN=
```

**Usage:**
```python
# Post a tweet
result = twitter_post_skill(
    action="post",
    content="Excited to share our news!",
    hashtags=["innovation", "tech"]
)

# Get tweet history
result = twitter_post_skill(action="history", count=10)
```

**CLI:**
```bash
python .claude/skills/twitter-post/twitter_post.py --action post --content "Hello Twitter!" --hashtags tech innovation
```

---

#### 6. Social Meta Skill (`.claude/skills/social-meta/`)

Combined Facebook and Instagram posting via Facebook Graph API.

**Capabilities:**
- `post_facebook` - Post to Facebook Page (text or with image)
- `post_instagram` - Post to Instagram (requires public image URL)
- `get_facebook_insights` - Get Page insights
- `get_instagram_insights` - Get media insights
- Logging to `Logs/social.log` (JSON Lines format)

**Setup:**
```bash
# Install dependencies
pip install requests

# Configure credentials in .env
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
FACEBOOK_PAGE_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=
```

**Usage:**
```python
# Post to Facebook
result = social_meta_skill(
    platform="facebook",
    action="post",
    content="Exciting news from our team!"
)

# Post to Instagram (requires public image URL)
result = social_meta_skill(
    platform="instagram",
    action="post",
    content="Beautiful sunset!",
    image_url="https://example.com/image.jpg"
)

# Get insights
result = social_meta_skill(
    platform="facebook",
    action="insights",
    since="2026-02-01",
    until="2026-02-20"
)
```

**CLI:**
```bash
python .claude/skills/social-meta/social_poster.py --platform facebook --action post --content "Hello Facebook!"
```

---

#### 7. Personal Task Handler (`.claude/skills/personal-task-handler/`)

Personal productivity management system integrated with the vault workflow.

**Capabilities:**
- `create_task` - Create personal tasks with priority and due date
- `list_tasks` - List tasks by status/priority/category
- `complete_task` - Mark tasks as complete
- `track_habit` - Track daily habit completion with streaks
- `add_goal` - Set personal goals
- `list_goals` - View goal status
- `add_journal` - Add dated journal entries
- `get_summary` - Get personal dashboard summary

**File Structure:**
```
Personal/
├── Tasks/
│   ├── pending/      # Active tasks
│   └── completed/    # Completed tasks
├── Goals/            # Personal goals
├── Habits/
│   ├── habits.json   # Habit definitions and history
│   └── history/      # Daily logs
└── Journal/
    └── entries/      # Dated journal files
```

**Usage:**
```python
# Create a task
result = personal_task_handler_skill(
    action="create_task",
    title="Complete project proposal",
    priority="high",
    due_date="2026-02-25",
    checklist=["Research", "Draft", "Review", "Submit"]
)

# Track a habit
result = personal_task_handler_skill(
    action="track_habit",
    habit_name="Morning Exercise",
    completed=True
)

# Get summary
result = personal_task_handler_skill(action="get_summary")
```

**CLI:**
```bash
python .claude/skills/personal-task-handler/personal_handler.py --action get_summary --json
```

---

## Folder Structure

```
AI_Employee_Vault/
├── Inbox/                  # Input files trigger automatic reports
├── Needs_Action/           # Files requiring action
├── Plans/                  # Generated action plans
├── Done/                   # Completed tasks
├── Reports/                # Generated reports
│   └── twitter_log.md      # Twitter activity log
├── Logs/                   # Operation logs
│   ├── business.log        # Business operations
│   ├── odoo.log            # Odoo MCP operations
│   ├── social.log          # Social media operations
│   └── personal.log        # Personal task operations
├── Pending_Approval/       # Awaiting human approval
├── Personal/               # Personal productivity
│   ├── Tasks/
│   ├── Goals/
│   ├── Habits/
│   └── Journal/
├── Accounting/             # Financial records
├── mcp/                    # MCP servers
│   ├── business_mcp/
│   ├── email_mcp/
│   ├── fileops_mcp/
│   ├── social_mcp/
│   └── odoo_mcp/           # Gold Tier: Odoo integration
├── .claude/skills/         # Claude Agent skills
│   ├── twitter-post/       # Gold Tier: Twitter
│   ├── social-meta/        # Gold Tier: Facebook/Instagram
│   ├── personal-task-handler/  # Gold Tier: Personal
│   └── ...                 # Other skills
├── scripts/                # Python scripts
├── .env.example            # Environment template
├── .env                    # Your credentials (gitignored)
└── README.md               # This file
```

## How to Use

### Basic Workflow

1. Place files in the `Inbox` folder
2. Run `filesystem_watcher.py` to generate reports in `Needs_Action`
3. Run `orchestrator.py` to process files and create plans
4. Monitor progress in `Dashboard.md`

### Gold Tier Workflows

#### Odoo Invoice Management
```bash
# Check Odoo connection
python mcp/odoo_mcp/server.py --test-connection

# Run MCP server for Claude integration
python mcp/odoo_mcp/server.py
```

#### Social Media Posting
```bash
# Post to Twitter
python .claude/skills/twitter-post/twitter_post.py --action post --content "News!" --hashtags tech

# Post to Facebook
python .claude/skills/social-meta/social_poster.py --platform facebook --action post --content "Update"
```

#### Personal Productivity
```bash
# Daily summary
python .claude/skills/personal-task-handler/personal_handler.py --action get_summary

# Track habits
python .claude/skills/personal-task-handler/personal_handler.py --action track_habit --habit-name "Exercise"
```

## Environment Variables

See `.env.example` for all available configuration options:

| Variable | Description | Tier |
|----------|-------------|------|
| `EMAIL_ADDRESS` | Gmail address | Core |
| `EMAIL_PASSWORD` | Gmail app password | Core |
| `ODOO_URL` | Odoo server URL | Gold |
| `ODOO_DB` | Odoo database | Gold |
| `ODOO_USERNAME` | Odoo username | Gold |
| `ODOO_PASSWORD` | Odoo password | Gold |
| `TWITTER_API_KEY` | Twitter API key | Gold |
| `TWITTER_API_SECRET` | Twitter API secret | Gold |
| `TWITTER_ACCESS_TOKEN` | Twitter access token | Gold |
| `TWITTER_ACCESS_SECRET` | Twitter access secret | Gold |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Facebook Page token | Gold |
| `FACEBOOK_PAGE_ID` | Facebook Page ID | Gold |
| `INSTAGRAM_ACCESS_TOKEN` | Instagram token | Gold |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Instagram Business ID | Gold |
| `LINKEDIN_EMAIL` | LinkedIn email | Silver |
| `LINKEDIN_PASSWORD` | LinkedIn password | Silver |

## Safety Features

- No files are deleted - they are moved between folders
- Duplicate processing prevention
- Comprehensive error handling
- Safe dashboard updates with backup mechanism
- Structured JSON logging
- **Approval workflows** for sensitive operations (Odoo write operations)
- **Rate limiting** for API calls
- **Audit trails** for all operations

## Troubleshooting

### Core Issues
- If the watcher doesn't detect new files, ensure the `Inbox` folder exists
- Check the log files in the `Logs` folder for error details
- Make sure you have write permissions for all folders

### Gold Tier Issues

**Odoo Connection Failed:**
- Verify Odoo URL includes `https://` or `http://`
- Check Odoo server is accessible
- Verify credentials in Odoo user settings

**Twitter Authentication Failed:**
- Ensure all 5 Twitter credentials are set
- Verify Twitter Developer account is active
- Check API permissions in Twitter Developer Portal

**Facebook/Instagram Errors:**
- Verify Facebook App has required permissions
- Ensure Instagram Business account is connected to Facebook Page
- Check token expiration and refresh if needed

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AI Employee Vault System                     │
├─────────────────────────────────────────────────────────────────┤
│  Core Tier                                                       │
│  ├── Filesystem Watcher → Inbox monitoring                      │
│  ├── Orchestrator → Workflow management                         │
│  └── Process Tasks Skill → Claude integration                   │
├─────────────────────────────────────────────────────────────────┤
│  Silver Tier                                                     │
│  ├── Email MCP → Gmail integration                              │
│  ├── LinkedIn Skill → LinkedIn posting                          │
│  └── Business MCP → Combined email/LinkedIn                     │
├─────────────────────────────────────────────────────────────────┤
│  Gold Tier (NEW)                                                 │
│  ├── Odoo MCP Server → ERP integration                          │
│  ├── Twitter Post Skill → Twitter API                           │
│  ├── Social Meta Skill → Facebook/Instagram                     │
│  └── Personal Task Handler → Productivity management            │
└─────────────────────────────────────────────────────────────────┘
```

## License

This project is available for use under the terms of the MIT License.

## Contributing

1. Follow existing code patterns
2. Add tests for new features
3. Update documentation
4. Never commit credentials
