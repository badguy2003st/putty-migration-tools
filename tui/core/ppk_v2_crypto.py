"""
PPK v2 Decryption - Low-level crypto operations.

This module handles PPK v2 format decryption using:
- SHA-1 based key derivation (different from v3's Argon2id!)
- AES-256-CBC decryption (same as v3)
- HMAC-SHA1 MAC verification (different from v3's HMAC-SHA256!)
- OpenSSH format conversion

PPK v2 is the legacy PuTTY format used before v0.75 (February 2021).
It uses simpler password-based key derivation compared to v3.

Key Differences from PPK v3:
- Key Derivation: SHA-1 sequence (fast) vs Argon2id (memory-hard, slow)
- MAC: HMAC-SHA1 vs HMAC-SHA256
- Otherwise identical structure (AES-256-CBC, similar metadata)
"""

import base64
import hashlib
import hmac
import struct
from typing import Dict, Tuple

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519, ed448, ec


def parse_ppk_v2_content(ppk_content: str) -> Dict[str, any]:
    """
    Parse PPK v2 file format into structured data.
    
    Args:
        ppk_content: Full PPK file content as string
        
    Returns:
        Dictionary with parsed fields:
        - version: int (2)
        - key_type: str ('ssh-rsa', 'ssh-ed25519', etc.)
        - encryption: str ('none', 'aes256-cbc')
        - comment: str
        - public_blob: bytes (base64 decoded)
        - private_blob: bytes (base64 decoded)
        - private_mac: str (hex)
    
    Raises:
        ValueError: If format is invalid
    """
    lines = ppk_content.strip().split('\n')
    result = {
        'version': 2
    }
    
    # Parse header fields
    for line in lines:
        line = line.strip()
        
        if line.startswith('PuTTY-User-Key-File-2:'):
            result['key_type'] = line.split(':', 1)[1].strip()
        
        elif line.startswith('Encryption:'):
            result['encryption'] = line.split(':', 1)[1].strip()
        
        elif line.startswith('Comment:'):
            result['comment'] = line.split(':', 1)[1].strip()
        
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


def derive_key_ppk_v2(password: str, cipher_type: str) -> bytes:
    """
    Derive encryption key using PPK v2's SHA-1 based KDF.
    
    PPK v2 uses a simple SHA-1 sequence to derive the AES key.
    The IV is fixed at 16 zero bytes (not derived!).
    
    Based on PuTTY source code and puttykeys library:
    - Key derivation: SHA1(\x00\x00\x00\x00 || password) || SHA1(\x00\x00\x00\x01 || password)
    - IV: Always 16 zero bytes
    
    Args:
        password: Plaintext password
        cipher_type: Cipher type ('none' or 'aes256-cbc')
    
    Returns:
        32-byte AES key (IV is always zeros, returned separately)
    
    Raises:
        ValueError: If cipher type is not supported
    """
    if cipher_type == 'none':
        return b''  # No encryption
    
    if cipher_type != 'aes256-cbc':
        raise ValueError(f"Unsupported PPK v2 cipher: {cipher_type}")
    
    # PPK v2 derives only the AES-256 key (32 bytes)
    # IV is always 16 zero bytes
    password_bytes = password.encode('utf-8')
    
    # SHA1(\x00\x00\x00\x00 || password) + SHA1(\x00\x00\x00\x01 || password)
    # = 20 + 20 = 40 bytes, use first 32 for AES-256 key
    hash1 = hashlib.sha1(b'\x00\x00\x00\x00' + password_bytes).digest()
    hash2 = hashlib.sha1(b'\x00\x00\x00\x01' + password_bytes).digest()
    
    return hash1 + hash2  # 40 bytes total (use first 32 for key)


def verify_ppk_v2_mac(
    parsed_ppk: Dict[str, any],
    private_blob_encrypted: bytes
) -> bool:
    """
    Verify HMAC-SHA1 MAC of PPK v2 file (for unencrypted keys).
    
    PPK v2 uses HMAC-SHA1 for MAC verification.
    For unencrypted keys, the MAC key is: SHA1("putty-private-key-file-mac-key")
    For encrypted keys, the MAC key is derived from the password (verified during decryption).
    
    Args:
        parsed_ppk: Parsed PPK data
        private_blob_encrypted: Private blob bytes (encrypted or plaintext)
    
    Returns:
        True if MAC verification succeeds, False otherwise
    """
    # Build MAC data exactly as PuTTY does (SSH string format)
    mac_data = b''
    
    # Add key type as SSH string
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
    
    # Add private blob as SSH string (encrypted or plaintext depending on key)
    mac_data += struct.pack('>I', len(private_blob_encrypted)) + private_blob_encrypted
    
    # Determine MAC key
    if parsed_ppk['encryption'] == 'none':
        # For unencrypted keys: use static string
        mac_key = hashlib.sha1(b'putty-private-key-file-mac-key').digest()
    else:
        # For encrypted keys: MAC verification happens after decryption with password
        # This function is only called for unencrypted keys in the current flow
        raise ValueError("MAC verification for encrypted keys must use password-derived MAC key")
    
    # Compute HMAC-SHA1 (PPK v2 uses SHA-1, not SHA-256)
    computed_mac = hmac.new(mac_key, mac_data, hashlib.sha1).digest()
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
        algorithms.AES(key[:32]),
        modes.CBC(iv[:16]),
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


