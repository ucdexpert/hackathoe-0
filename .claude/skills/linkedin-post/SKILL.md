# linkedin-post

## Description
Create real LinkedIn posts using Playwright browser automation. Logs in and publishes text posts programmatically.

## Environment Variables
```
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your-password
```

## Usage
```bash
python .claude/skills/linkedin-post/scripts/post_linkedin.py --content "Your post content here"
python .claude/skills/linkedin-post/scripts/post_linkedin.py --content "Post text" --headless
```

## Inputs
- `--content`: Post text content (required, max 3000 chars)
- `--headless`: Run browser in headless mode (optional)
- `--timeout`: Page load timeout in seconds (default: 60)

## Output
```
SUCCESS: LinkedIn post published
Post URL: https://www.linkedin.com/feed/update/urn:li:activity:123456
```

## Requirements
- Python 3.10+
- Playwright: `pip install playwright`
- Install browsers: `playwright install`

## Error Handling
- Login failure → ERROR: Authentication failed
- Post too long → ERROR: Content exceeds 3000 characters
- Network error → ERROR: Connection failed
- Already posted → SUCCESS: Post published

## Security
- Never commit credentials
- Use environment variables or secret manager
- Consider using LinkedIn API for production
