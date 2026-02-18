#!/usr/bin/env python3
"""
Test script for Social Media MCP Server

Tests all MCP methods with various inputs.
"""

import subprocess
import json
import sys
from pathlib import Path


def test_server(request: dict) -> dict:
    """Send a request to the MCP server and get response."""
    server_path = Path(__file__).parent / "server.py"
    
    result = subprocess.run(
        [sys.executable, str(server_path)],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    try:
        response = json.loads(result.stdout)
        return response
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Invalid JSON response: {str(e)}',
            'stdout': result.stdout,
            'stderr': result.stderr
        }


def test_twitter():
    """Test Twitter methods."""
    print("\n" + "="*60)
    print("Twitter Tests")
    print("="*60)
    
    # Test post_tweet
    print("\n1. post_tweet (valid)")
    response = test_server({
        "method": "post_tweet",
        "params": {
            "text": "Test tweet from API! #automation",
            "image_url": None
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Platform: {response.get('platform')}")
    if response.get('success'):
        print(f"   Post ID: {response.get('post_id')}")
        print(f"   URL: {response.get('url')}")
    else:
        print(f"   Error: {response.get('error')}")
        print(f"   Error Code: {response.get('error_code')}")
    
    # Test post_tweet with long text
    print("\n2. post_tweet (text too long)")
    response = test_server({
        "method": "post_tweet",
        "params": {
            "text": "x" * 300,  # Exceeds 280 limit
            "image_url": None
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    
    # Test get_mentions
    print("\n3. get_mentions")
    response = test_server({
        "method": "get_mentions",
        "params": {
            "count": 5
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Count: {response.get('count')}")
        if response.get('mentions'):
            print(f"   First mention: {response['mentions'][0].get('text')}")


def test_facebook():
    """Test Facebook methods."""
    print("\n" + "="*60)
    print("Facebook Tests")
    print("="*60)
    
    # Test post_to_page
    print("\n1. post_to_page")
    response = test_server({
        "method": "post_to_page",
        "params": {
            "message": "Test post from MCP server!",
            "page_id": None,
            "image_url": None
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Platform: {response.get('platform')}")
    if response.get('success'):
        print(f"   Post ID: {response.get('post_id')}")
    else:
        print(f"   Error: {response.get('error')}")
    
    # Test get_page_insights
    print("\n2. get_page_insights")
    response = test_server({
        "method": "get_page_insights",
        "params": {
            "page_id": None
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        insights = response.get('insights', {})
        print(f"   Page Likes: {insights.get('page_likes', 'N/A')}")
        print(f"   Followers: {insights.get('page_followers', 'N/A')}")


def test_instagram():
    """Test Instagram methods."""
    print("\n" + "="*60)
    print("Instagram Tests")
    print("="*60)
    
    # Test post_image (will fail without valid image)
    print("\n1. post_image (invalid path)")
    response = test_server({
        "method": "post_image",
        "params": {
            "image_path": "nonexistent.jpg",
            "caption": "Test caption",
            "hashtags": ["#test"]
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    
    # Test get_recent_media
    print("\n2. get_recent_media")
    response = test_server({
        "method": "get_recent_media",
        "params": {
            "count": 5
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Count: {response.get('count')}")
        if response.get('media'):
            print(f"   First media: {response['media'][0].get('caption')}")


def test_drafts():
    """Test draft creation."""
    print("\n" + "="*60)
    print("Draft Creation Tests")
    print("="*60)
    
    # Test create_post_draft - Twitter
    print("\n1. create_post_draft (Twitter)")
    response = test_server({
        "method": "create_post_draft",
        "params": {
            "platform": "twitter",
            "content": "Draft tweet content"
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Draft Path: {response.get('draft_path')}")
        print(f"   Requires Approval: {response.get('requires_approval')}")
    
    # Test create_post_draft - Instagram
    print("\n2. create_post_draft (Instagram)")
    response = test_server({
        "method": "create_post_draft",
        "params": {
            "platform": "instagram",
            "content": "Draft Instagram post",
            "hashtags": ["#business", "#automation"]
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Draft Path: {response.get('draft_path')}")
    
    # Test create_post_draft - Invalid platform
    print("\n3. create_post_draft (Invalid platform)")
    response = test_server({
        "method": "create_post_draft",
        "params": {
            "platform": "tiktok",  # Not supported
            "content": "Draft"
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")


def test_error_handling():
    """Test error handling."""
    print("\n" + "="*60)
    print("Error Handling Tests")
    print("="*60)
    
    # Test invalid JSON
    print("\n1. Invalid JSON")
    server_path = Path(__file__).parent / "server.py"
    result = subprocess.run(
        [sys.executable, str(server_path)],
        input="not valid json",
        capture_output=True,
        text=True
    )
    try:
        response = json.loads(result.stdout)
        print(f"   Success: {response.get('success')}")
        print(f"   Error: {response.get('error')}")
        print(f"   Error Code: {response.get('error_code')}")
    except json.JSONDecodeError:
        print("   ERROR: Server didn't return valid JSON!")
    
    # Test unknown method
    print("\n2. Unknown method")
    response = test_server({
        "method": "unknown_method",
        "params": {}
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    print(f"   Error Code: {response.get('error_code')}")
    
    # Test missing method
    print("\n3. Missing method")
    response = test_server({
        "method": "",
        "params": {}
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Social Media MCP Server - Test Suite")
    print("="*60)
    
    test_twitter()
    test_facebook()
    test_instagram()
    test_drafts()
    test_error_handling()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
    print("\nNote: Most tests simulate successful responses.")
    print("For real API calls, configure credentials in .env file.")
    print("\nCheck Logs/ for audit logs and error logs.")


if __name__ == '__main__':
    main()
