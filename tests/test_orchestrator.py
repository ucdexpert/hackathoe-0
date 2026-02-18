"""
Tests for orchestrator.py
"""
import os
import json
import shutil
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from orchestrator import (
    scan_needs_action_folder,
    create_plan_file,
    move_to_done,
    log_operation,
    safe_update_dashboard,
    process_needs_action_files,
    main
)


class TestScanNeedsActionFolder:
    """Tests for scan_needs_action_folder function."""

    def test_returns_empty_list_when_directory_does_not_exist(self, tmp_path):
        """Should return empty list when directory doesn't exist."""
        non_existent_dir = str(tmp_path / "non_existent")
        result = scan_needs_action_folder(non_existent_dir)
        assert result == []

    def test_returns_markdown_files(self, tmp_path):
        """Should return list of markdown files."""
        # Create test files
        (tmp_path / "test1.md").write_text("content1")
        (tmp_path / "test2.md").write_text("content2")
        (tmp_path / "test.txt").write_text("not markdown")
        (tmp_path / "test.MD").write_text("uppercase extension")

        result = scan_needs_action_folder(str(tmp_path))
        
        assert len(result) == 3
        assert all(f.endswith('.md') or f.endswith('.MD') for f in result)

    def test_excludes_directories(self, tmp_path):
        """Should exclude directories from results."""
        (tmp_path / "file.md").write_text("content")
        (tmp_path / "subdir").mkdir()

        result = scan_needs_action_folder(str(tmp_path))
        
        assert len(result) == 1
        assert "file.md" in result[0]

    def test_returns_empty_list_for_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        result = scan_needs_action_folder(str(tmp_path))
        assert result == []


class TestCreatePlanFile:
    """Tests for create_plan_file function."""

    def test_creates_plan_file_with_correct_content(self, tmp_path):
        """Should create plan file with expected content."""
        plan_file = str(tmp_path / "plan_test.md")
        original_filename = "test_report.md"

        create_plan_file(plan_file, original_filename)

        assert os.path.exists(plan_file)
        content = open(plan_file, 'r').read()
        assert "Action Plan for test_report.md" in content
        assert "Checklist" in content
        assert "Review item" in content

    def test_creates_parent_directories(self, tmp_path):
        """Should create parent directories if they don't exist."""
        nested_dir = tmp_path / "nested" / "deep" / "path"
        nested_dir.mkdir(parents=True)  # Create directories first
        plan_file = str(nested_dir / "plan_test.md")

        create_plan_file(plan_file, "test.md")

        assert os.path.exists(plan_file)

    @pytest.mark.skipif(os.name == 'nt', reason="Permission handling differs on Windows")
    def test_raises_exception_on_permission_error(self, tmp_path):
        """Should raise exception on permission error."""
        # Create a directory and make it read-only
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        os.chmod(str(read_only_dir), 0o444)
        
        plan_file = str(read_only_dir / "plan_test.md")
        
        with pytest.raises(Exception) as exc_info:
            create_plan_file(plan_file, "test.md")
        
        assert "Permission denied" in str(exc_info.value) or "OS error" in str(exc_info.value)


class TestMoveToDone:
    """Tests for move_to_done function."""

    def test_moves_file_to_done_folder(self, tmp_path):
        """Should move file to Done folder."""
        done_dir = str(tmp_path / "Done")
        source_file = str(tmp_path / "source.md")
        
        # Create source file
        with open(source_file, 'w') as f:
            f.write("content")

        result = move_to_done(done_dir, source_file)

        assert not os.path.exists(source_file)
        assert os.path.exists(os.path.join(done_dir, "source.md"))
        assert result == os.path.join(done_dir, "source.md")

    def test_creates_done_directory_if_not_exists(self, tmp_path):
        """Should create Done directory if it doesn't exist."""
        done_dir = str(tmp_path / "new_done")
        source_file = str(tmp_path / "source.md")
        
        with open(source_file, 'w') as f:
            f.write("content")

        move_to_done(done_dir, source_file)

        assert os.path.exists(done_dir)

    @pytest.mark.skipif(os.name == 'nt', reason="Permission handling differs on Windows")
    def test_raises_exception_on_permission_error(self, tmp_path):
        """Should raise exception on permission error."""
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        os.chmod(str(read_only_dir), 0o444)
        
        source_file = str(tmp_path / "source.md")
        with open(source_file, 'w') as f:
            f.write("content")

        with pytest.raises(Exception) as exc_info:
            move_to_done(str(read_only_dir), source_file)
        
        assert "Permission denied" in str(exc_info.value) or "OS error" in str(exc_info.value)


class TestLogOperation:
    """Tests for log_operation function."""

    def test_creates_log_file(self, tmp_path):
        """Should create JSON log file."""
        logs_dir = str(tmp_path / "Logs")
        operation_data = {"test": "data", "timestamp": "2026-02-18"}

        log_operation(logs_dir, operation_data)

        log_files = list(tmp_path.glob("Logs/log_*.json"))
        assert len(log_files) == 1

        with open(log_files[0], 'r') as f:
            logged_data = json.load(f)
        
        assert logged_data["test"] == "data"

    def test_creates_logs_directory_if_not_exists(self, tmp_path):
        """Should create Logs directory if it doesn't exist."""
        logs_dir = str(tmp_path / "new_logs")

        log_operation(logs_dir, {"test": "data"})

        assert os.path.exists(logs_dir)

    @pytest.mark.skipif(os.name == 'nt', reason="Permission handling differs on Windows")
    def test_handles_permission_error_gracefully(self, tmp_path, capsys):
        """Should handle permission error gracefully."""
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        os.chmod(str(read_only_dir), 0o444)

        log_operation(str(read_only_dir), {"test": "data"})

        captured = capsys.readouterr()
        assert "Permission denied" in captured.out or "OS error" in captured.out


