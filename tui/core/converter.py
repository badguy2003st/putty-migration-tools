"""
PPK Converter Module - Async conversion of PPK keys to OpenSSH format.

This module uses the pure Python 'puttykeys' library for converting
PuTTY .ppk files to OpenSSH format. Works cross-platform without
external tools.
"""

import asyncio
import os
import stat
import shutil
from pathlib import Path
from typing import Callable, Optional, List, Literal, Dict, Any
from dataclasses import dataclass

try:
    import puttykeys
except ImportError:
    puttykeys = None

# Import new unified PPK parser (v1.0.4+)
from .ppk_parser import decrypt_ppk, detect_ppk_info, get_ppk_version

# Import platform detection for line ending handling
from ..utils.platform import get_platform


@dataclass
class ConversionResult:
    """Result of a PPK conversion operation."""
    
    success: bool
    """Whether the conversion succeeded"""
    
    ppk_file: str
    """Original PPK file path"""
    
    output_file: Optional[str] = None
    """Output file path (if successful)"""
    
    error: Optional[str] = None
    """Error message (if failed)"""
    
    format: str = "openssh"
    """Output format: openssh, ssh.com, etc."""
    
    password_index: Optional[int] = None
    """Which password from list succeeded (v1.1.0, 0=unencrypted, 1+=password number)"""


class ConversionError(Exception):
    """Exception raised when PPK conversion fails."""
    pass


def normalize_key_name(name: str) -> str:
    """
    Normalize key names for filesystem compatibility.
    
    Replaces spaces with hyphens to avoid path issues and improve
    compatibility with SSH config files.
    
    Args:
        name: Original key name (may contain spaces)
        
    Returns:
        Normalized name (spaces replaced with hyphens)
        
    Example:
        >>> normalize_key_name("bggaming.de dagobert23.de")
        'bggaming.de-dagobert23.de'
        
        >>> normalize_key_name("my server key")
        'my-server-key'
    """
    return name.replace(" ", "-")


def get_line_ending() -> str:
    """
    Get the appropriate line ending for the current platform.
    
    Returns:
        "\\r\\n" for Windows, "\\n" for Linux
        
    Example:
        ending = get_line_ending()
        # On Windows: "\\r\\n"
        # On Linux: "\\n"
    """
    platform_type = get_platform()
    if platform_type == "windows":
        return "\r\n"
    else:
        return "\n"


def write_key_file(file_path: Path, content: str, add_trailing_newline: bool = True) -> None:
    """
    Write a key file with platform-appropriate line endings.
    
    This ensures that SSH keys are written with the correct line endings
    for the target platform (CRLF on Windows, LF on Linux).
    
    Args:
        file_path: Path to the file to write
        content: Content to write (line endings will be normalized)
        add_trailing_newline: Whether to add a trailing newline (default: True)
        
    Example:
        write_key_file(Path("~/.ssh/id_rsa"), openssh_key_content)
    """
    line_ending = get_line_ending()
    
    # Normalize existing line endings to the platform-appropriate format
    # First normalize all line endings to \n, then convert to platform format
    normalized_content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Convert to platform-appropriate line endings
    if line_ending != '\n':
        normalized_content = normalized_content.replace('\n', line_ending)
    
    # Add trailing newline if requested
    if add_trailing_newline and not normalized_content.endswith(line_ending):
        normalized_content += line_ending
    
    # Write the file
    file_path.write_text(normalized_content, encoding='utf-8')


def detect_key_type(ppk_content: str) -> Optional[str]:
    """
    Detect the key type from PPK file content.
    
    Args:
        ppk_content: PPK file content
        
    Returns:
        Key type string (e.g., 'ssh-rsa', 'ssh-dss', 'ssh-ed25519') or None
    """
    for line in ppk_content.split('\n'):
        if line.startswith('PuTTY-User-Key-File-'):
            parts = line.split(':')
            if len(parts) >= 2:
                return parts[1].strip()
    return None


def interpret_conversion_error(error: Exception) -> str:
    """
    Convert puttykeys error to user-friendly text.
    
    Args:
        error: Exception from puttykeys
        
    Returns:
        User-friendly error message
    """
    error_str = str(error).lower()
    
    # Common error patterns
    if "password" in error_str or "passphrase" in error_str or "encrypted" in error_str:
        return "Key is encrypted - passphrase required"
    
    elif "invalid" in error_str or "corrupt" in error_str or "bad format" in error_str:
        return "Invalid or corrupted PPK file format"
    
    elif "unsupported" in error_str or "not supported" in error_str:
        return "Unsupported key type (only RSA and Ed25519 are supported)"
    
    elif "dsa" in error_str:
        return "DSA keys are not supported (use RSA or Ed25519)"
    
    elif "ecdsa" in error_str and "not ed25519" in error_str:
        return "ECDSA keys (except Ed25519) are not supported"
    
    elif "public key only" in error_str or "no private key" in error_str:
        return "File contains only public key (private key required)"
    
    # Return original error if no pattern matches
    return str(error)


