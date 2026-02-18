"""
Tests for vault_file_manager.py
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

# Import vault_file_manager functions
from scripts.vault_file_manager import (
    ensure_folders,
    list_files,
    count_files,
    find_file,
    get_file_location,
    move_file,
    copy_file,
    get_status,
    FOLDERS
)


class TestEnsureFolders:
    """Tests for ensure_folders function."""

    def test_creates_all_vault_folders(self, tmp_path, monkeypatch):
        """Should create all vault folders."""
        # Temporarily change FOLDERS to use tmp_path
        test_folders = {
            'Inbox': str(tmp_path / 'Inbox'),
            'Needs_Action': str(tmp_path / 'Needs_Action'),
            'Plans': str(tmp_path / 'Plans'),
            'Done': str(tmp_path / 'Done'),
        }
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            ensure_folders()
        
        for folder_path in test_folders.values():
            assert os.path.exists(folder_path)

    def test_does_not_fail_if_folders_exist(self, tmp_path):
        """Should not fail if folders already exist."""
        test_folders = {
            'Inbox': str(tmp_path / 'Inbox'),
        }
        
        os.makedirs(test_folders['Inbox'])
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            # Should not raise any exception
            ensure_folders()
        
        assert os.path.exists(test_folders['Inbox'])


class TestListFiles:
    """Tests for list_files function."""

    def test_returns_list_of_files(self, tmp_path):
        """Should return list of files in folder."""
        test_folders = {'TestFolder': str(tmp_path / 'TestFolder')}
        os.makedirs(test_folders['TestFolder'])
        
        # Create test files
        (tmp_path / 'TestFolder' / 'file1.txt').write_text('content1')
        (tmp_path / 'TestFolder' / 'file2.md').write_text('content2')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = list_files('TestFolder')
        
        assert len(result) == 2
        assert 'file1.txt' in result
        assert 'file2.md' in result

    def test_returns_empty_list_for_nonexistent_folder(self, tmp_path):
        """Should return empty list for non-existent folder."""
        test_folders = {'NonExistent': str(tmp_path / 'NonExistent')}
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = list_files('NonExistent')
        
        assert result == []

    def test_excludes_directories(self, tmp_path):
        """Should exclude directories from results."""
        test_folders = {'TestFolder': str(tmp_path / 'TestFolder')}
        os.makedirs(test_folders['TestFolder'])
        os.makedirs(str(tmp_path / 'TestFolder' / 'subdir'))
        
        (tmp_path / 'TestFolder' / 'file.txt').write_text('content')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = list_files('TestFolder')
        
        assert len(result) == 1
        assert 'file.txt' in result


class TestCountFiles:
    """Tests for count_files function."""

    def test_returns_correct_count(self, tmp_path):
        """Should return correct file count."""
        test_folders = {'TestFolder': str(tmp_path / 'TestFolder')}
        os.makedirs(test_folders['TestFolder'])
        
        for i in range(5):
            (tmp_path / 'TestFolder' / f'file{i}.txt').write_text(f'content{i}')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = count_files('TestFolder')
        
        assert result == 5

    def test_returns_zero_for_empty_folder(self, tmp_path):
        """Should return zero for empty folder."""
        test_folders = {'TestFolder': str(tmp_path / 'TestFolder')}
        os.makedirs(test_folders['TestFolder'])
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = count_files('TestFolder')
        
        assert result == 0


class TestFindFile:
    """Tests for find_file function."""

    def test_finds_file_in_folder(self, tmp_path):
        """Should find file and return full path."""
        test_folders = {
            'Folder1': str(tmp_path / 'Folder1'),
            'Folder2': str(tmp_path / 'Folder2'),
        }
        os.makedirs(test_folders['Folder1'])
        os.makedirs(test_folders['Folder2'])
        
        (tmp_path / 'Folder1' / 'target.txt').write_text('content')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = find_file('target.txt')
        
        assert result is not None
        assert result.endswith('target.txt')

    def test_returns_none_when_file_not_found(self, tmp_path):
        """Should return None when file is not found."""
        test_folders = {'Folder1': str(tmp_path / 'Folder1')}
        os.makedirs(test_folders['Folder1'])
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = find_file('nonexistent.txt')
        
        assert result is None


class TestGetFileLocation:
    """Tests for get_file_location function."""

    def test_returns_folder_name(self, tmp_path):
        """Should return the folder name where file is located."""
        test_folders = {
            'Inbox': str(tmp_path / 'Inbox'),
            'Done': str(tmp_path / 'Done'),
        }
        os.makedirs(test_folders['Inbox'])
        os.makedirs(test_folders['Done'])
        
        (tmp_path / 'Inbox' / 'file.txt').write_text('content')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = get_file_location('file.txt')
        
        assert result == 'Inbox'

    def test_returns_none_when_file_not_found(self, tmp_path):
        """Should return None when file is not found."""
        test_folders = {'Folder1': str(tmp_path / 'Folder1')}
        os.makedirs(test_folders['Folder1'])
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = get_file_location('nonexistent.txt')
        
        assert result is None


class TestMoveFile:
    """Tests for move_file function."""

    def test_moves_file_successfully(self, tmp_path):
        """Should move file from source to destination."""
        test_folders = {
            'Source': str(tmp_path / 'Source'),
            'Destination': str(tmp_path / 'Destination'),
        }
        os.makedirs(test_folders['Source'])
        os.makedirs(test_folders['Destination'])
        
        source_file = tmp_path / 'Source' / 'file.txt'
        source_file.write_text('content')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = move_file('file.txt', 'Destination', 'Source')
        
        assert result['success'] is True
        assert not source_file.exists()
        assert (tmp_path / 'Destination' / 'file.txt').exists()

    def test_returns_error_for_invalid_destination(self, tmp_path):
        """Should return error for invalid destination folder."""
        test_folders = {'Folder1': str(tmp_path / 'Folder1')}
        os.makedirs(test_folders['Folder1'])
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = move_file('file.txt', 'NonExistent')
        
        assert result['success'] is False
        assert 'Invalid destination folder' in result['message']

    def test_returns_error_when_file_not_found(self, tmp_path):
        """Should return error when file is not found."""
        test_folders = {'Folder1': str(tmp_path / 'Folder1')}
        os.makedirs(test_folders['Folder1'])
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = move_file('nonexistent.txt', 'Folder1')
        
        assert result['success'] is False
        assert 'File not found' in result['message']

    def test_adds_timestamp_to_avoid_overwrite(self, tmp_path):
        """Should add timestamp to filename if destination file exists."""
        test_folders = {
            'Source': str(tmp_path / 'Source'),
            'Destination': str(tmp_path / 'Destination'),
        }
        os.makedirs(test_folders['Source'])
        os.makedirs(test_folders['Destination'])
        
        # Create file in both source and destination
        (tmp_path / 'Source' / 'file.txt').write_text('source content')
        (tmp_path / 'Destination' / 'file.txt').write_text('dest content')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = move_file('file.txt', 'Destination', 'Source')
        
        assert result['success'] is True
        # Original destination file should still exist
        assert (tmp_path / 'Destination' / 'file.txt').exists()
        # New file should have timestamp
        dest_files = list((tmp_path / 'Destination').glob('file_*.txt'))
        assert len(dest_files) >= 1


class TestCopyFile:
    """Tests for copy_file function."""

    def test_copies_file_successfully(self, tmp_path):
        """Should copy file to destination."""
        test_folders = {
            'Source': str(tmp_path / 'Source'),
            'Destination': str(tmp_path / 'Destination'),
        }
        os.makedirs(test_folders['Source'])
        os.makedirs(test_folders['Destination'])
        
        source_file = tmp_path / 'Source' / 'file.txt'
        source_file.write_text('content')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = copy_file('file.txt', 'Destination')
        
        assert result['success'] is True
        assert source_file.exists()  # Original should still exist
        assert (tmp_path / 'Destination' / 'file.txt').exists()

    def test_returns_error_when_file_not_found(self, tmp_path):
        """Should return error when file is not found."""
        test_folders = {'Folder1': str(tmp_path / 'Folder1')}
        os.makedirs(test_folders['Folder1'])
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = copy_file('nonexistent.txt', 'Folder1')
        
        assert result['success'] is False
        assert 'File not found' in result['message']


class TestGetStatus:
    """Tests for get_status function."""

    def test_returns_file_counts_for_all_folders(self, tmp_path):
        """Should return file counts for all folders."""
        test_folders = {
            'Inbox': str(tmp_path / 'Inbox'),
            'Done': str(tmp_path / 'Done'),
            'Plans': str(tmp_path / 'Plans'),
        }
        os.makedirs(test_folders['Inbox'])
        os.makedirs(test_folders['Done'])
        os.makedirs(test_folders['Plans'])
        
        # Add files to folders
        (tmp_path / 'Inbox' / 'file1.txt').write_text('content')
        (tmp_path / 'Inbox' / 'file2.txt').write_text('content')
        (tmp_path / 'Done' / 'file3.txt').write_text('content')
        
        with patch('scripts.vault_file_manager.FOLDERS', test_folders):
            result = get_status()
        
        assert 'Inbox' in result
        assert 'Done' in result
        assert 'Plans' in result
        assert result['Inbox'] == 2
        assert result['Done'] == 1
        assert result['Plans'] == 0
