"""
PuTTY Authentication Method Detection.

Detects which authentication method a PuTTY session uses:
1. Password only (no key)
2. Direct key (PPK file path in session)
3. Pageant (external SSH agent)
"""

import os
from typing import Tuple, Optional, Literal
from dataclasses import dataclass

AuthMethod = Literal["password", "key", "pageant"]


@dataclass
class AuthInfo:
    """Information about detected authentication method."""
    
    method: AuthMethod
    """Authentication method: 'password', 'key', or 'pageant'"""
    
    key_file: Optional[str] = None
    """Path to PPK file (only for 'key' method)"""
    
    confidence: float = 1.0
    """Confidence level in the detection (0.0 to 1.0)"""
    
    notes: str = ""
    """Additional notes about the detection"""


def detect_auth_method(session_data: dict) -> AuthInfo:
    """
    Detect authentication method from PuTTY session data.
    
    Args:
        session_data: Dictionary containing PuTTY session properties:
            - PublicKeyFile: Path to PPK file (str, may be empty)
            - AuthKI: Keyboard-interactive auth enabled (int, 0 or 1)
            - AuthTIS: TIS auth enabled (int, 0 or 1)
            
    Returns:
        AuthInfo object with detected method and details
        
    Examples:
        # Scenario 1: Password only
        >>> session = {"PublicKeyFile": "", "AuthKI": 1}
        >>> auth = detect_auth_method(session)
        >>> auth.method
        'password'
        
        # Scenario 2: Direct key
        >>> session = {"PublicKeyFile": "C:\\Keys\\my.ppk", "AuthKI": 0}
        >>> auth = detect_auth_method(session)
        >>> auth.method
        'key'
        >>> auth.key_file
        'C:\\Keys\\my.ppk'
        
        # Scenario 3: Pageant
        >>> session = {"PublicKeyFile": "", "AuthKI": 0}
        >>> auth = detect_auth_method(session)
        >>> auth.method
        'pageant'
    """
    ppk_file = session_data.get("PublicKeyFile", "").strip()
    auth_ki = session_data.get("AuthKI", 0)  # Keyboard-interactive
    auth_tis = session_data.get("AuthTIS", 0)  # TIS authentication
    
    # Scenario 2: Explicit PPK file specified
    if ppk_file:
        # Check if file exists
        if os.path.exists(ppk_file):
            return AuthInfo(
                method="key",
                key_file=ppk_file,
                confidence=1.0,
                notes="Direct key file specified in session"
            )
        else:
            # File specified but doesn't exist
            return AuthInfo(
                method="key",
                key_file=ppk_file,
                confidence=0.5,
                notes=f"Key file specified but not found: {ppk_file}"
            )
    
    # Scenario 3: Pageant (no key file, but key auth likely)
    # If keyboard-interactive is disabled, likely using key auth via Pageant
    if auth_ki == 0 and auth_tis == 0:
        return AuthInfo(
            method="pageant",
            key_file=None,
            confidence=0.8,
            notes="No key file specified, keyboard-interactive disabled (likely Pageant)"
        )
    
    # Scenario 1: Password only (keyboard-interactive enabled)
    if auth_ki == 1:
        return AuthInfo(
            method="password",
            key_file=None,
            confidence=1.0,
            notes="Keyboard-interactive authentication enabled"
        )
    
    # Default: assume password if uncertain
    return AuthInfo(
        method="password",
        key_file=None,
        confidence=0.5,
        notes="Authentication method unclear, defaulting to password"
    )


def format_auth_info(auth: AuthInfo) -> str:
    """
    Format authentication info for display.
    
    Args:
        auth: AuthInfo object
        
    Returns:
        Human-readable string describing the authentication method
        
    Example:
        >>> auth = detect_auth_method(session)
        >>> print(format_auth_info(auth))
        'Auth: Direct key (C:\\Keys\\my.ppk)'
    """
    if auth.method == "password":
        return "Auth: Password"
    elif auth.method == "key":
        filename = os.path.basename(auth.key_file) if auth.key_file else "unknown"
        return f"Auth: Direct key ({filename})"
    elif auth.method == "pageant":
        return "Auth: Pageant (external agent)"
    else:
        return "Auth: Unknown"
