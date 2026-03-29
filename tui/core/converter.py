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


class ConversionError(Exception):
    """Exception raised when PPK conversion fails."""
    pass


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
    progress_callback: Optional[Callable[[int], None]] = None,
    clean_format: bool = True
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
        
        # Convert using puttykeys library
        # Run in executor since it's CPU-intensive
        # Note: puttykeys expects empty string for unencrypted keys, not None
        passphrase = password if password is not None else ''
        openssh_key = await loop.run_in_executor(
            None,
            lambda: puttykeys.ppkraw_to_openssh(ppk_content, passphrase)
        )
        
        # Check if conversion failed (puttykeys returns None for unsupported keys)
        if openssh_key is None:
            key_type = detect_key_type(ppk_content)
            if key_type == 'ssh-dss':
                error_msg = "DSA keys are not supported (deprecated and insecure). Please generate a new RSA or Ed25519 key."
            elif key_type and key_type not in ['ssh-rsa', 'ssh-ed25519']:
                error_msg = f"Key type '{key_type}' is not supported. Only RSA and Ed25519 keys are supported."
            else:
                error_msg = "Unsupported key type. Only RSA and Ed25519 keys are supported."
            
            return ConversionResult(
                success=False,
                ppk_file=str(ppk_file),
                error=error_msg
            )
        
        if progress_callback:
            progress_callback(70)
        
        # Optional: Re-serialize with cryptography for guaranteed clean format
        # This is important for Bitwarden compatibility
        if clean_format:
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
        
        # Write output file
        await loop.run_in_executor(
            None,
            lambda: output_file.write_text(openssh_key, encoding='utf-8')
        )
        
        # Set secure permissions (600 - owner read/write only)
        os.chmod(output_file, stat.S_IRUSR | stat.S_IWUSR)
        
        if progress_callback:
            progress_callback(100)
        
        return ConversionResult(
            success=True,
            ppk_file=str(ppk_file),
            output_file=str(output_file)
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
        
        # Write public key to file
        await loop.run_in_executor(
            None,
            lambda: output_file.write_text(public_key + "\n", encoding='utf-8')
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
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[ConversionResult]:
    """
    Convert multiple PPK files in batch.
    
    Args:
        ppk_files: List of PPK file paths to convert
        output_dir: Directory for output files
        password: Optional passphrase for encrypted PPK files (same for all)
        progress_callback: Optional callback(current, total, filename)
        
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
        
        # Generate output filename (remove .ppk extension)
        output_name = ppk_file.stem
        output_file = output_dir / output_name
        
        # Convert the file
        result = await convert_ppk_to_openssh(ppk_file, output_file, password)
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
    
    Args:
        base_path: Original file path
        
    Returns:
        Available path (may be same as input if doesn't exist)
        
    Example:
        find_next_available_name(Path("~/.ssh/oracle"))
        # If oracle exists → returns ~/.ssh/oracle.1
        # If oracle.1 exists → returns ~/.ssh/oracle.2
    """
    if not base_path.exists():
        return base_path
    
    counter = 1
    while True:
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
            
            # Copy to new name
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: shutil.copy2(source_file, dest_path)
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
            
            # Now overwrite
            await loop.run_in_executor(
                None,
                lambda: shutil.copy2(source_file, dest_path)
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
        # No conflict - simple copy
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: shutil.copy2(source_file, dest_path)
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
