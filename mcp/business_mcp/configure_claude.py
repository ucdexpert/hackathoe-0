#!/usr/bin/env python3
"""
Claude Desktop Configuration Script

Automatically configures Claude Desktop to use the Business MCP Server.

Usage:
    python configure_claude.py
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime


def find_claude_config():
    """Find Claude Desktop configuration file."""
    possible_paths = []
    
    # Windows
    if sys.platform == 'win32':
        appdata = os.environ.get('APPDATA', '')
        possible_paths.append(Path(appdata) / 'Claude' / 'claude_desktop_config.json')
    
    # macOS
    elif sys.platform == 'darwin':
        home = Path.home()
        possible_paths.append(home / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json')
    
    # Linux
    elif sys.platform == 'linux':
        home = Path.home()
        possible_paths.append(home / '.config' / 'Claude' / 'claude_desktop_config.json')
        possible_paths.append(home / '.claude' / 'claude_desktop_config.json')
    
    # Check which path exists
    for path in possible_paths:
        if path.parent.exists():
            return path
    
    # Return default (Windows) if none exist
    return possible_paths[0] if possible_paths else None


def load_env_file():
    """Load environment variables from .env file."""
    env_vars = {}
    
    # Try root .env file
    root_env = Path(__file__).parent.parent.parent / '.env'
    if root_env.exists():
        with open(root_env, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Try local .env file
    local_env = Path(__file__).parent / '.env'
    if local_env.exists():
        with open(local_env, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars


def create_backup(config_path):
    """Create backup of existing config."""
    if not config_path.exists():
        return None
    
    backup_path = config_path.with_suffix('.json.backup')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = config_path.parent / f'claude_desktop_config_{timestamp}.backup'
    
    shutil.copy2(config_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    return backup_path


def configure_claude():
    """Configure Claude Desktop for Business MCP Server."""
    print("\n" + "="*60)
    print("Claude Desktop Configuration - Business MCP Server")
    print("="*60 + "\n")
    
    # Find Claude config
    config_path = find_claude_config()
    print(f"📁 Configuration path: {config_path}")
    
    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load environment variables
    env_vars = load_env_file()
    
    if not env_vars:
        print("\n⚠️  No .env file found. You'll need to configure credentials manually.")
    else:
        print(f"✓ Loaded environment variables from .env")
    
    # Get server path
    server_path = Path(__file__).parent / 'server.py'
    
    # Create configuration
    mcp_config = {
        "business-mcp": {
            "command": "python",
            "args": [str(server_path)],
            "env": {}
        }
    }
    
    # Add environment variables if available
    required_vars = ['EMAIL_ADDRESS', 'EMAIL_PASSWORD']
    optional_vars = ['SMTP_SERVER', 'SMTP_PORT', 'LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'LOGS_DIR']
    
    for var in required_vars + optional_vars:
        if var in env_vars:
            mcp_config["business-mcp"]["env"][var] = env_vars[var]
    
    # Check if required vars are missing
    missing_vars = [var for var in required_vars if var not in env_vars]
    if missing_vars:
        print(f"\n⚠️  Missing required variables: {', '.join(missing_vars)}")
        print("   You'll need to add these to the configuration manually.")
    
    # Set default LOGS_DIR if not set
    if 'LOGS_DIR' not in env_vars:
        logs_dir = Path(__file__).parent.parent.parent / 'Logs'
        mcp_config["business-mcp"]["env"]['LOGS_DIR'] = str(logs_dir)
    
    # Load existing config or create new
    existing_config = {}
    if config_path.exists():
        print(f"✓ Found existing configuration")
        create_backup(config_path)
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
        except json.JSONDecodeError:
            print("⚠️  Existing config is invalid, will create new one")
            existing_config = {}
    
    # Merge configurations
    if 'mcpServers' not in existing_config:
        existing_config['mcpServers'] = {}
    
    if 'business-mcp' in existing_config['mcpServers']:
        print(f"⚠️  business-mcp already configured, will be overwritten")
    
    existing_config['mcpServers']['business-mcp'] = mcp_config["business-mcp"]
    
    # Write configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        print(f"\n✅ Configuration saved to: {config_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("Configuration Summary")
        print("="*60)
        print(f"Server: {server_path}")
        print(f"Email configured: {'✓ Yes' if 'EMAIL_ADDRESS' in env_vars else '✗ No'}")
        print(f"LinkedIn configured: {'✓ Yes' if 'LINKEDIN_EMAIL' in env_vars else '✗ No'}")
        print(f"Logs directory: {mcp_config['business-mcp']['env'].get('LOGS_DIR', 'default')}")
        
        print("\n" + "="*60)
        print("Next Steps")
        print("="*60)
        print("1. Restart Claude Desktop")
        print("2. Claude will now have access to:")
        print("   • send_email - Send emails via Gmail")
        print("   • post_linkedin - Create LinkedIn posts")
        print("   • log_activity - Log business activities")
        print("\n3. Test with: python server.py --status")
        
        print("\n" + "="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to save configuration: {str(e)}")
        print("\nManual configuration required:")
        print(f"Edit: {config_path}")
        print("\nAdd this to mcpServers:")
        print(json.dumps(mcp_config, indent=2))
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Configure Claude Desktop for Business MCP Server'
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show configuration without applying'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be configured without making changes'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    env_vars = load_env_file()
    server_path = Path(__file__).parent / 'server.py'
    
    if args.show_config or args.dry_run:
        config = {
            "mcpServers": {
                "business-mcp": {
                    "command": "python",
                    "args": [str(server_path)],
                    "env": env_vars or {}
                }
            }
        }
        print(json.dumps(config, indent=2))
        return 0
    
    # Run configuration
    success = configure_claude()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
