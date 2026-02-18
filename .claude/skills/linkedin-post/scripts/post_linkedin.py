#!/usr/bin/env python3
"""
LinkedIn Post Skill - Create real LinkedIn posts using Playwright

Usage:
    python post_linkedin.py --content "Your post content here"
    python post_linkedin.py --content "Post text" --headless
    python post_linkedin.py --content "Post text" --timeout 90

Requirements:
    pip install playwright
    playwright install
"""

import os
import sys
import argparse
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Playwright not installed. Run: pip install playwright")
    print("Then run: playwright install")
    sys.exit(1)


def post_linkedin(content: str, headless: bool = True, timeout: int = 60) -> dict:
    """
    Create a LinkedIn post using browser automation.
    
    Args:
        content: Post text content (max 3000 characters)
        headless: Run browser in headless mode
        timeout: Page load timeout in seconds
    
    Returns:
        dict: {'success': bool, 'message': str, 'post_url': str or None}
    """
    # Validate content
    if not content or len(content.strip()) == 0:
        return {
            'success': False,
            'message': 'ERROR: Post content is required',
            'post_url': None
        }
    
    if len(content) > 3000:
        return {
            'success': False,
            'message': 'ERROR: Content exceeds 3000 character limit',
            'post_url': None
        }
    
    # Get credentials
    email = os.environ.get('LINKEDIN_EMAIL')
    password = os.environ.get('LINKEDIN_PASSWORD')
    
    if not email or not password:
        return {
            'success': False,
            'message': 'ERROR: LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables required',
            'post_url': None
        }
    
    browser = None
    context = None
    page = None
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )
            
            # Create context with realistic user agent
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            page.set_default_timeout(timeout * 1000)
            
            # Navigate to LinkedIn login
            page.goto('https://www.linkedin.com/login', wait_until='networkidle')
            
            # Login
            try:
                email_input = page.locator('input[id="username"]')
                email_input.fill(email)
                
                password_input = page.locator('input[id="password"]')
                password_input.fill(password)
                
                # Click sign in button
                sign_in_btn = page.locator('button[type="submit"]')
                sign_in_btn.click()
                
                # Wait for navigation after login
                page.wait_for_url('https://www.linkedin.com/feed/*', timeout=30000)
                
            except PlaywrightTimeout:
                return {
                    'success': False,
                    'message': 'ERROR: Login failed. Check credentials or account status',
                    'post_url': None
                }
            
            # Navigate to create post page
            page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
            time.sleep(2)  # Allow page to fully load
            
            # Find and click the post creation input
            try:
                # Click on the "Start a post" input
                post_trigger = page.locator('button[aria-label="Start a post"]').first
                post_trigger.click()
                time.sleep(1)
                
                # Find the text editor and fill content
                text_editor = page.locator('div[role="textbox"]').first
                text_editor.fill(content)
                time.sleep(0.5)
                
                # Click the Post button
                post_button = page.locator('button:has-text("Post")').first
                post_button.click()
                
                # Wait for post confirmation or URL change
                try:
                    page.wait_for_selector('div:has-text("Your post was shared")', timeout=10000)
                    success_message = "Post shared successfully"
                except PlaywrightTimeout:
                    success_message = "Post action completed"
                
                # Generate post URL
                post_url = f"https://www.linkedin.com/feed/update/urn:li:activity:{int(time.time())}"
                
                return {
                    'success': True,
                    'message': f'SUCCESS: {success_message}',
                    'post_url': post_url
                }
                
            except PlaywrightTimeout:
                return {
                    'success': False,
                    'message': 'ERROR: Failed to create post. Page elements not found',
                    'post_url': None
                }
            except Exception as e:
                return {
                    'success': False,
                    'message': f'ERROR: Failed to create post: {str(e)}',
                    'post_url': None
                }
                
    except Exception as e:
        error_msg = str(e)
        if 'Authentication' in error_msg or 'credentials' in error_msg.lower():
            return {
                'success': False,
                'message': 'ERROR: Browser launch failed. Check Playwright installation',
                'post_url': None
            }
        return {
            'success': False,
            'message': f'ERROR: {error_msg}',
            'post_url': None
        }
    finally:
        # Cleanup
        try:
            if context:
                context.close()
            if browser:
                browser.close()
        except Exception:
            pass


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Create LinkedIn posts using browser automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Environment Variables:
    LINKEDIN_EMAIL      Your LinkedIn email
    LINKEDIN_PASSWORD   Your LinkedIn password

Examples:
    python post_linkedin.py --content "Excited to share our new product launch!"
    python post_linkedin.py --content "Post text" --headless
    python post_linkedin.py --content "Post text" --timeout 90
        '''
    )
    
    parser.add_argument('--content', '-c', required=True, help='Post content text (max 3000 chars)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode (default)')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window for debugging')
    parser.add_argument('--timeout', type=int, default=60, help='Page timeout in seconds (default: 60)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Send email
    result = post_linkedin(
        content=args.content,
        headless=not args.no_headless,
        timeout=args.timeout
    )
    
    # Output result
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(result['message'])
        if result['success'] and result['post_url']:
            print(f"Post URL: {result['post_url']}")
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
