"""
Pytest configuration and shared fixtures for AI Employee Vault tests.
"""
import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def vault_root(tmp_path_factory):
    """Create a temporary vault root directory for testing."""
    return tmp_path_factory.mktemp("vault")


@pytest.fixture
def vault_folders(vault_root):
    """Create standard vault folder structure."""
    folders = {
        'Inbox': vault_root / 'Inbox',
        'Needs_Action': vault_root / 'Needs_Action',
        'Plans': vault_root / 'Plans',
        'Done': vault_root / 'Done',
        'Logs': vault_root / 'Logs',
        'Needs_Approval': vault_root / 'Needs_Approval',
        'Approved': vault_root / 'Approved',
        'Rejected': vault_root / 'Rejected',
    }
    
    for folder in folders.values():
        folder.mkdir(exist_ok=True)
    
    return folders


@pytest.fixture(autouse=True)
def change_to_temp_dir(tmp_path, monkeypatch):
    """Change working directory to temp directory for each test."""
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    def _mock_env(vars_dict):
        for key, value in vars_dict.items():
            monkeypatch.setenv(key, value)
        return monkeypatch
    return _mock_env
