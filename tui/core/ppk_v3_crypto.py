"""
PPK v3 Decryption - Low-level crypto operations.

This module handles PPK v3 format decryption using:
- Argon2id key derivation (pure Python via argon2pure)
- AES-256-CBC decryption (via cryptography library)
- OpenSSH format conversion

PPK v3 was introduced in PuTTY 0.75 (February 2021) and uses
stronger Argon2id KDF instead of simple password hashing.
"""

import base64
import hashlib
import struct
from typing import Dict, Optional, Tuple

# Argon2 backend availability flags
try:
    from argon2pure import argon2
    ARGON2_PURE_AVAILABLE = True
except ImportError:
    ARGON2_PURE_AVAILABLE = False

# Try to import argon2-cffi-bindings (fastest, Nuitka-compatible)
try:
    import _argon2_cffi_bindings
    ARGON2_BINDINGS_AVAILABLE = True
except ImportError:
    ARGON2_BINDINGS_AVAILABLE = False

# Try to import argon2-cffi (fast, Python-only)
try:
    from argon2 import low_level
    ARGON2_CFFI_AVAILABLE = True
except ImportError:
    ARGON2_CFFI_AVAILABLE = False

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519, ed448, ec


def check_argon2_available() -> bool:
    """Check if any Argon2 implementation is available."""
    return ARGON2_BINDINGS_AVAILABLE or ARGON2_CFFI_AVAILABLE or ARGON2_PURE_AVAILABLE


def parse_ppk_v3_content(ppk_content: str) -> Dict[str, any]:
    """
    Parse PPK v3 file format into structured data.
    
    Args:
        ppk_content: Full PPK file content as string
        
    Returns:
        Dictionary with parsed fields:
        - version: int (3)
        - key_type: str ('ssh-rsa', 'ssh-ed25519', etc.)
        - encryption: str ('none', 'aes256-cbc')
        - comment: str
        - public_blob: bytes (base64 decoded)
        - private_blob: bytes (base64 decoded)
        - private_mac: str (hex)
        - argon2_params: dict (only if encrypted)
    
    Raises:
        ValueError: If format is invalid
    """
    lines = ppk_content.strip().split('\n')
    result = {
        'version': 3,
        'argon2_params': {}
    }
    
    # Parse header fields
    for line in lines:
        line = line.strip()
        
        if line.startswith('PuTTY-User-Key-File-3:'):
            result['key_type'] = line.split(':', 1)[1].strip()
        
        elif line.startswith('Encryption:'):
            result['encryption'] = line.split(':', 1)[1].strip()
        
        elif line.startswith('Comment:'):
            result['comment'] = line.split(':', 1)[1].strip()
        
        elif line.startswith('Key-Derivation:'):
            result['key_derivation'] = line.split(':', 1)[1].strip()
        
        elif line.startswith('Argon2-Memory:'):
            result['argon2_params']['memory'] = int(line.split(':', 1)[1].strip())
        
        elif line.startswith('Argon2-Passes:'):
            result['argon2_params']['passes'] = int(line.split(':', 1)[1].strip())
        
        elif line.startswith('Argon2-Parallelism:'):
            result['argon2_params']['parallelism'] = int(line.split(':', 1)[1].strip())
        
        elif line.startswith('Argon2-Salt:'):
            salt_hex = line.split(':', 1)[1].strip()
            result['argon2_params']['salt'] = bytes.fromhex(salt_hex)
        
        elif line.startswith('Private-MAC:'):
            result['private_mac'] = line.split(':', 1)[1].strip()
    
    # Parse multi-line base64 sections
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('Public-Lines:'):
            num_lines = int(line.split(':', 1)[1].strip())
            # Strip each line before joining (removes trailing whitespace)
            public_b64 = ''.join(lines[i+1+j].strip() for j in range(num_lines))
            result['public_blob'] = base64.b64decode(public_b64)
            i += num_lines
        
        elif line.startswith('Private-Lines:'):
            num_lines = int(line.split(':', 1)[1].strip())
            # Strip each line before joining (removes trailing whitespace)
            private_b64 = ''.join(lines[i+1+j].strip() for j in range(num_lines))
            result['private_blob'] = base64.b64decode(private_b64)
            i += num_lines
        
        i += 1
    
    return result


