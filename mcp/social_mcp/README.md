# Social Media MCP Server

A unified production-ready MCP (Model Context Protocol) server for Twitter, Facebook, and Instagram operations using the stdin/stdout JSON protocol.

## Features

### Twitter
- ✅ **post_tweet** - Post tweets with optional images
- ✅ **get_mentions** - Get recent mentions
- ✅ Rate limiting: 50 tweets/day

### Facebook
- ✅ **post_to_page** - Post to Facebook pages
- ✅ **get_page_insights** - Get page analytics
- ✅ Rate limiting: API default

### Instagram
- ✅ **post_image** - Post images with captions and hashtags
- ✅ **get_recent_media** - Get recent posts
- ✅ Rate limiting: 25 posts/day

### General
- ✅ **create_post_draft** - Create drafts requiring approval
- ✅ Multi-platform support in single MCP
- ✅ Retry logic with exponential backoff
- ✅ Comprehensive audit logging
- ✅ Rate limit handling per platform

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
  "method": "post_tweet",
  "params": {
    "text": "Check out our new product! #business",
    "image_url": null
  }
}
```

### Response Format

```json
{
  "success": true,
  "platform": "twitter",
  "post_id": "1234567890",
  "url": "https://twitter.com/user/status/1234567890",
  "timestamp": "2026-02-19T10:30:00Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Twitter credentials not configured",
  "error_code": "NOT_CONFIGURED",
  "timestamp": "2026-02-19T10:30:00Z"
}
```

## Installation

### 1. Install Dependencies

```bash
cd mcp/social_mcp
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API credentials
# See API_SETUP_GUIDE.md for detailed setup instructions
```

### 3. Test the Server

```bash
# Start server (interactive mode)
python server.py

# Send test requests:
echo '{"method": "post_tweet", "params": {"text": "Test tweet"}}' | python server.py
```

## Configuration in claude_desktop_config.json

### Windows

Edit: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "social-mcp": {
      "command": "python",
      "args": [
        "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault/mcp/social_mcp/server.py"
      ],
      "env": {
        "TWITTER_BEARER_TOKEN": "your_bearer_token",
        "TWITTER_API_KEY": "your_api_key",
        "TWITTER_API_SECRET": "your_api_secret",
        "FACEBOOK_ACCESS_TOKEN": "your_access_token",
        "FACEBOOK_PAGE_ID": "your_page_id",
        "INSTAGRAM_ACCESS_TOKEN": "your_instagram_token",
        "INSTAGRAM_BUSINESS_ACCOUNT_ID": "your_account_id",
        "VAULT_PATH": "D:/hackathons-Q-4/hackthon-0/AI_Employee_Vault"
      }
    }
  }
}
```

**Restart Claude Desktop** after editing the configuration.

## Available Methods

### Twitter

#### 1. post_tweet

Post a tweet to Twitter.

**Parameters:**
- `text` (required): Tweet text (max 280 characters)
- `image_url` (optional): URL of image to attach

**Example:**
```json
{
  "method": "post_tweet",
  "params": {
    "text": "Excited to announce our new product! #innovation #business",
    "image_url": "https://example.com/image.jpg"
  }
}
```

**Response:**
```json
{
  "success": true,
  "platform": "twitter",
  "post_id": "1234567890",
  "url": "https://twitter.com/user/status/1234567890",
  "text": "Excited to announce our new product! #innovation #business"
}
```

#### 2. get_mentions

Get recent mentions.

**Parameters:**
- `count` (optional): Number of mentions to retrieve (default: 10)

**Example:**
```json
{
  "method": "get_mentions",
  "params": {
    "count": 5
  }
}
```

### Facebook

#### 3. post_to_page

Post to a Facebook page.

**Parameters:**
- `message` (required): Post message
- `page_id` (optional): Page ID (uses default from config if not provided)
- `image_url` (optional): URL of image to attach

**Example:**
```json
{
  "method": "post_to_page",
  "params": {
    "message": "Check out our latest update!",
    "page_id": "123456789",
    "image_url": "https://example.com/image.jpg"
  }
}
```

#### 4. get_page_insights

Get Facebook page insights.

**Parameters:**
- `page_id` (optional): Page ID (uses default from config)

**Example:**
```json
{
  "method": "get_page_insights",
  "params": {
    "page_id": "123456789"
  }
}
```

### Instagram

#### 5. post_image

Post an image to Instagram.

**Parameters:**
- `image_path` (required): Local path to image file
- `caption` (required): Post caption
- `hashtags` (optional): List of hashtags

**Example:**
```json
{
  "method": "post_image",
  "params": {
    "image_path": "D:/images/product.jpg",
    "caption": "New product launch!",
    "hashtags": ["#newproduct", "#innovation", "#business"]
  }
}
```

#### 6. get_recent_media

Get recent Instagram media.

**Parameters:**
- `count` (optional): Number of posts to retrieve (default: 10)

**Example:**
```json
{
  "method": "get_recent_media",
  "params": {
    "count": 5
  }
}
```

