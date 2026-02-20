#!/usr/bin/env python3
"""
Social Media Configuration

Configuration management for Facebook and Instagram Graph API integration.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class SocialMediaConfig:
    """Social media configuration from environment variables."""

    # Facebook settings
    FACEBOOK_APP_ID: str = ''
    FACEBOOK_APP_SECRET: str = ''
    FACEBOOK_PAGE_ACCESS_TOKEN: str = ''
    FACEBOOK_PAGE_ID: str = ''

    # Instagram settings
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ''
    INSTAGRAM_ACCESS_TOKEN: str = ''

    # Vault path
    VAULT_PATH: Path = Path(__file__).parent.parent.parent

    # Logging settings
    LOGS_DIR: str = 'Logs'
    SOCIAL_LOG: str = 'social.log'

    def __init__(self):
        """Load configuration from environment variables."""
        self._load_env()

    def _load_env(self):
        """Load .env file if it exists."""
        env_files = [
            Path(__file__).parent.parent.parent / ".env",
            Path(__file__).parent / ".env",
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
        self.FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
        self.FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')
        self.FACEBOOK_PAGE_ACCESS_TOKEN = os.environ.get('FACEBOOK_PAGE_ACCESS_TOKEN', '')
        self.FACEBOOK_PAGE_ID = os.environ.get('FACEBOOK_PAGE_ID', '')
        self.INSTAGRAM_BUSINESS_ACCOUNT_ID = os.environ.get('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')
        self.INSTAGRAM_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN', '')

        # Paths
        vault_path = os.environ.get('VAULT_PATH')
        if vault_path:
            self.VAULT_PATH = Path(vault_path)

        self.LOGS_DIR = self.VAULT_PATH / "Logs"
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def is_facebook_configured(self) -> bool:
        """Check if Facebook is fully configured."""
        return bool(
            self.FACEBOOK_PAGE_ACCESS_TOKEN and
            self.FACEBOOK_PAGE_ID
        )

    def is_instagram_configured(self) -> bool:
        """Check if Instagram is fully configured."""
        return bool(
            self.INSTAGRAM_ACCESS_TOKEN and
            self.INSTAGRAM_BUSINESS_ACCOUNT_ID
        )

    def get_facebook_config(self) -> Dict[str, Any]:
        """Get Facebook configuration (without secrets)."""
        return {
            'app_id': self.FACEBOOK_APP_ID if self.FACEBOOK_APP_ID else 'Not set',
            'page_id': self.FACEBOOK_PAGE_ID if self.FACEBOOK_PAGE_ID else 'Not set',
            'access_token_configured': bool(self.FACEBOOK_PAGE_ACCESS_TOKEN),
            'configured': self.is_facebook_configured()
        }

    def get_instagram_config(self) -> Dict[str, Any]:
        """Get Instagram configuration (without secrets)."""
        return {
            'business_account_id': self.INSTAGRAM_BUSINESS_ACCOUNT_ID if self.INSTAGRAM_BUSINESS_ACCOUNT_ID else 'Not set',
            'access_token_configured': bool(self.INSTAGRAM_ACCESS_TOKEN),
            'configured': self.is_instagram_configured()
        }

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return status."""
        config = cls()
        return {
            'facebook': config.get_facebook_config(),
            'instagram': config.get_instagram_config(),
            'logs_dir': str(config.LOGS_DIR),
            'fully_operational': config.is_facebook_configured() or config.is_instagram_configured()
        }


# Singleton instance
_config_instance: Optional[SocialMediaConfig] = None


def get_config() -> SocialMediaConfig:
    """Get the configuration singleton."""
    global _config_instance
    if _config_instance is None:
        _config_instance = SocialMediaConfig()
    return _config_instance
