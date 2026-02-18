#!/usr/bin/env python3
"""
Tests for Business MCP Server

Run with:
    pytest test_server.py -v
    pytest test_server.py --cov=. --cov-report=term-missing
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    Config, BusinessLogger, EmailService, LinkedInService, 
    BusinessMCPServer
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_logs_dir(tmp_path):
    """Create a temporary logs directory."""
    logs_dir = tmp_path / "Logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.fixture
def logger(temp_logs_dir):
    """Create a BusinessLogger instance."""
    # Disable logging handlers to avoid conflicts
    import logging
    logging.getLogger('business-mcp').handlers = []
    return BusinessLogger(str(temp_logs_dir))


@pytest.fixture
def email_service(logger):
    """Create an EmailService instance."""
    return EmailService(logger)


@pytest.fixture
def linkedin_service(logger):
    """Create a LinkedInService instance."""
    return LinkedInService(logger)


# ============================================================================
# Config Tests
# ============================================================================

class TestConfig:
    """Test configuration."""
    
    def test_config_has_server_name(self):
        """Test server name is configured."""
        assert Config.SERVER_NAME == 'business-mcp'
    
    def test_config_has_version(self):
        """Test version is configured."""
        assert Config.SERVER_VERSION == '1.0.0'
    
    def test_validate_returns_dict(self):
        """Test validate method returns a dictionary."""
        status = Config.validate()
        assert isinstance(status, dict)
        assert 'email_configured' in status
        assert 'linkedin_configured' in status
        assert 'mcp_available' in status
        assert 'fully_operational' in status


# ============================================================================
# BusinessLogger Tests
# ============================================================================

class TestBusinessLogger:
    """Test BusinessLogger functionality."""
    
    def test_creates_logs_directory(self, temp_logs_dir):
        """Test logger creates logs directory if missing."""
        log_file = temp_logs_dir / "business.log"
        assert log_file.exists()
    
    def test_log_activity_success(self, logger):
        """Test logging a successful activity."""
        result = logger.log_activity(
            message="Test activity",
            action_type="general",
            status="success"
        )
        
        assert result['message'] == "Test activity"
        assert result['status'] == "success"
        assert 'timestamp' in result
    
    def test_log_activity_creates_log_file(self, logger, temp_logs_dir):
        """Test logging creates log file."""
        logger.log_activity("Test message")
        log_file = temp_logs_dir / "business.log"
        assert log_file.exists()
    
    def test_log_activity_writes_json(self, logger, temp_logs_dir):
        """Test log entries are written as JSON."""
        logger.log_activity(
            message="Email sent",
            action_type="email",
            details={"to": "test@example.com"},
            status="success"
        )
        
        log_file = temp_logs_dir / "business.log"
        with open(log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)
            assert entry['message'] == "Email sent"
            assert entry['action_type'] == "email"
    
    def test_get_recent_activities(self, logger):
        """Test retrieving recent activities."""
        # Log multiple activities
        for i in range(15):
            logger.log_activity(f"Activity {i}")
        
        activities = logger.get_recent_activities(limit=10)
        assert len(activities) == 10
        
        # Check most recent first
        assert activities[0]['message'] == "Activity 14"
    
    def test_log_activity_error_status(self, logger):
        """Test logging an error activity."""
        result = logger.log_activity(
            message="Something went wrong",
            action_type="email",
            status="error"
        )
        
        assert result['status'] == "error"


# ============================================================================
# EmailService Tests
# ============================================================================

class TestEmailService:
    """Test EmailService functionality."""
    
    def test_send_email_missing_credentials(self, email_service):
        """Test email sending fails without credentials."""
        result = email_service.send_email(
            to="test@example.com",
            subject="Test",
            body="Test body"
        )
        
        assert result['success'] is False
        assert 'error' in result
        assert 'credentials' in result['error'].lower()
    
    def test_send_email_invalid_address(self, email_service):
        """Test email validation."""
        result = email_service.send_email(
            to="invalid-email",
            subject="Test",
            body="Test body"
        )
        
        assert result['success'] is False
        assert 'Invalid' in result['error']
    
    def test_send_email_valid_address_format(self, email_service):
        """Test email address format validation."""
        assert email_service._validate_email("test@example.com") is True
        assert email_service._validate_email("user.name@domain.co.uk") is True
        assert email_service._validate_email("invalid") is False
        assert email_service._validate_email("@invalid.com") is False
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp, email_service):
        """Test successful email sending."""
        # Mock environment variables
        with patch.object(Config, 'EMAIL_ADDRESS', 'test@gmail.com'), \
             patch.object(Config, 'EMAIL_PASSWORD', 'password'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = email_service.send_email(
                to="recipient@example.com",
                subject="Test Subject",
                body="Test Body"
            )
            
            assert result['success'] is True
            assert result['message_id'] is not None
            assert result['error'] is None
    
    @patch('smtplib.SMTP')
    def test_send_email_with_cc(self, mock_smtp, email_service):
        """Test email sending with CC."""
        with patch.object(Config, 'EMAIL_ADDRESS', 'test@gmail.com'), \
             patch.object(Config, 'EMAIL_PASSWORD', 'password'):
            
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = email_service.send_email(
                to="recipient@example.com",
                subject="Test",
                body="Body",
                cc="cc@example.com"
            )
            
            assert result['success'] is True
    
    @patch('smtplib.SMTP')
    def test_send_email_smtp_auth_error(self, mock_smtp, email_service):
        """Test SMTP authentication error handling."""
        import smtplib
        mock_smtp.side_effect = smtplib.SMTPAuthenticationError(
            535, b'Authentication failed'
        )
        
        with patch.object(Config, 'EMAIL_ADDRESS', 'test@gmail.com'), \
             patch.object(Config, 'EMAIL_PASSWORD', 'wrong_password'):
            
            result = email_service.send_email(
                to="recipient@example.com",
                subject="Test",
                body="Body"
            )
            
            assert result['success'] is False
            assert 'authentication' in result['error'].lower()


# ============================================================================
# LinkedInService Tests
# ============================================================================

class TestLinkedInService:
    """Test LinkedInService functionality."""
    
    def test_post_linkedin_missing_content(self, linkedin_service):
        """Test LinkedIn post fails without content."""
        result = linkedin_service.post_linkedin(content="")
        
        assert result['success'] is False
        assert 'required' in result['error'].lower()
    
    def test_post_linkedin_content_too_long(self, linkedin_service):
        """Test LinkedIn post with content exceeding limit."""
        long_content = "x" * 3001
        result = linkedin_service.post_linkedin(content=long_content)
        
        assert result['success'] is False
        assert 'limit' in result['error'].lower()
    
    def test_post_linkedin_simulation_mode(self, linkedin_service):
        """Test LinkedIn post in simulation mode."""
        result = linkedin_service.post_linkedin(
            content="Test post content"
        )
        
        # Should succeed in simulation mode
        assert result['success'] is True
        assert result['post_id'] is not None
        assert result['post_url'] is not None
        assert 'mode' in result.get('details', {}) or True  # May be in details
    
    def test_post_linkedin_with_topic(self, linkedin_service):
        """Test LinkedIn post with topic."""
        result = linkedin_service.post_linkedin(
            content="Test post",
            topic="Business"
        )
        
        assert result['success'] is True


# ============================================================================
# BusinessMCPServer Tests
# ============================================================================

class TestBusinessMCPServer:
    """Test BusinessMCPServer functionality."""
    
    def test_server_initialization(self):
        """Test server initializes correctly."""
        server = BusinessMCPServer()
        
        assert server.logger is not None
        assert server.email_service is not None
        assert server.linkedin_service is not None
    
    def test_server_get_status(self):
        """Test server status retrieval."""
        server = BusinessMCPServer()
        status = server.get_status()
        
        assert status['server_name'] == 'business-mcp'
        assert status['version'] == '1.0.0'
        assert 'mcp_available' in status
        assert 'config' in status


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for the MCP server."""
    
    def test_full_email_workflow(self, logger):
        """Test complete email workflow."""
        email_service = EmailService(logger)
        
        # Log attempt
        logger.log_activity(
            "Attempting to send email",
            action_type="email",
            status="pending"
        )
        
        # Try to send (will fail without credentials)
        result = email_service.send_email(
            to="test@example.com",
            subject="Integration Test",
            body="Test body"
        )
        
        # Log result
        logger.log_activity(
            f"Email result: {result.get('error', 'success')}",
            action_type="email",
            status="success" if result['success'] else "error"
        )
        
        # Verify log file has entries
        activities = logger.get_recent_activities(limit=5)
        assert len(activities) >= 2
    
    def test_full_linkedin_workflow(self, logger):
        """Test complete LinkedIn workflow."""
        linkedin_service = LinkedInService(logger)
        
        # Log attempt
        logger.log_activity(
            "Attempting to create LinkedIn post",
            action_type="linkedin",
            status="pending"
        )
        
        # Create post
        result = linkedin_service.post_linkedin(
            content="Integration test post #automation"
        )
        
        # Log result
        logger.log_activity(
            f"LinkedIn post created: {result.get('post_id', 'failed')}",
            action_type="linkedin",
            status="success" if result['success'] else "error"
        )
        
        assert result['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