### General

#### 7. create_post_draft

Create a draft post requiring human approval.

**Parameters:**
- `platform` (required): Platform (twitter/facebook/instagram)
- `content` (required): Post content
- `hashtags` (optional): List of hashtags (for Instagram)
- `image_url` (optional): Image URL

**Example:**
```json
{
  "method": "create_post_draft",
  "params": {
    "platform": "twitter",
    "content": "Announcing our Q2 results..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Draft created successfully",
  "draft_path": "D:/.../Pending_Approval/draft_twitter_20260219_103000.md",
  "requires_approval": true
}
```

## Rate Limits

| Platform | Limit | Period | Notes |
|----------|-------|--------|-------|
| Twitter | 50 | Per day | Customizable in .env |
| Facebook | API default | Varies | Depends on page size |
| Instagram | 25 | Per day | Customizable in .env |

When rate limit is exceeded, the server returns:

```json
{
  "success": false,
  "error": "Twitter rate limit exceeded. 0 posts remaining today.",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

## Testing Instructions

### Interactive Testing

```bash
# Start server
python server.py

# Test Twitter
echo '{"method": "post_tweet", "params": {"text": "Test tweet"}}' | python server.py

# Test Facebook
echo '{"method": "post_to_page", "params": {"message": "Test post"}}' | python server.py

# Test Instagram
echo '{"method": "post_image", "params": {"image_path": "test.jpg", "caption": "Test"}}' | python server.py

# Test draft creation
echo '{"method": "create_post_draft", "params": {"platform": "twitter", "content": "Draft"}}' | python server.py
```

### Automated Testing

```python
import subprocess
import json

def test_social_mcp(method, params):
    request = {"method": method, "params": params}
    result = subprocess.run(
        ['python', 'server.py'],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

# Test Twitter
print(test_social_mcp('post_tweet', {'text': 'Test'}))

# Test Facebook
print(test_social_mcp('post_to_page', {'message': 'Test'}))

# Test Instagram
print(test_social_mcp('create_post_draft', {
    'platform': 'instagram',
    'content': 'Test'
}))
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

### Platform Not Configured

**Symptom:** `NOT_CONFIGURED` error

**Solution:**
1. Verify credentials in `.env` file
2. Check API_SETUP_GUIDE.md for setup instructions
3. Ensure tokens haven't expired

### Rate Limit Exceeded

**Symptom:** `RATE_LIMIT_EXCEEDED` error

**Solution:**
- Wait for limit to reset (next day)
- Check `Logs/social_rate_limit.json` for current usage
- Increase limits in `.env` (within platform guidelines)

### Invalid Credentials

**Symptom:** Authentication errors

**Solution:**
- Twitter: Regenerate Bearer Token in Developer Portal
- Facebook: Regenerate Page Access Token
- Instagram: Ensure Business Account is linked to Facebook Page

### Posts Not Appearing

**Symptom:** Success response but post not visible

**Solution:**
- Check `Logs/social_audit_*.json` for actual API responses
- Verify account/page permissions
- Check if post requires review (Facebook)

## File Structure

```
mcp/social_mcp/
├── server.py              # Main MCP server
├── README.md              # This file
├── API_SETUP_GUIDE.md     # API credential setup
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── .env                  # Your configuration (DO NOT COMMIT)

# Generated files:
../Logs/
├── social_mcp.log                    # Error logs
├── social_audit_YYYY-MM-DD.json      # Daily audit logs
└── social_rate_limit.json            # Rate limit state

../Pending_Approval/
└── draft_*.md                        # Post drafts
```

## Audit Logging

All operations are logged to `Logs/social_audit_YYYY-MM-DD.json`:

```json
[
  {
    "timestamp": "2026-02-19T10:30:00",
    "platform": "twitter",
    "operation": "post_tweet",
    "success": true,
    "details": {
      "text": "Test tweet",
      "tweet_id": "1234567890",
      "duration_ms": 250.5
    }
  }
]
```

## Security Best Practices

1. **Never commit `.env`** - Contains API credentials
2. **Use environment variables** - Don't hardcode tokens
3. **Rotate tokens regularly** - Especially for production
4. **Review audit logs** - Monitor for unusual activity
5. **Respect rate limits** - Don't exceed platform limits
6. **Use app tokens** - Never use personal credentials

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│    (Client)     │
└────────┬────────┘
         │ JSON via stdin/stdout
         ▼
┌─────────────────┐
│  Social MCP     │
│  Server         │
├─────────────────┤
│  Twitter Client │
│  Facebook Client│
│  Instagram Client│
│  Draft Manager  │
│  Rate Limiter   │
│  Audit Logger   │
└────────┬────────┘
         │ API Calls
         ▼
┌─────────────────┐
│  Twitter API    │
│  Facebook Graph │
│  Instagram API  │
└─────────────────┘
```

## License

MIT License - See project LICENSE file.

## Support

For API setup issues, see `API_SETUP_GUIDE.md`.
For general troubleshooting, check `Logs/social_mcp.log`.
