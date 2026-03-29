"""
File Operations Module - Safe file I/O with atomic writes and backups.

Provides utilities for secure file handling including:
- Atomic file writes (temp → rename)
- Automatic backups
- Permission management
- Path validation
"""

import tempfile
import shutil
import os
from pathlib import Path
from typing import Optional


def ensure_ppk_directory(ppk_dir: Path = Path("./ppk_keys")) -> dict:
    """
    Ensure ppk_keys directory exists, creating it if necessary.
    
    This function provides a consistent way to check and create the ppk_keys
    directory across both CLI and TUI modes, with appropriate messaging for each.
    
    Args:
        ppk_dir: Path to PPK keys directory (default: ./ppk_keys)
        
    Returns:
        dict with:
        - 'created': bool - True if directory was just created
        - 'path': Path - Absolute path to the directory
        - 'cli_message': str - Ready-to-print message for CLI mode
        - 'tui_title': str - Title for TUI modal dialog
        - 'tui_message': str - Message for TUI modal dialog
        
    Example (CLI):
        >>> check = ensure_ppk_directory()
        >>> if check['created']:
        ...     print(check['cli_message'])
        ...     return 0
        
    Example (TUI):
        >>> check = ensure_ppk_directory()
        >>> if check['created']:
        ...     self.push_screen(MessageBox(
        ...         title=check['tui_title'],
        ...         message=check['tui_message']
        ...     ))
    """
    ppk_dir = ppk_dir.resolve()
    
    if not ppk_dir.exists():
        ppk_dir.mkdir(parents=True, exist_ok=True)
        return {
            'created': True,
            'path': ppk_dir,
            # For CLI output
            'cli_message': (
                "📁 First-time setup complete!\n\n"
                f"   Created directory: {ppk_dir}\n\n"
                "Next steps:\n"
                "  1. Copy your .ppk files to this directory\n"
                "  2. Run this command again\n"
            ),
            # For TUI modal dialog
            'tui_title': "📁 First-Time Setup",
            'tui_message': (
                f"Created working directory:\n"
                f"  {ppk_dir}\n\n"
                "Place your .ppk files in this directory.\n\n"
                "What to do next:\n"
                "  • If headless: Press 'q' to quit\n"
                "  • Otherwise: Copy .ppk files there\n"
                "  • Then use 'Convert PPK Keys' from the menu\n\n"
                f"Directory: {ppk_dir.name}/"
            )
        }
    
    return {'created': False, 'path': ppk_dir}


def write_file_atomic(
    content: str,
    target_path: Path,
    backup: bool = True,
    permissions: Optional[int] = None
) -> None:
    """
    Write file atomically with optional backup.
    
    This ensures the file is either fully written or not written at all,
    preventing partial writes that could corrupt the file.
    
    Args:
        content: Content to write
        target_path: Final file path
        backup: Create .backup file if target exists
        permissions: Unix file permissions (e.g., 0o600 for private)
        
    Example:
        write_file_atomic(
            "Host example\\n  HostName 192.168.1.1",
            Path("~/.ssh/config"),
            backup=True,
            permissions=0o644
        )
    """
    target_path = Path(target_path).expanduser().resolve()
    
    # Create parent directory if needed
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup if file exists
    if backup and target_path.exists():
        backup_path = target_path.with_suffix(target_path.suffix + '.backup')
        shutil.copy2(target_path, backup_path)
    
    # Write to temp file first (in same directory for atomic rename)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=target_path.parent,
        delete=False,
        prefix='.tmp_',
        suffix=target_path.suffix,
        encoding='utf-8'
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    # Set permissions if specified
    if permissions is not None:
        os.chmod(tmp_path, permissions)
    
    # Atomic rename (replaces target if exists)
    tmp_path.replace(target_path)


def append_file_atomic(
    content: str,
    target_path: Path,
    backup: bool = True,
    separator: str = "\n"
) -> None:
    """
    Append content to a file atomically.
    
    Args:
        content: Content to append
        target_path: File to append to
        backup: Create backup before modifying
        separator: Separator to add before content
        
    Example:
        append_file_atomic(
            "Host newserver\\n  HostName 10.0.0.1",
            Path("~/.ssh/config")
        )
    """
    target_path = Path(target_path).expanduser().resolve()
    
    # Read existing content if file exists
    existing_content = ""
    if target_path.exists():
        existing_content = target_path.read_text(encoding='utf-8')
    
    # Combine content
    if existing_content and not existing_content.endswith('\n'):
        new_content = existing_content + separator + content
    elif existing_content:
        new_content = existing_content + content
    else:
        new_content = content
    
    # Write atomically
    write_file_atomic(new_content, target_path, backup=backup)


