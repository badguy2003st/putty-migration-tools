"""
Utility functions and helper modules.
"""

from .platform import get_platform, is_windows, is_linux
from .security import SecureString, secure_file_permissions, cleanup_temp_files

__all__ = [
    'get_platform',
    'is_windows',
    'is_linux',
    'SecureString',
    'secure_file_permissions',
    'cleanup_temp_files',
]
