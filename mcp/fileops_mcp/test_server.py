#!/usr/bin/env python3
"""
Test script for FileOps MCP Server

Tests all browser and file operation methods.
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


def test_file_operations():
    """Test file operation methods."""
    print("\n" + "="*60)
    print("File Operations Tests")
    print("="*60)
    
    # Test list_files
    print("\n1. list_files")
    response = test_server({
        "method": "file.list_files",
        "params": {
            "directory": ".",
            "pattern": "*.md"
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Count: {response['result'].get('count')}")
        print(f"   Files: {[f['name'] for f in response['result'].get('files', [])[:5]]}")
    else:
        print(f"   Error: {response.get('error')}")
    
    # Test read_file
    print("\n2. read_file")
    response = test_server({
        "method": "file.read_file",
        "params": {
            "path": "README.md"
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        content = response['result'].get('content', '')
        print(f"   Size: {response['result'].get('size_bytes')} bytes")
        print(f"   Preview: {content[:100]}...")
    else:
        print(f"   Error: {response.get('error')}")
    
    # Test write_file
    print("\n3. write_file")
    response = test_server({
        "method": "file.write_file",
        "params": {
            "path": "test_output.txt",
            "content": "Test content from MCP server"
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Path: {response['result'].get('path')}")
        print(f"   Size: {response['result'].get('size_bytes')} bytes")
    else:
        print(f"   Error: {response.get('error')}")
    
    # Test parse_json
    print("\n4. parse_json")
    # First create a JSON file
    test_server({
        "method": "file.write_file",
        "params": {
            "path": "test_data.json",
            "content": '{"name": "Test", "value": 123}'
        }
    })
    
    response = test_server({
        "method": "file.parse_json",
        "params": {
            "path": "test_data.json"
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Data: {response['result'].get('data')}")
    else:
        print(f"   Error: {response.get('error')}")
    
    # Test delete_file (with approval)
    print("\n5. delete_file (requires approval)")
    response = test_server({
        "method": "file.delete_file",
        "params": {
            "path": "test_output.txt",
            "require_approval": True
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Requires Approval: {response.get('requires_approval')}")
    print(f"   Message: {response.get('message')}")


def test_browser_operations():
    """Test browser operation methods."""
    print("\n" + "="*60)
    print("Browser Operations Tests")
    print("="*60)
    
    # Test navigate
    print("\n1. navigate")
    response = test_server({
        "method": "browser.navigate",
        "params": {
            "url": "https://example.com"
        }
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   URL: {response['result'].get('url')}")
        print(f"   Title: {response['result'].get('title')}")
    else:
        print(f"   Error: {response.get('error')}")
        print(f"   Error Code: {response.get('error_code')}")
    
    # Test screenshot
    print("\n2. screenshot")
    response = test_server({
        "method": "browser.screenshot",
        "params": {}
    })
    print(f"   Success: {response.get('success')}")
    if response.get('success'):
        print(f"   Path: {response['result'].get('path')}")
    else:
        print(f"   Error: {response.get('error')}")
    
    # Test linkedin_post (will fail without login)
    print("\n3. linkedin_post (requires login)")
    response = test_server({
        "method": "browser.linkedin_post",
        "params": {
            "message": "Test post from MCP server"
        }
    })
    print(f"   Success: {response.get('success')}")
    if not response.get('success'):
        print(f"   Error: {response.get('error')}")
        print(f"   Error Code: {response.get('error_code')}")
        if response.get('error_code') == 'NOT_LOGGED_IN':
            print(f"   → This is expected! See LINKEDIN_AUTOMATION_GUIDE.md for setup.")


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
    
    # Test missing namespace
    print("\n2. Missing namespace")
    response = test_server({
        "method": "unknown_method",
        "params": {}
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    
    # Test unknown namespace
    print("\n3. Unknown namespace")
    response = test_server({
        "method": "unknown.read_file",
        "params": {"path": "test.txt"}
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    
    # Test access denied (path outside whitelist)
    print("\n4. Access denied (path outside whitelist)")
    response = test_server({
        "method": "file.read_file",
        "params": {
            "path": "C:/Windows/System32/config/SAM"  # Should be denied
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    print(f"   Error Code: {response.get('error_code')}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FileOps MCP Server - Test Suite")
    print("="*60)
    
    test_file_operations()
    test_browser_operations()
    test_error_handling()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
    print("\nNote: Browser tests require Playwright installed.")
    print("Run: pip install playwright && playwright install chromium")
    print("\nLinkedIn posting requires manual first-time login.")
    print("See LINKEDIN_AUTOMATION_GUIDE.md for setup instructions.")
    print("\nCheck Logs/ for audit logs and error logs.")


if __name__ == '__main__':
    main()