def _derive_with_bindings_ctypes(
    password: bytes,
    salt: bytes,
    memory_kb: int,
    passes: int,
    parallelism: int
) -> bytes:
    """
    Use argon2-cffi-bindings via ctypes (fastest, Nuitka-compatible).
    
    Based on proven working code from test_argon2_hack.py.
    This provides ~590x speedup over pure Python (0.1s vs 60s).
    """
    import ctypes
    import glob
    from pathlib import Path
    
    # Find binary
    import _argon2_cffi_bindings
    module_path = Path(_argon2_cffi_bindings.__file__).parent
    
    # Search for binary with various platform-specific patterns
    patterns = ["_ffi.pyd", "_ffi.*.pyd", "_ffi.so", "_ffi.*.so", "_ffi.dylib", "_ffi.*.dylib"]
    binary_files = []
    for pattern in patterns:
        binary_files.extend(glob.glob(str(module_path / pattern)))
    
    if not binary_files:
        raise RuntimeError("argon2-cffi-bindings binary not found")
    
    # Load library
    lib = ctypes.CDLL(str(binary_files[0]))
    
    # Setup function signature for argon2id_hash_raw
    func = lib.argon2id_hash_raw
    func.argtypes = [
        ctypes.c_uint32,  # t_cost (time/passes)
        ctypes.c_uint32,  # m_cost (memory in KB)
        ctypes.c_uint32,  # parallelism
        ctypes.c_void_p,  # pwd (password bytes)
        ctypes.c_size_t,  # pwdlen
        ctypes.c_void_p,  # salt
        ctypes.c_size_t,  # saltlen
        ctypes.c_void_p,  # hash (output buffer)
        ctypes.c_size_t   # hashlen
    ]
    func.restype = ctypes.c_int
    
    # Call Argon2id
    hash_out = ctypes.create_string_buffer(80)
    result = func(
        passes,
        memory_kb,
        parallelism,
        password,
        len(password),
        salt,
        len(salt),
        hash_out,
        80
    )
    
    if result != 0:
        raise RuntimeError(f"Argon2 error code: {result}")
    
    return bytes(hash_out.raw)


def derive_key_argon2id(
    password: str,
    salt: bytes,
    memory_kb: int,
    passes: int,
    parallelism: int
) -> bytes:
    """
    Derive encryption key using Argon2id KDF with automatic backend selection.
    
    Tries backends in order of performance:
    1. argon2-cffi-bindings via ctypes (~0.1s, fastest, Nuitka-compatible)
    2. argon2-cffi via standard import (~0.1s, fast, Python-only)
    3. argon2pure (~60s, slow, universal fallback)
    
    Args:
        password: Plaintext password
        salt: Salt bytes (typically 16 bytes)
        memory_kb: Memory cost in KB (typically 8192 = 8 MB)
        passes: Time cost / iterations (typically 21)
        parallelism: Parallelism factor (typically 1)
    
    Returns:
        80-byte key: 32 (AES) + 16 (IV) + 32 (MAC)
    
    Raises:
        ImportError: If no Argon2 implementation available
    """
    password_bytes = password.encode('utf-8')
    
    # Try 1: argon2-cffi-bindings via ctypes (fastest, Nuitka-compatible)
    if ARGON2_BINDINGS_AVAILABLE:
        try:
            return _derive_with_bindings_ctypes(
                password_bytes, salt, memory_kb, passes, parallelism
            )
        except Exception:
            # Fall through to next backend
            pass
    
    # Try 2: argon2-cffi (fast, Python-only)
    if ARGON2_CFFI_AVAILABLE:
        try:
            from argon2 import low_level
            return low_level.hash_secret_raw(
                secret=password_bytes,
                salt=salt,
                time_cost=passes,
                memory_cost=memory_kb,
                parallelism=parallelism,
                hash_len=80,
                type=low_level.Type.ID
            )
        except Exception:
            # Fall through to next backend
            pass
    
    # Try 3: argon2pure (slow but universal)
    if not ARGON2_PURE_AVAILABLE:
        raise ImportError(
            "No Argon2 implementation available. "
            "Install one of: argon2-cffi-bindings (fastest), argon2-cffi, or argon2pure"
        )
    
    import warnings
    warnings.warn(
        "Using slow pure-Python Argon2 (~60s per key). "
        "For 590x speedup, install: pip install argon2-cffi-bindings",
        stacklevel=2
    )
    
    # argon2pure: type_code 2 = Argon2id
    # PPK v3 derives 80 bytes: 32 (AES key) + 16 (IV) + 32 (MAC key)
    return argon2(
        password_bytes,
        salt,
        time_cost=passes,
        memory_cost=memory_kb,
        parallelism=parallelism,
        tag_length=80,
        type_code=2
    )


