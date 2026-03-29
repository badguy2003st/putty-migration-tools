"""
Security utilities for handling sensitive data.

Includes:
- SecureString class for memory-safe string handling
- File permission management
- Temporary file cleanup
"""

import os
import stat
import tempfile
import atexit
import shutil
from typing import Optional
from pathlib import Path


class SecureString:
    """
    Store sensitive strings with zeroing capability.
    
    This class helps minimize exposure of sensitive data in memory
    by zeroing out the data when the object is deleted.
    
    Example:
        password = SecureString("my_secret_password")
        # Use password.get() when needed
        value = password.get()
        # Automatically zeroed when deleted
        del password
    """
    
    def __init__(self, value: str):
        """
        Initialize with a sensitive string value.
        
        Args:
            value: The sensitive string to protect
        """
        self._data = bytearray(value.encode('utf-8'))
    
    def get(self) -> str:
        """
        Retrieve the string value.
        
        Returns:
            The original string value
        """
        return self._data.decode('utf-8')
    
    def __del__(self):
        """Zero out memory before deletion."""
        if hasattr(self, '_data'):
            # Zero out the memory
            for i in range(len(self._data)):
                self._data[i] = 0
            del self._data
    
    def __repr__(self) -> str:
        """Don't leak the value in repr."""
        return "<SecureString(****)>"
    
    def __str__(self) -> str:
        """Don't leak the value in str."""
        return "****"


def secure_file_permissions(filepath: str, is_private: bool = True) -> None:
    """
    Set secure permissions on sensitive files.
    
    Args:
        filepath: Path to the file
        is_private: If True, set 600 (owner only). If False, set 644 (readable by all)
        
    Example:
        # Private key: only owner can read/write
        secure_file_permissions("~/.ssh/id_rsa", is_private=True)
        
        # Public key: readable by all
        secure_file_permissions("~/.ssh/id_rsa.pub", is_private=False)
    """
    filepath = os.path.expanduser(filepath)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if is_private:
        # Private: owner read/write only (600)
        os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)
    else:
        # Public: owner rw, group/others read (644)
        os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


# Global registry of temporary directories to clean up
_temp_dirs: list = []


def create_secure_temp_dir(prefix: str = "putty_migration_") -> str:
    """
    Create a temporary directory with secure permissions.
    
    The directory is automatically registered for cleanup on exit.
    
    Args:
        prefix: Prefix for the temporary directory name
        
    Returns:
        Path to the created temporary directory
        
    Example:
        temp_dir = create_secure_temp_dir()
        # Use temp_dir for temporary files
        # Automatically cleaned up on exit
    """
    # Create with mode 0o700 (owner only)
    temp_dir = tempfile.mkdtemp(prefix=prefix, mode=0o700)
    _temp_dirs.append(temp_dir)
    return temp_dir


def cleanup_temp_files() -> None:
    """
    Clean up all registered temporary directories.
    
    This is automatically called on script exit via atexit.
    """
    global _temp_dirs
    
    for temp_dir in _temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            # Ignore cleanup errors
            pass
    
    _temp_dirs.clear()


# Register cleanup on exit
atexit.register(cleanup_temp_files)


def clear_environment_variable(var_name: str) -> None:
    """
    Safely clear an environment variable.
    
    Args:
        var_name: Name of the environment variable to clear
        
    Example:
        # Clear Bitwarden session after use
        clear_environment_variable('BW_SESSION')
    """
    if var_name in os.environ:
        del os.environ[var_name]


def show_security_reminder() -> None:
    """Display security cleanup recommendations to the user."""
    print("\n" + "=" * 60)
    print("🔒 SECURITY REMINDERS")
    print("=" * 60)
    print("\nAfter successful conversion:")
    print("  ✅ Your keys are now in ~/.ssh/")
    print("  ⚠️  Original .ppk files still exist in ./ppk_keys/")
    print("  ⚠️  Original PuTTY Registry entries still exist")
    print("\n📋 Cleanup recommendations:")
    print("  1. Backup .ppk files to secure location")
    print("  2. Securely delete .ppk files after verification:")
    print("     shred -vfz -n 3 ./ppk_keys/*.ppk  # Linux")
    print("     del /P .\\ppk_keys\\*.ppk  # Windows (basic)")
    print("  3. Clear PuTTY sessions if no longer needed:")
    print("     Registry: HKCU:\\Software\\SimonTatham\\PuTTY\\Sessions")
    print("  4. Verify BW_SESSION is cleared (if using Bitwarden):")
    print("     echo $BW_SESSION  # Should be empty")
    print("=" * 60 + "\n")
