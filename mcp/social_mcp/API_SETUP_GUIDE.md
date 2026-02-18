# Social Media API Setup Guide

Step-by-step instructions for obtaining API credentials for Twitter, Facebook, and Instagram.

---

## Table of Contents

1. [Twitter API Setup](#twitter-api-setup)
2. [Facebook API Setup](#facebook-api-setup)
3. [Instagram API Setup](#instagram-api-setup)
4. [Testing Your Credentials](#testing-your-credentials)
5. [Troubleshooting](#troubleshooting)

---

## Twitter API Setup

### Step 1: Create Twitter Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Click **Apply for a developer account**
3. Choose account type:
   - **Individual** - For personal projects
   - **Business** - For company accounts
4. Fill out the application:
   - **Use case description**: Explain how you'll use Twitter API
   - **Country/Region**: Your location
   - **Agree to terms**: Developer Agreement and Policy
5. Wait for approval (usually 1-3 business days)

### Step 2: Create a Project

1. Once approved, go to [Developer Dashboard](https://developer.twitter.com/en/portal/dashboard)
2. Click **Create a project**
3. Fill in project details:
   - **Project name**: e.g., "AI Employee Social Media"
   - **Use case**: Describe what your app will do
   - **Will you use tweets?**: Yes
4. Click **Create**

### Step 3: Create an App

1. In your project dashboard, click **Create an app**
2. Fill in app details:
   - **App name**: Unique name for your app
   - **Description**: What your app does
   - **Website URL**: Your company website (can be placeholder)
   - **Will your app use Twitter login?**: No (for server-to-server)
3. Click **Create**

### Step 4: Get API Credentials

1. In your app dashboard, go to **Keys and tokens**
2. **Generate Bearer Token** (OAuth 2.0):
   - Click **Generate** under "Bearer Token"
   - **Copy immediately** - won't be shown again
   - Add to `.env`: `TWITTER_BEARER_TOKEN=your_token_here`
3. **Get API Key & Secret** (OAuth 1.0a):
   - Click **Generate** under "API Key"
   - **Copy API Key** → `TWITTER_API_KEY`
   - **Copy API Secret** → `TWITTER_API_SECRET`
   - Store securely in `.env`

### Step 5: Configure .env

```bash
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAMLheAAAAAAA0%2BuSeid...
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_RATE_LIMIT=50
```

### Twitter Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /tweets | 50 | Per day |
| GET /mentions | 15 | Per 15 min |

---

## Facebook API Setup

### Step 1: Create Facebook Developer Account

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **Get Started** or **Log In**
3. Complete developer registration:
   - Accept Facebook Platform Policy
   - Verify email if required

### Step 2: Create a Business App

1. Go to [My Apps](https://developers.facebook.com/apps/)
2. Click **Create App**
3. Select use case: **Business**
4. Click **Next**
5. Fill in app details:
   - **App name**: e.g., "AI Employee Social Media"
   - **App contact email**: Your email
   - **Business account**: Select or create
6. Click **Create app**

### Step 3: Add Facebook Login Product

1. In app dashboard, scroll to **Add Products**
2. Find **Facebook Login**
3. Click **Set Up**
4. Choose **Web** as platform
5. Configure settings:
   - **Valid OAuth Redirect URIs**: `https://localhost`
   - Save changes

### Step 4: Get Page Access Token

#### Option A: Graph API Explorer (Easiest)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from dropdown
3. Click **Generate Access Token**
4. Grant permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `publish_to_groups` (if posting to groups)
5. Select your Page from the dropdown
6. Copy the **Access Token**
7. Add to `.env`: `FACEBOOK_ACCESS_TOKEN=your_token_here`

#### Option B: Manual Token Generation

1. Go to [Access Token Tool](https://developers.facebook.com/tools/accesstoken/)
2. Select your app
3. Add permissions listed above
4. Click **Generate Token**
5. Copy and save to `.env`

### Step 5: Get Page ID

#### Method 1: Graph API Explorer

1. In Graph API Explorer, run query:
   ```
   me/accounts
   ```
2. Find your page in results
3. Copy the **id** field
4. Add to `.env`: `FACEBOOK_PAGE_ID=123456789`

#### Method 2: From Page URL

1. Go to your Facebook Page
2. Click **About**
3. Find **Page ID** (usually at bottom)
4. Or use URL: `facebook.com/your-page-name-123456789`
   - Numbers at end are Page ID

### Step 6: Configure .env

```bash
FACEBOOK_ACCESS_TOKEN=EAAc...long_token_here
FACEBOOK_PAGE_ID=123456789012345
```

### Facebook Rate Limits

| Action | Limit | Notes |
|--------|-------|-------|
| Page Posts | 200 | Per day |
| Page Insights | 200 | Per hour |

---

## Instagram API Setup

### Prerequisites

Before starting Instagram setup, you must:

1. ✅ Have a Facebook Developer account
2. ✅ Have a Facebook Business Page
3. ✅ Have an Instagram **Business** or **Creator** account
4. ✅ Link Instagram account to Facebook Page

### Step 1: Convert to Business Account

If you haven't already:

1. Open Instagram app
2. Go to **Settings** → **Account**
3. Tap **Switch to Professional Account**
4. Choose **Business** or **Creator**
5. Connect to your Facebook Page

### Step 2: Link Instagram to Facebook Page

1. In Instagram app: **Settings** → **Account** → **Linked Accounts**
2. Select **Facebook**
3. Choose your Business Page
4. Confirm linking

### Step 3: Get Instagram Business Account ID

#### Method 1: Graph API Explorer

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Generate token with permissions:
   - `instagram_basic`
   - `pages_show_list`
   - `pages_read_engagement`
4. Run query:
   ```
   me/accounts
   ```
5. Copy your Page ID from results
6. Run query with Page ID:
   ```
   {page-id}?fields=instagram_business_account
   ```
7. Copy the **instagram_business_account.id**
8. Add to `.env`: `INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000`

#### Method 2: Instagram Graph API Direct

1. Run in Graph API Explorer:
   ```
   GET /v18.0/me/accounts?fields=instagram_business_account{id,username}
   ```
2. Copy the Instagram account ID

### Step 4: Get Instagram Access Token

1. In Graph API Explorer, generate token with:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
2. Copy the **Access Token**
3. Add to `.env`: `INSTAGRAM_ACCESS_TOKEN=your_token_here`

**Note:** Instagram uses the same access token as Facebook (they're both Meta platforms).

### Step 5: Configure .env

```bash
INSTAGRAM_ACCESS_TOKEN=EAAc...same_as_facebook_token...
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000
INSTAGRAM_RATE_LIMIT=25
```

### Instagram Rate Limits

| Action | Limit | Window |
|--------|-------|--------|
| Content Publishing | 25 | Per day |
| Content Reading | 200 | Per hour |

---

## Testing Your Credentials

### Test Twitter

```bash
cd mcp/social_mcp
python server.py

# In another terminal:
echo '{"method": "post_tweet", "params": {"text": "Test tweet from API"}}' | python server.py
```

**Expected Response:**
```json
{
  "success": true,
  "platform": "twitter",
  "post_id": "1234567890",
  "url": "https://twitter.com/user/status/1234567890"
}
```

### Test Facebook

```bash
echo '{"method": "post_to_page", "params": {"message": "Test post from API"}}' | python server.py
```

**Expected Response:**
```json
{
  "success": true,
  "platform": "facebook",
  "post_id": "123456789_987654321",
  "url": "https://facebook.com/123456789/posts/987654321"
}
```

### Test Instagram

```bash
echo '{"method": "create_post_draft", "params": {"platform": "instagram", "content": "Test post"}}' | python server.py
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Draft created successfully",
  "draft_path": "Pending_Approval/draft_instagram_20260219_103000.md",
  "requires_approval": true
}
```

---

## Troubleshooting

### Twitter Issues

**Problem:** "Invalid Bearer Token"

**Solution:**
1. Regenerate Bearer Token in Developer Portal
2. Check token doesn't have extra spaces
3. Ensure token starts with numbers/letters (not "Bearer ")

**Problem:** "Rate limit exceeded"

**Solution:**
1. Check `Logs/social_rate_limit.json`
2. Wait 24 hours for reset
3. Increase `TWITTER_RATE_LIMIT` in `.env` (within Twitter limits)

### Facebook Issues

**Problem:** "Page Access Token expired"

**Solution:**
1. Generate new token in Graph API Explorer
2. Use long-lived token (60 days) instead of short-lived (1 hour)
3. To extend token: Use OAuth debug endpoint

**Problem:** "Permissions not granted"

**Solution:**
1. Regenerate token with required permissions
2. Ensure app is in **Live** mode (not Development)
3. Submit for App Review if needed

### Instagram Issues

**Problem:** "Instagram Business Account not found"

**Solution:**
1. Verify account is Business/Creator (not Personal)
2. Ensure linked to Facebook Page
3. Re-link Instagram to Facebook Page

**Problem:** "Media upload failed"

**Solution:**
1. Check image format (JPG, PNG)
2. Verify image size (< 8MB)
3. Ensure image URL is publicly accessible

### General Issues

**Problem:** "NOT_CONFIGURED" error

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check environment variables loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.environ.get('TWITTER_BEARER_TOKEN', 'NOT SET'))"
```

**Problem:** Server crashes on startup

**Solution:**
```bash
# Check Python version
python --version  # Need 3.8+

# Install dependencies
pip install -r requirements.txt

# Check syntax
python -m py_compile server.py
```

---

## Security Best Practices

### Token Storage

✅ **DO:**
- Store tokens in `.env` file
- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate tokens every 90 days

❌ **DON'T:**
- Commit `.env` to Git
- Share tokens in chat/email
- Hardcode tokens in code
- Use personal accounts for business

### Token Rotation Schedule

| Platform | Rotate Every | How |
|----------|-------------|-----|
| Twitter | 90 days | Developer Portal → Regenerate |
| Facebook | 60 days | Graph API Explorer → New token |
| Instagram | 60 days | Same as Facebook |

### Monitoring

Check audit logs regularly:
```bash
# View today's audit log
cat Logs/social_audit_$(date +%Y-%m-%d).json

# Check for errors
grep -i error Logs/social_mcp.log
```

---

## Additional Resources

- **Twitter API Docs:** https://developer.twitter.com/en/docs
- **Facebook Graph API:** https://developers.facebook.com/docs/graph-api
- **Instagram Graph API:** https://developers.facebook.com/docs/instagram-api
- **Meta for Developers:** https://developers.facebook.com/

---

**Need Help?**

1. Check this guide first
2. Review platform documentation
3. Check `Logs/social_mcp.log` for errors
4. Verify credentials in `.env`
