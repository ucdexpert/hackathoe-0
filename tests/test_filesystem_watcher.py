"""
Tests for filesystem_watcher.py
"""
import os
import json
import pytest
import time
from datetime import datetime
from unittest.mock import patch, MagicMock, Mock
from watchdog.events import FileCreatedEvent

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from filesystem_watcher import (
    FileCreatedHandler,
    ensure_directories_exist,
    setup_logging,
    main
)


class TestFileCreatedHandler:
    """Tests for FileCreatedHandler class."""

    @pytest.fixture
    def handler(self, tmp_path):
        """Create a FileCreatedHandler instance."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        return FileCreatedHandler(inbox_dir, needs_action_dir)

    def test_initialization(self, tmp_path):
        """Should initialize with correct directories."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        handler = FileCreatedHandler(inbox_dir, needs_action_dir)
        
        assert handler.inbox_dir == inbox_dir
        assert handler.needs_action_dir == needs_action_dir
        assert isinstance(handler.processed_files, set)

    def test_on_created_calls_process_new_file(self, tmp_path):
        """Should call process_new_file when file is created."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        handler = FileCreatedHandler(inbox_dir, needs_action_dir)
        
        # Create a test file
        test_file = str(tmp_path / "Inbox" / "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Create event
        event = FileCreatedEvent(test_file)
        handler.on_created(event)
        
        # Check that report was created
        report_files = list(tmp_path.glob("Needs_Action/*_report.md"))
        assert len(report_files) == 1

    def test_process_new_file_creates_markdown_report(self, tmp_path):
        """Should create markdown report for new file."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        handler = FileCreatedHandler(inbox_dir, needs_action_dir)
        
        # Create a test file
        test_file = str(tmp_path / "Inbox" / "document.pdf")
        with open(test_file, 'w') as f:
            f.write("pdf content")
        
        handler.process_new_file(test_file)
        
        # Check report was created
        report_file = tmp_path / "Needs_Action" / "document_report.md"
        assert report_file.exists()
        
        content = report_file.read_text()
        assert "document.pdf" in content
        assert "File Size" in content
        assert "Timestamp" in content
        assert "Status" in content

    def test_process_new_file_prevents_duplicates(self, tmp_path):
        """Should prevent processing same file twice."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        handler = FileCreatedHandler(inbox_dir, needs_action_dir)
        
        # Create a test file
        test_file = str(tmp_path / "Inbox" / "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Process twice
        handler.process_new_file(test_file)
        initial_count = len(list(tmp_path.glob("Needs_Action/*_report.md")))
        
        handler.process_new_file(test_file)
        final_count = len(list(tmp_path.glob("Needs_Action/*_report.md")))
        
        assert initial_count == final_count

    def test_process_new_file_logs_operation(self, tmp_path):
        """Should log operation in JSON format."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        handler = FileCreatedHandler(inbox_dir, needs_action_dir)
        
        # Create a test file
        test_file = str(tmp_path / "Inbox" / "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        handler.process_new_file(test_file)
        
        # Check log file was created
        log_files = list(tmp_path.glob("Logs/filesystem_watcher_*.json"))
        assert len(log_files) >= 1

    def test_handles_file_not_found_error(self, tmp_path, caplog):
        """Should handle FileNotFoundError gracefully."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        handler = FileCreatedHandler(inbox_dir, needs_action_dir)
        
        # Try to process non-existent file
        handler.process_new_file(str(tmp_path / "Inbox" / "nonexistent.txt"))
        
        assert "File not found" in caplog.text

    def test_handles_permission_error(self, tmp_path, caplog):
        """Should handle PermissionError gracefully."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        handler = FileCreatedHandler(inbox_dir, needs_action_dir)
        
        # Mock os.path.getsize to raise PermissionError
        with patch('filesystem_watcher.os.path.getsize', side_effect=PermissionError("Permission denied")):
            test_file = str(tmp_path / "Inbox" / "test.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            
            handler.process_new_file(test_file)
        
        assert "Permission denied" in caplog.text


class TestEnsureDirectoriesExist:
    """Tests for ensure_directories_exist function."""

    def test_creates_missing_directories(self, tmp_path):
        """Should create directories that don't exist."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        
        ensure_directories_exist(inbox_dir, needs_action_dir)
        
        assert os.path.exists(inbox_dir)
        assert os.path.exists(needs_action_dir)

    def test_does_not_fail_if_directories_exist(self, tmp_path):
        """Should not fail if directories already exist."""
        inbox_dir = str(tmp_path / "Inbox")
        needs_action_dir = str(tmp_path / "Needs_Action")
        
        os.makedirs(inbox_dir)
        os.makedirs(needs_action_dir)
        
        # Should not raise any exception
        ensure_directories_exist(inbox_dir, needs_action_dir)
        
        assert os.path.exists(inbox_dir)
        assert os.path.exists(needs_action_dir)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_configures_logging(self, tmp_path):
        """Should configure logging with file and stream handlers."""
        original_dir = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            setup_logging()
            
            # Check that log file is created when logging
            import logging
            logging.info("Test log message")
            
            assert os.path.exists("filesystem_watcher.log")
        finally:
            os.chdir(original_dir)


class TestMain:
    """Tests for main function."""

    def test_main_starts_observer(self, tmp_path):
        """Should start the file system observer."""
        original_dir = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            # Mock the observer to avoid infinite loop
            with patch('filesystem_watcher.Observer') as mock_observer_class:
                mock_observer = MagicMock()
                mock_observer_class.return_value = mock_observer
                
                # Mock time.sleep to exit quickly
                with patch('filesystem_watcher.time.sleep', side_effect=InterruptedError("Stop")):
                    with pytest.raises(InterruptedError):
                        main()
                
                # Verify observer was started
                mock_observer.start.assert_called_once()
                mock_observer.schedule.assert_called_once()
        finally:
            os.chdir(original_dir)

    def test_main_creates_directories(self, tmp_path):
        """Should create Inbox and Needs_Action directories."""
        original_dir = os.getcwd()
        os.chdir(str(tmp_path))
        
        try:
            with patch('filesystem_watcher.Observer') as mock_observer_class:
                mock_observer = MagicMock()
                mock_observer_class.return_value = mock_observer
                
                with patch('filesystem_watcher.time.sleep', side_effect=InterruptedError("Stop")):
                    with pytest.raises(InterruptedError):
                        main()
                
                assert os.path.exists("Inbox")
                assert os.path.exists("Needs_Action")
        finally:
            os.chdir(original_dir)