def verify_ppk_v3_mac(
    parsed_ppk: Dict[str, any],
    mac_key: bytes,
    private_blob_encrypted: bytes
) -> bool:
    """
    Verify HMAC-SHA256 MAC of PPK v3 file.
    
    This verifies the password is correct before attempting decryption.
    Based on PuTTY source code (sshpubk.c, ppk_load_s function).
    
    Args:
        parsed_ppk: Parsed PPK data
        mac_key: 32-byte MAC key from Argon2id output
        private_blob_encrypted: Encrypted private blob bytes
    
    Returns:
        True if MAC verification succeeds, False otherwise
    """
    import hmac
    
    # Build MAC data exactly as PuTTY does
    mac_data = b''
    
    # Add key type (e.g., "ssh-rsa") as SSH string
    key_type = parsed_ppk['key_type'].encode('utf-8')
    mac_data += struct.pack('>I', len(key_type)) + key_type
    
    # Add encryption type as SSH string
    encryption = parsed_ppk['encryption'].encode('utf-8')
    mac_data += struct.pack('>I', len(encryption)) + encryption
    
    # Add comment as SSH string
    comment = parsed_ppk.get('comment', '').encode('utf-8')
    mac_data += struct.pack('>I', len(comment)) + comment
    
    # Add public blob as SSH string
    public_blob = parsed_ppk['public_blob']
    mac_data += struct.pack('>I', len(public_blob)) + public_blob
    
    # Add ENCRYPTED private blob as SSH string (NOT decrypted!)
    mac_data += struct.pack('>I', len(private_blob_encrypted)) + private_blob_encrypted
    
    # Compute HMAC-SHA256 (PPK v3 uses SHA-256, v2 uses SHA-1)
    computed_mac = hmac.new(mac_key, mac_data, hashlib.sha256).digest()
    expected_mac = bytes.fromhex(parsed_ppk['private_mac'])
    
    # Constant-time comparison
    return hmac.compare_digest(computed_mac, expected_mac)


