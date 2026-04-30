"""
Unified PPK Parser - Support for both PPK v2 and v3 formats.

This module provides a native Python implementation for PPK conversion:
- PPK v2: Uses custom ppk_v2_crypto implementation
- PPK v3: Uses custom Argon2id implementation

Architecture is designed to be future-proof for v1.0.5 features:
- Multi-password support (passwords parameter)
- Re-encryption support (keep_encryption parameter)
- Smart password fallback
"""

from typing import Optional, List
from dataclasses import dataclass

from .ppk_v2_crypto import ppk_v2_to_openssh
from .ppk_v3_crypto import (
    ppk_v3_to_openssh,
    check_argon2_available
)


@dataclass
class PPKInfo:
    """PPK file metadata extracted from headers."""
    
    version: int
    """PPK format version (2 or 3)"""
    
    key_type: str
    """Key algorithm: 'ssh-rsa', 'ssh-ed25519', etc."""
    
    is_encrypted: bool
    """Whether the private key is encrypted"""
    
    encryption_type: Optional[str] = None
    """Encryption algorithm: 'aes256-cbc', 'none', etc."""
    
    comment: Optional[str] = None
    """User comment from PPK file"""


@dataclass
class DecryptionResult:
    """Result of PPK decryption/conversion attempt."""
    
    success: bool
    """Whether conversion succeeded"""
    
    openssh_key: Optional[str] = None
    """OpenSSH private key (if successful)"""
    
    error: Optional[str] = None
    """Error message (if failed)"""
    
    was_encrypted: bool = False
    """Whether the key was encrypted"""
    
    ppk_version: Optional[int] = None
    """Detected PPK version (2 or 3)"""
    
    # Future v1.0.5 feature:
    password_index: Optional[int] = None
    """Which password from list succeeded (for multi-password support)"""
    
    password_used: Optional[str] = None
    """v1.1.0: Password that successfully decrypted the key (for re-encryption)"""


def detect_ppk_info(ppk_content: str) -> PPKInfo:
    """
    Detect PPK version and extract metadata from file content.
    
    This examines the header to determine PPK format version and
    extract key metadata without full parsing.
    
    Enhanced in v1.1.0 with better error detection:
    - SSH2 PUBLIC KEY detection (skip message)
    - OpenSSH format detection (already converted)
    - SSH-1 detection (obsolete warning)
    - DSA detection (deprecated warning)
    
    Args:
        ppk_content: Full PPK file content as string
        
    Returns:
        PPKInfo object with version and metadata
        
    Raises:
        ValueError: If format is unrecognized or invalid
        
    Example:
        info = detect_ppk_info(ppk_content)
        if info.version == 3:
            print("Modern PPK v3 format detected")
    """
    lines = ppk_content.strip().split('\n')
    if not lines:
        raise ValueError("Empty file")
    
    first_line = lines[0].strip()
    
    # Detect non-PPK formats (Phase 4: Better error detection)
    if '---- BEGIN SSH2 PUBLIC KEY ----' in ppk_content:
        raise ValueError(
            "This is an SSH2 public key (.pub), not a private key.\n"
            "Public keys don't need conversion.\n"
            "Tip: Remove public keys from ppk_keys/ directory."
        )
    
    if '-----BEGIN OPENSSH PRIVATE KEY-----' in ppk_content:
        raise ValueError(
            "This key is already in OpenSSH format.\n"
            "No conversion needed."
        )
    
    if first_line.startswith('SSH PRIVATE KEY FILE FORMAT'):
        raise ValueError(
            "SSH-1 protocol is obsolete (deprecated since ~2001).\n"
            "Please generate a new RSA or Ed25519 key."
        )
    
    # Parse PPK version
    if first_line.startswith('PuTTY-User-Key-File-3:'):
        version = 3
        key_type = first_line.split(':', 1)[1].strip()
    elif first_line.startswith('PuTTY-User-Key-File-2:'):
        version = 2
        key_type = first_line.split(':', 1)[1].strip()
    else:
        raise ValueError(
            f"Unrecognized format. Expected PPK v2 or v3.\n"
            f"First line: {first_line[:60]}"
        )
    
    # Check for unsupported key types (Phase 4)
    if key_type == 'ssh-dss':
        raise ValueError(
            "DSA keys are not supported (deprecated since 2015, insecure).\n"
            "Please generate a new RSA or Ed25519 key."
        )
    
    # Supported types (v1.1.0)
    supported_types = [
        'ssh-rsa',
        'ssh-ed25519',
        'ssh-ed448',  # Note: Limited cryptography library support
        'ecdsa-sha2-nistp256',
        'ecdsa-sha2-nistp384',
        'ecdsa-sha2-nistp521'
    ]
    
    if key_type not in supported_types:
        raise ValueError(
            f"Unsupported key type: {key_type}\n"
            f"Supported: RSA, Ed25519, Ed448, ECDSA (P-256/384/521)"
        )
    
    # Extract additional metadata
    encryption = None
    is_encrypted = False
    comment = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('Encryption:'):
            encryption = line.split(':', 1)[1].strip()
            is_encrypted = (encryption != 'none')
        
        elif line.startswith('Comment:'):
            comment = line.split(':', 1)[1].strip()
    
    return PPKInfo(
        version=version,
        key_type=key_type,
        is_encrypted=is_encrypted,
        encryption_type=encryption,
        comment=comment
    )


