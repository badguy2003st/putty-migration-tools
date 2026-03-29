"""
Bitwarden Export Module - Generate Bitwarden-compatible SSH Key exports.

This module converts PuTTY sessions with SSH keys to Bitwarden Type 5 (SSH Key)
items for import into Bitwarden vault and use with Bitwarden SSH Agent.

Strategy: puttykeys (PPK parsing) → cryptography (clean OpenSSH) → Bitwarden Type 5
"""

import json
import hashlib
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .registry import PuttySession
import struct


def ensure_clean_openssh_format(openssh_key: str) -> str:
    """
    Ensure SSH key is in a Bitwarden-compatible format.
    
    Bitwarden supports both OpenSSH and traditional PEM formats.
    This function validates the key and optionally re-serializes it.
    
    For unencrypted keys: Re-serializes to clean OpenSSH format
    For encrypted keys or already-valid formats: Returns as-is
    
    Args:
        openssh_key: SSH private key string (OpenSSH or PEM format)
        
    Returns:
        Clean, Bitwarden-compatible SSH private key string
        
    Raises:
        ValueError: If key cannot be validated
        
    Example:
        clean_key = ensure_clean_openssh_format(puttykeys_output)
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        
        key_bytes = openssh_key.encode('utf-8')
        
        # Check if key appears encrypted
        if "ENCRYPTED" in openssh_key or "Proc-Type: 4,ENCRYPTED" in openssh_key:
            # For encrypted keys, just validate format and return as-is
            # Bitwarden can handle encrypted PEM format
            if "BEGIN" in openssh_key and "PRIVATE KEY" in openssh_key:
                return openssh_key
            else:
                raise ValueError("Encrypted key has invalid format")
        
        # Try to parse and re-serialize unencrypted keys
        private_key = None
        
        # Try OpenSSH format first
        try:
            private_key = serialization.load_ssh_private_key(
                key_bytes,
                password=None,
                backend=default_backend()
            )
        except Exception:
            # If OpenSSH format fails, try PEM format (RSA, EC, DSA, etc.)
            try:
                private_key = serialization.load_pem_private_key(
                    key_bytes,
                    password=None,
                    backend=default_backend()
                )
            except Exception:
                # If both fail but key has valid headers, return as-is
                # (Bitwarden may still accept it)
                if "BEGIN" in openssh_key and "PRIVATE KEY" in openssh_key:
                    return openssh_key
                raise ValueError("Could not parse SSH key")
        
        # Successfully parsed - re-serialize to clean OpenSSH format
        if private_key:
            clean_openssh = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.OpenSSH,
                encryption_algorithm=serialization.NoEncryption()
            )
            return clean_openssh.decode('utf-8')
        
        # Fallback: return original if it looks valid
        if "BEGIN" in openssh_key and "PRIVATE KEY" in openssh_key:
            return openssh_key
        
        raise ValueError("Invalid SSH key format")
        
    except Exception as e:
        # If re-serialization fails but key has valid structure, use it anyway
        if "BEGIN" in openssh_key and "PRIVATE KEY" in openssh_key:
            return openssh_key
        raise ValueError(f"Failed to validate SSH key: {str(e)}")


def extract_public_key_from_ppk(ppk_file: Path) -> str:
    """
    Extract public key directly from PPK file.
    
    This is more reliable than extracting from converted OpenSSH keys,
    as puttykeys sometimes produces malformed output.
    
    Args:
        ppk_file: Path to PPK file
        
    Returns:
        OpenSSH format public key string
        
    Raises:
        ValueError: If PPK file cannot be parsed
        
    Example:
        public_key = extract_public_key_from_ppk(Path("mykey.ppk"))
        # Returns: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."
    """
    try:
        ppk_content = ppk_file.read_text(encoding='utf-8')
        
        # Find the Public-Lines section
        lines = ppk_content.split('\n')
        in_public_section = False
        public_lines = []
        
        for line in lines:
            if line.startswith('Public-Lines:'):
                in_public_section = True
                continue
            elif in_public_section:
                if line.startswith('Private-'):
                    break
                if line.strip():
                    public_lines.append(line.strip())
        
        if not public_lines:
            raise ValueError("No public key found in PPK")
        
        # Decode the public key blob
        public_blob = base64.b64decode(''.join(public_lines))
        
        # Parse key type from blob
        offset = 0
        
        # Read key type string length (4 bytes, big-endian)
        type_len = struct.unpack('>I', public_blob[offset:offset+4])[0]
        offset += 4
        
        # Read key type string
        key_type = public_blob[offset:offset+type_len].decode('utf-8')
        
        # Encode back to OpenSSH format
        public_key_b64 = base64.b64encode(public_blob).decode('utf-8')
        
        return f"{key_type} {public_key_b64}"
        
    except Exception as e:
        raise ValueError(f"Failed to extract public key from PPK: {str(e)}")


def extract_public_key_from_private(private_key_content: str) -> str:
    """
    Extract OpenSSH public key from private key.
    
    Uses cryptography library to parse the private key and export
    the corresponding public key in OpenSSH format.
    
    Supports both OpenSSH and PEM format private keys.
    Falls back to using puttykeys if cryptography fails (for malformed keys).
    
    Args:
        private_key_content: Private key string (OpenSSH or PEM format)
        
    Returns:
        OpenSSH format public key string (e.g., "ssh-rsa AAAAB3NzaC1...")
        
    Raises:
        ValueError: If private key cannot be parsed
        
    Example:
        public_key = extract_public_key_from_private(private_key)
        # Returns: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."
    """
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend
        import puttykeys
        
        key_bytes = private_key_content.encode('utf-8')
        private_key = None
        
        # Try OpenSSH format first
        try:
            private_key = serialization.load_ssh_private_key(
                key_bytes,
                password=None,
                backend=default_backend()
            )
        except Exception:
            # Try PEM format (RSA, EC, DSA, etc.)
            try:
                private_key = serialization.load_pem_private_key(
                    key_bytes,
                    password=None,
                    backend=default_backend()
                )
            except Exception:
                # Cryptography failed - try puttykeys' public key extraction
                # (Works even with malformed OpenSSH output from puttykeys)
                try:
                    # puttykeys can extract public key from its own output
                    public_key_bytes = puttykeys.PublicKey.from_string(private_key_content)
                    if public_key_bytes:
                        return public_key_bytes.decode('utf-8').strip()
                except Exception:
                    pass
                
                raise ValueError("Could not parse private key with any method")
        
        if not private_key:
            raise ValueError("Failed to load private key")
        
        # Extract public key
        public_key = private_key.public_key()
        
        # Serialize to OpenSSH format
        public_openssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        
        return public_openssh.decode('utf-8').strip()
        
    except Exception as e:
        raise ValueError(f"Failed to extract public key: {str(e)}")


def calculate_ssh_fingerprint(public_key: str) -> str:
    """
    Calculate SHA256 fingerprint of SSH public key.
    
    This matches the format used by ssh-keygen and Bitwarden.
    
    Args:
        public_key: OpenSSH format public key string
        
    Returns:
        Fingerprint in format "SHA256:base64string"
        
    Raises:
        ValueError: If public key format is invalid
        
    Example:
        fingerprint = calculate_ssh_fingerprint(public_key)
        # Returns: "SHA256:abc123def456..."
    """
    try:
        # Parse public key (format: "ssh-rsa AAAAB3... [comment]")
        parts = public_key.strip().split()
        if len(parts) < 2:
            raise ValueError("Invalid public key format")
        
        # Decode base64 key data (second part)
        key_data = base64.b64decode(parts[1])
        
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(key_data).digest()
        
        # Encode as base64 (without padding)
        fingerprint = base64.b64encode(sha256_hash).decode('utf-8').rstrip('=')
        
        return f"SHA256:{fingerprint}"
        
    except Exception as e:
        raise ValueError(f"Failed to calculate fingerprint: {str(e)}")


def session_to_bitwarden_ssh_key(
    session: PuttySession,
    openssh_key_content: str,
    public_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert PuTTY session + OpenSSH key to Bitwarden Type 5 item.
    
    Bitwarden Type 5 (SSH Key) format:
    - type: 5 (SSH Key item type)
    - name: Display name (e.g., "SSH: servername")
    - notes: Session metadata (host, port, username)
    - privateKey: OpenSSH private key
    - publicKey: Corresponding public key
    - keyFingerprint: SHA256 fingerprint
    
    Args:
        session: PuTTY session object
        openssh_key_content: Clean OpenSSH private key string
        public_key: Optional pre-extracted public key (from .pub file)
        
    Returns:
        Bitwarden SSH Key item dictionary (Type 5)
        
    Raises:
        ValueError: If key extraction/validation fails
        
    Example:
        item = session_to_bitwarden_ssh_key(session, openssh_key)
    """
    # Extract public key if not provided
    if not public_key:
        public_key = extract_public_key_from_private(openssh_key_content)
    
    # Calculate fingerprint
    fingerprint = calculate_ssh_fingerprint(public_key)
    
    # Build notes field with session metadata
    notes_lines = []
    if session.hostname:
        notes_lines.append(f"Host: {session.hostname}")
    if session.port and session.port != 22:
        notes_lines.append(f"Port: {session.port}")
    if session.username:
        notes_lines.append(f"Username: {session.username}")
    
    notes_lines.append("")  # Empty line separator
    notes_lines.append("Imported from PuTTY")
    notes_lines.append(f"Original session: {session.name}")
    
    notes = "\n".join(notes_lines)
    
    # Build Bitwarden Type 5 item
    item = {
        "type": 5,  # SSH Key type
        "name": f"SSH: {session.name}",
        "notes": notes,
        "favorite": False,
        "fields": [],
        "sshKey": {
            "privateKey": openssh_key_content,
            "publicKey": public_key,
            "keyFingerprint": fingerprint
        }
    }
    
    return item


