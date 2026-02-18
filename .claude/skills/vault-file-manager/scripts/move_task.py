#!/usr/bin/env python3
"""
Vault File Manager - Manage task workflow between vault folders

Usage:
    python move_task.py --file document.pdf --to Needs_Action
    python move_task.py --file task.md --to Done
    python move_task.py --list Inbox
    python move_task.py --status
"""

import os
import sys
import argparse
import shutil
from datetime import datetime
from typing import List, Optional


# Resolve vault paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))

FOLDERS = {
    'Inbox': os.path.join(VAULT_ROOT, 'Inbox'),
    'Needs_Action': os.path.join(VAULT_ROOT, 'Needs_Action'),
    'Plans': os.path.join(VAULT_ROOT, 'Plans'),
    'Done': os.path.join(VAULT_ROOT, 'Done'),
    'Needs_Approval': os.path.join(VAULT_ROOT, 'Needs_Approval'),
    'Approved': os.path.join(VAULT_ROOT, 'Approved'),
    'Rejected': os.path.join(VAULT_ROOT, 'Rejected')
}


def ensure_folders():
    """Ensure all vault folders exist."""
    for path in FOLDERS.values():
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)


def list_files(folder: str) -> List[str]:
    """List files in a folder."""
    folder_path = FOLDERS.get(folder)
    if not folder_path or not os.path.exists(folder_path):
        return []
    
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]


def count_files(folder: str) -> int:
    """Count files in a folder."""
    return len(list_files(folder))


def find_file(filename: str) -> Optional[str]:
    """Find a file in any vault folder. Returns full path or None."""
    for folder_name, folder_path in FOLDERS.items():
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            return file_path
    return None


def get_file_location(filename: str) -> Optional[str]:
    """Get the folder name where a file is located."""
    for folder_name, folder_path in FOLDERS.items():
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            return folder_name
    return None


def move_file(filename: str, to_folder: str, from_folder: str = None) -> dict:
    """
    Move a file between vault folders.
    
    Args:
        filename: Name of file to move
        to_folder: Destination folder name
        from_folder: Source folder (optional, auto-detected if not provided)
    
    Returns:
        dict: {'success': bool, 'message': str, 'source': str, 'destination': str}
    """
    ensure_folders()
    
    # Validate destination folder
    if to_folder not in FOLDERS:
        return {
            'success': False,
            'message': f'ERROR: Invalid destination folder: {to_folder}',
            'source': None,
            'destination': None
        }
    
    # Find the file
    if from_folder:
        source_path = os.path.join(FOLDERS.get(from_folder, ''), filename)
        if not os.path.exists(source_path):
            return {
                'success': False,
                'message': f'ERROR: File not found in {from_folder}: {filename}',
                'source': None,
                'destination': None
            }
    else:
        source_path = find_file(filename)
        if not source_path:
            return {
                'success': False,
                'message': f'ERROR: File not found in any vault folder: {filename}',
                'source': None,
                'destination': None
            }
        from_folder = get_file_location(filename)
    
    # Build destination path
    dest_path = os.path.join(FOLDERS[to_folder], filename)
    
    # Check if destination file already exists
    if os.path.exists(dest_path):
        # Add timestamp to avoid overwrite
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{base}_{timestamp}{ext}"
        dest_path = os.path.join(FOLDERS[to_folder], new_filename)
    
    try:
        # Move the file
        shutil.move(source_path, dest_path)
        
        return {
            'success': True,
            'message': f'SUCCESS: Moved {filename} from {from_folder} to {to_folder}',
            'source': os.path.join(from_folder, filename),
            'destination': dest_path
        }
        
    except PermissionError:
        return {
            'success': False,
            'message': f'ERROR: Permission denied moving {filename}',
            'source': source_path,
            'destination': dest_path
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'ERROR: {str(e)}',
            'source': source_path,
            'destination': dest_path
        }