def decrypt_ppk(
    ppk_content: str,
    password: Optional[str] = None,
    passwords: Optional[List[str]] = None,
    keep_encryption: bool = False,
) -> DecryptionResult:
    """
    Unified decryption for PPK v2 and v3 formats.
    
    This is the main entry point for PPK conversion. It automatically
    detects the PPK version and routes to the appropriate handler.
    
    v1.1.0 Features:
    - Multi-password support: Try multiple passwords automatically
    - Smart password handling: Ignore password on unencrypted keys
    
    Args:
        ppk_content: Full PPK file content as string
        password: Single password for encrypted keys (None/empty for unencrypted)
        passwords: List of passwords to try (v1.1.0 feature)
        keep_encryption: Re-encrypt output key (v1.1.0 feature)
        
    Returns:
        DecryptionResult with openssh_key or error message.
        If passwords list was used, password_index indicates which one worked.
        
    Example:
        # Unencrypted key
        result = decrypt_ppk(ppk_content)
        
        # Encrypted key with single password
        result = decrypt_ppk(ppk_content, password="mypassword")
        
        # Try multiple passwords (v1.1.0)
        result = decrypt_ppk(ppk_content, passwords=["pass1", "pass2", "pass3"])
        if result.success and result.password_index:
            print(f"Password #{result.password_index} worked!")
    """
    try:
        # Detect PPK version and metadata
        info = detect_ppk_info(ppk_content)
        
        # Multi-password support (v1.1.0)
        if passwords and len(passwords) > 0:
            return _try_multiple_passwords(ppk_content, passwords, info)
        
        # Single password or no password
        if info.version == 3:
            return _decrypt_ppk_v3(ppk_content, password, info)
        elif info.version == 2:
            return _decrypt_ppk_v2(ppk_content, password, info)
        else:
            return DecryptionResult(
                success=False,
                error=f"Unsupported PPK version: {info.version}",
                ppk_version=info.version
            )
    
    except Exception as e:
        return DecryptionResult(
            success=False,
            error=f"Failed to parse PPK file: {str(e)}"
        )


def _try_multiple_passwords(
    ppk_content: str,
    passwords: List[str],
    info: PPKInfo
) -> DecryptionResult:
    """
    Try decrypting with multiple passwords until one succeeds.
    
    v1.1.0 Feature: Multi-password file support
    v1.1.0 FIX: Preserve structural errors (Ed448, DSA, etc.) instead of "passwords failed"
    
    Args:
        ppk_content: PPK file content
        passwords: List of passwords to try
        info: Detected PPK metadata
        
    Returns:
        DecryptionResult with password_index set to which password worked (1-indexed)
    """
    if not info.is_encrypted:
        # Key is not encrypted - try without password first
        if info.version == 3:
            result = _decrypt_ppk_v3(ppk_content, None, info)
        else:
            result = _decrypt_ppk_v2(ppk_content, None, info)
        
        if result.success:
            result.password_index = 0  # 0 = no password needed
            return result
        else:
            # Unencrypted key failed - return the actual error (Ed448, DSA, etc.)
            return result
    
    # Try each password
    last_error = None
    for i, pwd in enumerate(passwords, 1):
        if info.version == 3:
            result = _decrypt_ppk_v3(ppk_content, pwd, info)
        else:
            result = _decrypt_ppk_v2(ppk_content, pwd, info)
        
        if result.success:
            result.password_index = i  # 1-indexed for user display
            result.password_used = pwd  # v1.1.0: Store for re-encryption
            return result
        
        # Save error for analysis
        last_error = result.error if result.error else "Unknown error"
    
    # All passwords failed - check if it's a structural error (not password-related)
    if last_error:
        # List of structural errors that should NOT be replaced with "passwords failed"
        structural_errors = [
            "Ed448",
            "not yet supported",
            "DSA",
            "deprecated",
            "SSH2 public key",
            "already in OpenSSH",
            "Unsupported key type",
            "Invalid",
            "corrupt"
        ]
        
        # If any structural error keyword found, preserve the original error
        if any(keyword in last_error for keyword in structural_errors):
            return DecryptionResult(
                success=False,
                error=last_error,  # Preserve the specific error!
                was_encrypted=info.is_encrypted,
                ppk_version=info.version
            )
    
    # Generic password failure
    return DecryptionResult(
        success=False,
        error=f"None of the {len(passwords)} passwords worked",
        was_encrypted=info.is_encrypted,
        ppk_version=info.version
    )


