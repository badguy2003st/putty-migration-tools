"""
Core business logic modules for PuTTY migration tools.

This package contains the core functionality that powers both
the CLI tools and the TUI interface.
"""

from .key_registry import KeyRegistry
from .auth_detection import detect_auth_method, AuthMethod

__all__ = [
    'KeyRegistry',
    'detect_auth_method',
    'AuthMethod',
]