def copy_file(filename: str, to_folder: str) -> dict:
    """
    Copy a file to another folder (keep original).
    
    Args:
        filename: Name of file to copy
        to_folder: Destination folder name
    
    Returns:
        dict: {'success': bool, 'message': str, 'destination': str}
    """
    ensure_folders()
    
    # Find the file
    source_path = find_file(filename)
    if not source_path:
        return {
            'success': False,
            'message': f'ERROR: File not found: {filename}',
            'destination': None
        }
    
    # Build destination path
    dest_path = os.path.join(FOLDERS[to_folder], filename)
    
    # Handle existing file
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{base}_copy_{timestamp}{ext}"
        dest_path = os.path.join(FOLDERS[to_folder], new_filename)
    
    try:
        shutil.copy2(source_path, dest_path)
        
        return {
            'success': True,
            'message': f'SUCCESS: Copied {filename} to {to_folder}',
            'destination': dest_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'ERROR: {str(e)}',
            'destination': None
        }


def get_status() -> dict:
    """Get file count status for all folders."""
    ensure_folders()
    status = {}
    for folder_name in FOLDERS.keys():
        status[folder_name] = count_files(folder_name)
    return status


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Manage task workflow between vault folders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Folders:
    Inbox           New files arrive here
    Needs_Action    Files requiring attention
    Plans           Generated action plans
    Done            Completed items
    Needs_Approval  Pending approvals
    Approved        Approved items
    Rejected        Rejected items

Examples:
    python move_task.py --file document.pdf --to Needs_Action
    python move_task.py --file task.md --to Done --from Inbox
    python move_task.py --list Inbox
    python move_task.py --status
        '''
    )
    
    # File operations
    parser.add_argument('--file', '-f', help='File to move/copy')
    parser.add_argument('--to', '-t', help='Destination folder')
    parser.add_argument('--from', '-F', dest='from_folder', help='Source folder (optional)')
    parser.add_argument('--copy', '-c', action='store_true', help='Copy instead of move')
    
    # List operations
    parser.add_argument('--list', '-l', metavar='FOLDER', help='List files in folder')
    
    # Status
    parser.add_argument('--status', '-s', action='store_true', help='Show folder status')
    
    # Output format
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    result = None
    
    # Handle status command
    if args.status:
        status = get_status()
        if args.json:
            import json
            print(json.dumps(status, indent=2))
        else:
            print("\nVault Folder Status")
            print("=" * 40)
            for folder, count in status.items():
                print(f"  {folder:20} {count} files")
            print("=" * 40)
        sys.exit(0)
    
    # Handle list command
    if args.list:
        if args.list not in FOLDERS:
            print(f"ERROR: Invalid folder: {args.list}")
            sys.exit(1)
        
        files = list_files(args.list)
        if args.json:
            import json
            print(json.dumps({'folder': args.list, 'files': files, 'count': len(files)}, indent=2))
        else:
            print(f"\nFiles in {args.list} ({len(files)}):")
            print("-" * 40)
            if files:
                for f in sorted(files):
                    print(f"  {f}")
            else:
                print("  (empty)")
            print("-" * 40)
        sys.exit(0)
    
    # Handle move/copy command
    if args.file:
        if not args.to:
            print("ERROR: --to folder is required")
            sys.exit(1)
        
        if args.to not in FOLDERS:
            print(f"ERROR: Invalid destination folder: {args.to}")
            sys.exit(1)
        
        if args.copy:
            result = copy_file(args.file, args.to)
        else:
            result = move_file(args.file, args.to, args.from_folder)
        
        if args.json:
            import json
            print(json.dumps(result, indent=2))
        else:
            print(result['message'])
            if result['success'] and result.get('destination'):
                print(f"Destination: {result['destination']}")
        
        sys.exit(0 if result['success'] else 1)
    
    # No valid command
    parser.print_help()
    sys.exit(1)


if __name__ == '__main__':
    main()
