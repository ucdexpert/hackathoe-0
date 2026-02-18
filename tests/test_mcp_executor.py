"""
Tests for mcp_executor.py
"""
import os
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.mcp_executor import (
    ActionType,
    ApprovalStatus,
    ExecutionStatus,
    ActionLogger,
    ApprovalChecker,
    MCPClient,
    RetryHandler,
    MCPExecutor
)


class TestActionType:
    """Tests for ActionType enum."""

    def test_email_action_type(self):
        """Should have EMAIL action type."""
        assert ActionType.EMAIL.value == "email"

    def test_linkedin_action_type(self):
        """Should have LINKEDIN action type."""
        assert ActionType.LINKEDIN.value == "linkedin"

    def test_invalid_action_type_raises_error(self):
        """Should raise ValueError for invalid action type."""
        with pytest.raises(ValueError):
            ActionType("invalid")


class TestApprovalStatus:
    """Tests for ApprovalStatus enum."""

    def test_approval_statuses(self):
        """Should have all approval statuses."""
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    def test_execution_statuses(self):
        """Should have all execution statuses."""
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.REJECTED.value == "rejected"
        assert ExecutionStatus.TIMEOUT.value == "timeout"
        assert ExecutionStatus.ERROR.value == "error"


class TestActionLogger:
    """Tests for ActionLogger class."""

    @pytest.fixture
    def logger(self, tmp_path):
        """Create an ActionLogger instance."""
        logs_dir = str(tmp_path / "Logs")
        os.makedirs(logs_dir)
        return ActionLogger(logs_dir)

    def test_initialization(self, tmp_path):
        """Should initialize with correct logs directory."""
        logs_dir = str(tmp_path / "Logs")
        os.makedirs(logs_dir)
        
        logger = ActionLogger(logs_dir)
        
        assert logger.logs_dir == logs_dir
        assert logger.log_file.endswith("actions.log")

    def test_ensures_logs_directory(self, tmp_path):
        """Should create logs directory if it doesn't exist."""
        logs_dir = str(tmp_path / "new_logs")
        
        logger = ActionLogger(logs_dir)
        
        assert os.path.exists(logs_dir)

    def test_log_action_writes_entry(self, logger, tmp_path):
        """Should write log entry to file."""
        action_data = {"recipient": "test@example.com", "subject": "Test"}
        
        logger.log_action("email", action_data, ExecutionStatus.SUCCESS)
        
        assert os.path.exists(logger.log_file)
        
        with open(logger.log_file, 'r') as f:
            content = f.read()
        
        assert "email" in content
        assert "success" in content

    def test_sanitizes_sensitive_data(self, logger):
        """Should sanitize sensitive data like passwords."""
        action_data = {"password": "secret123", "user": "test"}
        
        sanitized = logger._sanitize_action_data(action_data)
        
        assert sanitized["password"] == "***"
        assert sanitized["user"] == "test"

    def test_log_action_handles_write_error(self, tmp_path, capsys):
        """Should handle write errors gracefully."""
        logs_dir = str(tmp_path / "readonly")
        os.makedirs(logs_dir)
        os.chmod(logs_dir, 0o444)
        
        logger = ActionLogger(logs_dir)
        
        # Should not raise exception
        logger.log_action("email", {}, ExecutionStatus.SUCCESS)


class TestApprovalChecker:
    """Tests for ApprovalChecker class."""

    @pytest.fixture
    def checker(self, tmp_path):
        """Create an ApprovalChecker instance."""
        needs_approval_dir = str(tmp_path / "Needs_Approval")
        os.makedirs(needs_approval_dir)
        return ApprovalChecker(needs_approval_dir)

    def test_returns_none_when_directory_not_exists(self, tmp_path):
        """Should return None when directory doesn't exist."""
        checker = ApprovalChecker(str(tmp_path / "nonexistent"))
        result = checker.check_approval_status("request_123")
        assert result is None

    def test_returns_none_when_request_not_found(self, checker):
        """Should return None when request file not found."""
        result = checker.check_approval_status("nonexistent_request")
        assert result is None

    def test_finds_approved_status(self, checker, tmp_path):
        """Should detect approved status from file."""
        request_file = tmp_path / "Needs_Approval" / "email_123.md"
        request_file.write_text("""
# Approval Request
**Status:** Approved
""")
        
        result = checker.check_approval_status("email_123")
        assert result == ApprovalStatus.APPROVED

    def test_finds_rejected_status(self, checker, tmp_path):
        """Should detect rejected status from file."""
        request_file = tmp_path / "Needs_Approval" / "email_123.md"
        request_file.write_text("""
# Approval Request
**Status:** Rejected
""")
        
        result = checker.check_approval_status("email_123")
        assert result == ApprovalStatus.REJECTED

    def test_returns_pending_as_default(self, checker, tmp_path):
        """Should return pending when status not specified."""
        request_file = tmp_path / "Needs_Approval" / "email_123.md"
        request_file.write_text("""
# Approval Request
Some content here
""")
        
        result = checker.check_approval_status("email_123")
        assert result == ApprovalStatus.PENDING

    def test_wait_for_approval_times_out(self, checker):
        """Should timeout when waiting for approval."""
        # Use very short timeout for testing
        result = checker.wait_for_approval("nonexistent", timeout=1, check_interval=0.1)
        assert result == ApprovalStatus.PENDING