def ensure_directory(directory: Path, mode: int = 0o755) -> None:
    """
    Ensure a directory exists with specific permissions.
    
    Args:
        directory: Directory path to create
        mode: Directory permissions (default: 0o755)
        
    Example:
        ensure_directory(Path("~/.ssh"), mode=0o700)
    """
    directory = Path(directory).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True, mode=mode)


def safe_delete(file_path: Path, secure: bool = False) -> bool:
    """
    Safely delete a file.
    
    Args:
        file_path: File to delete
        secure: If True, overwrite with zeros before deleting (slower)
        
    Returns:
        True if file was deleted
        
    Example:
        # Regular delete
        safe_delete(Path("temp.txt"))
        
        # Secure delete (overwrite first)
        safe_delete(Path("private_key.ppk"), secure=True)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False
    
    try:
        if secure:
            # Overwrite with zeros
            size = file_path.stat().st_size
            with open(file_path, 'wb') as f:
                f.write(b'\x00' * size)
        
        # Delete the file
        file_path.unlink()
        return True
        
    except Exception:
        return False


def get_safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Convert a string to a safe filename.
    
    Removes/replaces characters that are problematic in filenames.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Safe filename string
        
    Example:
        >>> get_safe_filename("my server: production")
        'my_server_production'
    """
    # Characters to remove/replace
    unsafe_chars = '<>:"/\\|?*'
    
    safe = filename
    for char in unsafe_chars:
        safe = safe.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    safe = safe.strip(). strip('.')
    
    # Collapse multiple underscores
    while '__' in safe:
        safe = safe.replace('__', '_')
    
    # Truncate to max length
    if len(safe) > max_length:
        safe = safe[:max_length]
    
    return safe


def validate_path_safe(path: Path, allowed_dir: Optional[Path] = None) -> bool:
    """
    Validate that a path is safe to write to.
    
    Checks for directory traversal attempts and ensures path is within
    allowed directory if specified.
    
    Args:
        path: Path to validate
        allowed_dir: If specified, path must be within this directory
        
    Returns:
        True if path is safe
        
    Example:
        # Check path doesn't escape home directory
        validate_path_safe(
            Path("~/.ssh/config"),
            allowed_dir=Path("~/.ssh")
        )
    """
    path = Path(path).expanduser().resolve()
    
    # Check for directory traversal
    if '..' in path.parts:
        return False
    
    # If allowed_dir specified, ensure path is within it
    if allowed_dir:
        allowed_dir = Path(allowed_dir).expanduser().resolve()
        try:
            path.relative_to(allowed_dir)
        except ValueError:
            # Path is not within allowed_dir
            return False
    
    return True


def merge_ssh_config(
    new_entries: str,
    config_path: Path,
    interactive: bool = True
) -> tuple[bool, str]:
    """
    Merge new entries into SSH config file.
    
    Args:
        new_entries: New SSH config entries to add
        config_path: Path to SSH config file
        interactive: If True, ask user before merging
        
    Returns:
        Tuple of (success, message)
        
    Example:
        success, msg = merge_ssh_config(
            "Host myserver\\n  HostName 192.168.1.1",
            Path("~/.ssh/config"),
            interactive=False
        )
    """
    config_path = Path(config_path).expanduser().resolve()
    
    # If file doesn't exist, just create it
    if not config_path.exists():
        write_file_atomic(new_entries, config_path, backup=False, permissions=0o644)
        return True, f"Created new SSH config at {config_path}"
    
    # File exists - append to it
    try:
        # Read existing content
        existing = config_path.read_text(encoding='utf-8')
        
        # Check if any entries already exist (basic check)
        new_hosts = [line.strip() for line in new_entries.split('\n') 
                     if line.strip().startswith('Host ')]
        existing_hosts = [line.strip() for line in existing.split('\n')
                         if line.strip().startswith('Host ')]
        
        duplicates = set(new_hosts) & set(existing_hosts)
        
        if duplicates and interactive:
            return False, f"Duplicate hosts found: {', '.join(duplicates)}"
        
        # Append new entries
        append_file_atomic(
            "\n# Added by PuTTY Migration Tools\n" + new_entries,
            config_path,
            backup=True
        )
        
        return True, f"Merged entries into {config_path}"
        
    except Exception as e:
        return False, f"Error merging config: {str(e)}"
