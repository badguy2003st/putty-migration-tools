"""
Windows Registry reader for PuTTY sessions.

This module reads PuTTY session data from the Windows Registry.
On non-Windows platforms, it provides stub implementations.
"""

import os
import urllib.parse
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Conditional import of winreg (Windows only)
try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

from ..utils.platform import is_windows


@dataclass
class PuttySession:
    """Represents a PuTTY session with all its properties."""
    
    name: str
    """Session name (URL-decoded)"""
    
    hostname: str
    """Hostname or IP address"""
    
    port: int = 22
    """SSH port number"""
    
    username: str = ""
    """SSH username"""
    
    protocol: str = "ssh"
    """Protocol type (ssh, telnet, etc.)"""
    
    public_key_file: str = ""
    """Path to PPK file (if using key auth)"""
    
    auth_ki: int = 0
    """Keyboard-interactive authentication (0 or 1)"""
    
    auth_tis: int = 0
    """TIS authentication (0 or 1)"""
    
    raw_data: Dict = field(default_factory=dict)
    """Raw registry data for this session"""
    
    @property
    def is_ssh(self) -> bool:
        """Check if this is an SSH session."""
        return self.protocol.lower() == "ssh"


def read_putty_sessions() -> List[PuttySession]:
    """
    Read all PuTTY sessions from Windows Registry.
    
    Returns:
        List of PuttySession objects
        
    Raises:
        RuntimeError: If not running on Windows
        OSError: If Registry cannot be accessed
        
    Example:
        sessions = read_putty_sessions()
        for session in sessions:
            if session.is_ssh:
                print(f"{session.name} -> {session.hostname}:{session.port}")
    """
    if not is_windows():
        raise RuntimeError("PuTTY Registry reading is only supported on Windows")
    
    if not HAS_WINREG:
        raise RuntimeError("winreg module not available")
    
    registry_path = r"Software\SimonTatham\PuTTY\Sessions"
    sessions = []
    
    try:
        # Open PuTTY Sessions registry key
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            # Enumerate all subkeys (sessions)
            index = 0
            while True:
                try:
                    session_name_encoded = winreg.EnumKey(key, index)
                    index += 1
                    
                    # Skip "Default Settings"
                    if session_name_encoded == "Default%20Settings":
                        continue
                    
                    # Read session data
                    session = _read_session_data(registry_path, session_name_encoded)
                    if session:
                        sessions.append(session)
                        
                except OSError:
                    # No more items
                    break
                    
    except FileNotFoundError:
        # Registry key doesn't exist - no PuTTY sessions
        return []
    except OSError as e:
        raise OSError(f"Cannot access PuTTY Registry: {e}")
    
    return sessions


def _read_session_data(registry_path: str, session_name_encoded: str) -> Optional[PuttySession]:
    """
    Read data for a specific PuTTY session.
    
    Args:
        registry_path: Base registry path
        session_name_encoded: URL-encoded session name
        
    Returns:
        PuttySession object or None if invalid
    """
    # Decode session name (PuTTY URL-encodes special characters)
    session_name = urllib.parse.unquote(session_name_encoded)
    
    session_key_path = f"{registry_path}\\{session_name_encoded}"
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, session_key_path) as session_key:
            # Read all relevant values
            hostname = _read_registry_string(session_key, "HostName", "")
            port = _read_registry_int(session_key, "PortNumber", 22)
            username = _read_registry_string(session_key, "UserName", "")
            protocol = _read_registry_string(session_key, "Protocol", "ssh")
            public_key_file = _read_registry_string(session_key, "PublicKeyFile", "")
            auth_ki = _read_registry_int(session_key, "AuthKI", 0)
            auth_tis = _read_registry_int(session_key, "AuthTIS", 0)
            
            # Build raw data dictionary
            raw_data = {
                "HostName": hostname,
                "PortNumber": port,
                "UserName": username,
                "Protocol": protocol,
                "PublicKeyFile": public_key_file,
                "AuthKI": auth_ki,
                "AuthTIS": auth_tis,
            }
            
            return PuttySession(
                name=session_name,
                hostname=hostname,
                port=port,
                username=username,
                protocol=protocol,
                public_key_file=public_key_file,
                auth_ki=auth_ki,
                auth_tis=auth_tis,
                raw_data=raw_data
            )
            
    except OSError:
        # Cannot read this session
        return None


def _read_registry_string(key, value_name: str, default: str = "") -> str:
    """Read a string value from registry, return default if not found."""
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        return str(value) if value else default
    except OSError:
        return default


def _read_registry_int(key, value_name: str, default: int = 0) -> int:
    """Read an integer value from registry, return default if not found."""
    try:
        value, _ = winreg.QueryValueEx(key, value_name)
        return int(value) if value is not None else default
    except (OSError, ValueError):
        return default


def split_user_at_host(hostname: str, existing_username: str = "") -> tuple[str, str]:
    """
    Split user@host notation if present.
    
    Args:
        hostname: Hostname that may contain user@ prefix
        existing_username: Existing username from session
        
    Returns:
        Tuple of (hostname, username)
        
    Example:
        >>> split_user_at_host("admin@192.168.1.1", "")
        ('192.168.1.1', 'admin')
        
        >>> split_user_at_host("192.168.1.1", "root")
        ('192.168.1.1', 'root')
    """
    if "@" in hostname:
        parts = hostname.split("@", 1)
        if len(parts) == 2:
            user_part, host_part = parts
            # Only use the user@ part if no username was already set
            if not existing_username:
                return host_part, user_part
            else:
                return host_part, existing_username
    
    return hostname, existing_username


def count_putty_sessions() -> int:
    """
    Count the number of PuTTY sessions in the registry.
    
    Returns:
        Number of sessions (excluding Default Settings)
    """
    if not is_windows() or not HAS_WINREG:
        return 0
    
    try:
        sessions = read_putty_sessions()
        return len(sessions)
    except Exception:
        return 0