def _decrypt_ppk_v2(
    ppk_content: str,
    password: Optional[str],
    info: PPKInfo
) -> DecryptionResult:
    """
    Handle PPK v2 format using custom ppk_v2_crypto implementation.
    
    v1.1.0: Custom implementation supports RSA, Ed25519, ECDSA.
    Native implementation - no external dependencies.
    
    Smart password handling: If password is provided but key
    is unencrypted, automatically works without error.
    """
    try:
        # Convert using custom implementation
        openssh_key = ppk_v2_to_openssh(
            ppk_content,
            password if password else ''
        )
        
        return DecryptionResult(
            success=True,
            openssh_key=openssh_key,
            was_encrypted=info.is_encrypted,
            ppk_version=2,
            password_used=password if info.is_encrypted else None
        )
    
    except ValueError as e:
        # Expected errors from our parser (already user-friendly)
        return DecryptionResult(
            success=False,
            error=str(e),
            was_encrypted=info.is_encrypted,
            ppk_version=2
        )
    
    except Exception as e:
        # Unexpected errors
        return DecryptionResult(
            success=False,
            error=f"PPK v2 conversion failed: {str(e)}",
            was_encrypted=info.is_encrypted,
            ppk_version=2
        )


def _decrypt_ppk_v3(
    ppk_content: str,
    password: Optional[str],
    info: PPKInfo
) -> DecryptionResult:
    """
    Handle PPK v3 format using custom Argon2id implementation.
    
    This uses our ppk_v3_crypto module with Argon2id KDF.
    
    Smart password handling (v1.1.0): If password is provided but key
    is unencrypted, automatically works without error.
    """
    if not check_argon2_available():
        return DecryptionResult(
            success=False,
            error=(
                "argon2pure library required for PPK v3 decryption. "
                "Install with: pip install argon2pure"
            ),
            was_encrypted=info.is_encrypted,
            ppk_version=3
        )
    
    try:
        # PPK v3 requires password if encrypted
        if info.is_encrypted and not password:
            return DecryptionResult(
                success=False,
                error="PPK v3 key is encrypted - password required",
                was_encrypted=True,
                ppk_version=3
            )
        
        # Convert using custom implementation
        # Smart handling: Pass password even if key is unencrypted (will be ignored)
        openssh_key = ppk_v3_to_openssh(
            ppk_content,
            password if password else ''
        )
        
        return DecryptionResult(
            success=True,
            openssh_key=openssh_key,
            was_encrypted=info.is_encrypted,
            ppk_version=3,
            password_used=password if info.is_encrypted else None
        )
    
    except ValueError as e:
        # Smart password handling: If password provided but key unencrypted, retry
        error_str = str(e).lower()
        
        if password and not info.is_encrypted and ("password" in error_str or "required" in error_str):
            # Retry without password
            try:
                openssh_key = ppk_v3_to_openssh(ppk_content, '')
                return DecryptionResult(
                    success=True,
                    openssh_key=openssh_key,
                    was_encrypted=False,
                    ppk_version=3
                )
            except:
                pass  # Fall through to original error
        
        # Expected errors from our parser
        return DecryptionResult(
            success=False,
            error=str(e),
            was_encrypted=info.is_encrypted,
            ppk_version=3
        )
    
    except Exception as e:
        # Unexpected errors
        return DecryptionResult(
            success=False,
            error=f"PPK v3 decryption failed: {str(e)}",
            was_encrypted=info.is_encrypted,
            ppk_version=3
        )


def get_ppk_version(ppk_content: str) -> Optional[int]:
    """
    Quick check to get PPK version without full parsing.
    
    Args:
        ppk_content: PPK file content
        
    Returns:
        Version number (2 or 3) or None if unrecognized
    """
    try:
        info = detect_ppk_info(ppk_content)
        return info.version
    except Exception:
        return None