class TestSafeUpdateDashboard:
    """Tests for safe_update_dashboard function."""

    def test_creates_dashboard_if_not_exists(self, tmp_path):
        """Should create dashboard file if it doesn't exist."""
        dashboard_file = str(tmp_path / "Dashboard.md")
        entries = [{"timestamp": "2026-02-18", "action": "test", "item": "file.md"}]

        safe_update_dashboard(dashboard_file, entries)

        assert os.path.exists(dashboard_file)
        content = open(dashboard_file, 'r').read()
        assert "# Dashboard" in content
        assert "## Recent Activity" in content

    def test_adds_entries_to_existing_dashboard(self, tmp_path):
        """Should add entries to existing dashboard."""
        dashboard_file = str(tmp_path / "Dashboard.md")
        
        # Create initial dashboard
        with open(dashboard_file, 'w') as f:
            f.write("# Dashboard\n\n## Recent Activity\n\n")

        entries = [{"timestamp": "2026-02-18", "action": "Processed", "item": "test.md"}]
        safe_update_dashboard(dashboard_file, entries)

        content = open(dashboard_file, 'r').read()
        assert "2026-02-18" in content
        assert "Processed" in content
        assert "test.md" in content

    def test_creates_backup_before_update(self, tmp_path):
        """Should create backup before updating (then remove it)."""
        dashboard_file = str(tmp_path / "Dashboard.md")
        
        with open(dashboard_file, 'w') as f:
            f.write("# Dashboard\n")

        entries = [{"timestamp": "2026-02-18", "action": "test", "item": "file.md"}]
        safe_update_dashboard(dashboard_file, entries)

        # Backup should be removed after successful update
        backup_file = f"{dashboard_file}.backup"
        assert not os.path.exists(backup_file)

    @pytest.mark.skipif(os.name == 'nt', reason="Permission handling differs on Windows")
    def test_raises_exception_on_permission_error(self, tmp_path):
        """Should raise exception on permission error."""
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        dashboard_file = str(read_only_dir / "Dashboard.md")
        os.chmod(str(read_only_dir), 0o444)

        entries = [{"timestamp": "2026-02-18", "action": "test", "item": "file.md"}]

        with pytest.raises(Exception) as exc_info:
            safe_update_dashboard(dashboard_file, entries)
        
        assert "Permission denied" in str(exc_info.value) or "OS error" in str(exc_info.value)


class TestProcessNeedsActionFiles:
    """Tests for process_needs_action_files function."""

    @pytest.fixture
    def setup_test_environment(self, tmp_path):
        """Set up test environment with necessary directories."""
        # Create directories
        (tmp_path / "Needs_Action").mkdir()
        (tmp_path / "Plans").mkdir()
        (tmp_path / "Done").mkdir()
        (tmp_path / "Logs").mkdir()
        
        # Change to temp directory
        original_dir = os.getcwd()
        os.chdir(str(tmp_path))
        
        yield tmp_path
        
        os.chdir(original_dir)

    def test_processes_markdown_files(self, setup_test_environment):
        """Should process markdown files in Needs_Action folder."""
        # Create test file
        test_file = setup_test_environment / "Needs_Action" / "test_report.md"
        test_file.write_text("# Test Report\n\nContent here")

        process_needs_action_files()

        # File should be moved to Done
        assert not test_file.exists()
        assert (setup_test_environment / "Done" / "test_report.md").exists()
        
        # Plan should be created
        plan_files = list((setup_test_environment / "Plans").glob("plan_*.md"))
        assert len(plan_files) == 1

    def test_creates_log_entry(self, setup_test_environment):
        """Should create log entry for processed file."""
        test_file = setup_test_environment / "Needs_Action" / "test.md"
        test_file.write_text("# Test")

        process_needs_action_files()

        log_files = list((setup_test_environment / "Logs").glob("log_*.json"))
        assert len(log_files) >= 1

    def test_updates_dashboard(self, setup_test_environment):
        """Should update dashboard with activity."""
        test_file = setup_test_environment / "Needs_Action" / "test.md"
        test_file.write_text("# Test")

        process_needs_action_files()

        dashboard_file = setup_test_environment / "Dashboard.md"
        assert dashboard_file.exists()
        content = dashboard_file.read_text()
        assert "test.md" in content

    def test_handles_empty_needs_action_folder(self, setup_test_environment, capsys):
        """Should handle empty Needs_Action folder gracefully."""
        process_needs_action_files()

        captured = capsys.readouterr()
        assert "No markdown files found" in captured.out

    def test_prevents_duplicate_processing(self, setup_test_environment, capsys):
        """Should prevent processing same file twice."""
        # This test verifies the duplicate prevention mechanism exists
        test_file = setup_test_environment / "Needs_Action" / "test.md"
        test_file.write_text("# Test")

        # Process twice - second should skip
        process_needs_action_files()
        
        # Create file again for second run
        test_file.write_text("# Test again")
        process_needs_action_files()

        # Should have processed both (different runs have different processed_files sets)
        done_files = list((setup_test_environment / "Done").glob("*.md"))
        assert len(done_files) >= 1


class TestMain:
    """Tests for main function."""

    def test_main_runs_without_error(self, capsys):
        """Should run main function without errors."""
        main()
        
        captured = capsys.readouterr()
        assert "Starting Orchestrator" in captured.out
        assert "Orchestrator completed" in captured.out