async def check_puttykeys_available() -> bool:
    """
    Check if puttykeys library is available.
    
    Returns:
        True if puttykeys is installed
        
    Example:
        if not await check_puttykeys_available():
            print("Please install puttykeys: pip install puttykeys")
    """
    return puttykeys is not None


def encrypt_openssh_key(openssh_key: str, password: str) -> str:
    """
    Encrypt an OpenSSH private key with a password.
    
    v1.1.0: Re-encryption support for keeping original PPK password.
    Uses cryptography library's best_available_encryption().
    
    Args:
        openssh_key: Unencrypted OpenSSH private key
        password: Password to encrypt with
        
    Returns:
        Encrypted OpenSSH private key
        
    Raises:
        ValueError: If encryption fails
        
    Example:
        encrypted = encrypt_openssh_key(openssh_key, "mypassword")
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        # Load the unencrypted key
        private_key = serialization.load_ssh_private_key(
            openssh_key.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Re-serialize with encryption
        encrypted_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.BestAvailableEncryption(
                password.encode('utf-8')
            )
        )
        
        return encrypted_key.decode('utf-8')
        
    except Exception as e:
        raise ValueError(f"Failed to encrypt OpenSSH key: {str(e)}")


def extract_public_key_from_openssh(openssh_private_key: str) -> str:
    """
    Extract the public key from an OpenSSH private key.
    
    ⚠️ DEPRECATED: This function only works with true OpenSSH format keys.
    It FAILS with PEM format keys (which puttykeys produces).
    
    Use extract_public_key_from_ppk() from bitwarden_export.py instead,
    which extracts directly from PPK files (more reliable).
    
    OpenSSH private keys contain the public key in the footer comment.
    If not present, we'll generate it using cryptography library.
    
    Args:
        openssh_private_key: OpenSSH format private key string (NOT PEM!)
        
    Returns:
        OpenSSH format public key string, or empty string on failure
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        # Load the private key
        private_key = serialization.load_ssh_private_key(
            openssh_private_key.encode(),
            password=None,
            backend=default_backend()
        )
        
        # Extract public key
        public_key = private_key.public_key()
        
        # Serialize to OpenSSH format
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        
        return public_key_bytes.decode('utf-8')
        
    except Exception as e:
        # Fallback: return empty string if extraction fails
        return ""