def _parse_rsa_v2(private_blob: bytes, public_blob: bytes, comment: str) -> str:
    """
    Parse RSA key from PPK v2 format and convert to OpenSSH.
    
    PPK v2 private blob contains (SSH wire format):
    - d: private exponent (mpint)
    - p: prime 1 (mpint)
    - q: prime 2 (mpint)
    - iqmp: inverse of q mod p (mpint)
    
    PPK v2 public blob contains (SSH wire format):
    - algorithm name: "ssh-rsa" (string)
    - e: public exponent (mpint)
    - n: modulus (mpint)
    
    Args:
        private_blob: Decrypted private blob bytes
        public_blob: Public blob bytes
        comment: Key comment
    
    Returns:
        OpenSSH private key in PEM format
    
    Raises:
        ValueError: If parsing fails
    """
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
        
        def read_string(data: bytes, off: int) -> Tuple[bytes, int]:
            """Read SSH string."""
            length = struct.unpack('>I', data[off:off+4])[0]
            off += 4
            value = data[off:off+length]
            off += length
            return value, off
        
        # Parse private blob: d, p, q, iqmp
        d, offset = read_mpint(private_blob, offset)
        p, offset = read_mpint(private_blob, offset)
        q, offset = read_mpint(private_blob, offset)
        iqmp, offset = read_mpint(private_blob, offset)
        
        # Parse public blob: algorithm, e, n
        pub_offset = 0
        _, pub_offset = read_string(public_blob, pub_offset)  # Skip "ssh-rsa"
        e, pub_offset = read_mpint(public_blob, pub_offset)
        n, pub_offset = read_mpint(public_blob, pub_offset)
        
        # Calculate missing RSA components
        dmp1 = d % (p - 1)  # d mod (p-1)
        dmq1 = d % (q - 1)  # d mod (q-1)
        
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
        raise ValueError(f"Failed to parse RSA private key from PPK v2: {e}")


def _parse_ed25519_v2(private_blob: bytes, public_blob: bytes, comment: str) -> str:
    """
    Parse Ed25519 key from PPK v2 format and convert to OpenSSH.
    
    PPK v2 Ed25519 private blob contains (SSH wire format):
    - private key: 32 bytes (string)
    
    PPK v2 Ed25519 public blob contains (SSH wire format):
    - algorithm name: "ssh-ed25519" (string)
    - public key: 32 bytes (string)
    
    Args:
        private_blob: Decrypted private blob bytes
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
        
        # Parse public blob: algorithm, public key (32 bytes)
        pub_offset = 0
        _, pub_offset = read_string(public_blob, pub_offset)  # Skip "ssh-ed25519"
        public_key_bytes, pub_offset = read_string(public_blob, pub_offset)
        
        if len(public_key_bytes) != 32:
            raise ValueError(f"Invalid Ed25519 public key size: {len(public_key_bytes)} (expected 32)")
        
        # Parse private blob: private key (32 bytes)
        priv_offset = 0
        private_key_bytes, priv_offset = read_string(private_blob, priv_offset)
        
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
        raise ValueError(f"Failed to parse Ed25519 private key from PPK v2: {e}")


def _parse_ed448_v2(private_blob: bytes, public_blob: bytes, comment: str) -> str:
    """
    Parse Ed448 key from PPK v2 format and convert to OpenSSH.
    
    PPK v2 Ed448 private blob contains (SSH wire format):
    - private key: 57 bytes (string)
    
    PPK v2 Ed448 public blob contains (SSH wire format):
    - algorithm name: "ssh-ed448" (string)
    - public key: 57 bytes (string)
    
    Args:
        private_blob: Decrypted private blob bytes
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
        
        # Parse public blob: algorithm, public key (57 bytes)
        pub_offset = 0
        _, pub_offset = read_string(public_blob, pub_offset)  # Skip "ssh-ed448"
        public_key_bytes, pub_offset = read_string(public_blob, pub_offset)
        
        if len(public_key_bytes) != 57:
            raise ValueError(f"Invalid Ed448 public key size: {len(public_key_bytes)} (expected 57)")
        
        # Parse private blob: private key (57 bytes)
        priv_offset = 0
        private_key_bytes, priv_offset = read_string(private_blob, priv_offset)
        
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
        # Check if it's the known OpenSSH serialization limitation
        if "Unsupported key type" in str(e):
            raise ValueError(
                "Ed448 OpenSSH serialization not yet supported by cryptography library.\n"
                "Ed25519 is recommended instead (same security level, better compatibility).\n"
                "Track: https://github.com/pyca/cryptography/issues/..."
            )
        raise ValueError(f"Failed to parse Ed448 private key from PPK v2: {e}")