def standalone_key_to_bitwarden_item(
    key_name: str,
    openssh_key_content: str,
    public_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert standalone SSH key to Bitwarden Type 5 item.
    
    Used for SSH keys that don't have an associated PuTTY session.
    
    Args:
        key_name: Name of the key file (without extension)
        openssh_key_content: Clean OpenSSH private key string
        public_key: Optional pre-extracted public key (from .pub file)
        
    Returns:
        Bitwarden SSH Key item dictionary (Type 5)
        
    Raises:
        ValueError: If key extraction/validation fails
        
    Example:
        item = standalone_key_to_bitwarden_item("personal-backup", openssh_key)
    """
    # Extract public key if not provided
    if not public_key:
        public_key = extract_public_key_from_private(openssh_key_content)
    
    # Calculate fingerprint
    fingerprint = calculate_ssh_fingerprint(public_key)
    
    # Build notes for standalone key
    notes = f"Standalone SSH key (no PuTTY session)\n\nImported from: {key_name}.ppk"
    
    # Build Bitwarden Type 5 item
    item = {
        "type": 5,  # SSH Key type
        "name": f"SSH Key: {key_name}",
        "notes": notes,
        "favorite": False,
        "fields": [],
        "sshKey": {
            "privateKey": openssh_key_content,
            "publicKey": public_key,
            "keyFingerprint": fingerprint
        }
    }
    
    return item


def generate_bitwarden_export(
    sessions: List[PuttySession],
    openssh_keys_dir: Path,
    ppk_keys_dir: Optional[Path] = None,
    include_standalone_keys: bool = True
) -> str:
    """
    Generate complete Bitwarden JSON export from PuTTY sessions.
    
    This function reads converted OpenSSH keys from the specified directory
    and generates a Bitwarden-compatible JSON export file with Type 5 items.
    
    Args:
        sessions: List of PuTTY sessions with SSH key authentication
        openssh_keys_dir: Directory containing converted OpenSSH private keys
        ppk_keys_dir: Optional directory containing original PPK files
                     (used to extract public keys if OpenSSH extraction fails)
        include_standalone_keys: Include keys without associated sessions (default: True)
        
    Returns:
        JSON string ready for Bitwarden import via:
        `bw import bitwardenjson bitwarden-export.json`
        
    Raises:
        FileNotFoundError: If OpenSSH key directory doesn't exist
        ValueError: If key conversion/validation fails
        
    Example:
        sessions = read_putty_sessions()
        json_export = generate_bitwarden_export(
            sessions,
            Path("./openssh_keys"),
            Path("./ppk_keys"),
            include_standalone_keys=True
        )
        Path("bitwarden-export.json").write_text(json_export)
    """
    from .auth_detection import detect_auth_method
    import puttykeys
    
    openssh_keys_dir = Path(openssh_keys_dir).resolve()
    
    if not openssh_keys_dir.exists():
        raise FileNotFoundError(
            f"OpenSSH keys directory not found: {openssh_keys_dir}\n"
            "Please convert PPK files to OpenSSH format first."
        )
    
    if ppk_keys_dir:
        ppk_keys_dir = Path(ppk_keys_dir).resolve()
    
    items = []
    skipped = []
    errors = []
    session_key_names = set()  # Track keys used by sessions
    
    for session in sessions:
        # Only process sessions with SSH key authentication
        auth_info = detect_auth_method(session.raw_data)
        if auth_info.method != "key":
            skipped.append((session.name, "Not using SSH key authentication"))
            continue
        
        # Get key filename from PPK path in session data
        key_filename = None
        if auth_info.key_file:
            # Extract base filename without extension
            # "C:\\Keys\\production.ppk" → "production"
            key_filename = Path(auth_info.key_file).stem
        
        if not key_filename:
            # Fallback: try session name directly
            key_filename = session.name
        
        # Look for corresponding OpenSSH key file
        key_file = openssh_keys_dir / key_filename
        
        # Also try with common variations
        if not key_file.exists():
            key_file = openssh_keys_dir / f"{key_filename}.key"
        if not key_file.exists():
            key_file = openssh_keys_dir / f"{key_filename}_id_rsa"
        
        if not key_file.exists():
            skipped.append((session.name, f"Key file '{key_filename}' not found in {openssh_keys_dir}"))
            continue
        
        try:
            # Read the OpenSSH private key
            openssh_key = key_file.read_text(encoding='utf-8')
            
            # Ensure clean format (re-serialize with cryptography)
            openssh_key = ensure_clean_openssh_format(openssh_key)
            
            # Try multiple methods to get public key:
            pub_key_content = None
            
            # Method 1: Extract from PPK file if available (MOST RELIABLE)
            if ppk_keys_dir:
                # Try exact match with session name first
                ppk_file = ppk_keys_dir / f"{session.name}.ppk"
                if not ppk_file.exists():
                    # Try with key_filename
                    ppk_file = ppk_keys_dir / f"{key_filename}.ppk"
                
                if ppk_file.exists():
                    try:
                        # Use direct PPK extraction (more reliable)
                        pub_key_content = extract_public_key_from_ppk(ppk_file)
                    except Exception:
                        pass
            
            # Method 2: Check for .pub file
            if not pub_key_content:
                pub_file = key_file.parent / f"{key_file.name}.pub"
                if pub_file.exists():
                    try:
                        pub_key_content = pub_file.read_text(encoding='utf-8').strip()
                    except Exception:
                        pass
            
            # Convert to Bitwarden Type 5 item
            item = session_to_bitwarden_ssh_key(session, openssh_key, pub_key_content)
            items.append(item)
            
            # Track this key as used by a session
            session_key_names.add(key_filename)
            
        except Exception as e:
            errors.append((session.name, str(e)))
            continue
    
    # Add standalone keys (keys without associated sessions)
    if include_standalone_keys:
        # Find all OpenSSH keys in directory
        for key_file in openssh_keys_dir.iterdir():
            # Skip .pub files
            if key_file.suffix == ".pub":
                continue
            
            # Skip if not a file
            if not key_file.is_file():
                continue
            
            key_name = key_file.stem
            
            # Skip if already exported via session
            if key_name in session_key_names:
                continue
            
            # This is a standalone key - export it!
            try:
                # Read the OpenSSH private key
                openssh_key = key_file.read_text(encoding='utf-8')
                
                # Ensure clean format
                openssh_key = ensure_clean_openssh_format(openssh_key)
                
                # Try to extract public key from PPK file first
                pub_key_content = None
                
                if ppk_keys_dir:
                    ppk_file = ppk_keys_dir / f"{key_name}.ppk"
                    if ppk_file.exists():
                        try:
                            # Use direct PPK extraction (more reliable)
                            pub_key_content = extract_public_key_from_ppk(ppk_file)
                        except Exception:
                            pass
                
                # Fallback: Check for .pub file
                if not pub_key_content:
                    pub_file = key_file.parent / f"{key_file.name}.pub"
                    if pub_file.exists():
                        try:
                            pub_key_content = pub_file.read_text(encoding='utf-8').strip()
                        except Exception:
                            pass
                
                # Convert to Bitwarden Type 5 item
                item = standalone_key_to_bitwarden_item(key_name, openssh_key, pub_key_content)
                items.append(item)
                
            except Exception as e:
                errors.append((f"{key_name} (standalone)", str(e)))
                continue
    
    # Build Bitwarden export format
    export = {
        "encrypted": False,
        "items": items,
        "folders": [],
        "collections": []
    }
    
    # Log summary
    total = len(sessions)
    exported = len(items)
    
    if skipped or errors:
        summary_lines = [f"Export Summary: {exported}/{total} sessions exported"]
        
        if skipped:
            summary_lines.append(f"\nSkipped {len(skipped)} sessions:")
            for name, reason in skipped[:5]:  # Show first 5
                summary_lines.append(f"  - {name}: {reason}")
            if len(skipped) > 5:
                summary_lines.append(f"  ... and {len(skipped) - 5} more")
        
        if errors:
            summary_lines.append(f"\nErrors in {len(errors)} sessions:")
            for name, error in errors[:5]:  # Show first 5
                summary_lines.append(f"  - {name}: {error}")
            if len(errors) > 5:
                summary_lines.append(f"  ... and {len(errors) - 5} more")
        
        # Add summary as a comment in the export
        # (Bitwarden will ignore unknown fields)
        export["_export_summary"] = "\n".join(summary_lines)
    
    return json.dumps(export, indent=2, ensure_ascii=False)


def validate_bitwarden_export(json_str: str) -> tuple[bool, str]:
    """
    Validate a Bitwarden SSH Key export JSON.
    
    Args:
        json_str: JSON export string
        
    Returns:
        Tuple of (is_valid, message)
        
    Example:
        valid, msg = validate_bitwarden_export(json_export)
        if not valid:
            print(f"Validation failed: {msg}")
    """
    try:
        data = json.loads(json_str)
        
        # Check top-level structure
        if "items" not in data:
            return False, "Missing 'items' field"
        
        if not isinstance(data["items"], list):
            return False, "'items' must be a list"
        
        # Validate each SSH Key item
        for i, item in enumerate(data["items"]):
            if not isinstance(item, dict):
                return False, f"Item {i} is not an object"
            
            # Check required fields for Type 5
            if item.get("type") != 5:
                return False, f"Item {i}: type must be 5 (SSH Key)"
            
            # Check for required top-level fields
            if "name" not in item or not item["name"]:
                return False, f"Item {i}: missing or empty 'name' field"
            
            # Check for sshKey nested object (NEW STRUCTURE)
            if "sshKey" not in item:
                return False, f"Item {i}: missing 'sshKey' nested object"
            
            if not isinstance(item["sshKey"], dict):
                return False, f"Item {i}: 'sshKey' must be an object"
            
            ssh_key = item["sshKey"]
            
            # Validate sshKey nested fields
            required_ssh_fields = ["privateKey", "publicKey", "keyFingerprint"]
            for field in required_ssh_fields:
                if field not in ssh_key:
                    return False, f"Item {i}: missing 'sshKey.{field}'"
                if not ssh_key[field]:
                    return False, f"Item {i}: 'sshKey.{field}' is empty"
            
            # Validate key formats (accept both OpenSSH and PEM)
            private_key = ssh_key["privateKey"]
            if not ("BEGIN" in private_key and "PRIVATE KEY" in private_key):
                return False, f"Item {i}: sshKey.privateKey format invalid"
            
            public_key = ssh_key["publicKey"]
            if not (public_key.startswith("ssh-rsa") or 
                    public_key.startswith("ssh-ed25519") or
                    public_key.startswith("ecdsa-")):
                return False, f"Item {i}: sshKey.publicKey format invalid"
            
            fingerprint = ssh_key["keyFingerprint"]
            if not fingerprint.startswith("SHA256:"):
                return False, f"Item {i}: sshKey.keyFingerprint must start with 'SHA256:'"
        
        return True, f"Valid Bitwarden export with {len(data['items'])} SSH key(s)"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