async def convert_ppk_to_openssh(
    ppk_file: Path,
    output_file: Path,
    password: Optional[str] = None,
    passwords: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
    clean_format: bool = True,
    keep_encryption: bool = False
) -> ConversionResult:
    """
    Convert a PPK file to OpenSSH format using puttykeys library.
    
    Args:
        ppk_file: Input .ppk file path
        output_file: Output OpenSSH key file path
        password: Optional passphrase for encrypted PPK files
        progress_callback: Optional callback for progress updates (0-100)
        clean_format: Re-serialize using cryptography for guaranteed compatibility (default: True)
        
    Returns:
        ConversionResult object with status and details
        
    Raises:
        ConversionError: If puttykeys is not available or conversion fails
        
    Example:
        # Unencrypted key
        result = await convert_ppk_to_openssh(
            Path("./ppk_keys/mykey.ppk"),
            Path("~/.ssh/mykey")
        )
        
        # Encrypted key with password
        result = await convert_ppk_to_openssh(
            Path("./ppk_keys/encrypted.ppk"),
            Path("~/.ssh/encrypted"),
            password="my_passphrase"
        )
        
        # With clean format disabled (legacy behavior)
        result = await convert_ppk_to_openssh(
            Path("./ppk_keys/mykey.ppk"),
            Path("~/.ssh/mykey"),
            clean_format=False
        )
        
        if result.success:
            print(f"Converted to {result.output_file}")
    """
    ppk_file = Path(ppk_file).resolve()
    output_file = Path(output_file).expanduser().resolve()
    
    # Validate input file exists
    if not ppk_file.exists():
        return ConversionResult(
            success=False,
            ppk_file=str(ppk_file),
            error=f"PPK file not found: {ppk_file}"
        )
    
    # Check puttykeys is available
    if not await check_puttykeys_available():
        return ConversionResult(
            success=False,
            ppk_file=str(ppk_file),
            error="puttykeys library not found - please install: pip install puttykeys"
        )
    
    # Report initial progress
    if progress_callback:
        progress_callback(10)
    
    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if progress_callback:
        progress_callback(20)
    
    try:
        # Read PPK file content
        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        ppk_content = await loop.run_in_executor(
            None,
            lambda: ppk_file.read_text(encoding='utf-8')
        )
        
        if progress_callback:
            progress_callback(40)
        
        # Convert using unified PPK parser (supports v2 and v3)
        # v1.1.0: Supports multi-password file
        # Run in executor since it's CPU-intensive (especially for v3 Argon2id)
        result = await loop.run_in_executor(
            None,
            lambda: decrypt_ppk(ppk_content, password=password, passwords=passwords)
        )
        
        # Check if conversion failed
        if not result.success:
            return ConversionResult(
                success=False,
                ppk_file=str(ppk_file),
                error=result.error
            )
        
        openssh_key = result.openssh_key
        
        if progress_callback:
            progress_callback(70)
        
        # CRITICAL: Extract public key BEFORE re-encryption!
        # Encrypted keys cannot be used for public key extraction
        public_key_content = None
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            
            # Parse the decrypted private key
            private_key = serialization.load_ssh_private_key(
                openssh_key.encode(),
                password=None,
                backend=default_backend()
            )
            
            # Extract public key
            public_key = private_key.public_key()
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            )
            public_key_content = public_key_bytes.decode('utf-8')
        except Exception:
            # Public key extraction failed - not critical, continue
            pass
        
        # v1.1.0: Re-encrypt with original password if requested
        if keep_encryption and result.was_encrypted and result.password_used:
            try:
                openssh_key = await loop.run_in_executor(
                    None,
                    lambda: encrypt_openssh_key(openssh_key, result.password_used)
                )
            except Exception as e:
                # Re-encryption failed - log but continue with unencrypted key
                # This prevents data loss on encryption failure
                pass
        
        # Optional: Re-serialize with cryptography for guaranteed clean format
        # This is important for Bitwarden compatibility
        # NOTE: Skip if key was just encrypted (already in clean format)
        if clean_format and not (keep_encryption and result.was_encrypted):
            try:
                from .bitwarden_export import ensure_clean_openssh_format
                openssh_key = await loop.run_in_executor(
                    None,
                    lambda: ensure_clean_openssh_format(openssh_key)
                )
            except Exception as e:
                # If re-serialization fails, fall back to original puttykeys output
                # This preserves backward compatibility
                pass
        
        if progress_callback:
            progress_callback(80)
        
        # Write private key file with platform-appropriate line endings
        await loop.run_in_executor(
            None,
            lambda: write_key_file(output_file, openssh_key, add_trailing_newline=True)
        )
        
        # Set secure permissions (600 - owner read/write only)
        os.chmod(output_file, stat.S_IRUSR | stat.S_IWUSR)
        
        # Write public key file if extraction succeeded
        # BUG FIX: Use string concat to avoid with_suffix() bug with dots in filename
        if public_key_content:
            pub_file = Path(str(output_file) + '.pub')
            await loop.run_in_executor(
                None,
                lambda: write_key_file(pub_file, public_key_content, add_trailing_newline=True)
            )
            # Set public key permissions (644)
            os.chmod(pub_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        if progress_callback:
            progress_callback(100)
        
        return ConversionResult(
            success=True,
            ppk_file=str(ppk_file),
            output_file=str(output_file),
            password_index=getattr(result, 'password_index', None)
        )
        
    except Exception as e:
        # Make error more user-friendly
        friendly_error = interpret_conversion_error(e)
        
        return ConversionResult(
            success=False,
            ppk_file=str(ppk_file),
            error=friendly_error
        )


async def convert_ppk_to_public_key(
    ppk_file: Path,
    output_file: Path,
    password: Optional[str] = None,
    progress_callback: Optional[Callable[[int], None]] = None
) -> ConversionResult:
    """
    Extract the public key from a PPK file.
    
    This function extracts the public key DIRECTLY from the PPK file,
    which is more reliable than converting to OpenSSH first.
    
    Args:
        ppk_file: Input .ppk file path
        output_file: Output public key file path (.pub)
        password: Optional passphrase for encrypted PPK files (not needed for public key)
        progress_callback: Optional callback for progress updates (0-100)
        
    Returns:
        ConversionResult object with status and details
    """
    ppk_file = Path(ppk_file).resolve()
    output_file = Path(output_file).expanduser().resolve()
    
    if not ppk_file.exists():
        return ConversionResult(
            success=False,
            ppk_file=str(ppk_file),
            error=f"PPK file not found: {ppk_file}"
        )
    
    if progress_callback:
        progress_callback(20)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Import the direct PPK extraction function
        from .bitwarden_export import extract_public_key_from_ppk
        
        if progress_callback:
            progress_callback(50)
        
        # Extract public key DIRECTLY from PPK file (more reliable)
        loop = asyncio.get_event_loop()
        public_key = await loop.run_in_executor(
            None,
            lambda: extract_public_key_from_ppk(ppk_file)
        )
        
        if not public_key:
            return ConversionResult(
                success=False,
                ppk_file=str(ppk_file),
                error="Could not extract public key from PPK file"
            )
        
        if progress_callback:
            progress_callback(80)
        
        # Write public key to file with platform-appropriate line endings
        await loop.run_in_executor(
            None,
            lambda: write_key_file(output_file, public_key, add_trailing_newline=True)
        )
        
        # Set public key permissions (644)
        os.chmod(output_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        if progress_callback:
            progress_callback(100)
        
        return ConversionResult(
            success=True,
            ppk_file=str(ppk_file),
            output_file=str(output_file),
            format="public"
        )
        
    except Exception as e:
        friendly_error = interpret_conversion_error(e)
        
        return ConversionResult(
            success=False,
            ppk_file=str(ppk_file),
            error=friendly_error
        )


async def batch_convert_ppk_files(
    ppk_files: List[Path],
    output_dir: Path,
    password: Optional[str] = None,
    passwords: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    keep_encryption: bool = True
) -> List[ConversionResult]:
    """
    Convert multiple PPK files in batch.
    
    Args:
        ppk_files: List of PPK file paths to convert
        output_dir: Directory for output files
        password: Optional passphrase for encrypted PPK files (same for all)
        progress_callback: Optional callback(current, total, filename)
        keep_encryption: v1.1.0: Re-encrypt with original password (default: True)
        
    Returns:
        List of ConversionResult objects
        
    Example:
        results = await batch_convert_ppk_files(
            ppk_files=[Path("key1.ppk"), Path("key2.ppk")],
            output_dir=Path("~/.ssh/"),
            progress_callback=lambda cur, tot, name: print(f"{cur}/{tot}: {name}")
        )
        
        successful = sum(1 for r in results if r.success)
        print(f"Converted {successful}/{len(results)} keys")
    """
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    total = len(ppk_files)
    
    for i, ppk_file in enumerate(ppk_files, 1):
        ppk_file = Path(ppk_file)
        
        # Notify progress
        if progress_callback:
            progress_callback(i, total, ppk_file.name)
        
        # Generate output filename (remove .ppk extension + normalize spaces)
        output_name = normalize_key_name(ppk_file.stem)
        output_file = output_dir / output_name
        
        # Convert the file (v1.1.0: with multi-password support + re-encryption)
        result = await convert_ppk_to_openssh(
            ppk_file, output_file, password, passwords,
            keep_encryption=keep_encryption
        )
        results.append(result)
        
        # Also extract public key if private conversion succeeded
        if result.success:
            pub_file = output_dir / f"{output_name}.pub"
            await convert_ppk_to_public_key(ppk_file, pub_file, password)
    
    return results


def find_next_available_name(base_path: Path) -> Path:
    """
    Find next available filename with numeric suffix.
    
    If the file exists, tries appending .1, .2, .3, etc. until
    finding an available name.
    
    For public keys (.pub), the number is inserted BEFORE the .pub extension
    to maintain SSH compatibility (key.2.pub instead of key.pub.2).
    
    Args:
        base_path: Original file path
        
    Returns:
        Available path (may be same as input if doesn't exist)
        
    Example:
        find_next_available_name(Path("~/.ssh/oracle"))
        # If oracle exists → returns ~/.ssh/oracle.1
        
        find_next_available_name(Path("~/.ssh/oracle.pub"))
        # If oracle.pub exists → returns ~/.ssh/oracle.1.pub (NOT oracle.pub.1!)
    """
    if not base_path.exists():
        return base_path
    
    # Check if this is a public key file
    is_pub_key = base_path.name.endswith('.pub')
    
    counter = 1
    while True:
        if is_pub_key:
            # Insert number BEFORE .pub extension
            # unraid31.pub → unraid31.1.pub → unraid31.2.pub
            base_name = base_path.name[:-4]  # Remove .pub
            new_path = base_path.parent / f"{base_name}.{counter}.pub"
        else:
            # Normal file: append number at end
            # unraid31 → unraid31.1 → unraid31.2
            new_path = base_path.parent / f"{base_path.name}.{counter}"
        
        if not new_path.exists():
            return new_path
        counter += 1
        
        # Safety limit
        if counter > 999:
            raise ValueError(f"Too many conflicting files for {base_path.name}")


async def copy_key_to_ssh(
    source_file: Path,
    mode: Literal["rename", "overwrite", "skip"]
) -> Dict[str, Any]:
    """
    Copy a converted key to ~/.ssh with specified conflict handling.
    
    Args:
        source_file: Path to converted OpenSSH key file
        mode: How to handle conflicts:
            - "rename": Add numeric suffix (oracle → oracle.1)
            - "overwrite": Replace existing (creates .bak backup)
            - "skip": Don't copy if file exists
            
    Returns:
        Dictionary with copy result:
        {
            'success': bool,
            'source': str,
            'destination': str,
            'action': 'copied'|'renamed'|'skipped'|'overwritten',
            'backup': str (only for overwrite mode)
        }
        
    Example:
        result = await copy_key_to_ssh(
            Path("./openssh_keys/oracle"),
            mode="rename"
        )
        print(f"{result['action']}: {result['destination']}")
    """
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(mode=0o700, exist_ok=True)
    
    source_file = Path(source_file)
    dest_path = ssh_dir / source_file.name
    
    # Check if source and destination are the same file
    # This happens when keys are already in ~/.ssh
    if source_file.resolve() == dest_path.resolve():
        return {
            'success': True,
            'source': str(source_file),
            'destination': str(dest_path),
            'action': 'skipped'  # Already in correct location
        }
    
    # Determine if source is public or private key
    is_public = source_file.suffix == ".pub"
    
    # Handle conflicts
    if dest_path.exists():
        if mode == "skip":
            return {
                'success': True,
                'source': str(source_file),
                'destination': str(dest_path),
                'action': 'skipped'
            }
        
        elif mode == "rename":
            # Find next available name
            dest_path = find_next_available_name(dest_path)
            
            # Read source content and write with platform-appropriate line endings
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: source_file.read_text(encoding='utf-8')
            )
            await loop.run_in_executor(
                None,
                lambda: write_key_file(dest_path, content)
            )
            
            # Set appropriate permissions
            if is_public:
                os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
            else:
                os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
            
            return {
                'success': True,
                'source': str(source_file),
                'destination': str(dest_path),
                'action': 'renamed'
            }
        
        elif mode == "overwrite":
            # Create backup first
            backup_path = dest_path.with_suffix(dest_path.suffix + '.bak')
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: shutil.copy2(dest_path, backup_path)
            )
            
            # Read source content and write with platform-appropriate line endings
            content = await loop.run_in_executor(
                None,
                lambda: source_file.read_text(encoding='utf-8')
            )
            await loop.run_in_executor(
                None,
                lambda: write_key_file(dest_path, content)
            )
            
            # Set appropriate permissions
            if is_public:
                os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
            else:
                os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
            
            return {
                'success': True,
                'source': str(source_file),
                'destination': str(dest_path),
                'action': 'overwritten',
                'backup': str(backup_path)
            }
    
    else:
        # No conflict - read source content and write with platform-appropriate line endings
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            lambda: source_file.read_text(encoding='utf-8')
        )
        await loop.run_in_executor(
            None,
            lambda: write_key_file(dest_path, content)
        )
        
        # Set appropriate permissions
        if is_public:
            os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
        else:
            os.chmod(dest_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
        
        return {
            'success': True,
            'source': str(source_file),
            'destination': str(dest_path),
            'action': 'copied'
        }


def get_conversion_summary(results: List[ConversionResult]) -> dict:
    """
    Generate a summary of conversion results.
    
    Args:
        results: List of ConversionResult objects
        
    Returns:
        Dictionary with summary statistics
        
    Example:
        summary = get_conversion_summary(results)
        print(f"Success: {summary['successful']}/{summary['total']}")
    """
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    
    errors = {}
    for r in results:
        if not r.success and r.error:
            errors[r.ppk_file] = r.error
    
    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": (successful / total * 100) if total > 0 else 0,
        "errors": errors
    }
