#!/usr/bin/env python3
"""
LinkedIn API Post - Official way to post on LinkedIn

Usage:
    python linkedin_api_post.py --content "Your post" --access-token "YOUR_TOKEN"

Get Access Token:
    https://developer.microsoft.com/en-us/linkedin
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime


def post_linkedin_api(content: str, access_token: str, person_urn: str = None) -> dict:
    """Post to LinkedIn using official API."""
    if not content or len(content.strip()) == 0:
        return {'success': False, 'message': 'ERROR: Post content is required', 'post_url': None}
    
    if not access_token:
        return {'success': False, 'message': 'ERROR: Access token required', 'post_url': None}
    
    url = 'https://api.linkedin.com/v2/ugcPosts'
    
    if not person_urn:
        person_urn = get_person_urn(access_token)
        if not person_urn:
            return {'success': False, 'message': 'ERROR: Could not get person URN', 'post_url': None}
    
    body = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    try:
        data = json.dumps(body).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            post_id = result.get('id', 'unknown')
            post_url = f"https://www.linkedin.com/feed/update/{post_id}"
            
            return {'success': True, 'message': 'SUCCESS: LinkedIn post published', 'post_url': post_url}
    
    except urllib.error.HTTPError as e:
        return {'success': False, 'message': f'ERROR: LinkedIn API error ({e.code})', 'post_url': None}
    except Exception as e:
        return {'success': False, 'message': f'ERROR: {str(e)}', 'post_url': None}


def get_person_urn(access_token: str) -> str:
    """Get LinkedIn person URN from access token."""
    try:
        req = urllib.request.Request(
            'https://api.linkedin.com/v2/me',
            headers={'Authorization': f'Bearer {access_token}', 'X-Restli-Protocol-Version': '2.0.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return f"urn:li:person:{result.get('id', '')}"
    except:
        return None


def main():
    """CLI entry point."""
    print("\n" + "=" * 60)
    print("LinkedIn API Post - Official Method")
    print("=" * 60)
    
    access_token = os.environ.get('LINKEDIN_ACCESS_TOKEN')
    content = os.environ.get('LINKEDIN_POST_CONTENT')
    
    if not access_token:
        print("\nLINKEDIN_ACCESS_TOKEN not found in .env file")
        print("\nTo get access token:")
        print("  1. Go to: https://developer.microsoft.com/en-us/linkedin")
        print("  2. Create an app")
        print("  3. Enable OAuth 2.0 with scopes: r_liteprofile, w_member_social")
        print("  4. Generate access token")
        print("  5. Add to .env file: LINKEDIN_ACCESS_TOKEN=your_token")
        print("\n" + "=" * 60 + "\n")
        sys.exit(1)
    
    if not content:
        content = "Hello LinkedIn! Posted via AI Employee API."
    
    person_urn = os.environ.get('LINKEDIN_PERSON_URN')
    result = post_linkedin_api(content, access_token, person_urn)
    
    print(f"\nStatus: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Message: {result['message']}")
    if result.get('post_url'):
        print(f"Post URL: {result['post_url']}")
    print("=" * 60 + "\n")
    
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