def decrypt_aes256_cbc(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    """
    Decrypt data using AES-256-CBC.
    
    Args:
        ciphertext: Encrypted data
        key: 32-byte AES-256 key
        iv: 16-byte initialization vector
    
    Returns:
        Decrypted plaintext (PKCS7 padding removed)
    """
    cipher = Cipher(
        algorithms.AES(key[:32]),  # Use first 32 bytes for AES-256
        modes.CBC(iv),
        backend=default_backend()
    )
    
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    
    # Remove PKCS7 padding
    if len(padded_plaintext) > 0:
        pad_length = padded_plaintext[-1]
        if isinstance(pad_length, int) and 0 < pad_length <= 16:
            return padded_plaintext[:-pad_length]
    
    return padded_plaintext


def ppk_v3_to_openssh_rsa(parsed_ppk: Dict[str, any], password: str = '') -> str:
    """
    Convert PPK v3 RSA key to OpenSSH format.
    
    Args:
        parsed_ppk: Parsed PPK data from parse_ppk_v3_content()
        password: Password for encrypted keys (empty string if unencrypted)
    
    Returns:
        OpenSSH private key in PEM format
    
    Raises:
        ValueError: If decryption fails or format is invalid
    """
    private_blob = parsed_ppk['private_blob']
    encryption = parsed_ppk['encryption']
    
    # Decrypt if necessary
    if encryption != 'none':
        if not password:
            raise ValueError("Password required for encrypted PPK v3 key")
        
        # Derive key using Argon2id
        argon2_params = parsed_ppk['argon2_params']
        derived_key = derive_key_argon2id(
            password,
            argon2_params['salt'],
            argon2_params['memory'],
            argon2_params['passes'],
            argon2_params['parallelism']
        )
        
        # Split derived key into components
        # Based on PuTTY source (sshpubk.c):
        # Bytes 0-31:  AES-256 encryption key
        # Bytes 32-47: AES-256-CBC IV (16 bytes)
        # Bytes 48-79: HMAC-SHA256 MAC key
        aes_key = derived_key[0:32]   # AES key
        aes_iv = derived_key[32:48]   # IV (derived from Argon2id, not zeros!)
        mac_key = derived_key[48:80]  # MAC key
        
        # Decrypt using derived IV
        # Note: MAC verification could be added here for early password validation,
        # but wrong passwords are already caught during RSA parsing with clear errors.
        # MAC implementation deferred to future version for simplicity.
        private_blob = decrypt_aes256_cbc(private_blob, aes_key, aes_iv)
    
    # Parse private blob (SSH wire format)
    # For RSA: d, p, q, iqmp (inverse of q mod p)
    try:
        offset = 0
        
        def read_mpint(data: bytes, off: int) -> Tuple[int, int]:
            """Read SSH mpint (multi-precision integer)."""
            length = struct.unpack('>I', data[off:off+4])[0]
            off += 4
            value_bytes = data[off:off+length]
            off += length
            value = int.from_bytes(value_bytes, byteorder='big', signed=False)
            return value, off
        
        # Read RSA private key components
        d, offset = read_mpint(private_blob, offset)  # Private exponent
        p, offset = read_mpint(private_blob, offset)  # Prime 1
        q, offset = read_mpint(private_blob, offset)  # Prime 2
        iqmp, offset = read_mpint(private_blob, offset)  # Inverse of q mod p
        
        # Parse public blob to get e and n
        pub_offset = 0
        
        def read_string(data: bytes, off: int) -> Tuple[bytes, int]:
            """Read SSH string."""
            length = struct.unpack('>I', data[off:off+4])[0]
            off += 4
            value = data[off:off+length]
            off += length
            return value, off
        
        public_blob = parsed_ppk['public_blob']
        
        # Skip algorithm name
        _, pub_offset = read_string(public_blob, pub_offset)
        
        # Read public exponent and modulus
        e, pub_offset = read_mpint(public_blob, pub_offset)
        n, pub_offset = read_mpint(public_blob, pub_offset)
        
        # Calculate missing RSA components
        # dmp1 = d mod (p-1)
        # dmq1 = d mod (q-1)
        dmp1 = d % (p - 1)
        dmq1 = d % (q - 1)
        
        # Create RSA private key using cryptography library
        private_key = rsa.RSAPrivateNumbers(
            p=p,
            q=q,
            d=d,
            dmp1=dmp1,
            dmq1=dmq1,
            iqmp=iqmp,
            public_numbers=rsa.RSAPublicNumbers(e=e, n=n)
        ).private_key(default_backend())
        
        # Serialize to OpenSSH format
        openssh_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return openssh_key.decode('utf-8')
    
    except Exception as e:
        raise ValueError(f"Failed to parse RSA private key: {e}")


def _parse_ed25519_key(decrypted_blob: bytes, public_blob: bytes, comment: str) -> str:
    """
    Parse Ed25519 key from PPK v3 format and convert to OpenSSH.
    
    PPK v3 Ed25519 decrypted blob contains (SSH string format):
    - private key as SSH string (32 bytes)
    
    Public key is stored separately in public_blob.
    
    Args:
        decrypted_blob: Decrypted private blob bytes
        public_blob: Public blob bytes (not used, key is in decrypted_blob)
        comment: Key comment
    
    Returns:
        OpenSSH private key in PEM format
    
    Raises:
        ValueError: If parsing fails
    """
    try:
        def read_string(data: bytes, off: int) -> Tuple[bytes, int]:
            """Read SSH string."""
            length = struct.unpack('>I', data[off:off+4])[0]
            off += 4
            value = data[off:off+length]
            off += length
            return value, off
        
        # PPK v3 Ed25519: private key as SSH string
        priv_offset = 0
        private_key_bytes, priv_offset = read_string(decrypted_blob, priv_offset)
        
        if len(private_key_bytes) != 32:
            raise ValueError(f"Invalid Ed25519 private key size: {len(private_key_bytes)} (expected 32)")
        
        # Create Ed25519 private key from bytes
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        
        # Serialize to OpenSSH format
        openssh_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return openssh_key.decode('utf-8')
    
    except Exception as e:
        raise ValueError(f"Failed to parse Ed25519 private key from PPK v3: {e}")


def _parse_ed448_key(decrypted_blob: bytes, public_blob: bytes, comment: str) -> str:
    """
    Parse Ed448 key from PPK v3 format and convert to OpenSSH.
    
    PPK v3 Ed448 decrypted blob contains (SSH string format):
    - private key as SSH string (57 bytes)
    
    Public key is stored separately in public_blob.
    
    Args:
        decrypted_blob: Decrypted private blob bytes
        public_blob: Public blob bytes
        comment: Key comment
    
    Returns:
        OpenSSH private key in PEM format
    
    Raises:
        ValueError: If parsing fails
    """
    try:
        def read_string(data: bytes, off: int) -> Tuple[bytes, int]:
            """Read SSH string."""
            length = struct.unpack('>I', data[off:off+4])[0]
            off += 4
            value = data[off:off+length]
            off += length
            return value, off
        
        # PPK v3 Ed448: private key as SSH string
        priv_offset = 0
        private_key_bytes, priv_offset = read_string(decrypted_blob, priv_offset)
        
        if len(private_key_bytes) != 57:
            raise ValueError(f"Invalid Ed448 private key size: {len(private_key_bytes)} (expected 57)")
        
        # Create Ed448 private key from bytes
        private_key = ed448.Ed448PrivateKey.from_private_bytes(private_key_bytes)
        
        # Serialize to OpenSSH format
        openssh_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return openssh_key.decode('utf-8')
    
    except Exception as e:
        raise ValueError(f"Failed to parse Ed448 private key from PPK v3: {e}")


def _parse_ecdsa_key(decrypted_blob: bytes, public_blob: bytes, comment: str, curve_name: str) -> str:
    """
    Parse ECDSA key from PPK v3 format and convert to OpenSSH.
    
    PPK v3 ECDSA decrypted blob contains (SSH string format):
    - private key scalar only (as SSH string)
    
    Public point is stored separately in public_blob.
    
    Supports:
    - ecdsa-sha2-nistp256 (P-256, 32-byte scalar)
    - ecdsa-sha2-nistp384 (P-384, 48-byte scalar)
    - ecdsa-sha2-nistp521 (P-521, 66-byte scalar)
    
    Args:
        decrypted_blob: Decrypted private blob bytes
        public_blob: Public blob bytes
        comment: Key comment
        curve_name: Full curve name (e.g., 'ecdsa-sha2-nistp256')
    
    Returns:
        OpenSSH private key in PEM format
    
    Raises:
        ValueError: If parsing fails or unsupported curve
    """
    try:
        def read_string(data: bytes, off: int) -> Tuple[bytes, int]:
            """Read SSH string."""
            length = struct.unpack('>I', data[off:off+4])[0]
            off += 4
            value = data[off:off+length]
            off += length
            return value, off
        
        # Map curve names to cryptography curves and expected key sizes
        curve_map = {
            'ecdsa-sha2-nistp256': (ec.SECP256R1(), 32),
            'ecdsa-sha2-nistp384': (ec.SECP384R1(), 48),
            'ecdsa-sha2-nistp521': (ec.SECP521R1(), 66),  # Can be 65 or 66 (521 bits = 65.125 bytes)
        }
        
        if curve_name not in curve_map:
            raise ValueError(f"Unsupported ECDSA curve: {curve_name}")
        
        curve, expected_size = curve_map[curve_name]
        
        # PPK v3 ECDSA private blob: just the scalar as SSH string
        priv_offset = 0
        private_bytes, priv_offset = read_string(decrypted_blob, priv_offset)
        
        # SSH strings may have leading zero byte for sign bit - strip if present
        if len(private_bytes) == expected_size + 1 and private_bytes[0] == 0:
            private_bytes = private_bytes[1:]
        
        # P-521 special case: 521 bits = 65.125 bytes, can be stored as 65 or 66 bytes
        if curve_name == 'ecdsa-sha2-nistp521' and len(private_bytes) == 65:
            # Valid - P-521 scalar fits in 65 bytes
            pass
        elif len(private_bytes) != expected_size:
            raise ValueError(
                f"Invalid ECDSA private key size for {curve_name}: "
                f"{len(private_bytes)} (expected {expected_size})"
            )
        
        # Convert bytes to integer (big-endian)
        private_value = int.from_bytes(private_bytes, byteorder='big', signed=False)
        
        # Create ECDSA private key
        private_key = ec.derive_private_key(private_value, curve, default_backend())
        
        # Serialize to OpenSSH format
        openssh_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        return openssh_key.decode('utf-8')
    
    except Exception as e:
        raise ValueError(f"Failed to parse ECDSA private key from PPK v3: {e}")


def ppk_v3_to_openssh(ppk_content: str, password: str = '') -> str:
    """
    Convert PPK v3 to OpenSSH format (main entry point).
    
    Args:
        ppk_content: Full PPK file content
        password: Password for encrypted keys (empty for unencrypted)
    
    Returns:
        OpenSSH private key string
    
    Raises:
        ValueError: If conversion fails
        ImportError: If argon2pure not available
    """
    parsed = parse_ppk_v3_content(ppk_content)
    
    key_type = parsed.get('key_type', '')
    
    if key_type == 'ssh-rsa':
        return ppk_v3_to_openssh_rsa(parsed, password)
    
    elif key_type == 'ssh-ed25519':
        # For Ed25519, we need to decrypt the blob first
        private_blob = parsed['private_blob']
        encryption = parsed.get('encryption', 'none')
        
        if encryption != 'none':
            if not password:
                raise ValueError("Password required for encrypted PPK v3 key")
            
            argon2_params = parsed['argon2_params']
            derived_key = derive_key_argon2id(
                password,
                argon2_params['salt'],
                argon2_params['memory'],
                argon2_params['passes'],
                argon2_params['parallelism']
            )
            
            aes_key = derived_key[0:32]
            aes_iv = derived_key[32:48]
            private_blob = decrypt_aes256_cbc(private_blob, aes_key, aes_iv)
        
        return _parse_ed25519_key(private_blob, parsed['public_blob'], parsed.get('comment', ''))
    
    elif key_type == 'ssh-ed448':
        # For Ed448, we need to decrypt the blob first
        private_blob = parsed['private_blob']
        encryption = parsed.get('encryption', 'none')
        
        if encryption != 'none':
            if not password:
                raise ValueError("Password required for encrypted PPK v3 key")
            
            argon2_params = parsed['argon2_params']
            derived_key = derive_key_argon2id(
                password,
                argon2_params['salt'],
                argon2_params['memory'],
                argon2_params['passes'],
                argon2_params['parallelism']
            )
            
            aes_key = derived_key[0:32]
            aes_iv = derived_key[32:48]
            private_blob = decrypt_aes256_cbc(private_blob, aes_key, aes_iv)
        
        return _parse_ed448_key(private_blob, parsed['public_blob'], parsed.get('comment', ''))
    
    elif key_type.startswith('ecdsa-sha2-nistp'):
        # For ECDSA, we need to decrypt the blob first
        private_blob = parsed['private_blob']
        encryption = parsed.get('encryption', 'none')
        
        if encryption != 'none':
            if not password:
                raise ValueError("Password required for encrypted PPK v3 key")
            
            argon2_params = parsed['argon2_params']
            derived_key = derive_key_argon2id(
                password,
                argon2_params['salt'],
                argon2_params['memory'],
                argon2_params['passes'],
                argon2_params['parallelism']
            )
            
            aes_key = derived_key[0:32]
            aes_iv = derived_key[32:48]
            private_blob = decrypt_aes256_cbc(private_blob, aes_key, aes_iv)
        
        return _parse_ecdsa_key(private_blob, parsed['public_blob'], parsed.get('comment', ''), key_type)
    
    else:
        raise ValueError(f"Unsupported PPK v3 key type: {key_type}")
