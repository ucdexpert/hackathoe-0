#!/usr/bin/env python3
"""
Odoo MCP Server - Test Suite

Basic tests for the Odoo MCP server components.
Run with: python test_server.py
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config, get_config
from odoo_client import OdooClient, OdooClientError


def test_config():
    """Test configuration loading."""
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    config = get_config()
    status = Config.validate()

    print(f"\nConfiguration Status:")
    print(f"  Odoo URL: {status['odoo_url']}")
    print(f"  Database: {status['odoo_db']}")
    print(f"  Username: {status['odoo_username']}")
    print(f"  Logs Dir: {status['logs_dir']}")
    print(f"  Fully Operational: {status['fully_operational']}")

    # Test directories exist
    assert config.LOGS_DIR.exists(), f"Logs directory should exist: {config.LOGS_DIR}"
    assert config.PENDING_APPROVAL_DIR.exists(), f"Pending approval directory should exist: {config.PENDING_APPROVAL_DIR}"

    print("\n✓ Configuration test passed")
    return status['fully_operational']


def test_odoo_client_init():
    """Test Odoo client initialization."""
    print("\n" + "=" * 60)
    print("Testing Odoo Client Initialization")
    print("=" * 60)

    config = get_config()

    if not config.is_configured():
        print("\n⚠ Odoo not configured - skipping client tests")
        return False

    try:
        client = OdooClient(config)
        print(f"\n✓ Client initialized successfully")
        print(f"  JSON-RPC URL: {client.jsonrpc_url}")
        return True
    except Exception as e:
        print(f"\n✗ Client initialization failed: {e}")
        return False


def test_odoo_authentication():
    """Test Odoo authentication."""
    print("\n" + "=" * 60)
    print("Testing Odoo Authentication")
    print("=" * 60)

    config = get_config()

    if not config.is_configured():
        print("\n⚠ Odoo not configured - skipping authentication test")
        return False

    client = OdooClient(config)

    try:
        uid = client.authenticate()
        print(f"\n✓ Authentication successful")
        print(f"  User ID: {uid}")
        client.close()
        return True
    except OdooClientError as e:
        print(f"\n✗ Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_list_invoices():
    """Test listing invoices."""
    print("\n" + "=" * 60)
    print("Testing List Invoices")
    print("=" * 60)

    config = get_config()

    if not config.is_configured():
        print("\n⚠ Odoo not configured - skipping invoice test")
        return False

    client = OdooClient(config)

    try:
        client.authenticate()
        invoices = client.list_invoices(limit=5)
        print(f"\n✓ Retrieved {len(invoices)} invoices")

        if invoices:
            print(f"  First invoice: {invoices[0].get('name', 'N/A')}")

        client.close()
        return True
    except OdooClientError as e:
        print(f"\n✗ List invoices failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_get_account_summary():
    """Test getting account summary."""
    print("\n" + "=" * 60)
    print("Testing Account Summary")
    print("=" * 60)

    config = get_config()

    if not config.is_configured():
        print("\n⚠ Odoo not configured - skipping summary test")
        return False

    client = OdooClient(config)

    try:
        client.authenticate()
        summary = client.get_account_summary()
        print(f"\n✓ Retrieved account summary")
        print(f"  Total Receivable: ${summary.get('total_receivable', 0):,.2f}")
        print(f"  Invoices Count: {summary.get('invoices_count', 0)}")
        print(f"  Bills Count: {summary.get('bills_count', 0)}")

        client.close()
        return True
    except OdooClientError as e:
        print(f"\n✗ Account summary failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_search_partner():
    """Test searching partners."""
    print("\n" + "=" * 60)
    print("Testing Partner Search")
    print("=" * 60)

    config = get_config()

    if not config.is_configured():
        print("\n⚠ Odoo not configured - skipping partner search test")
        return False

    client = OdooClient(config)

    try:
        client.authenticate()
        partners = client.search_partner("", limit=5)
        print(f"\n✓ Found {len(partners)} partners")

        for partner in partners[:3]:
            print(f"  - {partner.get('name', 'N/A')}")

        client.close()
        return True
    except OdooClientError as e:
        print(f"\n✗ Partner search failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_approval_manager():
    """Test approval manager."""
    print("\n" + "=" * 60)
    print("Testing Approval Manager")
    print("=" * 60)

    from server import ApprovalManager

    config = get_config()
    approval_manager = ApprovalManager(config.PENDING_APPROVAL_DIR)

    # Create a test approval request
    test_details = {
        'action': 'test_action',
        'test_value': 123
    }

    result = approval_manager.create_approval_request('test_action', test_details)

    print(f"\n✓ Created approval request")
    print(f"  Request ID: {result['request_id']}")
    print(f"  File Path: {result['filepath']}")

    # Check status
    status = approval_manager.check_approval_status(result['request_id'])
    print(f"  Initial Status: {status}")

    assert status == 'PENDING', "Initial status should be PENDING"

    # Cleanup test file
    try:
        os.remove(result['filepath'])
        print(f"  Cleaned up test file")
    except Exception:
        pass

    print("\n✓ Approval manager test passed")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Odoo MCP Server - Test Suite")
    print("=" * 60)

    results = {
        'config': False,
        'client_init': False,
        'authentication': False,
        'list_invoices': False,
        'account_summary': False,
        'partner_search': False,
        'approval_manager': True  # Always passes (doesn't need Odoo)
    }

    # Run tests
    results['config'] = test_config()
    results['client_init'] = test_odoo_client_init()

    if results['client_init']:
        results['authentication'] = test_odoo_authentication()

        if results['authentication']:
            results['list_invoices'] = test_list_invoices()
            results['account_summary'] = test_get_account_summary()
            results['partner_search'] = test_search_partner()

    results['approval_manager'] = test_approval_manager()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60 + "\n")

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
