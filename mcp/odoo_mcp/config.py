#!/usr/bin/env python3
"""
Odoo MCP Server Configuration

Configuration management for Odoo JSON-RPC integration.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Odoo server configuration from environment variables."""

    # Odoo connection settings
    ODOO_URL: str = ''
    ODOO_DB: str = ''
    ODOO_USERNAME: str = ''
    ODOO_PASSWORD: str = ''
    ODOO_PORT: int = 80

    # Server settings
    SERVER_NAME: str = 'odoo-mcp'
    SERVER_VERSION: str = '1.0.0'

    # Logging settings
    LOGS_DIR: str = 'Logs'
    ODOO_LOG: str = 'odoo.log'

    # Vault path
    VAULT_PATH: Path = Path(__file__).resolve().parent.parent.parent

    # Approval settings
    PENDING_APPROVAL_DIR: str = 'Pending_Approval'

    def __init__(self):
        """Load configuration from environment variables."""
        self._load_env()

    def _load_env(self):
        """Load .env file if it exists."""
        env_files = [
            Path(__file__).parent / ".env",
            Path(__file__).parent.parent.parent / ".env",
        ]

        for env_file in env_files:
            if env_file.exists():
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                os.environ[key.strip()] = value.strip()
                except Exception:
                    pass

        # Load from environment
        self.ODOO_URL = os.environ.get('ODOO_URL', '').rstrip('/')
        self.ODOO_DB = os.environ.get('ODOO_DB', '')
        self.ODOO_USERNAME = os.environ.get('ODOO_USERNAME', '')
        self.ODOO_PASSWORD = os.environ.get('ODOO_PASSWORD', '')
        self.ODOO_PORT = int(os.environ.get('ODOO_PORT', '80'))

        # Paths
        vault_path = os.environ.get('VAULT_PATH')
        if vault_path:
            self.VAULT_PATH = Path(vault_path)

        self.LOGS_DIR = self.VAULT_PATH / "Logs"
        self.PENDING_APPROVAL_DIR = self.VAULT_PATH / "Pending_Approval"

        # Ensure directories exist
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.PENDING_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        """Check if Odoo is fully configured."""
        return bool(
            self.ODOO_URL and
            self.ODOO_DB and
            self.ODOO_USERNAME and
            self.ODOO_PASSWORD
        )

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information (without password)."""
        return {
            'url': self.ODOO_URL,
            'port': self.ODOO_PORT,
            'database': self.ODOO_DB,
            'username': self.ODOO_USERNAME,
            'configured': self.is_configured()
        }

    def get_jsonrpc_url(self) -> str:
        """Get the JSON-RPC endpoint URL."""
        return f"{self.ODOO_URL}/jsonrpc"

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return status."""
        config = cls()
        status = {
            'odoo_configured': config.is_configured(),
            'odoo_url': config.ODOO_URL if config.ODOO_URL else 'Not set',
            'odoo_db': config.ODOO_DB if config.ODOO_DB else 'Not set',
            'odoo_username': config.ODOO_USERNAME if config.ODOO_USERNAME else 'Not set',
            'logs_dir': str(config.LOGS_DIR),
            'pending_approval_dir': str(config.PENDING_APPROVAL_DIR),
        }
        status['fully_operational'] = status['odoo_configured']
        return status


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the configuration singleton."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