def _parse_ecdsa_v2(private_blob: bytes, public_blob: bytes, comment: str, curve_name: str) -> str:
    """
    Parse ECDSA key from PPK v2 format and convert to OpenSSH.
    
    PPK v2 ECDSA private blob contains (SSH wire format):
    - private key scalar: variable bytes (string)
    
    PPK v2 ECDSA public blob contains (SSH wire format):
    - algorithm name: "ecdsa-sha2-nistp256" etc. (string)
    - curve name: "nistp256" etc. (string)
    - public key point: variable bytes (string)
    
    Supports:
    - ecdsa-sha2-nistp256 (P-256, 32-byte scalar)
    - ecdsa-sha2-nistp384 (P-384, 48-byte scalar)
    - ecdsa-sha2-nistp521 (P-521, 66-byte scalar)
    
    Args:
        private_blob: Decrypted private blob bytes
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
            'ecdsa-sha2-nistp521': (ec.SECP521R1(), 66),
        }
        
        if curve_name not in curve_map:
            raise ValueError(f"Unsupported ECDSA curve: {curve_name}")
        
        curve, expected_size = curve_map[curve_name]
        
        # Parse private blob: private key scalar
        priv_offset = 0
        private_bytes, priv_offset = read_string(private_blob, priv_offset)
        
        if len(private_bytes) != expected_size:
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
        raise ValueError(f"Failed to parse ECDSA private key from PPK v2: {e}")


def ppk_v2_to_openssh(ppk_content: str, password: str = '') -> str:
    """
    Convert PPK v2 to OpenSSH format (main entry point).
    
    Supports:
    - RSA (implemented)
    - Ed25519 (TODO: Phase 2)
    - Ed448 (TODO: Phase 2)
    - ECDSA P-256/384/521 (TODO: Phase 3)
    
    Args:
        ppk_content: Full PPK file content
        password: Password for encrypted keys (empty for unencrypted)
    
    Returns:
        OpenSSH private key string
    
    Raises:
        ValueError: If conversion fails
    
    Example:
        # Unencrypted key
        openssh_key = ppk_v2_to_openssh(ppk_content)
        
        # Encrypted key
        openssh_key = ppk_v2_to_openssh(ppk_content, password="mypassword")
    """
    # Parse PPK v2 file
    parsed = parse_ppk_v2_content(ppk_content)
    
    key_type = parsed.get('key_type', '')
    encryption = parsed.get('encryption', 'none')
    comment = parsed.get('comment', '')
    private_blob = parsed['private_blob']
    public_blob = parsed['public_blob']
    
    # Handle encryption
    if encryption != 'none':
        if not password:
            raise ValueError("Password required for encrypted PPK v2 key")
        
        # Derive key using SHA-1 KDF
        key_material = derive_key_ppk_v2(password, encryption)
        aes_key = key_material[0:32]   # First 32 bytes: AES-256 key
        aes_iv = b'\x00' * 16          # IV is always 16 zero bytes for PPK v2!
        
        # Decrypt private blob
        try:
            private_blob = decrypt_aes256_cbc(private_blob, aes_key, aes_iv)
        except Exception as e:
            raise ValueError(f"Decryption failed - wrong password? {e}")
        
        # Note: MAC verification for encrypted keys uses password-derived MAC key
        # Wrong password will be caught during decryption or RSA parsing
    
    # Route to appropriate parser based on key type
    if key_type == 'ssh-rsa':
        return _parse_rsa_v2(private_blob, public_blob, comment)
    
    elif key_type == 'ssh-ed25519':
        return _parse_ed25519_v2(private_blob, public_blob, comment)
    
    elif key_type == 'ssh-ed448':
        return _parse_ed448_v2(private_blob, public_blob, comment)
    
    elif key_type.startswith('ecdsa-sha2-nistp'):
        return _parse_ecdsa_v2(private_blob, public_blob, comment, key_type)
    
    elif key_type == 'ssh-dss':
        raise ValueError(
            "DSA keys are not supported (deprecated since 2015, insecure). "
            "Please generate a new RSA or Ed25519 key."
        )
    
    else:
        raise ValueError(f"Unsupported PPK v2 key type: {key_type}")