class TestMCPClient:
    """Tests for MCPClient class."""

    @pytest.fixture
    def client(self):
        """Create an MCPClient instance."""
        return MCPClient("http://test-server:8080")

    def test_initialization(self):
        """Should initialize with base URL."""
        client = MCPClient("http://test:8080")
        assert client.base_url == "http://test:8080"

    def test_send_email_returns_success(self, client):
        """Should return success response for send_email."""
        result = client.send_email("test@example.com", "Subject", "Body")
        
        assert result["success"] is True
        assert "message_id" in result["data"]

    def test_post_linkedin_returns_success(self, client):
        """Should return success response for post_linkedin."""
        result = client.post_linkedin("Post content", "Topic")
        
        assert result["success"] is True
        assert "post_id" in result["data"]
        assert "post_url" in result["data"]

    def test_call_mcp_endpoint_simulates_call(self, client):
        """Should simulate MCP endpoint call."""
        result = client._call_mcp_endpoint("http://test/endpoint", {"key": "value"})
        
        assert result["success"] is True
        assert result["error"] is None


class TestRetryHandler:
    """Tests for RetryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a RetryHandler instance."""
        return RetryHandler(max_retries=3, retry_delay=0.01)

    def test_executes_successful_function(self, handler):
        """Should execute successful function on first try."""
        def success_func():
            return {"success": True, "data": "result"}
        
        result = handler.execute_with_retry(success_func)
        
        assert result["success"] is True
        assert result["attempts"] == 1

    def test_retries_on_failure(self, handler):
        """Should retry on failure."""
        call_count = [0]
        
        def fail_then_succeed():
            call_count[0] += 1
            if call_count[0] < 3:
                return {"success": False, "error": "Failed"}
            return {"success": True, "data": "success"}
        
        result = handler.execute_with_retry(fail_then_succeed)
        
        assert result["success"] is True
        assert result["attempts"] == 3

    def test_returns_failure_after_max_retries(self, handler):
        """Should return failure after max retries."""
        def always_fail():
            return {"success": False, "error": "Always fails"}
        
        result = handler.execute_with_retry(always_fail)
        
        assert result["success"] is False
        assert result["attempts"] == 3

    def test_handles_exceptions(self, handler):
        """Should handle exceptions during execution."""
        def raise_exception():
            raise Exception("Test exception")
        
        result = handler.execute_with_retry(raise_exception)
        
        assert result["success"] is False
        assert "Test exception" in result["error"]


class TestMCPExecutor:
    """Tests for MCPExecutor class."""

    @pytest.fixture
    def executor(self, tmp_path):
        """Create an MCPExecutor instance."""
        # Set up test directories
        needs_approval_dir = str(tmp_path / "Needs_Approval")
        logs_dir = str(tmp_path / "Logs")
        os.makedirs(needs_approval_dir)
        os.makedirs(logs_dir)
        
        # Patch the VAULT_FOLDERS
        with patch('scripts.mcp_executor.VAULT_FOLDERS', {
            "needs_approval": needs_approval_dir,
            "logs": logs_dir
        }):
            return MCPExecutor(max_retries=1, retry_delay=0.01)

    def test_execute_email_action(self, executor):
        """Should execute email action successfully."""
        action_data = {
            "recipient": "test@example.com",
            "subject": "Test Subject",
            "body": "Test Body"
        }
        
        result = executor.execute_action("email", action_data)
        
        assert result["status"] == ExecutionStatus.SUCCESS.value
        assert "Email sent" in result["message"]

    def test_execute_linkedin_action(self, executor):
        """Should execute LinkedIn action successfully."""
        action_data = {
            "content": "Test post content",
            "topic": "Test Topic"
        }
        
        result = executor.execute_action("linkedin", action_data)
        
        assert result["status"] == ExecutionStatus.SUCCESS.value
        assert "LinkedIn post published" in result["message"]

    def test_invalid_action_type(self, executor):
        """Should return error for invalid action type."""
        result = executor.execute_action("invalid", {})
        
        assert result["status"] == ExecutionStatus.ERROR.value
        assert "Invalid action type" in result["message"]

    def test_email_missing_fields(self, executor):
        """Should return error for missing email fields."""
        action_data = {"recipient": "test@example.com"}  # Missing subject and body
        
        result = executor.execute_action("email", action_data)
        
        assert result["status"] == ExecutionStatus.ERROR.value
        assert "Missing required fields" in result["message"]

    def test_linkedin_missing_content(self, executor):
        """Should return error for missing LinkedIn content."""
        action_data = {"topic": "Test"}  # Missing content
        
        result = executor.execute_action("linkedin", action_data)
        
        assert result["status"] == ExecutionStatus.ERROR.value
        assert "Missing required field" in result["message"]

    def test_logs_action_execution(self, executor, tmp_path):
        """Should log action execution."""
        action_data = {
            "content": "Test post",
            "topic": "Test"
        }
        
        executor.execute_action("linkedin", action_data)
        
        log_file = tmp_path / "Logs" / "actions.log"
        assert log_file.exists()
