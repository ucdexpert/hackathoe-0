"""
Tests for send_email.py
"""
import os
import pytest
from unittest.mock import patch, MagicMock, Mock

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.send_email import (
    validate_email,
    send_email
)


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_email(self):
        """Should return True for valid email."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.org") is True
        assert validate_email("user+tag@example.co.uk") is True

    def test_invalid_email_no_at(self):
        """Should return False for email without @."""
        assert validate_email("testexample.com") is False

    def test_invalid_email_no_domain(self):
        """Should return False for email without domain."""
        assert validate_email("test@") is False
        assert validate_email("test@.com") is False

    def test_invalid_email_no_tld(self):
        """Should return False for email without TLD."""
        assert validate_email("test@example") is False

    def test_invalid_email_spaces(self):
        """Should return False for email with spaces."""
        assert validate_email("test @example.com") is False
        assert validate_email("test@example .com") is False

    def test_strips_whitespace(self):
        """Should handle whitespace around email."""
        assert validate_email("  test@example.com  ") is True

    def test_empty_string(self):
        """Should return False for empty string."""
        assert validate_email("") is False
        assert validate_email("   ") is False


class TestSendEmail:
    """Tests for send_email function."""

    @pytest.fixture
    def mock_env(self):
        """Mock environment variables for email testing."""
        with patch.dict(os.environ, {
            'EMAIL_ADDRESS': 'test@gmail.com',
            'EMAIL_PASSWORD': 'testpassword',
            'SMTP_SERVER': 'smtp.gmail.com',
            'SMTP_PORT': '587'
        }):
            yield

    def test_missing_email_address(self):
        """Should return error when EMAIL_ADDRESS is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is False
        assert "EMAIL_ADDRESS" in result["message"]

    def test_missing_email_password(self, mock_env):
        """Should return error when EMAIL_PASSWORD is missing."""
        with patch.dict(os.environ, {'EMAIL_ADDRESS': 'test@gmail.com'}, clear=False):
            # Remove only EMAIL_PASSWORD
            env_copy = os.environ.copy()
            if 'EMAIL_PASSWORD' in env_copy:
                del env_copy['EMAIL_PASSWORD']
            with patch.dict(os.environ, env_copy, clear=False):
                result = send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is False
        assert "EMAIL_PASSWORD" in result["message"]

    def test_invalid_recipient_email(self, mock_env):
        """Should return error for invalid recipient email."""
        result = send_email("invalid-email", "Subject", "Body")
        
        assert result["success"] is False
        assert "Invalid email address" in result["message"]

    def test_missing_subject(self, mock_env):
        """Should return error when subject is missing."""
        result = send_email("test@example.com", "", "Body")
        
        assert result["success"] is False
        assert "subject is required" in result["message"]

    def test_missing_body(self, mock_env):
        """Should return error when body is missing."""
        result = send_email("test@example.com", "Subject", "")
        
        assert result["success"] is False
        assert "body is required" in result["message"]

    def test_whitespace_only_subject(self, mock_env):
        """Should return error for whitespace-only subject."""
        result = send_email("test@example.com", "   ", "Body")
        
        assert result["success"] is False

    def test_whitespace_only_body(self, mock_env):
        """Should return error for whitespace-only body."""
        result = send_email("test@example.com", "Subject", "   ")
        
        assert result["success"] is False

    @patch('scripts.send_email.smtplib.SMTP')
    def test_successful_email_send(self, mock_smtp, mock_env):
        """Should return success for valid email send."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda self: mock_server
        mock_smtp.return_value.__exit__ = lambda self, *args: None
        
        result = send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is True
        assert "Email sent" in result["message"]
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch('scripts.send_email.smtplib.SMTP')
    def test_email_with_cc(self, mock_smtp, mock_env):
        """Should handle CC recipients."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda self: mock_server
        mock_smtp.return_value.__exit__ = lambda self, *args: None
        
        result = send_email(
            "to@example.com", 
            "Subject", 
            "Body", 
            cc="cc1@example.com, cc2@example.com"
        )
        
        assert result["success"] is True

    @patch('scripts.send_email.smtplib.SMTP')
    def test_email_with_invalid_cc(self, mock_smtp, mock_env):
        """Should handle invalid CC recipients gracefully."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda self: mock_server
        mock_smtp.return_value.__exit__ = lambda self, *args: None
        
        result = send_email(
            "to@example.com", 
            "Subject", 
            "Body", 
            cc="invalid-email, valid@example.com"
        )
        
        assert result["success"] is True

    @patch('scripts.send_email.smtplib.SMTP')
    def test_email_with_attachments(self, mock_smtp, mock_env, tmp_path):
        """Should handle attachments."""
        # Create a test attachment file
        attachment_file = tmp_path / "test_attachment.txt"
        attachment_file.write_text("attachment content")
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda self: mock_server
        mock_smtp.return_value.__exit__ = lambda self, *args: None
        
        result = send_email(
            "test@example.com",
            "Subject",
            "Body",
            attachments=[str(attachment_file)]
        )
        
        assert result["success"] is True

    @patch('scripts.send_email.smtplib.SMTP')
    def test_email_with_nonexistent_attachment(self, mock_smtp, mock_env):
        """Should handle non-existent attachment gracefully."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = lambda self: mock_server
        mock_smtp.return_value.__exit__ = lambda self, *args: None
        
        result = send_email(
            "test@example.com",
            "Subject",
            "Body",
            attachments=["/nonexistent/file.txt"]
        )
        
        assert result["success"] is True

    @patch('scripts.send_email.smtplib.SMTP')
    def test_smtp_authentication_error(self, mock_smtp, mock_env):
        """Should handle SMTP authentication error."""
        import smtplib
        mock_smtp.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        
        result = send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is False
        assert "authentication failed" in result["message"].lower()

    @patch('scripts.send_email.smtplib.SMTP')
    def test_smtp_connect_error(self, mock_smtp, mock_env):
        """Should handle SMTP connection error."""
        import smtplib
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, "Connection failed")
        
        result = send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is False
        assert "connect" in result["message"].lower()

    @patch('scripts.send_email.smtplib.SMTP')
    def test_generic_smtp_error(self, mock_smtp, mock_env):
        """Should handle generic SMTP error."""
        import smtplib
        mock_server = MagicMock()
        mock_server.starttls.side_effect = smtplib.SMTPException("SMTP error")
        mock_smtp.return_value.__enter__ = lambda self: mock_server
        mock_smtp.return_value.__exit__ = lambda self, *args: None
        
        result = send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is False
        assert "SMTP error" in result["message"]

    @patch('scripts.send_email.smtplib.SMTP')
    def test_generic_exception(self, mock_smtp, mock_env):
        """Should handle generic exception."""
        mock_smtp.side_effect = Exception("Unexpected error")
        
        result = send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is False
        assert "Unexpected error" in result["message"]

    def test_default_smtp_server(self):
        """Should use default SMTP server when not specified."""
        with patch.dict(os.environ, {
            'EMAIL_ADDRESS': 'test@gmail.com',
            'EMAIL_PASSWORD': 'password'
        }):
            with patch('scripts.send_email.smtplib.SMTP') as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__ = lambda self: mock_server
                mock_smtp.return_value.__exit__ = lambda self, *args: None
                
                send_email("test@example.com", "Subject", "Body")
                
                mock_smtp.assert_called_once_with('smtp.gmail.com', 587, timeout=30)

    def test_custom_smtp_server(self):
        """Should use custom SMTP server when specified."""
        with patch.dict(os.environ, {
            'EMAIL_ADDRESS': 'test@custom.com',
            'EMAIL_PASSWORD': 'password',
            'SMTP_SERVER': 'smtp.custom.com',
            'SMTP_PORT': '465'
        }):
            with patch('scripts.send_email.smtplib.SMTP') as mock_smtp:
                mock_server = MagicMock()
                mock_smtp.return_value.__enter__ = lambda self: mock_server
                mock_smtp.return_value.__exit__ = lambda self, *args: None
                
                send_email("test@example.com", "Subject", "Body")
                
                mock_smtp.assert_called_once_with('smtp.custom.com', 465, timeout=30)
