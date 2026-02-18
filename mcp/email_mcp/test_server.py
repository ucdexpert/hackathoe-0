#!/usr/bin/env python3
"""
Test script for Email MCP Server

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


def test_validate_email():
    """Test validate_email method."""
    print("\n" + "="*60)
    print("Test: validate_email")
    print("="*60)
    
    # Test valid email
    print("\n1. Valid email (test@example.com)")
    response = test_server({
        "method": "validate_email",
        "params": {"email": "test@example.com"}
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Valid: {response.get('valid')}")
    print(f"   Message: {response.get('message')}")
    
    # Test invalid email
    print("\n2. Invalid email (invalid-email)")
    response = test_server({
        "method": "validate_email",
        "params": {"email": "invalid-email"}
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Valid: {response.get('valid')}")
    print(f"   Message: {response.get('message')}")
    
    # Test Gmail normalization
    print("\n3. Gmail normalization (test.user+spam@gmail.com)")
    response = test_server({
        "method": "validate_email",
        "params": {"email": "test.user+spam@gmail.com"}
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Valid: {response.get('valid')}")
    print(f"   Normalized: {response.get('normalized')}")


def test_send_email():
    """Test send_email method."""
    print("\n" + "="*60)
    print("Test: send_email")
    print("="*60)
    
    # Test missing recipient
    print("\n1. Missing recipient")
    response = test_server({
        "method": "send_email",
        "params": {
            "subject": "Test",
            "body": "Test body"
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    print(f"   Error Code: {response.get('error_code')}")
    
    # Test missing subject
    print("\n2. Missing subject")
    response = test_server({
        "method": "send_email",
        "params": {
            "to": "test@example.com",
            "body": "Test body"
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    
    # Test missing body
    print("\n3. Missing body")
    response = test_server({
        "method": "send_email",
        "params": {
            "to": "test@example.com",
            "subject": "Test"
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    
    # Test invalid email
    print("\n4. Invalid recipient email")
    response = test_server({
        "method": "send_email",
        "params": {
            "to": "invalid-email",
            "subject": "Test",
            "body": "Test body"
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    
    # Test with configuration (will fail if not configured)
    print("\n5. Valid request (requires configuration)")
    response = test_server({
        "method": "send_email",
        "params": {
            "to": "test@example.com",
            "subject": "Test Email",
            "body": "This is a test email body",
            "html": False
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Message: {response.get('message', response.get('error'))}")
    if response.get('attempts'):
        print(f"   Attempts: {response.get('attempts')}")


def test_draft_email():
    """Test draft_email method."""
    print("\n" + "="*60)
    print("Test: draft_email")
    print("="*60)
    
    # Test valid draft
    print("\n1. Create draft")
    response = test_server({
        "method": "draft_email",
        "params": {
            "to": "client@example.com",
            "subject": "Proposal",
            "body": "Please review the attached proposal...",
            "html": False
        }
    })
    print(f"   Success: {response.get('success')}")
    print(f"   Message: {response.get('message')}")
    if response.get('draft_path'):
        print(f"   Draft Path: {response.get('draft_path')}")
    if response.get('requires_approval'):
        print(f"   Requires Approval: Yes")


def test_invalid_json():
    """Test invalid JSON handling."""
    print("\n" + "="*60)
    print("Test: Invalid JSON handling")
    print("="*60)
    
    server_path = Path(__file__).parent / "server.py"
    
    # Send invalid JSON
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
        print(f"   Stdout: {result.stdout}")


def test_unknown_method():
    """Test unknown method handling."""
    print("\n" + "="*60)
    print("Test: Unknown method handling")
    print("="*60)
    
    response = test_server({
        "method": "unknown_method",
        "params": {}
    })
    
    print(f"   Success: {response.get('success')}")
    print(f"   Error: {response.get('error')}")
    print(f"   Error Code: {response.get('error_code')}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Email MCP Server - Test Suite")
    print("="*60)
    
    test_validate_email()
    test_send_email()
    test_draft_email()
    test_invalid_json()
    test_unknown_method()
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)
    print("\nNote: send_email tests will fail unless configured with")
    print("valid Gmail credentials in .env file.")
    print("\nCheck Logs/ for audit logs and error logs.")


if __name__ == '__main__':
    main()
